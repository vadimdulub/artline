package ingest

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"github.com/vadimdulub/artline/apps/server/internal/testdb"
)

func europeanFixture(t *testing.T) []byte {
	t.Helper()
	data, err := os.ReadFile("../../../../docs/research/european-paintings/inventory.json")
	if err != nil {
		t.Fatal(err)
	}
	return data
}
func TestEuropeanSnapshotAndNormalization(t *testing.T) {
	data := europeanFixture(t)
	if checksum(data) != EuropeanSnapshotSHA {
		t.Fatal("snapshot requires explicit review")
	}
	var m europeanManifest
	if err := json.Unmarshal(data, &m); err != nil {
		t.Fatal(err)
	}
	if len(m.Works) != 59 || len(m.Institutions) != 26 {
		t.Fatal("batch size")
	}
	qualified, unknown := 0, 0
	seen := map[string]bool{}
	for _, raw := range m.Works {
		var w europeanWork
		if err := json.Unmarshal(raw, &w); err != nil {
			t.Fatal(err)
		}
		if !europeanURL(w.Institution, w.URL) || seen[w.URL] {
			t.Fatal("URL validation", w.URL)
		}
		seen[w.URL] = true
		d, err := europeanCreationDate(w.DateDisplay)
		if err != nil {
			t.Fatal(err)
		}
		if d.Precision == "unknown" {
			unknown++
		} else if catalog.CreationScope(d.First, d.Last, d.Precision) != "eligible" {
			t.Fatal("cutoff", w.Title)
		}
		r, err := europeanRole(w)
		if err != nil {
			t.Fatal(err)
		}
		if r != "primary" {
			qualified++
		}
	}
	if qualified != 3 || unknown != 1 {
		t.Fatalf("qualifications %d dates %d", qualified, unknown)
	}
	for _, tc := range []struct {
		date        string
		first, last int
		precision   string
	}{
		{"circa 1510 - circa 1516", 1510, 1516, "circa_range"},
		{"Fines del s. XV", 1401, 1500, "century"},
		{"late 1570s", 1570, 1579, "decade"},
		{"1864/65", 1864, 1865, "range"},
		{"entre 1914 et 1926", 1914, 1926, "range"},
	} {
		d, e := europeanCreationDate(tc.date)
		if e != nil || d.First == nil || *d.First != tc.first || *d.Last != tc.last || d.Precision != tc.precision {
			t.Fatalf("date %+v: %+v %v", tc, d, e)
		}
	}
	for _, bad := range []string{"1971", "1900-2000", "1900-1899", "sometime 1882", "Signed 2020", "1899 or 1901"} {
		if _, err := europeanCreationDate(bad); err == nil {
			t.Fatal("invented date", bad)
		}
	}
	for _, bad := range []string{"http://www.nationalgallery.org.uk/a", "https://www.nationalgallery.org.uk.evil.example/a", "https://user@www.nationalgallery.org.uk/a", "https://www.nationalgallery.org.uk:8080/a"} {
		if europeanURL("ng", bad) {
			t.Fatal("unsafe URL", bad)
		}
	}
	if _, err := europeanRole(europeanWork{Attribution: "workshop maybe"}); err == nil {
		t.Fatal("unknown qualification accepted")
	}
	if _, err := ImportEuropean(context.Background(), nil, append(data, ' '), false); err == nil {
		t.Fatal("changed snapshot accepted")
	}
}

func europeanDB(t *testing.T) *pgxpool.Pool {
	t.Helper()
	db := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if db == "" {
		t.Skip("database URL not set")
	}
	pool, err := testdb.Open(t, db)
	if err != nil {
		t.Fatal(err)
	}
	// Prado is an earlier imported institution in the owner's catalogue, not
	// part of the original migrations. Reproduce that precondition explicitly.
	if _, err = pool.Exec(context.Background(), `INSERT INTO institutions(slug,name,normalized_name,website_url)
 VALUES('museo-del-prado','Museo Nacional del Prado','museo nacional del prado','https://www.museodelprado.es')`); err != nil {
		t.Fatal(err)
	}
	for painter, qid := range europeanPainters {
		artistSlug := slug(painter)
		if painter == "Monet" {
			artistSlug = "claude-monet"
		}
		_, err = pool.Exec(context.Background(), `INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status)
 VALUES($1,$2,$2,$2,1400,1950,'Test interval','estimated','review') ON CONFLICT(slug) DO NOTHING`, artistSlug, painter)
		if err != nil {
			t.Fatal(err)
		}
		_, err = pool.Exec(context.Background(), `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id) SELECT 'artist',id,'wikidata',$2 FROM artists WHERE slug=$1 ON CONFLICT DO NOTHING`, artistSlug, qid)
		if err != nil {
			t.Fatal(err)
		}
	}
	if _, err = pool.Exec(context.Background(), `INSERT INTO artist_movements(artist_id,movement_id,role)
 SELECT a.id,m.id,'associated' FROM artists a,movements m WHERE a.slug='pissarro' AND m.slug='impressionism'`); err != nil {
		t.Fatal(err)
	}
	return pool
}
func europeanCounts(t *testing.T, pool *pgxpool.Pool) string {
	t.Helper()
	var result string
	err := pool.QueryRow(context.Background(), `SELECT jsonb_build_array(
 (SELECT count(*) FROM artworks),(SELECT count(*) FROM institutions),(SELECT count(*) FROM places),
 (SELECT count(*) FROM sources),(SELECT count(*) FROM citations),(SELECT count(*) FROM audit_log),
 (SELECT count(*) FROM import_jobs),(SELECT count(*) FROM import_records),(SELECT count(*) FROM media_assets),
 (SELECT count(*) FROM curated_collection_items),(SELECT count(*) FROM artwork_location_assertions),
 (SELECT count(*) FROM institution_venues),(SELECT count(*) FROM artist_movements),
 (SELECT count(*) FROM artist_countries),(SELECT count(*) FROM external_identifiers),
 (SELECT count(*) FROM source_connector_config),(SELECT count(*) FROM editor_accounts),
 (SELECT count(*) FROM curated_collections),(SELECT count(*) FROM source_institutions))::text`).Scan(&result)
	if err != nil {
		t.Fatal(err)
	}
	return result
}
func TestEuropeanTransactionReplayAndAPIs(t *testing.T) {
	ctx := context.Background()
	pool := europeanDB(t)
	data := europeanFixture(t)
	before := europeanCounts(t, pool)
	preview, err := ImportEuropean(ctx, pool, data, false)
	if err != nil {
		t.Fatal(err)
	}
	if preview.Applied || preview.CreatedWorks != 59 || preview.CreatedMuseums != 25 {
		t.Fatalf("preview %+v", preview)
	}
	if europeanCounts(t, pool) != before {
		t.Fatal("dry run persisted data")
	}
	applied, err := ImportEuropean(ctx, pool, data, true)
	if err != nil {
		t.Fatal(err)
	}
	if !applied.Applied || applied.CreatedWorks != 59 || applied.QualifiedWorks != 3 || applied.UnknownDates != 1 || applied.ClassificationChanges != 2 {
		t.Fatalf("applied %+v", applied)
	}
	var unsafe int
	err = pool.QueryRow(ctx, `SELECT count(*) FROM artworks aw WHERE created_by=$1 AND (
 status<>'review' OR published_at IS NOT NULL OR primary_media_id IS NOT NULL OR
 EXISTS(SELECT 1 FROM artwork_location_assertions la WHERE la.artwork_id=aw.id AND la.claim_type='display') OR
 EXISTS(SELECT 1 FROM curated_collection_items ci WHERE ci.artwork_id=aw.id) OR
 EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=aw.id AND aa.representative_order IS NOT NULL))`, europeanActor).Scan(&unsafe)
	if err != nil || unsafe != 0 {
		t.Fatal("publication/media/display/selection leak", unsafe, err)
	}
	_, err = pool.Exec(ctx, `UPDATE artworks SET title='Owner-edited title' WHERE id=$1`, applied.Works[0].ID)
	if err != nil {
		t.Fatal(err)
	}
	after := europeanCounts(t, pool)
	replay, err := ImportEuropean(ctx, pool, data, true)
	if err != nil {
		t.Fatal(err)
	}
	if replay.CreatedWorks != 0 || replay.CreatedMuseums != 0 || replay.ReusedWorks != 59 || replay.AddedCitations != 0 || replay.ClassificationChanges != 0 {
		t.Fatalf("replay %+v", replay)
	}
	if europeanCounts(t, pool) != after {
		t.Fatal("replay not a data/audit no-op")
	}
	var title string
	if err = pool.QueryRow(ctx, `SELECT title FROM artworks WHERE id=$1`, applied.Works[0].ID).Scan(&title); err != nil || title != "Owner-edited title" {
		t.Fatal("overwrote editorial title", err)
	}
	repo := catalog.NewRepository(pool)
	monet, err := repo.ArtistWorks(ctx, "claude-monet", catalog.ArtistWorksFilter{Limit: 60}, true)
	if err != nil || monet.UndatedCount != 1 || monet.Total < 22 {
		t.Fatalf("Monet chronology %+v %v", monet, err)
	}
	p, err := repo.ArtistBySlug(ctx, "pissarro", true)
	if err != nil || p.Movement.Slug != "impressionism" || len(p.Countries) != 1 || p.Countries[0] != "FR" {
		t.Fatalf("Pissarro filters %+v %v", p, err)
	}
	m, err := repo.Museum(ctx, "national-gallery-london", true)
	if err != nil || m.WorkCount != 8 || m.OnViewCount != 0 || m.HighlightCount != 0 || len(m.Venues) != 1 {
		t.Fatalf("museum %+v %v", m, err)
	}
	filtered, err := repo.Museums(ctx, catalog.MuseumFilter{Limit: 60, Artists: []string{"claude-monet", "pissarro"}, Countries: []string{"FR", "GB"}}, true)
	if err != nil || filtered.Total != 8 {
		t.Fatalf("multi-select geography count=%d err=%v", filtered.Total, err)
	}
	public, err := repo.Museums(ctx, catalog.MuseumFilter{Limit: 60}, false)
	if err != nil || public.Total != 0 {
		t.Fatal("public review leak", err)
	}
	if _, err = pool.Exec(ctx, `DELETE FROM artist_movements WHERE artist_id=(SELECT id FROM artists WHERE slug='pissarro')`); err != nil {
		t.Fatal(err)
	}
	replay, err = ImportEuropean(ctx, pool, data, true)
	if err != nil || replay.ClassificationChanges != 0 {
		t.Fatal("replay replaced an intentionally cleared editorial classification", err)
	}
	// Fail late in the batch; any new source/citation changes must roll back.
	_, err = pool.Exec(ctx, `UPDATE artwork_artists SET attribution_role='workshop' WHERE artwork_id=$1`, applied.Works[58].ID)
	if err != nil {
		t.Fatal(err)
	}
	conflictBefore := europeanCounts(t, pool)
	if _, err = ImportEuropean(ctx, pool, data, true); err == nil || !strings.Contains(err.Error(), "conflicts") {
		t.Fatal("attribution collision accepted", err)
	}
	if europeanCounts(t, pool) != conflictBefore {
		t.Fatal("failed transaction partially applied")
	}
}

func TestEuropeanPreexistingMatchAndAmbiguity(t *testing.T) {
	ctx := context.Background()
	pool := europeanDB(t)
	data := europeanFixture(t)
	var existingID string
	err := pool.QueryRow(ctx, `INSERT INTO artworks(slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,current_institution_id,accession_number,status)
 SELECT 'existing-garden','Keep existing title','keep existing title','Existing date',1490,1500,'range','painting',id,'P002823','review' FROM institutions WHERE slug='museo-del-prado' RETURNING id::text`).Scan(&existingID)
	if err != nil {
		t.Fatal(err)
	}
	_, err = pool.Exec(ctx, `INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role) SELECT $1,id,'primary' FROM artists WHERE slug='bosch'`, existingID)
	if err != nil {
		t.Fatal(err)
	}
	r, err := ImportEuropean(ctx, pool, data, true)
	if err != nil {
		t.Fatal(err)
	}
	if r.CreatedWorks != 58 || r.ReusedWorks != 1 || r.Works[19].ID != existingID {
		t.Fatal("accession match failed", r.CreatedWorks, r.ReusedWorks)
	}
	// A URL that points to a second object must not be hidden by LIMIT 1.
	_, err = pool.Exec(ctx, `INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_url,retrieved_at)
 SELECT 'artwork',$1,'identity-conflict',source_id,$2,now() FROM import_jobs WHERE id=$3`, r.Works[0].ID, r.Works[58].URL, r.JobID)
	if err != nil {
		t.Fatal(err)
	}
	before := europeanCounts(t, pool)
	if _, err = ImportEuropean(ctx, pool, data, true); err == nil || !strings.Contains(err.Error(), "ambiguous") {
		t.Fatal("ambiguous identity accepted", err)
	}
	if europeanCounts(t, pool) != before {
		t.Fatal("ambiguous import wrote data")
	}
}

func TestEuropeanMissingAuthorityNoWrites(t *testing.T) {
	ctx := context.Background()
	pool := europeanDB(t)
	_, err := pool.Exec(ctx, `DELETE FROM external_identifiers WHERE scheme='wikidata' AND external_id='Q134741'`)
	if err != nil {
		t.Fatal(err)
	}
	before := europeanCounts(t, pool)
	if _, err = ImportEuropean(ctx, pool, europeanFixture(t), true); err == nil {
		t.Fatal("invented missing painter authority")
	}
	if europeanCounts(t, pool) != before {
		t.Fatal("missing authority wrote data")
	}
}
