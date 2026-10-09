package catalog

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// This audit compares complete responses in a read-only repeatable-read
// transaction. It never uses test fixtures or ARTLINE_TEST_DATABASE_URL.
func TestMuseumOverviewReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("opt-in real-catalogue audit")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
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
	repo := &Repository{db: tx}
	legacy := museumScopedCTE + `SELECT ` + museumJSON + ` FROM institutions i WHERE i.slug=$1 AND ` + museumVisible + ` AND EXISTS(SELECT 1 FROM works w WHERE ` + museumMembership + `)`
	slugs := []string{"national-gallery-of-art", "the-met", "musee-du-louvre", "musee-orsay", "joconde-m5060", "cleveland-museum-of-art", "scrovegni-chapel", "london-museum", "ateneum-art-museum", "no-such-museum-overview-audit"}
	{
		for _, slug := range slugs {
			t.Run(slug, func(t *testing.T) {
				resolved, resolveErr := repo.canonicalMuseumSlug(ctx, slug)
				var expected Museum
				oldErr := resolveErr
				if oldErr == nil {
					var raw []byte
					oldErr = tx.QueryRow(ctx, legacy, museumQueryArgs(resolved)...).Scan(&raw)
					if errors.Is(oldErr, pgx.ErrNoRows) {
						oldErr = ErrNotFound
					} else if oldErr == nil {
						oldErr = json.Unmarshal(raw, &expected)
					}
				}
				start := time.Now()
				actual, gotErr := repo.Museum(ctx, slug)
				if !errors.Is(gotErr, oldErr) || (oldErr != nil && !errors.Is(oldErr, ErrNotFound)) {
					t.Fatalf("overview errors differ: old=%v new=%v", oldErr, gotErr)
				}
				if !reflect.DeepEqual(expected, actual) {
					t.Fatal("overview counts, cover, selections or venue metadata changed")
				}
				t.Logf("%s: %d works, identical response in %s", slug, actual.WorkCount, time.Since(start))
			})
		}
	}
	if dir := os.Getenv("ARTLINE_OVERVIEW_PLAN_DIR"); dir != "" {
		if err := os.MkdirAll(dir, 0700); err != nil {
			t.Fatal(err)
		}
		for _, slug := range slugs[:2] {
			for name, query := range map[string]string{"before": legacy, "after": museumOverviewSQL} {
				var raw []byte
				if err := tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+query, museumQueryArgs(slug)...).Scan(&raw); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(filepath.Join(dir, slug+"-"+name+".json"), raw, 0600); err != nil {
					t.Fatal(err)
				}
				var plan []map[string]any
				if err := json.Unmarshal(raw, &plan); err != nil {
					t.Fatal(err)
				}
				t.Logf("%s %s: %.3fms", slug, name, plan[0]["Execution Time"])
			}
		}
	}
}
