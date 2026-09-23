package atlas

import (
	"context"
	"encoding/json"
	"net/url"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type discoveryStatement struct {
	query string
	args  []any
}
type discoveryPlanDB struct {
	atlasDB
	statements []discoveryStatement
}

func (db *discoveryPlanDB) QueryRow(ctx context.Context, query string, args ...any) pgx.Row {
	db.statements = append(db.statements, discoveryStatement{query, slices.Clone(args)})
	return db.atlasDB.QueryRow(ctx, query, args...)
}

// Existing catalogue records only: no migrations, fixtures or data writes.
func TestDiscoveryFiltersReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue DSN required")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "10000"
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	for _, tc := range []struct {
		name   string
		filter Filter
	}{
		{"japan", Filter{Countries: []string{"japan"}}},
		{"japan-france", Filter{Countries: []string{"japan", "france"}}},
		{"japan-france-asia", Filter{Countries: []string{"japan", "france"}, Continents: []string{"asia"}}},
		{"japan-search", Filter{Countries: []string{"japan"}, Query: "wave"}},
		{"france-highlights", Filter{Countries: []string{"france"}, Highlights: true}},
		{"monet-geography", Filter{Countries: []string{"france"}, Continents: []string{"europe"}, Entities: map[string]url.Values{"artwork": {"painter": {"claude-monet"}, "work_type": {"painting"}}}}},
		{"empty-country", Filter{Countries: []string{"not-a-recorded-country"}}},
		{"full-all", Filter{}},
		{"full-all-images-true", Filter{Entities: map[string]url.Values{"artwork": {"image_only": {"true"}, "popular": {"false"}}}}},
		{"full-all-images-false", Filter{Entities: map[string]url.Values{"artwork": {"image_only": {"false"}}}}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			// A stable snapshot makes count/page comparisons independent of parallel research.
			tx, err := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback(ctx)
			recorder := &discoveryPlanDB{atlasDB: tx}
			repo := &Repository{db: recorder}
			f := tc.filter
			f.Range, f.Preview, f.Limit = Bounds, true, 30
			started := time.Now()
			data, err := repo.List(ctx, f)
			if err != nil {
				if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" && len(recorder.statements) > 0 {
					statement := recorder.statements[len(recorder.statements)-1]
					raw, _ := json.Marshal(map[string]any{"query": statement.query, "args": statement.args[1:]})
					_ = os.MkdirAll(dir, 0700)
					_ = os.WriteFile(filepath.Join(dir, tc.name+"-failed-query.json"), raw, 0600)
				}
				t.Fatal(err)
			}
			t.Logf("total=%d elapsed=%s", data.Total, time.Since(started))
			if len(data.Lanes) != 3 || len(recorder.statements) != 3 {
				t.Fatal("each lane must load with one bounded query")
			}
			statements := slices.Clone(recorder.statements)
			total := 0
			next := f
			next.After = map[string]string{}
			for _, lane := range data.Lanes {
				total += lane.Total
				if len(lane.Items) > 30 {
					t.Fatal("unbounded detail page")
				}
				// Independently count eligible IDs. Bound geographic discovery before
				// eligibility checks, including when production-place links are used.
				args := []any{pgx.QueryExecModeCacheDescribe, f.Start, f.End, f.Preview, strings.TrimSpace(f.Query), f.Highlights, f.Region}
				entity := entityPredicate(lane.Key, f.Entities[lane.Key], &args)
				if lane.Key == "artwork" {
					entity += ` AND EXISTS(SELECT 1 FROM media_assets image WHERE image.id=a.primary_media_id AND image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$')`
				}
				geo := geographyPredicate(lane.Key, f, &args)
				var expected int
				countQuery := `SELECT count(*) FROM (` + providers[lane.Key].keys + ` AND (` + entity + `) AND (` + geo + `)) eligible`
				if lane.Key == "artwork" && (len(f.Countries) > 0 || len(f.Continents) > 0) {
					countQuery = `WITH geographic_artworks AS MATERIALIZED (
 SELECT a.id,a.status,a.date_precision,a.creation_year_start,a.creation_year_end,a.title,a.unlinked_creator_label
 FROM artworks a WHERE (` + entity + `) AND (` + geo + `))
 SELECT count(*) FROM (` + strings.Replace(providers[lane.Key].keys, " FROM artworks a WHERE", " FROM geographic_artworks a WHERE", 1) + `) eligible`
				}
				if err := tx.QueryRow(ctx, countQuery, args...).Scan(&expected); err != nil {
					t.Fatal(err)
				}
				if lane.Total != expected {
					t.Fatalf("%s count %d != %d", lane.Key, lane.Total, expected)
				}
				if tc.name == "japan" && lane.Total == 0 {
					t.Fatalf("expected existing Japanese %s", lane.Key)
				}
				seen := map[string]bool{}
				for _, item := range lane.Items {
					if item.Type != lane.Key || seen[item.ID] || item.EndYear < item.StartYear {
						t.Fatalf("invalid item: %+v", item)
					}
					seen[item.ID] = true
				}
				if lane.Mode == "density" && (lane.Total <= 60 || len(lane.Density) == 0) {
					t.Fatal("density missing or mismatched")
				}
				if lane.Mode == "individual" && len(lane.Density) != 0 {
					t.Fatal("individual lane returned density")
				}
				if lane.NextCursor != "" {
					next.After[lane.Key] = lane.NextCursor
				}
			}
			if total != data.Total {
				t.Fatal("lane total mismatch")
			}
			if len(next.After) > 0 {
				page, err := repo.List(ctx, next)
				if err != nil {
					t.Fatal(err)
				}
				if len(page.Lanes) != 3 || page.Total != data.Total {
					t.Fatal("pagination changed scope")
				}
				for i, lane := range page.Lanes {
					previous := data.Lanes[i]
					if lane.Total != previous.Total || !slices.Equal(lane.Density, previous.Density) {
						t.Fatal("pagination changed lane aggregates")
					}
					if previous.NextCursor == "" {
						continue
					}
					if len(lane.Items) == 0 || len(lane.Items) > f.Limit {
						t.Fatal("missing or unbounded next page")
					}
					last := previous.Items[len(previous.Items)-1]
					for _, item := range lane.Items {
						if item.StartYear < last.StartYear || item.StartYear == last.StartYear && item.ID <= last.ID {
							t.Fatal("page is duplicated or out of order")
						}
						last = item
					}
				}
			}

			if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" {
				if err := os.MkdirAll(dir, 0700); err != nil {
					t.Fatal(err)
				}
				for index, statement := range statements {
					var plan []byte
					if err := tx.QueryRow(ctx, `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) `+statement.query, statement.args...).Scan(&plan); err != nil {
						t.Fatal(err)
					}
					if !json.Valid(plan) {
						t.Fatal("invalid query plan")
					}
					if tc.name == "monet-geography" && index == 0 && (!strings.Contains(string(plan), "artwork_artists_artist_work_idx") || !strings.Contains(string(plan), "artworks_pkey")) {
						t.Fatal("selected painter lost indexed artwork lookups")
					}
					if err := os.WriteFile(filepath.Join(dir, tc.name+"-"+Definitions[index].Key+".json"), plan, 0600); err != nil {
						t.Fatal(err)
					}
				}
			}
		})
	}
}
