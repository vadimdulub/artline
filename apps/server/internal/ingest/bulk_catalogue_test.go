package ingest

import (
	"context"
	"encoding/json"
	"testing"
)

func bulkFixture() []byte {
	m := map[string]any{"schema_version": 3, "accessed_on": "2026-09-09", "source": "nga", "revision": ngaBulkRevision, "authors": map[string]any{"99999999": bulkAuthor{ID: "99999999", Name: "Bulk Test Creator", SortName: "Test Creator, Bulk", ActivityStart: 1850, ActivityEnd: 1870, URL: "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/" + ngaBulkRevision + "/data/constituents.csv"}}, "institutions": []any{europeanInstitution{ID: "nga", Name: "National Gallery of Art", Country: "US", City: "Washington, DC", Rights: "CC0 metadata"}}, "works": []any{europeanWork{Painter: "99999999", Title: "Bulk Test Drawing", Institution: "nga", Accession: "TEST.BULK.1", ObjectID: "99999999", URL: "https://www.nga.gov/collection/art-object-page.99999999.html", DateDisplay: "1850", AttributionRole: "primary", WorkType: "drawing", Description: "Museum-sourced description", Medium: "Graphite"}}}
	b, _ := json.Marshal(m)
	return b
}
func TestBulkValidation(t *testing.T) {
	b := bulkFixture()
	if _, e := validateBulk(b, checksum(b)); e != nil {
		t.Fatal(e)
	}
	if _, e := validateBulk(append(b, ' '), checksum(b)); e == nil {
		t.Fatal("changed snapshot")
	}
	for _, change := range []func(map[string]any){
		func(m map[string]any) { m["source"] = "unapproved" },
		func(m map[string]any) { m["works"].([]any)[0].(map[string]any)["date_display"] = "1971" },
		func(m map[string]any) { m["works"].([]any)[0].(map[string]any)["work_type"] = "photograph" },
		func(m map[string]any) { m["works"] = append(m["works"].([]any), m["works"].([]any)[0]) },
	} {
		var m map[string]any
		json.Unmarshal(b, &m)
		change(m)
		bad, _ := json.Marshal(m)
		if _, e := validateBulk(bad, checksum(bad)); e == nil {
			t.Fatal("invalid bulk accepted")
		}
	}
}
func TestBulkRollbackReplayAuthorityAndType(t *testing.T) {
	pool := europeanDB(t)
	ctx := context.Background()
	b := bulkFixture()
	before := europeanCounts(t, pool)
	r, e := ImportBulkCatalogue(ctx, pool, b, checksum(b), false)
	if e != nil || r.Applied || europeanCounts(t, pool) != before {
		t.Fatal("preview", e)
	}
	r, e = ImportBulkCatalogue(ctx, pool, b, checksum(b), true)
	if e != nil {
		t.Fatal(e)
	}
	if r.CreatedArtists != 1 || r.CreatedWorks != 1 {
		t.Fatal(r)
	}
	var good bool
	e = pool.QueryRow(ctx, `SELECT a.work_type='drawing' AND a.status='review' AND a.description_md='Museum-sourced description' AND p.birth_year IS NULL AND p.death_year IS NULL AND p.timeline_basis='activity' FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id JOIN artists p ON p.id=aa.artist_id WHERE a.id=$1`, r.Works[0].ID).Scan(&good)
	if e != nil || !good {
		t.Fatal("wrong type or invented life", e)
	}
	pool.Exec(ctx, `UPDATE artworks SET description_md='Owner edited',medium_text=NULL WHERE id=$1`, r.Works[0].ID)
	after := europeanCounts(t, pool)
	again, e := ImportBulkCatalogue(ctx, pool, b, checksum(b), true)
	if e != nil || !again.Replayed || again.CreatedWorks != 0 || europeanCounts(t, pool) != after {
		t.Fatal("replay mutation", e)
	}
	// Same name with a different authority must never silently become another person.
	var m map[string]any
	json.Unmarshal(b, &m)
	author := m["authors"].(map[string]any)["99999999"].(map[string]any)
	author["ID"] = "99999998"
	m["authors"] = map[string]any{"99999998": author}
	w := m["works"].([]any)[0].(map[string]any)
	w["Painter"] = "99999998"
	bad, _ := json.Marshal(m)
	if _, e = ImportBulkCatalogue(ctx, pool, bad, checksum(bad), true); e == nil {
		t.Fatal("identity collision accepted")
	}
	if europeanCounts(t, pool) != after {
		t.Fatal("collision wrote data")
	}
}

func TestBulkLifeDatesAndReviewedHomonym(t *testing.T) {
	pool := europeanDB(t)
	ctx := context.Background()
	makeData := func(id, name, literal, begin, end string) []byte {
		var m bulkManifest
		if e := json.Unmarshal(bulkFixture(), &m); e != nil {
			t.Fatal(e)
		}
		a := m.Authors["99999999"]
		a.ID = id
		a.Name = name
		a.DateDisplay = literal
		a.SourceBegin = begin
		a.SourceEnd = end
		m.Authors = map[string]bulkAuthor{id: a}
		var w europeanWork
		if e := json.Unmarshal(m.Works[0], &w); e != nil {
			t.Fatal(e)
		}
		w.Painter = id
		w.ObjectID = id
		w.Accession = "BULK-TEST-" + id
		w.URL = "https://www.nga.gov/collection/art-object-page." + id + ".html"
		m.Works = []json.RawMessage{rawJSON(w)}
		return rawJSON(m)
	}
	for _, tc := range []struct{ id, name, literal, begin, end, basis string }{
		{"99999001", "Literal Life Test", "French, 1820 - 1890", "1820", "1890", "life"},
		{"99999002", "Qualified Life Test", "French, c. 1820 - 1890", "1820", "1890", "activity"},
		{"4866", "Master CR", "Netherlandish, active c. 1616", "1536", "1676", "activity"},
		{"37703", "Master CR", "German, active c. 1530 - 1550", "1530", "1550", "activity"},
	} {
		b := makeData(tc.id, tc.name, tc.literal, tc.begin, tc.end)
		r, e := ImportBulkCatalogue(ctx, pool, b, checksum(b), true)
		if e != nil || r.CreatedArtists != 1 {
			t.Fatal(tc.id, e)
		}
		var basis string
		if e = pool.QueryRow(ctx, `SELECT a.timeline_basis FROM artists a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artist' WHERE e.scheme='nga-constituent' AND e.external_id=$1`, tc.id).Scan(&basis); e != nil || basis != tc.basis {
			t.Fatal(tc.id, basis, e)
		}
	}
	var distinct int
	if e := pool.QueryRow(ctx, `SELECT count(DISTINCT entity_id) FROM external_identifiers WHERE scheme='nga-constituent' AND external_id IN ('4866','37703')`).Scan(&distinct); e != nil || distinct != 2 {
		t.Fatal("homonyms merged", e)
	}
	// An unrelated third same-name authority is not covered by the exception.
	b := makeData("99999003", "Master CR", "German, active c. 1530 - 1550", "1530", "1550")
	if _, e := ImportBulkCatalogue(ctx, pool, b, checksum(b), true); e == nil {
		t.Fatal("broad homonym bypass")
	}
}
