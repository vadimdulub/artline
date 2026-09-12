package main

import "testing"

func TestPopularCycleImageIdentityDateAndAttribution(t *testing.T) {
	for _, pick := range popularCyclePicks {
		f := popularCycleFacts[pick.Object]
		x := coverageEntry{Pick: pick, Raw: map[string]any{
			"type": "Painting", "creation_date_earliest": float64(f.First), "creation_date_latest": float64(f.Last),
			"creators": []any{map[string]any{"description": f.Creator, "role": "artist"}},
		}}
		if err := validatePopularCycleMetadata(x); err != nil {
			t.Fatal(x.Pick, err)
		}
		old := x.Raw["creation_date_earliest"]
		x.Raw["creation_date_earliest"] = float64(2001)
		if validatePopularCycleMetadata(x) == nil {
			t.Fatal("changed dating accepted")
		}
		x.Raw["creation_date_earliest"] = old
		creators := x.Raw["creators"].([]any)
		creator := creators[0].(map[string]any)
		old = creator["qualifier"]
		creator["qualifier"] = "workshop of"
		if validatePopularCycleMetadata(x) == nil {
			t.Fatal("qualified attribution accepted")
		}
		creator["qualifier"] = old
	}
}
