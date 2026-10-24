package exhibitions

import (
	"encoding/base64"
	"strings"
	"testing"
)

func TestCursorAndAllYears(t *testing.T) {
	for _, raw := range []string{"invalid", base64.RawURLEncoding.EncodeToString([]byte(`{"year":2020,"id":"not-a-uuid"}`)), base64.RawURLEncoding.EncodeToString([]byte(`{"year":0,"id":"038c9af4-f059-50ae-aae5-085fcabc8842"}`))} {
		if _, err := DecodeCursor(raw); err == nil {
			t.Fatalf("accepted malformed cursor %q", raw)
		}
	}
	start, end := 1769, 2026
	if err := (Filter{Start: &start, End: &end, Limit: 50}).Validate(); err != nil {
		t.Fatal(err)
	}
	if err := (Filter{Limit: 101}).Validate(); err == nil {
		t.Fatal("unbounded page accepted")
	}
	if err := (Filter{Start: &end, End: &start, Limit: 50}).Validate(); err == nil {
		t.Fatal("reversed range accepted")
	}
}

func TestDefaultIncludesHistoricalArchive(t *testing.T) {
	for _, f := range []Filter{{Limit: 20}, {Limit: 20, Source: "royal-academy"}} {
		where, _ := scope(f)
		if strings.Contains(where, "exhibition_research er") {
			t.Fatal("catalogue excludes exhibitions without additional research")
		}
	}
}

func TestMuseumOptionalAndFiltersBound(t *testing.T) {
	if err := (Filter{Limit: 50}).Validate(); err != nil {
		t.Fatal(err)
	}
	if err := (Filter{Limit: 50, Institution: "' OR 1=1"}).Validate(); err == nil {
		t.Fatal("malformed institution accepted")
	}
	if err := (Filter{Limit: 50, State: "published"}).Validate(); err == nil {
		t.Fatal("publication status became an event-state filter")
	}
	where, args := scope(Filter{Limit: 50, Query: "'; DELETE FROM exhibitions; --", Format: "online"})
	if len(args) != 2 || args[0] != "'; DELETE FROM exhibitions; --" {
		t.Fatal("search is not separately bound")
	}
	if where == "" {
		t.Fatal("missing active catalogue scope")
	}
}
