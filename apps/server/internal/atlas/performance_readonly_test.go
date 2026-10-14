package atlas

import (
	"context"
	"encoding/json"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type performanceStatement struct {
	SQL          string  `json:"sql"`
	Args         []any   `json:"args"`
	Milliseconds float64 `json:"milliseconds"`
}
type performanceDB struct {
	atlasDB
	statements []*performanceStatement
}

func (d *performanceDB) statement(query string, args []any) (*performanceStatement, func()) {
	bound := args
	if len(bound) > 0 {
		if _, ok := bound[0].(pgx.QueryExecMode); ok {
			bound = bound[1:]
		}
	}
	s := &performanceStatement{SQL: query, Args: bound}
	d.statements = append(d.statements, s)
	start := time.Now()
	return s, func() { s.Milliseconds = float64(time.Since(start).Microseconds()) / 1000 }
}

type performanceRow struct {
	pgx.Row
	done func()
}

func (r performanceRow) Scan(values ...any) error { defer r.done(); return r.Row.Scan(values...) }
func (d *performanceDB) QueryRow(ctx context.Context, q string, args ...any) pgx.Row {
	_, done := d.statement(q, args)
	return performanceRow{d.atlasDB.QueryRow(ctx, q, args...), done}
}

type performanceRows struct {
	pgx.Rows
	done func()
}

func (r *performanceRows) finish() {
	if r.done != nil {
		r.done()
		r.done = nil
	}
}
func (r *performanceRows) Close() { r.Rows.Close(); r.finish() }
func (r *performanceRows) Next() bool {
	ok := r.Rows.Next()
	if !ok {
		r.finish()
	}
	return ok
}
func (d *performanceDB) Query(ctx context.Context, q string, args ...any) (pgx.Rows, error) {
	_, done := d.statement(q, args)
	rows, err := d.atlasDB.Query(ctx, q, args...)
	if err != nil {
		done()
		return nil, err
	}
	return &performanceRows{rows, done}, nil
}

// Opt-in audit of existing catalogue rows. No fixtures, schema changes, cache
// flushes or data writes. Plans execute sequentially with one read-only connection.
func TestAtlasPerformanceReadOnly(t *testing.T) {
	dsn, raw, dir := os.Getenv("ARTLINE_READONLY_DATABASE_URL"), os.Getenv("ARTLINE_PERFORMANCE_URL"), os.Getenv("ARTLINE_PERFORMANCE_OUT")
	if dsn == "" || raw == "" || dir == "" {
		t.Skip("read-only DSN, exact URL and audit output directory required")
	}
	u, err := url.Parse(raw)
	if err != nil {
		t.Fatal(err)
	}
	q := u.Query()
	dates := Bounds
	if id := q.Get("preset"); id != "" {
		preset, ok := FindPreset(id)
		if !ok {
			t.Fatal("unknown preset")
		}
		ApplyStartingFilters(q, preset)
		dates = preset.Context
		if q.Get("window") == "period" {
			dates = preset.Period
		}
	}
	integer := func(key string, fallback int) int {
		if !q.Has(key) {
			return fallback
		}
		n, err := strconv.Atoi(q.Get(key))
		if err != nil {
			t.Fatal(err)
		}
		return n
	}
	f := Filter{Range: Range{Start: integer("start", dates.Start), End: integer("end", dates.End)}, PresetID: q.Get("preset"), Query: q.Get("q"), Region: q.Get("region"), CountryScope: q.Get("country_scope"), Creators: q["creator"], Countries: q["country"], Continents: q["continent"], Types: q["type"], Highlights: q.Get("highlights") != "false", Selection: q.Get("selection") == "true" || (q.Get("selection") == "" && len(q["type"]) == 0 && !q.Has("preset") && !q.Has("start") && !q.Has("q") && !q.Has("creator")), Limit: integer("limit", 150), Entities: map[string]url.Values{}, Picks: map[string][]string{}, After: map[string]string{}, NeighborOf: q.Get("neighbor_of"), Direction: q.Get("direction")}
	for kind, fields := range EntityFields {
		v := url.Values{}
		for _, field := range fields {
			if x, ok := q[kind+"_"+field]; ok {
				v[field] = x
			}
		}
		if len(v) > 0 {
			f.Entities[kind] = v
		}
		if ids := q["pick_"+kind]; len(ids) > 0 {
			f.Picks[kind] = ids
		}
		if cursor := q.Get("after_" + kind); cursor != "" {
			f.After[kind] = cursor
		}
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.MaxConns = 1
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	cfg.ConnConfig.RuntimeParams["application_name"] = "artline-performance-review-readonly"
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	db := &performanceDB{atlasDB: tx}
	repo := &Repository{db: db}
	began := time.Now()
	result, callErr := repo.List(ctx, f)
	elapsed := time.Since(began)
	if err = os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	save := func(name string, v any) {
		t.Helper()
		body, e := json.MarshalIndent(v, "", "  ")
		if e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(filepath.Join(dir, name), body, 0600); e != nil {
			t.Fatal(e)
		}
	}
	save("trace.json", db.statements)
	save("filter.json", f)
	save("response.json", result)
	if callErr != nil {
		t.Fatal(callErr)
	}
	t.Logf("total=%d elapsed=%s queries=%d", result.Total, elapsed, len(db.statements))
	for i, s := range db.statements {
		var plan json.RawMessage
		args := append([]any{pgx.QueryExecModeCacheDescribe}, s.Args...)
		if err = tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,SETTINGS,FORMAT JSON) "+s.SQL, args...).Scan(&plan); err != nil {
			t.Fatal(err)
		}
		save("plan-"+strconv.Itoa(i)+".json", plan)
		t.Logf("query %d: %.2fms", i, s.Milliseconds)
	}
}
