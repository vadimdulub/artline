package main

import (
	"strings"
	"testing"
)

func TestPopularSMKResearchStates(t *testing.T) {
	states, err := popularSMKResearch("../../../..")
	if err != nil {
		t.Fatal(err)
	}
	if len(states) != 41 {
		t.Fatal("missing research rows")
	}
	for id, want := range map[string]string{"KMS3272": "has_image=false", "KMS3325": "no downloadable IIIF", "KMSsp198": "dating review required", "KMSsp722": "public-domain image candidate"} {
		if !strings.Contains(states["https://open.smk.dk/artwork/image/"+id], want) {
			t.Fatalf("wrong state for %s", id)
		}
	}
}
