package main

import (
	"net/url"
	"strings"
	"testing"
)

func TestChicagoCreatorAndDescription(t *testing.T) {
	r := map[string]any{"artist_title": "Claude Monet", "artist_titles": []any{"Claude Monet"}, "artist_id": float64(1), "artist_ids": []any{float64(1)}, "alt_artist_ids": []any{}, "artist_display": "Claude Monet\nFrench, 1840–1926"}
	name, life, ok := chicagoCreator(r)
	if !ok || name != "Claude Monet" || life != "1840-1926" {
		t.Fatal(name, life, ok)
	}
	for _, display := range []string{"After Claude Monet", "Claude Monet (attributed)", "Claude Monet; printed by X", "Circle of Claude Monet"} {
		r["artist_display"] = display
		if _, _, ok := chicagoCreator(r); ok {
			t.Fatal("qualified creator accepted", display)
		}
	}
	if _, ok := campaignDate("n.d.", 1840, 1926); ok {
		t.Fatal("undated Chicago work assigned artist lifetime")
	}
	d := chicagoDescription("<p>A <em>painting</em> &amp; a [link](https://example.org).</p>", "https://www.artic.edu/artworks/9")
	if strings.Contains(d, "<p>") || strings.Contains(d, "[link]") || !strings.Contains(d, "CC BY 4.0") || !strings.Contains(d, "Art Institute of Chicago") || !strings.Contains(d, "wording retained") {
		t.Fatal(d)
	}
}

func TestCampaignDates(t *testing.T) {
	for _, tt := range []struct {
		s           string
		first, last int
		ok          bool
		precision   string
	}{
		{"1902", 1902, 1902, true, "exact"},
		{"c. 1895", 1890, 1900, true, "circa_range"},
		{"ca. 1870–75", 1870, 1875, true, "circa_range"},
		{"1960–1970", 1960, 1970, true, "range"},
		{"c. 1970", 1965, 1975, false, ""},
		{"c. 1965", 1960, 1970, false, ""},
		{"1971", 1971, 1971, false, ""},
		{"", 1840, 1926, false, ""},
		{"1902", 1830, 1903, false, ""},
		{"after 1902", 1902, 1970, false, ""},
		{"1902 or 1907", 1902, 1907, false, ""},
		{"1902, printed 1980", 1902, 1980, false, ""},
		{"c. 1895", 1840, 1926, false, ""},
		{"1890s", 1890, 1899, true, "decade"},
	} {
		d, ok := campaignDate(tt.s, tt.first, tt.last)
		if ok != tt.ok || ok && d.Precision != tt.precision {
			t.Errorf("%q got%+v eligible%v", tt.s, d, ok)
		}
	}
}

func TestCampaignAuthoritiesAndHosts(t *testing.T) {
	b, d := 1840, 1926
	a := knownAuthor{"Q296", "Claude Monet", &b, &d}
	index := map[string][]knownAuthor{authorityKey(a.Name): {a}}
	byQID := map[string]knownAuthor{a.QID: a}
	if _, ok := campaignAuthor(index, byQID, "Claude Monet", "1840-1926", "https://www.wikidata.org/wiki/Q296"); !ok {
		t.Fatal("source authority rejected")
	}
	if _, ok := campaignAuthor(index, byQID, "Claude Monet", "1841-1926", "https://www.wikidata.org/wiki/Q296"); ok {
		t.Fatal("lifespan conflict accepted")
	}
	if _, ok := campaignAuthor(index, byQID, "Monet", "", "https://example.org/Q296"); ok {
		t.Fatal("foreign authority accepted")
	}
	for _, raw := range []string{metExport, clevelandExport, chicagoExport, "https://www.dati.lombardia.it/api/views/ay8b-p38f.json"} {
		u, _ := url.Parse(raw)
		if !campaignURL(u) {
			t.Fatal(raw)
		}
	}
	for _, raw := range []string{"https://media.githubusercontent.com/media/other/repo/file", "https://artic-api-data.s3.amazonaws.com/private", "https://www.dati.lombardia.it/unknown"} {
		u, _ := url.Parse(raw)
		if campaignURL(u) {
			t.Fatal("unapproved route", raw)
		}
	}
}
