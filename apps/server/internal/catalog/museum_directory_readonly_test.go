package catalog

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// This opt-in audit never uses the fixture database variable and runs every
// query in a read-only repeatable-read transaction against the real catalogue.
func TestMuseumDirectoryReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("ARTLINE_READONLY_DATABASE_URL is not set")
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
	db := &museumDirectoryAuditDB{Tx: tx, t: t, dir: os.Getenv("ARTLINE_DIRECTORY_AUDIT_DIR")}
	repo := &Repository{db: db}
	start := time.Now()
	filter := MuseumFilter{Limit: 5, Countries: []string{"NL"}, Query: "Frans Hals"}
	if os.Getenv("ARTLINE_DIRECTORY_AUDIT_CASE") == "unfiltered" {
		filter = MuseumFilter{Limit: 24}
	}
	if os.Getenv("ARTLINE_DIRECTORY_AUDIT_CASE") == "owner" {
		filter = MuseumFilter{Limit: 5, Selection: "owner"}
	}
	if os.Getenv("ARTLINE_DIRECTORY_AUDIT_CASE") == "maximum" {
		filter = MuseumFilter{Limit: 60}
	}
	if os.Getenv("ARTLINE_DIRECTORY_AUDIT_CASE") == "movement" {
		filter = MuseumFilter{Limit: 5, Movement: "impressionism"}
	}
	if os.Getenv("ARTLINE_DIRECTORY_AUDIT_CASE") == "selection-artist" {
		filter = MuseumFilter{Limit: 5, Selection: "museum", Artist: "rembrandt"}
	}
	page, err := repo.Museums(ctx, filter, true)
	if err != nil {
		t.Fatal(err)
	}
	t.Logf("directory: total=%d items=%d elapsed=%s", page.Total, len(page.Items), time.Since(start))
	if db.dir != "" {
		data, err := json.MarshalIndent(page, "", "  ")
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(db.dir, "response.json"), data, 0600); err != nil {
			t.Fatal(err)
		}
	}
	if os.Getenv("ARTLINE_DIRECTORY_AUDIT_CASE") != "" {
		return
	}
	legacy := &Repository{db: &museumDirectoryLegacyDB{Tx: tx}}
	current := &Repository{db: tx}
	cases := []struct {
		name   string
		filter MuseumFilter
	}{
		{"frans-hals", MuseumFilter{Limit: 5, Countries: []string{"NL"}, Query: "Frans Hals"}},
		{"folkwang", MuseumFilter{Limit: 5, Countries: []string{"DE"}, Query: "Folkwang"}},
		{"dutch", MuseumFilter{Limit: 5, Countries: []string{"NL"}}},
		{"german", MuseumFilter{Limit: 5, Countries: []string{"DE"}}},
		{"both", MuseumFilter{Limit: 5, Countries: []string{"NL", "DE"}}},
		{"unfiltered", MuseumFilter{Limit: 24}},
		{"maximum-page", MuseumFilter{Limit: 60}},
		{"no-match", MuseumFilter{Limit: 5, Query: "no-such-museum-audit-20260917"}},
		{"region", MuseumFilter{Limit: 5, Regions: []string{"western-europe"}}},
		{"highlights", MuseumFilter{Limit: 5, Selection: "museum"}},
		{"owner", MuseumFilter{Limit: 5, Selection: "owner"}},
		{"on-view", MuseumFilter{Limit: 5, Display: "on_view"}},
		{"artist", MuseumFilter{Limit: 5, Artist: "rembrandt"}},
		{"movement", MuseumFilter{Limit: 5, Movement: "impressionism"}},
		{"work-type", MuseumFilter{Limit: 5, WorkTypes: []string{"painting", "drawing"}}},
		{"combined", MuseumFilter{Limit: 5, Countries: []string{"NL", "DE"}, Artist: "rembrandt", Movement: "baroque", WorkType: "painting"}},
		{"selection-artist", MuseumFilter{Limit: 5, Selection: "museum", Artist: "rembrandt"}},
	}
	var summary []map[string]any
	for _, preview := range []bool{true, false} {
		for _, tc := range cases {
			t.Run(fmt.Sprintf("%s/preview-%t", tc.name, preview), func(t *testing.T) {
				start := time.Now()
				before, err := legacy.Museums(ctx, tc.filter, preview)
				if err != nil {
					t.Fatal(err)
				}
				oldDuration := time.Since(start)
				start = time.Now()
				after, err := current.Museums(ctx, tc.filter, preview)
				if err != nil {
					t.Fatal(err)
				}
				newDuration := time.Since(start)
				if !reflect.DeepEqual(before, after) {
					t.Fatal("directory response changed: items, counts, facets or cursor")
				}
				if after.NextCursor != "" {
					next := tc.filter
					next.Cursor = after.NextCursor
					oldNext, err := legacy.Museums(ctx, next, preview)
					if err != nil {
						t.Fatal(err)
					}
					newNext, err := current.Museums(ctx, next, preview)
					if err != nil {
						t.Fatal(err)
					}
					if !reflect.DeepEqual(oldNext, newNext) {
						t.Fatal("keyset page changed")
					}
				}
				t.Logf("total=%d legacy=%s indexed=%s complete response and next page equivalent", after.Total, oldDuration, newDuration)
				summary = append(summary, map[string]any{"case": tc.name, "preview": preview, "total": after.Total,
					"legacy_ms": float64(oldDuration.Microseconds()) / 1000, "indexed_ms": float64(newDuration.Microseconds()) / 1000,
					"equivalent": true, "next_page_checked": after.NextCursor != ""})
			})
		}
	}
	for n := 0; n < 8; n++ {
		requestCtx, requestCancel := context.WithTimeout(ctx, 8*time.Second)
		_, err := current.Museums(requestCtx, cases[n%5].filter, true)
		requestCancel()
		if err != nil {
			t.Fatal(err)
		}
	}
	if db.dir != "" {
		data, err := json.MarshalIndent(summary, "", "  ")
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(db.dir, "comparison.json"), data, 0600); err != nil {
			t.Fatal(err)
		}
	}
}

type museumDirectoryAuditDB struct {
	pgx.Tx
	t   *testing.T
	dir string
	n   int
}

func (d *museumDirectoryAuditDB) plan(ctx context.Context, sql string, args []any) {
	d.n++
	var raw []byte
	if err := d.Tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+sql, args...).Scan(&raw); err != nil {
		d.t.Fatal(err)
	}
	var plan []map[string]any
	if err := json.Unmarshal(raw, &plan); err != nil {
		d.t.Fatal(err)
	}
	d.t.Logf("query %d execution=%vms", d.n, plan[0]["Execution Time"])
	var inspect func(map[string]any)
	inspect = func(node map[string]any) {
		if node["Relation Name"] == "artworks" && node["Actual Loops"].(float64) > 0 {
			if node["Node Type"] == "Seq Scan" {
				d.t.Error("directory scanned the complete artwork table")
			}
			if d.n == 1 && os.Getenv("ARTLINE_DIRECTORY_AUDIT_CASE") == "" && node["Actual Rows"].(float64) > 1 {
				d.t.Error("single-museum existence check did not stop at its first artwork")
			}
		}
		if node["CTE Name"] == "museum_memberships" && d.n != 2 {
			d.t.Error("global membership materialization outside bounded cards")
		}
		if children, ok := node["Plans"].([]any); ok {
			for _, child := range children {
				inspect(child.(map[string]any))
			}
		}
	}
	inspect(plan[0]["Plan"].(map[string]any))
	if d.dir != "" {
		if err := os.MkdirAll(d.dir, 0700); err != nil {
			d.t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(d.dir, fmt.Sprintf("query-%d-plan.json", d.n)), raw, 0600); err != nil {
			d.t.Fatal(err)
		}
	}
}

// Reconstruct the deployed directory queries for exact old/new comparisons in
// the same database snapshot. Detail/card SQL stays identical in both variants.
type museumDirectoryLegacyDB struct{ pgx.Tx }

func legacyDirectorySQL(sql string) string {
	sql = strings.Replace(sql, museumDirectoryCTE, museumCTE, 1)
	if start := strings.Index(sql, ", directory_filter_candidates AS MATERIALIZED ("); start >= 0 {
		end := strings.Index(sql, "/* directory filter end */") + len("/* directory filter end */")
		sql = sql[:start] + sql[end:]
		sql = strings.ReplaceAll(sql, "directory_filtered_memberships", "museum_memberships")
	}
	sql = strings.Replace(sql, museumDirectoryCardCTE, strings.ReplaceAll(museumScopedCTE, "$2", "page.slug"), 1)
	sql = strings.Replace(sql, museumDirectoryCardJSON, museumJSON, 1)
	sql = strings.Replace(sql, museumDirectoryFacetChoicesSQL, museumScopedFacetChoicesSQL, 1)
	return strings.ReplaceAll(sql, " OFFSET 0", "")
}

func (d *museumDirectoryLegacyDB) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	return d.Tx.Query(ctx, legacyDirectorySQL(sql), args...)
}

func (d *museumDirectoryLegacyDB) QueryRow(ctx context.Context, sql string, args ...any) pgx.Row {
	return d.Tx.QueryRow(ctx, legacyDirectorySQL(sql), args...)
}

func (d *museumDirectoryAuditDB) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	d.plan(ctx, sql, args)
	return d.Tx.Query(ctx, sql, args...)
}

func (d *museumDirectoryAuditDB) QueryRow(ctx context.Context, sql string, args ...any) pgx.Row {
	d.plan(ctx, sql, args)
	return d.Tx.QueryRow(ctx, sql, args...)
}
