package catalog

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"path/filepath"
	"testing"
	"time"
)

type museumWorksPlanDB struct {
	pgx.Tx
	t   *testing.T
	n   int
	dir string
}

func (d *museumWorksPlanDB) plan(ctx context.Context, sql string, args []any) {
	d.n++
	var raw []byte
	if err := d.Tx.QueryRow(ctx, "EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON) "+sql, args...).Scan(&raw); err != nil {
		d.t.Fatal(err)
	}
	var p []map[string]any
	if err := json.Unmarshal(raw, &p); err != nil {
		d.t.Fatal(err)
	}
	d.t.Logf("query %d: %.3f ms", d.n, p[0]["Execution Time"])
	if d.dir != "" {
		if err := os.MkdirAll(d.dir, 0700); err != nil {
			d.t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(d.dir, fmt.Sprintf("query-%d.json", d.n)), raw, 0600); err != nil {
			d.t.Fatal(err)
		}
	}
}
func (d *museumWorksPlanDB) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	d.plan(ctx, sql, args)
	return d.Tx.Query(ctx, sql, args...)
}
func (d *museumWorksPlanDB) QueryRow(ctx context.Context, sql string, args ...any) pgx.Row {
	d.plan(ctx, sql, args)
	return d.Tx.QueryRow(ctx, sql, args...)
}

func TestMuseumWorksReadOnlyPlan(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	slug := os.Getenv("ARTLINE_MUSEUM_PLAN_SLUG")
	if dsn == "" || slug == "" {
		t.Skip("opt-in real-catalogue plan audit")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly, IsoLevel: pgx.RepeatableRead})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	db := &museumWorksPlanDB{Tx: tx, t: t, dir: os.Getenv("ARTLINE_MUSEUM_PLAN_DIR")}
	repo := &Repository{db: db}
	result, err := repo.MuseumWorks(ctx, slug, MuseumFilter{Limit: 24})
	if err != nil {
		t.Fatal(err)
	}
	t.Logf("%s: %d works, %d images, %d cards; real-catalogue audit, not a 10-million-row benchmark", slug, result.Total, result.ImageCount, len(result.Items))
}
