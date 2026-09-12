package main

import (
	"encoding/json"
	"os"
	"testing"
)

func TestPopularSMKMetadata(t *testing.T) {
	picks := append(append([]coveragePick{}, popularSMKPicks...), smkMatissePicks...)
	picks = append(picks, imageFocusSMKPicks...)
	for _, pick := range picks {
		fixture := func() coverageEntry {
			t.Helper()
			dir := "../../../../content/imports/popular-smk-20260911/"
			for _, focus := range imageFocusSMKPicks {
				if focus == pick {
					dir = "../../../../content/imports/image-focus-20260912/smk/"
				}
			}
			if pick.Artist == "Henri Matisse" {
				dir = "../../../../content/imports/popular-resume-20260911-1852/smk-matisse/"
			}
			b, err := os.ReadFile(dir + "smk-" + pick.Object + ".json")
			if err != nil {
				t.Fatal(err)
			}
			var doc struct{ Items []map[string]any }
			if err = json.Unmarshal(b, &doc); err != nil {
				t.Fatal(err)
			}
			return coverageEntry{Pick: pick, Candidate: candidate{Title: popularSMKFacts[pick.Object].Title}, Raw: doc.Items[0]}
		}
		t.Run(pick.Object, func(t *testing.T) {
			x := fixture()
			if err := validatePopularSMKMetadata(x); err != nil {
				t.Fatal(err)
			}
			mutations := []func(*coverageEntry){
				func(x *coverageEntry) { obj(x.Raw["production"].([]any)[0])["creator_lref"] = "other_person" },
				func(x *coverageEntry) { obj(x.Raw["production"].([]any)[0])["creator_role"] = "workshop of" },
				func(x *coverageEntry) { obj(x.Raw["production_date"].([]any)[0])["end"] = "2000-12-31" },
				func(x *coverageEntry) { x.Raw["production_dates_notes"] = []any{"baseret på kunstnerens årstal"} },
				func(x *coverageEntry) { x.Raw["titles"] = []any{} },
				func(x *coverageEntry) { x.Candidate.Title = "different painting" },
			}
			for _, mutate := range mutations {
				x = fixture()
				mutate(&x)
				if validatePopularSMKMetadata(x) == nil {
					t.Fatal("accepted changed evidence")
				}
			}
		})
	}
	if validatePopularSMKMetadata(coverageEntry{Pick: coveragePick{Object: "KMSsp198"}}) == nil {
		t.Fatal("accepted deferred source")
	}
}
