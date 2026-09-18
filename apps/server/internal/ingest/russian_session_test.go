package ingest

import (
	"encoding/json"
	"testing"
)

func TestRussianSelectionGuards(t *testing.T) {
	y := 1900
	w := europeanWork{Painter: "Q172911", Title: "Source title", Institution: "russian-session-museum", URL: "https://rusmuseumvrm.ru/data/collections/painting/test/index.php", ObjectID: "/data/collections/painting/test/index.php", DateDisplay: "1900", CreationDate: &europeanDate{First: &y, Last: &y, Precision: "exact"}, AttributionRole: "primary", WorkType: "painting", Description: "Source catalogue facts"}
	a := RussianAuthor{QID: "Q172911", Name: "Ilya Repin", Native: "Илья Ефимович Репин", URL: "https://rusmuseumvrm.ru/reference/classifier/author/repin_ie/index.php", AffiliationEvidence: "Authority describes a Russian-empire painter of Ukrainian birth", Start: 1900, End: 1900}
	check := func(w europeanWork, a RussianAuthor, want bool) {
		t.Helper()
		m := RussianChunk{Source: "russian-painters-20260913", Accessed: "2026-09-13", Authors: map[string]RussianAuthor{a.QID: a}, Works: []json.RawMessage{rawJSON(w)}}
		b := rawJSON(m)
		_, err := validateRussian(b, checksum(b))
		if (err == nil) != want {
			t.Fatalf("validation error=%v want valid=%v", err, want)
		}
	}
	check(w, a, true)
	unlinked := a
	unlinked.Start, unlinked.End = 0, 0
	check(w, unlinked, false)
	unknown := w
	unknown.DateDisplay = "Date unknown"
	unknown.CreationDate = &europeanDate{Precision: "unknown"}
	check(unknown, unlinked, true)
	unknown.CreationDate = nil
	check(unknown, unlinked, false)
	bad := w
	bad.URL = "https://example.org/data/collections/painting/test/index.php"
	check(bad, a, false)
	bad = w
	late := 1971
	bad.CreationDate = &europeanDate{First: &late, Last: &late, Precision: "exact"}
	check(bad, a, false)
	bad = w
	bad.CreationDate = &europeanDate{Precision: "unknown"}
	bad.DateDisplay = "Date unknown"
	check(bad, a, true)
	bad.CreationDate = &europeanDate{First: &y, Precision: "unknown"}
	check(bad, a, false)
	bad = w
	bad.MuseumHighlightURL = w.URL
	check(bad, a, false)
	bad = w
	bad.AttributionRole = "attributed_to"
	check(bad, a, false)
	a.AffiliationEvidence = ""
	check(w, a, false)
}
