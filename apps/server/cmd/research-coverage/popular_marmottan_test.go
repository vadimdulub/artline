package main

import "testing"

func TestMarmottanCreationDates(t *testing.T) {
	for _, tt := range []struct {
		raw         string
		first, last int
		precision   string
	}{
		{"1872", 1872, 1872, "exact"}, {"1916 entre ; 1919 et", 1916, 1919, "range"},
		{"entre 1862 et 1863", 1862, 1863, "range"}, {"1879 vers", 1879, 1879, "circa"},
	} {
		d, _, ok := marmottanDate(tt.raw)
		if !ok || d.First != tt.first || d.Last != tt.last || d.Precision != tt.precision {
			t.Fatalf("%s: %+v %v", tt.raw, d, ok)
		}
	}
	for _, raw := range []string{"", "entre 1916 de 1919", "1883 vers ; 1888", "1905 ; 1907", "1971", "1969–1972", "vers 1900 acquis", "1840 ; 1926"} {
		if _, _, ok := marmottanDate(raw); ok {
			t.Fatalf("unsafe date accepted: %s", raw)
		}
	}
}

func TestMarmottanInventoryAndPhysicalUnit(t *testing.T) {
	f := marmottanFact{URL: "https://www.marmottan.fr/notice/5013/", Title: "Nymphéas", Lines: []string{"MONET Claude (Paris, 1840 ; Giverny, 1926)", "Nymphéas", "1903", "Huile sur toile 73 × 92 cm", "inv. 5013", "Legs Michel Monet (1966)"}}
	name, life, literal, medium, dimensions, accession, kind, reason := marmottanFields(f)
	if reason != "" || name != "MONET Claude" || life != "1840-1926" || literal != "1903" || medium != "Huile sur toile" || dimensions != "73 × 92 cm" || accession != "5013" || kind != "painting" {
		t.Fatalf("bad caption: %s %s %s %s %s %s %s %s", name, life, literal, medium, dimensions, accession, kind, reason)
	}
	f.Lines[4] = "inv. 5013-bis"
	if _, _, _, _, _, _, _, reason = marmottanFields(f); reason != "inventory_caption_mismatch" {
		t.Fatalf("inventory collision accepted: %s", reason)
	}
	f.Lines[4] = "inv. 5013"
	f.Title = "carnet ; dessin"
	f.Lines[1] = f.Title
	if _, _, _, _, _, _, _, reason = marmottanFields(f); reason != "bound_volume_physical_unit_review" {
		t.Fatalf("volume accepted: %s", reason)
	}
}
