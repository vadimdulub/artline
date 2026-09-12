package main

import (
	"encoding/json"
	"os"
	"testing"
	"time"
)

func TestGreekArtworkCutoffNotLifespan(t *testing.T) {
	now := time.Date(2026, 9, 11, 0, 0, 0, 0, time.UTC)
	if !validGreekLifespan(GreekArtist{Start: 1904, End: 1984}, now) {
		t.Fatal("excluded artist who died after artwork cutoff")
	}
	for _, a := range []GreekArtist{{Start: 1892, End: 1891}, {Start: 1904, End: 2027}} {
		if validGreekLifespan(a, now) {
			t.Fatal("invalid lifespan accepted")
		}
	}
	for _, w := range []GreekWork{
		{Year: 1970, Date: "1970", Precision: "exact"},
		{Year: 1910, LastYear: 1915, Date: "1910 - 1915", Precision: "range"},
		{Year: 1969, LastYear: 1970, Date: "1969–1970", Precision: "range"},
		{Year: 1906, Date: "ca 1906", Precision: "circa"},
	} {
		if !validGreekDate(w) {
			t.Fatalf("eligible date rejected: %+v", w)
		}
	}
	for _, w := range []GreekWork{
		{Year: 1971, Date: "1971", Precision: "exact"},
		{Year: 1969, LastYear: 1971, Date: "1969–1971", Precision: "range"},
		{Year: 1910, LastYear: 1915, Date: "1910", Precision: "exact"},
		{Year: 1910, Date: "1910 - 1915", Precision: "range"},
		{Year: 1910, LastYear: 1908, Date: "1910–1908", Precision: "range"},
		{Year: 1905, Date: "1906", Precision: "exact"},
		{Year: 1905, Date: "unknown", Precision: "unknown"},
	} {
		if validGreekDate(w) {
			t.Fatalf("invalid/lossy date accepted: %+v", w)
		}
	}
}

func TestPinnedGreekSecondCohort(t *testing.T) {
	b, err := os.ReadFile("../../../../docs/research/painter-review/greek-round-01-selection-v2.json")
	if err != nil {
		t.Fatal(err)
	}
	var captured GreekManifest
	if err = json.Unmarshal(b, &captured); err != nil {
		t.Fatal(err)
	}
	m, err := validateGreekAt("../../../..", b, greekPinV2, captured.Created.Add(time.Minute))
	if err != nil {
		t.Fatal(err)
	}
	if len(m.Artists) != 4 || len(m.Works) != 8 || m.Works[0].lastYear() != 1915 {
		t.Fatal("changed selection/range")
	}
	for _, w := range m.Works {
		if w.Key == "messolonghi-lagoon-7672" {
			t.Fatal("unresolved source conflict imported")
		}
	}
	if _, err = validateGreekAt("../../../..", append(b, ' '), greekPinV2, captured.Created); err == nil {
		t.Fatal("changed pinned selection accepted")
	}
	if _, err = validateGreekAt("../../../..", b, greekPinV2, captured.Created.Add(25*time.Hour)); err == nil {
		t.Fatal("stale selection accepted")
	}
}
