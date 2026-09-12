package ingest

import (
	"context"
	"encoding/json"
	"os"
	"testing"
)

func museumManifest(t *testing.T, key string) []MuseumSelection {
	t.Helper()
	raw, err := os.ReadFile("../../../../content/curation/" + reviewedMuseums[key].Manifest)
	if err != nil {
		t.Fatal(err)
	}
	var items []MuseumSelection
	if err = json.Unmarshal(raw, &items); err != nil {
		t.Fatal(err)
	}
	return items
}

func museumEntity(key string, item MuseumSelection) wdEntity {
	claim := func(v any) map[string]any {
		return map[string]any{"rank": "normal", "mainsnak": map[string]any{"snaktype": "value", "datavalue": map[string]any{"value": v}}}
	}
	e := wdEntity{ID: item.QID, Claims: map[string][]map[string]any{
		"P170": {claim(map[string]any{"id": item.ArtistQID})}, "P195": {claim(map[string]any{"id": reviewedMuseums[key].Collection})},
	}}
	for _, inventory := range item.WDInventory {
		e.Claims["P217"] = append(e.Claims["P217"], claim(inventory))
	}
	return e
}

func TestReviewedMuseumManifest(t *testing.T) {
	for key, count := range map[string]int{"uffizi": 9, "mam": 1} {
		items := museumManifest(t, key)
		if len(items) != count {
			t.Fatalf("unexpected reviewed batch size: %s", key)
		}
		for _, item := range items {
			w, err := normalizeMuseumSelection(key, item, museumEntity(key, item))
			if err != nil {
				t.Fatal(err)
			}
			if w.Highlight != (item.Kind == "museum") {
				t.Fatal("owner selection misrepresented as museum highlight")
			}
			w.ImageURL, w.Rights = "https://upload.wikimedia.org/wikipedia/commons/a/ab/example.jpg", "public_domain"
			if w.ImageAllowed() {
				t.Fatal("copyright label bypassed the source-specific permission hold")
			}
		}
	}
}

func TestReviewedMuseumIdentityAndDatesFailClosed(t *testing.T) {
	base := museumManifest(t, "uffizi")[0]
	for _, mutation := range []string{"creator", "collection", "inventory", "qualified", "identity", "url", "selection_url", "kind", "date", "reason", "precision"} {
		t.Run(mutation, func(t *testing.T) {
			item := base
			e := museumEntity("uffizi", item)
			switch mutation {
			case "creator":
				e.Claims["P170"] = nil
			case "collection":
				e.Claims["P195"] = nil
			case "inventory":
				e.Claims["P217"] = nil
			case "qualified":
				e.Claims["P170"][0]["qualifiers"] = map[string]any{"P5102": "attributed to"}
			case "identity":
				e.ID = "Q1"
			case "url":
				item.URL = "https://www.uffizi.it.evil.example/en/artworks/birth-of-venus"
			case "selection_url":
				item.SelectionURL = "https://example.org/museum-highlight"
			case "kind":
				item.Kind = "famous"
			case "date":
				year := 1971
				item.First, item.Last = &year, &year
			case "reason":
				item.Reason = ""
			case "precision":
				item.Precision = "certain-ish"
			}
			if _, err := normalizeMuseumSelection("uffizi", item, e); err == nil {
				t.Fatal("invalid evidence passed")
			}
		})
	}
	for _, raw := range []string{"http://www.uffizi.it/en/artworks/test", "https://www.uffizi.it/en/artworks/test?redirect=elsewhere", "https://www.uffizi.it/en/artworks/../test", "https://user@www.uffizi.it/en/artworks/test"} {
		if reviewedMuseumURL("uffizi", raw) {
			t.Fatalf("unsafe museum URL: %s", raw)
		}
	}
	if err := checkMuseumPage([]byte("<p>Sandro <b>Botticelli</b> &amp; study</p>"), []string{"Sandro Botticelli", "& study"}); err != nil {
		t.Fatal(err)
	}
	if err := checkMuseumPage([]byte("<h1>Page removed</h1>"), []string{"Botticelli"}); err == nil {
		t.Fatal("changed source accepted")
	}
}

// Called inside the existing isolated-schema import integration fixture.
func testReviewedMuseumStore(t *testing.T, ctx context.Context, s Store, p Painter) {
	t.Helper()
	for _, key := range []string{"uffizi", "mam"} {
		item := museumManifest(t, key)[0]
		item.ArtistQID = p.QID
		w, err := normalizeMuseumSelection(key, item, museumEntity(key, item))
		if err != nil {
			t.Fatal(err)
		}
		sid, err := s.Source(ctx, key)
		if err != nil {
			t.Fatal(err)
		}
		institution, err := s.Institution(ctx, key, sid)
		if err != nil {
			t.Fatal(err)
		}
		job, err := s.Job(ctx, sid, "fixture-"+key, map[string]any{})
		if err != nil {
			t.Fatal(err)
		}
		for i := 0; i < 2; i++ {
			created, err := s.Work(ctx, job, sid, institution, p, w, nil, reviewedMuseums[key].ImageDeferral)
			if err != nil || created != (i == 0) {
				t.Fatal("reviewed museum replay", key, i, err)
			}
		}
		var id, country, kind string
		var revision, citations, selections int
		var media *string
		if err = s.Pool.QueryRow(ctx, `SELECT a.id::text,a.primary_media_id::text FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.scheme=$1 AND e.external_id=$2`, key+"-object", w.ID).Scan(&id, &media); err != nil || media != nil {
			t.Fatal("unlicensed media attached", err)
		}
		if err = s.Pool.QueryRow(ctx, `SELECT p.country_code FROM institution_venues v JOIN places p ON p.id=v.place_id WHERE v.institution_id=$1`, institution).Scan(&country); err != nil || country != sources[key].Country {
			t.Fatal("incorrect museum country", country, err)
		}
		if err = s.Pool.QueryRow(ctx, `SELECT cc.curator_kind,cc.revision FROM curated_collection_items ci JOIN curated_collections cc ON cc.id=ci.collection_id WHERE ci.artwork_id=$1`, id).Scan(&kind, &revision); err != nil || kind != item.Kind || revision != 2 {
			t.Fatal("selection kind/revision", kind, revision, err)
		}
		if err = s.Pool.QueryRow(ctx, `SELECT count(*) FROM citations WHERE entity_id=$1 AND field_name='image_permissions'`, id).Scan(&citations); err != nil || citations != 1 {
			t.Fatal("image permission citation missing/duplicated", err)
		}
		if _, err = s.Pool.Exec(ctx, `UPDATE artworks SET title='Owner-edited title' WHERE id=$1`, id); err != nil {
			t.Fatal(err)
		}
		if item.Kind == "owner" {
			if _, err = s.Pool.Exec(ctx, `DELETE FROM curated_collection_items WHERE artwork_id=$1`, id); err != nil {
				t.Fatal(err)
			}
		}
		if _, err = s.Work(ctx, job, sid, institution, p, w, nil, ""); err != nil {
			t.Fatal(err)
		}
		var title string
		if err = s.Pool.QueryRow(ctx, `SELECT title FROM artworks WHERE id=$1`, id).Scan(&title); err != nil || title != "Owner-edited title" {
			t.Fatal("owner title overwritten", err)
		}
		if item.Kind == "owner" {
			if err = s.Pool.QueryRow(ctx, `SELECT count(*) FROM curated_collection_items WHERE artwork_id=$1`, id).Scan(&selections); err != nil || selections != 0 {
				t.Fatal("owner removal overwritten", err)
			}
		}
		if key == "mam" {
			// Two distinct works can share the same museum highlights URL.
			other := w
			other.ID, other.Title = "Q987654322", "Second shared-page fixture"
			if fresh, err := s.Work(ctx, job, sid, institution, p, other, nil, ""); err != nil || !fresh {
				t.Fatal("shared museum page falsely merged distinct artworks", err)
			}
		}
	}
}
