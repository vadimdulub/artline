package atlas

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// Audits existing records only. Every connection is forced read-only; this test
// does not create a database, migrate, insert fixtures or use the fixture DSN.
func TestAtlasReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("set ARTLINE_READONLY_DATABASE_URL for a read-only catalogue audit")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "10000"
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	repo := NewRepository(db)
	var before int
	if err = db.QueryRow(ctx, `SELECT count(*) FROM atlas_drafts`).Scan(&before); err != nil {
		t.Fatal(err)
	}
	for _, tc := range []struct {
		name string
		f    Filter
	}{
		{"wwi-highlights", Filter{Range: Range{1910, 1930}, Limit: 60, Highlights: true, Preview: true}},
		{"wwi-all", Filter{Range: Range{1910, 1930}, Limit: 60, Preview: true}},
		{"full-all", Filter{Range: Bounds, Limit: 60, Preview: true}},
		{"eastern-europe", Filter{Range: Range{1800, 1950}, Region: "eastern-europe", Limit: 60, Preview: true}},
		{"creator-search", Filter{Range: Range{1800, 1950}, Query: "Tolstoy", Limit: 60, Preview: true}},
		{"recent", Filter{Range: Range{1999, 2000}, Limit: 60, Preview: true}},
		{"public", Filter{Range: Bounds, Limit: 60}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			started := time.Now()
			out, err := repo.List(ctx, tc.f)
			if err != nil {
				t.Fatal(err)
			}
			t.Logf("total=%d elapsed=%s", out.Total, time.Since(started))
			sum := 0
			for _, lane := range out.Lanes {
				sum += lane.Total
				if len(lane.Items) > 60 {
					t.Fatal("unbounded page")
				}
				ids := map[string]bool{}
				for _, item := range lane.Items {
					if ids[item.ID] || item.Type != lane.Key || item.StartYear > tc.f.End || item.EndYear < tc.f.Start || item.StartYear > item.EndYear || (item.EndYear > lane.Cutoff) {
						t.Fatalf("bad item: %+v", item)
					}
					ids[item.ID] = true
				}
				if lane.NextCursor != "" {
					next := tc.f
					next.After = map[string]string{lane.Key: lane.NextCursor}
					page, err := repo.List(ctx, next)
					if err != nil {
						t.Fatal(err)
					}
					for _, nextLane := range page.Lanes {
						if nextLane.Key != lane.Key {
							continue
						}
						if nextLane.Total != lane.Total {
							t.Fatal("page changed count")
						}
						for _, item := range nextLane.Items {
							if ids[item.ID] {
								t.Fatal("duplicate across pages")
							}
						}
					}
				}
				if lane.Key == "artwork" && len(lane.Items) > 0 {
					visible, err := repo.ArtworkVisible(ctx, lane.Items[0].ID, tc.f.Preview)
					if err != nil || !visible {
						t.Fatal("returned artwork not available", err)
					}
				}
			}
			if sum != out.Total {
				t.Fatal("total mismatch")
			}
			dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR")
			if dir == "" {
				return
			}
			if err = os.MkdirAll(dir, 0700); err != nil {
				t.Fatal(err)
			}
			for kind, p := range providers {
				var plan []byte
				args := []any{pgx.QueryExecModeCacheDescribe, tc.f.Start, tc.f.End, tc.f.Preview, strings.TrimSpace(tc.f.Query), tc.f.Highlights, tc.f.Region}
				if err = db.QueryRow(ctx, `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT count(*) FROM (`+p.keys+`) matching`, args...).Scan(&plan); err != nil {
					t.Fatal(err)
				}
				if !json.Valid(plan) {
					t.Fatal("invalid plan")
				}
				if err = os.WriteFile(filepath.Join(dir, fmt.Sprintf("%s-%s-plan.json", tc.name, kind)), plan, 0600); err != nil {
					t.Fatal(err)
				}
			}
		})
	}
	var after int
	if err = db.QueryRow(ctx, `SELECT count(*) FROM atlas_drafts`).Scan(&after); err != nil {
		t.Fatal(err)
	}
	if before != after {
		t.Fatal("intake count changed during read-only audit")
	}
}

func TestAtlasArtworkPlansReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue audit is opt-in")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	f := Filter{Range: Range{1910, 1930}, Highlights: true, Preview: true, Limit: 60, Types: []string{"artwork"}}
	out, err := NewRepository(pool).List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	if len(out.Lanes[0].Items) == 0 {
		t.Skip("no representative artwork")
	}
	id := out.Lanes[0].Items[0].ID
	p := providers["artwork"]
	for _, tc := range []struct {
		name, sql string
		args      []any
	}{
		{"bounded-artwork-page", `WITH matching AS NOT MATERIALIZED (` + p.keys + `), page AS MATERIALIZED(SELECT * FROM matching WHERE (start_year,id)>($7,$8) ORDER BY start_year,id LIMIT $9) ` + p.details + ` ORDER BY p.start_year,p.id`, []any{pgx.QueryExecModeCacheDescribe, 1910, 1930, true, "", true, "", Bounds.Start - 1, "", 61}},
		{"single-artwork-eligibility", `SELECT EXISTS(SELECT 1` + artScope + ` AND a.id=$7::uuid)`, []any{pgx.QueryExecModeCacheDescribe, Bounds.Start, Bounds.End, true, "", false, "", id}},
		{"single-artwork-detail", `SELECT to_jsonb(a),m.storage_path FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=$1 AND a.status<>'archived'`, []any{id}},
	} {
		var raw []byte
		if err = pool.QueryRow(ctx, `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) `+tc.sql, tc.args...).Scan(&raw); err != nil {
			t.Fatal(err)
		}
		if strings.HasPrefix(tc.name, "single-") && !strings.Contains(string(raw), "artworks_pkey") {
			t.Fatalf("point read lacks artwork PK lookup: %s", raw)
		}
		var decoded []struct {
			ExecutionTime float64 `json:"Execution Time"`
		}
		if err = json.Unmarshal(raw, &decoded); err != nil {
			t.Fatal(err)
		}
		t.Logf("%s: %.2fms", tc.name, decoded[0].ExecutionTime)
		if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" {
			if err = os.WriteFile(filepath.Join(dir, tc.name+"-plan.json"), raw, 0600); err != nil {
				t.Fatal(err)
			}
		}
	}
}

func TestAtlasPickedEntriesReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only audit is opt-in")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 40*time.Second)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	repo := NewRepository(pool)
	initial, err := repo.List(ctx, Filter{Range: Range{1910, 1930}, Limit: 60, Highlights: true, Preview: true})
	if err != nil {
		t.Fatal(err)
	}
	f := Filter{Range: Bounds, Limit: 60, Preview: true, Selection: true, Picks: map[string][]string{}}
	for _, lane := range initial.Lanes {
		if len(lane.Items) > 0 {
			f.Picks[lane.Key] = []string{lane.Items[0].ID}
		}
	}
	selected, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	if selected.Total != len(f.Picks) {
		t.Fatalf("selected %d, wanted %d", selected.Total, len(f.Picks))
	}
	for _, lane := range selected.Lanes {
		if lane.Total != 1 || len(lane.Items) != 1 || lane.Items[0].ID != f.Picks[lane.Key][0] {
			t.Fatalf("selection leaked: %+v", lane)
		}
	}
	f.Types = []string{"book"}
	combined, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	for _, lane := range combined.Lanes {
		if lane.Key == "book" && lane.Total <= 1 {
			t.Fatal("whole layer limited to picked IDs")
		}
		if lane.Key != "book" && lane.Total != 1 {
			t.Fatal("layer changed other types")
		}
	}
	f.Preview = false
	public, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	if public.Total != 0 {
		t.Fatal("current all-review records leaked to public selection")
	}
	f.Types = nil
	f.Picks = nil
	empty, err := repo.List(ctx, f)
	if err != nil || empty.Total != 0 || len(empty.Lanes) != 0 {
		t.Fatal("empty canvas queried a collection", err)
	}
	if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" {
		var plan []byte
		p := providers["artwork"]
		id := initial.Lanes[0].Items[0].ID
		err = pool.QueryRow(ctx, `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT count(*) FROM (`+p.keys+` AND a.id=ANY($7::text[]::uuid[])) matching`, pgx.QueryExecModeCacheDescribe, Bounds.Start, Bounds.End, true, "", false, "", []string{id}).Scan(&plan)
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(string(plan), "artworks_pkey") {
			t.Fatalf("selected IDs lost primary key lookup: %s", plan)
		}
		if err = os.WriteFile(filepath.Join(dir, "picked-artwork-plan.json"), plan, 0600); err != nil {
			t.Fatal(err)
		}
	}
}
