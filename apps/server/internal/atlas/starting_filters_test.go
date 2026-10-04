package atlas

import (
	"net/url"
	"reflect"
	"strings"
	"testing"
)

func TestStartingFilters(t *testing.T) {
	p, _ := FindPreset("civil-rights")
	q := url.Values{}
	ApplyStartingFilters(q, p)
	if !reflect.DeepEqual(q["country"], []string{"united states"}) || q.Get("country_scope") != "artwork" || q.Get("highlights") != "false" || !reflect.DeepEqual(q["creator"], p.StartingCreators) {
		t.Fatalf("missing reviewed defaults: %v", q)
	}
	q["country"][0] = "changed"
	q["creator"][0] = "changed"
	if p.StartingCountries[0] == "changed" || p.StartingCreators[0] == "changed" {
		t.Fatal("preset mutated")
	}
	for _, raw := range []string{
		"preset_filters=custom&highlights=false",
		"country=france&creator=painter:monet&highlights=true",
		"artwork_country=France&book_author=Homer&highlights=false",
		"continent=asia&artwork_painter=monet&highlights=false",
	} {
		q, _ := url.ParseQuery(raw)
		before := q.Encode()
		ApplyStartingFilters(q, p)
		if q.Encode() != before {
			t.Fatalf("explicit filters overwritten: %s -> %s", before, q.Encode())
		}
	}
}

func TestSelectedBooksCannotAdmitUnrelatedGeography(t *testing.T) {
	for _, global := range []bool{false, true} {
		focus := &PresetFocus{Global: global, Countries: []string{"France"}, Regions: []string{"western-europe"}, SelectedBooks: true, Related: map[string][]string{"book": {"selected-book"}}}
		args := []any{nil}
		sql := focusPredicate("book", focus, &args)
		if strings.Contains(sql, "true") || strings.Contains(sql, "countries") || strings.Contains(sql, "regions") || len(args) != 2 {
			t.Fatalf("unrelated books admitted: %s %v", sql, args)
		}
	}
}
