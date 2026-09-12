package ingest

import (
	"context"
	"encoding/json"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"os"
	"strings"
	"testing"
)

func ngaFixture(t *testing.T) []byte {
	t.Helper()
	b, e := os.ReadFile("../../../../" + NGACataloguePath)
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func TestNGACatalogueEvidence(t *testing.T) {
	data := ngaFixture(t)
	batch, e := ngaCatalogueBatch(data)
	if e != nil {
		t.Fatal(e)
	}
	var m europeanManifest
	if e = json.Unmarshal(data, &m); e != nil {
		t.Fatal(e)
	}
	seen := map[string]bool{}
	for _, raw := range m.Works {
		var w europeanWork
		if e = json.Unmarshal(raw, &w); e != nil {
			t.Fatal(e)
		}
		d, e := europeanWorkDate(w)
		if e != nil || catalog.CreationScope(d.First, d.Last, d.Precision) != "eligible" {
			t.Fatal(w.Title, e)
		}
		if seen[w.ObjectID] || w.Accession == "" || !europeanAllowedURL(batch.Definitions, w.Institution, w.URL) || batch.Painters[w.Painter] == "" || w.AttributionRole != "primary" || w.MuseumHighlightURL != "" {
			t.Fatal("identity/selection", w.Title)
		}
		seen[w.ObjectID] = true
	}
	if len(seen) != 1510 {
		t.Fatal(len(seen))
	}
	if _, e = ImportNGACatalogue(context.Background(), nil, append(data, ' '), false); e == nil {
		t.Fatal("changed snapshot accepted")
	}
}
func TestNGACatalogueRollbackReplayAndMuseum(t *testing.T) {
	pool := europeanDB(t)
	ctx := context.Background()
	data := ngaFixture(t)
	batch, e := ngaCatalogueBatch(data)
	if e != nil {
		t.Fatal(e)
	}
	// Seed migrations have these artists and their NGA works, but not authority
	// IDs. Reproduce the owner's reviewed identities, rather than adding twins.
	for slug, q := range map[string]string{"jan-van-eyck": "Q102272", "leonardo-da-vinci": "Q762"} {
		if _, e = pool.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id) SELECT 'artist',id,'wikidata',$2 FROM artists WHERE slug=$1 ON CONFLICT DO NOTHING`, slug, q); e != nil {
			t.Fatal(e)
		}
	}
	for _, q := range batch.Painters {
		var exists bool
		if e = pool.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM external_identifiers WHERE scheme='wikidata' AND external_id=$1 AND entity_type='artist')`, q).Scan(&exists); e != nil {
			t.Fatal(e)
		}
		if exists {
			continue
		}
		var id string
		e = pool.QueryRow(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status) VALUES($1,$2,$2,$2,1100,1970,'Test interval','estimated','review') RETURNING id::text`, "nga-test-"+strings.ToLower(q), q).Scan(&id)
		if e != nil {
			t.Fatal(e)
		}
		if _, e = pool.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id) VALUES('artist',$1,'wikidata',$2)`, id, q); e != nil {
			t.Fatal(e)
		}
	}
	before := europeanCounts(t, pool)
	preview, e := ImportNGACatalogue(ctx, pool, data, false)
	if e != nil || preview.Applied || europeanCounts(t, pool) != before {
		t.Fatal("rollback", e)
	}
	r, e := ImportNGACatalogue(ctx, pool, data, true)
	if e != nil {
		t.Fatal(e)
	}
	if r.CreatedWorks != 1508 || r.ReusedWorks != 2 {
		t.Fatal(r.CreatedWorks, r.ReusedWorks)
	}
	if _, e = pool.Exec(ctx, `UPDATE artworks SET title='Owner edit',medium_text=NULL WHERE id=$1`, r.Works[0].ID); e != nil {
		t.Fatal(e)
	}
	after := europeanCounts(t, pool)
	again, e := ImportNGACatalogue(ctx, pool, data, true)
	if e != nil || again.CreatedWorks != 0 || again.AddedCitations != 0 || again.EnrichedWorks != 0 || europeanCounts(t, pool) != after {
		t.Fatal("replay", e)
	}
	var good bool
	e = pool.QueryRow(ctx, `SELECT title='Owner edit' AND medium_text IS NULL FROM artworks WHERE id=$1`, r.Works[0].ID).Scan(&good)
	if e != nil || !good {
		t.Fatal("editor changes lost", e)
	}
	museum, e := catalog.NewRepository(pool).Museum(ctx, "national-gallery-of-art", true)
	if e != nil || museum.WorkCount != 1510 || museum.OnViewCount != 0 {
		t.Fatal("museum count", museum.WorkCount, e)
	}
	var unsafe int
	e = pool.QueryRow(ctx, `SELECT count(*) FROM artworks a JOIN import_records r ON r.matched_entity_id=a.id WHERE r.import_job_id=$1 AND (a.status<>'review' OR a.creation_year_end>1970 OR a.published_at IS NOT NULL)`, r.JobID).Scan(&unsafe)
	if e != nil || unsafe != 0 {
		t.Fatal("unsafe", unsafe, e)
	}
}
