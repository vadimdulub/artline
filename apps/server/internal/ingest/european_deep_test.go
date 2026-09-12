package ingest

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

func deepFixture(t *testing.T) []byte {
	t.Helper()
	b, e := os.ReadFile("../../../../" + EuropeanDeepPath)
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func deepDB(t *testing.T) *pgxpool.Pool {
	t.Helper()
	pool := europeanDB(t)
	ctx := context.Background()
	batch, e := deepEuropeanBatch(deepFixture(t))
	if e != nil {
		t.Fatal(e)
	}
	for _, qid := range batch.Painters {
		var exists bool
		if e = pool.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=$1)`, qid).Scan(&exists); e != nil {
			t.Fatal(e)
		}
		if exists {
			continue
		}
		var id string
		e = pool.QueryRow(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status)
 VALUES($1,$2,$2,$2,1100,1970,'Test interval','estimated','review') RETURNING id::text`, "deep-test-"+strings.ToLower(qid), qid).Scan(&id)
		if e != nil {
			t.Fatal(e)
		}
		if _, e = pool.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id) VALUES('artist',$1,'wikidata',$2)`, id, qid); e != nil {
			t.Fatal(e)
		}
	}
	return pool
}
func TestEuropeanDeepSnapshot(t *testing.T) {
	b := deepFixture(t)
	batch, e := deepEuropeanBatch(b)
	if e != nil {
		t.Fatal(e)
	}
	var m europeanManifest
	if e = json.Unmarshal(b, &m); e != nil {
		t.Fatal(e)
	}
	unknown, highlights, qualified, rich := 0, 0, 0, 0
	seen := map[string]bool{}
	for _, raw := range m.Works {
		var w europeanWork
		if e = json.Unmarshal(raw, &w); e != nil {
			t.Fatal(e)
		}
		if batch.Painters[w.Painter] == "" || !europeanAllowedURL(batch.Definitions, w.Institution, w.URL) || seen[w.URL] {
			t.Fatal("identity", w.Title)
		}
		seen[w.URL] = true
		d, e := europeanWorkDate(w)
		if e != nil {
			t.Fatal(w.Title, e)
		}
		if d.Precision == "unknown" {
			unknown++
		} else if catalog.CreationScope(d.First, d.Last, d.Precision) != "eligible" {
			t.Fatal("scope", w.Title)
		}
		if _, e = europeanRole(w); e != nil {
			t.Fatal(e)
		}
		if w.Attribution != "" {
			qualified++
		}
		if w.MuseumHighlightURL != "" {
			highlights++
			if !europeanAllowedURL(batch.Definitions, w.Institution, w.MuseumHighlightURL) {
				t.Fatal("designation URL")
			}
		}
		if w.Medium != "" && w.Dimensions != "" {
			rich++
		}
	}
	if len(m.Works) != 157 || len(m.Institutions) != 28 || unknown != 1 || highlights != 17 || qualified != 2 || rich != 157 {
		t.Fatalf("counts works=%d institutions=%d unknown=%d highlights=%d qualified=%d rich=%d", len(m.Works), len(m.Institutions), unknown, highlights, qualified, rich)
	}
	if _, e = ImportEuropeanDeep(context.Background(), nil, append(b, ' '), false); e == nil {
		t.Fatal("accepted changed snapshot")
	}
	if _, e = ImportEuropean(context.Background(), nil, b, false); e == nil {
		t.Fatal("v1 accepted deep snapshot")
	}
	for _, u := range []string{"https://museotik.euskadi.eus.evil.invalid/a", "https://www.nationalgallery.org.uk:443/a", "https://user@www.nationalgallery.org.uk/a"} {
		if europeanAllowedURL(batch.Definitions, "ng", u) {
			t.Fatal("unsafe host")
		}
	}
	a, z := 1500, 1971
	for _, d := range []europeanDate{{&a, &z, "range"}, {&a, &a, "unknown"}, {nil, &a, "range"}, {&a, &a, "before"}, {&a, &a, "fiction"}} {
		if _, e = europeanWorkDate(europeanWork{DateDisplay: "source", CreationDate: &d}); e == nil {
			t.Fatal("invalid structured date", d)
		}
	}
}
func TestEuropeanDeepEnrichmentReplayAndMuseumAPI(t *testing.T) {
	ctx := context.Background()
	pool := deepDB(t)
	if _, e := ImportEuropean(ctx, pool, europeanFixture(t), true); e != nil {
		t.Fatal(e)
	}
	// Preserve nonempty editorial metadata and titles on an exact accession match.
	_, e := pool.Exec(ctx, `UPDATE artworks SET title='Editor water lilies',medium_text='Editor material' WHERE accession_number='NG4240'`)
	if e != nil {
		t.Fatal(e)
	}
	before := europeanCounts(t, pool)
	preview, e := ImportEuropeanDeep(ctx, pool, deepFixture(t), false)
	if e != nil {
		t.Fatal(e)
	}
	if preview.Applied || preview.CreatedWorks != 155 || preview.ReusedWorks != 2 || preview.EnrichedWorks != 2 || preview.AddedHighlights != 17 {
		t.Fatalf("preview %+v", preview)
	}
	if europeanCounts(t, pool) != before {
		t.Fatal("preview leaked mutations")
	}
	report, e := ImportEuropeanDeep(ctx, pool, deepFixture(t), true)
	if e != nil {
		t.Fatal(e)
	}
	var preserved bool
	e = pool.QueryRow(ctx, `SELECT title='Editor water lilies' AND medium_text='Editor material' AND dimensions_text IS NOT NULL FROM artworks WHERE accession_number='NG4240'`).Scan(&preserved)
	if e != nil || !preserved {
		t.Fatal("overwrote existing edit", e)
	}
	var bad int
	e = pool.QueryRow(ctx, `SELECT count(*) FROM artworks a JOIN import_records r ON r.matched_entity_id=a.id AND r.matched_entity_type='artwork'
 WHERE r.import_job_id=$1 AND (a.status<>'review' OR a.primary_media_id IS NOT NULL OR a.published_at IS NOT NULL OR a.medium_text IS NULL OR a.dimensions_text IS NULL OR EXISTS(SELECT 1 FROM artwork_location_assertions la WHERE la.artwork_id=a.id AND la.claim_type='display'))`, report.JobID).Scan(&bad)
	if e != nil || bad != 0 {
		t.Fatal("unsafe imported state", bad, e)
	}
	// Editing/clearing metadata and removing a selected highlight after the batch
	// must survive replay. Count/audit fingerprint includes the deliberate edits.
	_, e = pool.Exec(ctx, `UPDATE artworks SET medium_text=NULL WHERE id=$1;`, report.Works[0].ID)
	if e != nil {
		t.Fatal(e)
	}
	_, e = pool.Exec(ctx, `DELETE FROM curated_collection_items WHERE artwork_id IN (SELECT a.id FROM artworks a WHERE accession_number='NGI.4535')`)
	if e != nil {
		t.Fatal(e)
	}
	after := europeanCounts(t, pool)
	again, e := ImportEuropeanDeep(ctx, pool, deepFixture(t), true)
	if e != nil {
		t.Fatal(e)
	}
	if again.CreatedWorks != 0 || again.EnrichedWorks != 0 || again.AddedHighlights != 0 || again.AddedCitations != 0 || europeanCounts(t, pool) != after {
		t.Fatal("not an audit/data no-op replay")
	}
	var empty bool
	if e = pool.QueryRow(ctx, `SELECT medium_text IS NULL FROM artworks WHERE id=$1`, report.Works[0].ID).Scan(&empty); e != nil || !empty {
		t.Fatal("repopulated cleared field", e)
	}
	// Original snapshot remains valid after enrichment and retains its exact job.
	if _, e = ImportEuropean(ctx, pool, europeanFixture(t), true); e != nil {
		t.Fatal("v1 compatibility", e)
	}
	if europeanCounts(t, pool) != after {
		t.Fatal("v1 replay changed expanded catalogue")
	}
	repo := catalog.NewRepository(pool)
	museum, e := repo.Museum(ctx, "national-gallery-ireland", true)
	if e != nil || museum.WorkCount != 7 || museum.HighlightCount != 6 || museum.OnViewCount != 0 {
		t.Fatalf("Ireland API %+v %v", museum, e)
	}
	_, e = pool.Exec(ctx, `UPDATE artworks SET status='archived' WHERE id=$1`, report.Works[0].ID)
	if e != nil {
		t.Fatal(e)
	}
	before = europeanCounts(t, pool)
	if _, e = ImportEuropeanDeep(ctx, pool, deepFixture(t), true); e == nil {
		t.Fatal("archived record reactivated")
	}
	if europeanCounts(t, pool) != before {
		t.Fatal("failed replay leaked mutations")
	}
}
