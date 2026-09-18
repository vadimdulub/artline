package ingest

import (
	"encoding/json"
	"strconv"
	"testing"
)

func TestDanishSourceGuards(t *testing.T) {
	year := 1900
	source := func(first int, notes string, role string) json.RawMessage {
		return rawJSON(map[string]any{
			"object_number": "KMS1", "frontend_url": "https://open.smk.dk/artwork/image/KMS1",
			"object_names": []map[string]string{{"name": "Painting"}}, "titles": []map[string]string{{"title": "Source title"}},
			"production":      []map[string]string{{"creator_lref": "123_person", "creator": "Source, Painter", "creator_nationality": "Danish", "creator_role": role}},
			"production_date": []map[string]string{{"start": strconv.Itoa(first) + "-01-01", "end": strconv.Itoa(first) + "-12-31", "period": strconv.Itoa(first)}}, "production_dates_notes": []string{notes},
		})
	}
	a := DanishAuthor{ID: "123_person", Name: "Painter Source", SortName: "Source, Painter", Nationality: "Danish", URL: "https://api.smk.dk/api/v1/person/?id=123_person&lang=en", Start: 1900, End: 1900, Painting: source(1900, "1900", ""), Person: json.RawMessage(`{}`)}
	w := danishWork{europeanWork: europeanWork{Painter: a.ID, Title: "Source title", Institution: "smk-statens-museum-for-kunst", Accession: "KMS1", ObjectID: "KMS1", URL: "https://open.smk.dk/artwork/image/KMS1", DateDisplay: "1900", CreationDate: &europeanDate{First: &year, Last: &year, Precision: "exact"}, AttributionRole: "primary", WorkType: "painting"}, Raw: source(1900, "1900", "")}
	check := func(w danishWork, a DanishAuthor, ok bool) {
		t.Helper()
		b := rawJSON(danishChunk{Source: danishSource, Accessed: "2026-09-13", Authors: map[string]DanishAuthor{a.ID: a}, Works: []danishWork{w}})
		e := ValidateDanishSession(b, checksum(b))
		if (e == nil) != ok {
			t.Fatalf("valid=%v error=%v", ok, e)
		}
	}
	check(w, a, true)
	bad := w
	bad.Raw = source(1900, "Dateringen følger kunstnerens virkeår, da værket er udateret", "")
	check(bad, a, false)
	bad.CreationDate = &europeanDate{Precision: "unknown"}
	check(bad, a, true)
	bad.Raw = source(1971, "1971", "")
	check(bad, a, false)
	bad = w
	bad.Raw = source(1900, "1900", "after")
	check(bad, a, false)
	bad = w
	bad.Title = "Invented title"
	check(bad, a, false)
	bad = w
	bad.CreationDate = nil
	check(bad, a, false)
	bad = w
	bad.MuseumHighlightURL = w.URL
	check(bad, a, false)
	a.Nationality = "Swedish"
	check(w, a, false)
}
