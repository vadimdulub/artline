package ingest

import (
	"context"
	"os"
	"strings"
	"testing"
)

func TestEuropeanIdentityQueryPlan(t *testing.T) {
	if os.Getenv("ARTLINE_TEST_QUERY_PLANS") != "1" {
		t.Skip("opt-in isolated 100k-row query-plan fixture")
	}
	ctx := context.Background()
	pool := europeanDB(t)
	report, err := ImportEuropean(ctx, pool, europeanFixture(t), true)
	if err != nil {
		t.Fatal(err)
	}
	// All generated records live in this test's disposable schema, never public.
	_, err = pool.Exec(ctx, `INSERT INTO artworks(slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,current_institution_id,accession_number,status)
 SELECT 'identity-plan-'||n,'Plan fixture','plan fixture','1900',1900,1900,'exact','painting',
 (SELECT id FROM institutions WHERE slug='national-gallery-london'),'plan-'||n,'review' FROM generate_series(1,100000) n;
 INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url)
 SELECT 'artwork',id,'identity-plan',slug,'https://example.invalid/'||slug FROM artworks WHERE slug LIKE 'identity-plan-%';
 INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_url,retrieved_at)
 SELECT 'artwork',id,'plan-fixture',(SELECT id FROM sources WHERE slug='national-gallery-london'),'https://example.invalid/'||slug,now() FROM artworks WHERE slug LIKE 'identity-plan-%';
 ANALYZE artworks; ANALYZE external_identifiers; ANALYZE citations;`)
	if err != nil {
		t.Fatal(err)
	}
	var institution string
	if err = pool.QueryRow(ctx, `SELECT current_institution_id::text FROM artworks WHERE id=$1`, report.Works[0].ID).Scan(&institution); err != nil {
		t.Fatal(err)
	}
	var plan string
	err = pool.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+europeanMatchSQL, "european-ng-object", "NG4744", report.Works[0].URL, institution, "NG4744").Scan(&plan)
	if err != nil {
		t.Fatal(err)
	}
	for _, index := range []string{"external_identifiers_url_idx", "citations_source_url_idx", "artworks_institution_accession_idx"} {
		if !strings.Contains(plan, index) {
			t.Fatalf("exact identity index %s not used: %s", index, plan)
		}
	}
	if strings.Contains(plan, `"Node Type": "Seq Scan"`) {
		t.Fatalf("identity reconciliation scanned catalogue: %s", plan)
	}
	t.Log("100k unrelated artworks + 100k identifiers + 100k citations: all three identity indexes used, no sequential scan. This is not a 10m-row benchmark.")
}
