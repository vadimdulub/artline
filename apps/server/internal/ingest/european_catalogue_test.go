package ingest

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"

	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

func catalogueFixture(t *testing.T) []byte {
	t.Helper()
	b, e := os.ReadFile("../../../../" + EuropeanCataloguePath)
	if e != nil {
		t.Fatal(e)
	}
	return b
}

func TestEuropeanCatalogueEvidenceAndCutoff(t *testing.T) {
	b := catalogueFixture(t)
	batch, e := catalogueEuropeanBatch(b)
	if e != nil {
		t.Fatal(e)
	}
	var m europeanManifest
	if e = json.Unmarshal(b, &m); e != nil {
		t.Fatal(e)
	}
	seen := map[string]bool{}
	for _, raw := range m.Works {
		var w europeanWork
		if e = json.Unmarshal(raw, &w); e != nil {
			t.Fatal(e)
		}
		key := w.Institution + ":" + w.Accession
		if w.Accession == "" || seen[key] || !europeanAllowedURL(batch.Definitions, w.Institution, w.URL) || batch.Painters[w.Painter] == "" {
			t.Fatal("identity", w.Title)
		}
		seen[key] = true
		d, e := europeanWorkDate(w)
		if e != nil || catalog.CreationScope(d.First, d.Last, d.Precision) != "eligible" {
			t.Fatal("date", w.Title, e)
		}
		if w.Medium == "" || w.Dimensions == "" || w.Publisher == "" {
			t.Fatal("missing technical evidence", w.Title)
		}
		if w.MuseumHighlightURL != "" || (w.Custody != "" && w.Accession != "RF 3745" && w.Accession != "RF 1979 9") {
			t.Fatal("unexpected highlight or loan", w.Title)
		}
		if w.Accession == "NG6700" && w.Dimensions != "96 x 121.2 cm" {
			t.Fatal("wrong Overall measurement")
		}
		if w.Accession == "NG524" && (d.First == nil || *d.First != 1839) {
			t.Fatal("subject year used as creation")
		}
	}
	if len(m.Works) != EuropeanCatalogueWorks || seen["ng:NG224"] {
		t.Fatal("snapshot counts/manual exclusion")
	}
	if _, e = ImportEuropeanCatalogue(context.Background(), nil, append(b, ' '), false); e == nil {
		t.Fatal("changed snapshot accepted")
	}
	if _, e = ImportEuropeanDeep(context.Background(), nil, b, false); e == nil {
		t.Fatal("wrong version accepted")
	}
}

func TestEuropeanCatalogueRollbackReplayAndAPI(t *testing.T) {
	ctx := context.Background()
	pool := deepDB(t)
	batch, e := catalogueEuropeanBatch(catalogueFixture(t))
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
		e = pool.QueryRow(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status) VALUES($1,$2,$2,$2,1100,1970,'Test interval','estimated','review') RETURNING id::text`, "catalogue-test-"+strings.ToLower(qid), qid).Scan(&id)
		if e != nil {
			t.Fatal(e)
		}
		if _, e = pool.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id) VALUES('artist',$1,'wikidata',$2)`, id, qid); e != nil {
			t.Fatal(e)
		}
	}
	if _, e = ImportEuropean(ctx, pool, europeanFixture(t), true); e != nil {
		t.Fatal(e)
	}
	if _, e = ImportEuropeanDeep(ctx, pool, deepFixture(t), true); e != nil {
		t.Fatal(e)
	}
	before := europeanCounts(t, pool)
	preview, e := ImportEuropeanCatalogue(ctx, pool, catalogueFixture(t), false)
	if e != nil {
		t.Fatal(e)
	}
	if preview.Applied || preview.CreatedWorks != EuropeanCatalogueWorks || preview.CreatedMuseums != 1 || europeanCounts(t, pool) != before {
		t.Fatal("preview/duplicates/rollback", preview)
	}
	report, e := ImportEuropeanCatalogue(ctx, pool, catalogueFixture(t), true)
	if e != nil {
		t.Fatal(e)
	}
	var bad int
	e = pool.QueryRow(ctx, `SELECT count(*) FROM artworks a JOIN import_records r ON r.matched_entity_id=a.id AND r.matched_entity_type='artwork' WHERE r.import_job_id=$1 AND (a.status<>'review' OR a.primary_media_id IS NOT NULL OR a.published_at IS NOT NULL OR a.creation_year_end>1970 OR a.medium_text IS NULL OR a.dimensions_text IS NULL OR EXISTS(SELECT 1 FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='display'))`, report.JobID).Scan(&bad)
	if e != nil || bad != 0 {
		t.Fatal("unsafe row", bad, e)
	}
	if _, e = pool.Exec(ctx, `UPDATE artworks SET title='Owner edited',medium_text=NULL WHERE id=$1`, report.Works[0].ID); e != nil {
		t.Fatal(e)
	}
	after := europeanCounts(t, pool)
	again, e := ImportEuropeanCatalogue(ctx, pool, catalogueFixture(t), true)
	if e != nil {
		t.Fatal(e)
	}
	if again.CreatedWorks != 0 || again.EnrichedWorks != 0 || again.AddedCitations != 0 || europeanCounts(t, pool) != after {
		t.Fatal("replay churn")
	}
	var preserved bool
	if e = pool.QueryRow(ctx, `SELECT title='Owner edited' AND medium_text IS NULL FROM artworks WHERE id=$1`, report.Works[0].ID).Scan(&preserved); e != nil || !preserved {
		t.Fatal("editorial change lost", e)
	}
	if _, e = ImportEuropean(ctx, pool, europeanFixture(t), true); e != nil {
		t.Fatal(e)
	}
	if _, e = ImportEuropeanDeep(ctx, pool, deepFixture(t), true); e != nil {
		t.Fatal(e)
	}
	if europeanCounts(t, pool) != after {
		t.Fatal("earlier snapshot replay changed catalogue")
	}
	repo := catalog.NewRepository(pool)
	museum, e := repo.Museum(ctx, "national-gallery-london", true)
	if e != nil || museum.WorkCount != 143 || museum.OnViewCount != 0 {
		t.Fatalf("NG API %+v %v", museum, e)
	}
	museum, e = repo.Museum(ctx, "musee-de-grenoble", true)
	if e != nil || museum.WorkCount != 1 || museum.OnViewCount != 0 {
		t.Fatalf("Grenoble API %+v %v", museum, e)
	}
	var deposits int
	e = pool.QueryRow(ctx, `SELECT count(*) FROM artworks a JOIN artwork_location_assertions l ON l.artwork_id=a.id JOIN institutions i ON i.id=l.institution_id WHERE l.claim_type='holding' AND l.context='loan' AND ((a.accession_number='RF 1979 9' AND i.slug='musee-de-grenoble') OR (a.accession_number='RF 3745' AND i.slug='musee-orsay'))`).Scan(&deposits)
	if e != nil || deposits != 2 {
		t.Fatal("deposits lost", deposits, e)
	}
}
