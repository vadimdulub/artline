package catalog

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Opt-in instrumentation of real reads, not a load test or fixture generator.
// Run on a quiet database: this performs the ordinary repository queries once.
type performanceRead struct {
	SQL        string  `json:"sql"`
	Args       []any   `json:"args"`
	DurationMS float64 `json:"duration_ms"`
	Error      string  `json:"error,omitempty"`
}

type performanceDB struct {
	pgx.Tx
	reads []performanceRead
}

func (d *performanceDB) record(sql string, args []any, start time.Time, err error) {
	r := performanceRead{SQL: sql, Args: args, DurationMS: float64(time.Since(start).Microseconds()) / 1000}
	if err != nil {
		r.Error = err.Error()
	}
	d.reads = append(d.reads, r)
}

type performanceRow struct {
	pgx.Row
	db    *performanceDB
	sql   string
	args  []any
	start time.Time
}

func (r performanceRow) Scan(dest ...any) error {
	err := r.Row.Scan(dest...)
	r.db.record(r.sql, r.args, r.start, err)
	return err
}

type performanceRows struct {
	pgx.Rows
	db       *performanceDB
	sql      string
	args     []any
	start    time.Time
	recorded bool
}

func (r *performanceRows) Close() {
	r.Rows.Close()
	if !r.recorded {
		r.recorded = true
		r.db.record(r.sql, r.args, r.start, r.Rows.Err())
	}
}

func (d *performanceDB) QueryRow(ctx context.Context, sql string, args ...any) pgx.Row {
	start := time.Now()
	return performanceRow{d.Tx.QueryRow(ctx, sql, args...), d, sql, args, start}
}

func (d *performanceDB) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	start := time.Now()
	rows, err := d.Tx.Query(ctx, sql, args...)
	if err != nil {
		d.record(sql, args, start, err)
		return nil, err
	}
	return &performanceRows{Rows: rows, db: d, sql: sql, args: args, start: start}, nil
}

func TestCataloguePerformanceReadOnly(t *testing.T) {
	dsn, dir := os.Getenv("ARTLINE_READONLY_DATABASE_URL"), os.Getenv("ARTLINE_PERFORMANCE_DIR")
	if dsn == "" || dir == "" {
		t.Skip("set ARTLINE_READONLY_DATABASE_URL and an output directory outside the repository")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.MaxConns = 1
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	if err = os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	cases := []struct {
		name string
		read func(*Repository) (any, error)
	}{
		{"artist", func(r *Repository) (any, error) { return r.ArtistBySlug(ctx, "rembrandt") }},
		{"artist_works", func(r *Repository) (any, error) { return r.ArtistWorks(ctx, "rembrandt", ArtistWorksFilter{Limit: 24}) }},
		{"artist_directory", func(r *Repository) (any, error) {
			return r.BrowseArtists(ctx, ArtistDirectoryFilter{Sort: "popular", Limit: 24})
		}},
		{"museum", func(r *Repository) (any, error) { return r.Museum(ctx, "the-met") }},
		{"museum_works", func(r *Repository) (any, error) { return r.MuseumWorks(ctx, "the-met", MuseumFilter{Limit: 24}) }},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly})
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback(ctx)
			db := &performanceDB{Tx: tx}
			start := time.Now()
			result, readErr := c.read(&Repository{db: db})
			elapsed := time.Since(start)
			body, err := json.Marshal(result)
			if err != nil {
				t.Fatal(err)
			}
			var fields map[string]json.RawMessage
			if err = json.Unmarshal(body, &fields); err != nil {
				t.Fatal(err)
			}
			sizes := map[string]int{}
			for name, value := range fields {
				sizes[name] = len(value)
			}
			var keyArtwork map[string]json.RawMessage
			if json.Unmarshal(fields["key_artwork"], &keyArtwork) == nil {
				for name, value := range keyArtwork {
					sizes["key_artwork."+name] = len(value)
				}
			}
			report, err := json.MarshalIndent(map[string]any{"reads": db.reads, "elapsed_ms": float64(elapsed.Microseconds()) / 1000, "json_bytes": len(body), "field_bytes": sizes}, "", "  ")
			if err != nil {
				t.Fatal(err)
			}
			if err = os.WriteFile(filepath.Join(dir, c.name+".json"), report, 0600); err != nil {
				t.Fatal(err)
			}
			t.Logf("%d queries, %s, %d JSON bytes (current catalogue only)", len(db.reads), elapsed, len(body))
			if readErr != nil {
				t.Fatal(readErr)
			}
		})
	}
}
