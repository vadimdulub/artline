package catalog

import (
	"context"
	"encoding/json"
	"os"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
)

func TestMuseumScopedQueryPlan(t *testing.T) {
	db := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if db == "" || os.Getenv("ARTLINE_TEST_QUERY_PLANS") != "1" {
		t.Skip("opt-in database plan test")
	}
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, db)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.Begin(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	// Private temporary tables shadow production on this transaction only.
	_, err = tx.Exec(ctx, `CREATE TEMP TABLE artworks (LIKE public.artworks INCLUDING ALL) ON COMMIT DROP;
 CREATE TEMP TABLE artwork_artists (LIKE public.artwork_artists INCLUDING ALL) ON COMMIT DROP;
 INSERT INTO artworks SELECT (jsonb_populate_record(NULL::artworks,to_jsonb(seed)||jsonb_build_object(
 'id',md5('museum-plan-'||n)::uuid,'slug','museum-plan-'||n,'title','Museum plan '||n,
 'current_institution_id',CASE WHEN n<=500 THEN (SELECT id FROM institutions WHERE slug='the-met') ELSE md5('other-institution-'||n/500)::uuid END))).*
 FROM (SELECT * FROM public.artworks ORDER BY id LIMIT 1) seed CROSS JOIN generate_series(1,100000) n;
 INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role)
 SELECT id,(SELECT id FROM artists WHERE slug='giotto'),'primary' FROM artworks;
 ANALYZE artworks;ANALYZE artwork_artists;`)
	if err != nil {
		t.Fatal(err)
	}
	var b []byte
	if err = tx.QueryRow(ctx, `EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON) `+museumScopedCTE+`SELECT id,title FROM works ORDER BY creation_year_start,title,id LIMIT 25`, true, "the-met").Scan(&b); err != nil {
		t.Fatal(err)
	}
	var data []map[string]any
	if err = json.Unmarshal(b, &data); err != nil {
		t.Fatal(err)
	}
	var walk func(map[string]any)
	scopedIndex := false
	walk = func(node map[string]any) {
		if node["Relation Name"] == "artworks" {
			if node["Node Type"] == "Seq Scan" {
				t.Error("scanned whole artwork catalogue")
			}
			if _, ok := node["Index Name"]; ok {
				scopedIndex = true
			}
		}
		if children, ok := node["Plans"].([]any); ok {
			for _, c := range children {
				walk(c.(map[string]any))
			}
		}
	}
	walk(data[0]["Plan"].(map[string]any))
	if !scopedIndex {
		t.Error("no artwork index used")
	}
	t.Logf("Museum-scoped query on 100,000 temporary artworks: %.3fms; not a full-scale benchmark", data[0]["Execution Time"])
}
