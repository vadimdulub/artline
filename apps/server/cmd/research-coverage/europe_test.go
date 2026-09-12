package main

import (
	"net/url"
	"testing"
)

func TestSMKCreationDates(t *testing.T) {
	for _, tt := range []struct {
		display, start, end, note string
		ok                        bool
	}{
		{"1860", "1860-01-01", "1860-12-31", "", true},
		{"1860-1865", "1860-01-01", "1865-12-31", "ca.", true},
		{"1960-1980", "1960-01-01", "1980-12-31", "", false},
		{"", "1840-01-01", "1926-12-31", "", false},
		{"1840-1926", "1840-01-01", "1926-12-31", "levetid", false},
		{"1850", "1850-01-01", "1850-12-31", "udateret", false},
		{"1874-1912", "1874-01-01", "1912-12-31", "Påbegyndt: baseret på kunstnerens årstal afsluttet: tilgået museet", false},
		{"1874-1912", "1874-01-01", "1912-12-31", "BASERET PÅ KUNSTNERENS ÅRSTAL", false},
		{"1874-1912", "1874-01-01", "1912-12-31", "Afsluttet: tilgået museet", false},
		{"1891", "1891-01-01", "1891-12-31", "Værkdatering: 1891", true},
	} {
		r := map[string]any{"production_date": []any{map[string]any{"period": tt.display, "start": tt.start, "end": tt.end}}, "production_dates_notes": []any{tt.note}}
		_, _, ok := smkDate(r)
		if ok != tt.ok {
			t.Errorf("%+v: %v", tt, ok)
		}
	}
}

func TestEuropeanSourceRoutes(t *testing.T) {
	for _, tt := range []struct {
		raw string
		ok  bool
	}{
		{"https://data.rijksmuseum.nl/200107928?_profile=la-framed", true},
		{"https://data.rijksmuseum.nl/search/collection?creator=Rembrandt&type=painting&imageAvailable=true", true},
		{"https://data.rijksmuseum.nl/search/collection?creator=anyone", false},
		{"https://data.rijksmuseum.nl/../../private?_profile=la-framed", false},
		{"https://data.rijksmuseum.nl.evil.example/200107928?_profile=la-framed", false},
	} {
		u, e := url.Parse(tt.raw)
		if e != nil {
			t.Fatal(e)
		}
		if campaignURL(u) != tt.ok {
			t.Fatal(tt)
		}
	}
	for _, s := range []string{"painter: after: Rembrandt", "toegeschreven aan Rembrandt", "workshop of Rembrandt"} {
		if !rijksQualified.MatchString(s) {
			t.Fatal("qualification lost", s)
		}
	}
}
