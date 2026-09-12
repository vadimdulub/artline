package ingest

import (
	"encoding/json"
	"os"
	"testing"
)

func TestPradoManifestAndRightsFailClosed(t *testing.T) {
	raw, err := os.ReadFile("../../../../content/curation/prado-highlights.json")
	if err != nil {
		t.Fatal(err)
	}
	var items []PradoSelection
	if err = json.Unmarshal(raw, &items); err != nil {
		t.Fatal(err)
	}
	if len(items) != 12 {
		t.Fatalf("expected reviewed twelve-work slice, got %d", len(items))
	}
	for _, item := range items {
		claim := func(v any) map[string]any {
			return map[string]any{"rank": "normal", "mainsnak": map[string]any{"snaktype": "value", "datavalue": map[string]any{"value": v}}}
		}
		e := wdEntity{ID: item.QID, Claims: map[string][]map[string]any{"P170": {claim(map[string]any{"id": item.ArtistQID})}, "P195": {claim(map[string]any{"id": "Q160112"})}, "P217": {claim(item.Accession)}}}
		w, err := normalizePrado(item, e)
		if err != nil {
			t.Fatal(err)
		}
		if w.ImageAllowed() {
			t.Fatal("metadata alone must not allow an image")
		}
		e.Claims["P170"] = []map[string]any{claim(map[string]any{"id": "Q1"})}
		if _, err = normalizePrado(item, e); err == nil {
			t.Fatal("incorrect painter accepted")
		}
	}
	var info commonsInfo
	json.Unmarshal([]byte(`{"extmetadata":{"LicenseShortName":{"value":"Public domain"},"UsageTerms":{"value":"Public domain"},"Copyrighted":{"value":"False"},"Restrictions":{"value":""},"Categories":{"value":"PD-Art (PD-old-100-expired)"}}}`), &info)
	if !commonsPublicDomain(info) {
		t.Fatal("explicit PD-Art evidence rejected")
	}
	changed := info.Metadata["Copyrighted"]
	changed.Value = "True"
	info.Metadata["Copyrighted"] = changed
	if commonsPublicDomain(info) {
		t.Fatal("conflicting copyright accepted")
	}
}
