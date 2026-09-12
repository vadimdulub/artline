package main

import (
	"encoding/json"
	"os"
	"testing"
	"time"
)

func roundTwoFixture(t *testing.T, pick coveragePick) coverageEntry {
	t.Helper()
	b, err := os.ReadFile("../../../../content/imports/painter-review-round02-20260911/" + pick.Source + "-" + pick.Object + ".json")
	if err != nil {
		t.Fatal(err)
	}
	var doc map[string]any
	if err = json.Unmarshal(b, &doc); err != nil {
		t.Fatal(err)
	}
	x := coverageEntry{Pick: pick, Retrieved: time.Now().UTC()}
	if pick.Source == "smk" {
		x.Raw = obj(doc["items"].([]any)[0])
		x.Candidate.Title = str(obj(x.Raw["titles"].([]any)[0]), "title")
	} else {
		x.Raw = obj(doc["data"])
	}
	return x
}

func TestRoundTwoExactReviewedMetadata(t *testing.T) {
	for _, pick := range roundTwoPicks {
		t.Run(pick.Object, func(t *testing.T) {
			x := roundTwoFixture(t, pick)
			if err := validateRoundTwoMetadata(x); err != nil {
				t.Fatal(err)
			}
			if pick.Source == "smk" {
				obj(x.Raw["production"].([]any)[0])["creator_lref"] = "different_person"
			} else {
				obj(x.Raw["creators"].([]any)[0])["qualifier"] = "workshop of"
			}
			if validateRoundTwoMetadata(x) == nil {
				t.Fatal("accepted altered creator")
			}
			x = roundTwoFixture(t, pick)
			if pick.Source == "smk" {
				obj(x.Raw["production_date"].([]any)[0])["start"] = "1900-01-01"
			} else {
				x.Raw["creation_date_earliest"] = float64(1900)
			}
			if validateRoundTwoMetadata(x) == nil {
				t.Fatal("accepted changed date")
			}
		})
	}
	for _, id := range []string{"KMS3192", "KMS8604", "unreviewed"} {
		if validateRoundTwoMetadata(coverageEntry{Pick: coveragePick{Source: "smk", Object: id}}) == nil {
			t.Fatal("accepted deferred object")
		}
	}
}
