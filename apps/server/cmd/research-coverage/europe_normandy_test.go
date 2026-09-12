package main

import "testing"

func TestNormandyDates(t *testing.T) {
	for _, tc := range []struct {
		value string
		ok    bool
	}{{"1894", true}, {"Vers 1850", true}, {"1879-1880", true}, {"c. 1850–1852", true}, {"1970", true}, {"vers 1970", false}, {"1900-1971", false}, {"Avant 1870", false}, {"Après 1920", false}, {"signé 1894", false}, {"", false}, {"1850-1840", false}, {"1909 (don)", false}} {
		if _, ok := normandyDate(tc.value); ok != tc.ok {
			t.Fatalf("%s: %v", tc.value, ok)
		}
	}
}
func TestNormandyFactualLabels(t *testing.T) {
	f := normandyFact{Source: "rouen", State: "extracted", Title: "La Seine à Port-Villez", Artist: "Claude Monet", ArtistDetails: "(1840 - 1926) | 909.1.33", Details: "Date : 1894 | Technique : Huile sur toile"}
	name, life, title, date, medium, _, accession, reason := normandyFields(f)
	if name != "Claude Monet" || life != "1840-1926" || title != f.Title || date != "1894" || medium != "Huile sur toile" || accession != "909.1.33" || reason != "" {
		t.Fatal(name, life, title, date, medium, accession, reason)
	}
	f.Artist = "Atelier de Claude Monet"
	if _, _, _, _, _, _, _, reason = normandyFields(f); reason != "qualified_attribution_review" {
		t.Fatal(reason)
	}
	f = normandyFact{Source: "muma", State: "extracted", Title: "MONET, Les Nymphéas", Lines: []string{"Claude MONET (1840-1926)", "Les Nymphéas", "1904", "huile sur toile", "89 x 93 cm", "don 1910"}}
	_, _, _, date, _, _, accession, reason = normandyFields(f)
	if date != "1904" || accession != "" || reason != "" {
		t.Fatal(date, accession, reason)
	}
	f.State = "group_or_layout_review"
	if _, _, _, _, _, _, _, reason = normandyFields(f); reason == "" {
		t.Fatal("group accepted")
	}
}

func TestNormandyNonoverlapReviewIsNarrow(t *testing.T) {
	w := &jocondeWave{Source: "normandy-joconde", ReviewedNonoverlap: map[string]string{"07200001088": "A 494", "07200001089": "A 495"}}
	r := map[string]string{"code_museofile": "M0720", "reference": "07200001089", "numero_inventaire": "A 495"}
	a := knownAuthor{QID: "Q134741"}
	d := creationDate{1903, 1903, "exact"}
	if !normandyReviewedNonoverlap(w, r, a, d) {
		t.Fatal("reviewed record rejected")
	}
	d.First = 1901
	if normandyReviewedNonoverlap(w, r, a, d) {
		t.Fatal("different date accepted")
	}
	d.First = 1903
	r["code_museofile"] = "M0729"
	if normandyReviewedNonoverlap(w, r, a, d) {
		t.Fatal("different holding accepted")
	}
	r["code_museofile"] = "M0720"
	r["numero_inventaire"] = "A 494"
	if normandyReviewedNonoverlap(w, r, a, d) {
		t.Fatal("different inventory accepted")
	}
}
