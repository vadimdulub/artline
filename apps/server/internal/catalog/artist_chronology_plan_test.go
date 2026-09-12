package catalog

import (
	"context"
	"encoding/json"
	"os"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Opt-in planner fixture: temporary tables shadow the real tables on this one
// transaction/connection. No real catalogue rows, audit history or stats change.
// This is a query-plan regression guard, NOT a 10-million-row load benchmark.
func TestArtistChronologyQueryPlan(t *testing.T) {
	url := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if url == "" || os.Getenv("ARTLINE_TEST_QUERY_PLANS") != "1" {
		t.Skip("set database URL and ARTLINE_TEST_QUERY_PLANS=1")
	}
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, url)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.Begin(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	_, err = tx.Exec(ctx, `CREATE TEMP TABLE artworks (
 id uuid PRIMARY KEY,title text,creation_year_start int,creation_year_end int,date_precision text,status text
 ) ON COMMIT DROP;
 CREATE TEMP TABLE artwork_artists(artwork_id uuid,artist_id uuid,attribution_role text,representative_order int) ON COMMIT DROP;
 CREATE INDEX chronology_plan_artist_work_idx ON artwork_artists(artist_id,artwork_id) INCLUDE(attribution_role,representative_order);
 INSERT INTO artworks SELECT md5('plan-work-'||n)::uuid,repeat('fixture ',16)||n,1800+n%100,1800+n%100,'exact','published' FROM generate_series(1,100000) n;
 INSERT INTO artwork_artists SELECT md5('plan-work-'||n)::uuid,md5('plan-artist-'||((n-1)/500))::uuid,'primary',NULL FROM generate_series(1,100000) n;
 ANALYZE artworks; ANALYZE artwork_artists;`)
	if err != nil {
		t.Fatal(err)
	}
	var id string
	if err = tx.QueryRow(ctx, `SELECT md5('plan-artist-0')::uuid::text`).Scan(&id); err != nil {
		t.Fatal(err)
	}
	for name, query := range map[string]string{
		"year-counts": artistWorksCTE + `SELECT chronology_year,count(*) FROM painter_works GROUP BY chronology_year ORDER BY chronology_year NULLS LAST`,
		"first-page":  artistWorksPageQuery,
	} {
		var data []byte
		args := []any{false, id}
		if name == "first-page" {
			args = append(args, nil, false, "", nil, "", "", 25, 0)
		}
		if err = tx.QueryRow(ctx, `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) `+query, args...).Scan(&data); err != nil {
			t.Fatal(err)
		}
		var reports []map[string]any
		if err = json.Unmarshal(data, &reports); err != nil {
			t.Fatal(err)
		}
		painterIndex := false
		var walk func(map[string]any)
		walk = func(node map[string]any) {
			if node["Relation Name"] == "artworks" && node["Node Type"] == "Seq Scan" {
				t.Errorf("%s scanned all artworks", name)
			}
			if node["Index Name"] == "chronology_plan_artist_work_idx" {
				painterIndex = true
				if node["Actual Rows"].(float64) > 500 {
					t.Errorf("artist lookup read too many links: %+v", node)
				}
			}
			if children, ok := node["Plans"].([]any); ok {
				for _, child := range children {
					walk(child.(map[string]any))
				}
			}
		}
		walk(reports[0]["Plan"].(map[string]any))
		if !painterIndex {
			t.Errorf("%s did not use painter index", name)
		}
		t.Logf("%s: 100,000 total artworks, 500 painter links via index, no full artwork scan; core SQL execution %.3f ms", name, reports[0]["Execution Time"])
	}
}
