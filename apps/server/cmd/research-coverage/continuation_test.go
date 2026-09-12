package main

import "testing"

func TestContinuationDatePolicy(t *testing.T) {
	for _, tc := range []struct {
		year, period string
		first, last  int
		valid        bool
	}{
		{"", "19e siècle", 1800, 1900, true}, {"", "3e quart 20e siècle", 1950, 1975, false}, {"", "1er quart 20e siècle", 1900, 1925, true}, {"", "2e moitié 19e siècle;1er quart 20e siècle", 1850, 1925, true}, {"1970", "20e siècle", 1970, 1970, true}, {"1970 vers", "20e siècle", 1970, 1970, false}, {"1850", "17e siècle", 1850, 1850, false}, {"", "", 0, 0, false}, {"1917 avant", "20e siècle", 0, 0, false}, {"1940-1970", "20e siècle", 1940, 1970, true},
	} {
		d, _, ok := jocondeDate(map[string]string{"millesime_de_creation": tc.year, "periode_de_creation": tc.period, "date_creation": "1850", "date_d_acquisition": "1850"})
		if ok != tc.valid || ok && (d.First != tc.first || d.Last != tc.last) {
			t.Fatalf("%+v got%+v %v", tc, d, ok)
		}
	}
	for _, tc := range []struct {
		a, z, v, l string
		valid      bool
	}{{"1800", "1850", "post", "ante", true}, {"1800", "1850", "ante", "", false}, {"1800", "1850", "", "post", false}, {"1970", "1970", "ca.", "ca.", false}, {"1850", "1800", "", "", false}, {"1850", "1850", "post", "ante", false}, {"", "", "", "", false}} {
		_, _, ok := sirbecDate(map[string]string{"dtsi": tc.a, "dtsf": tc.z, "dtsv": tc.v, "dtsl": tc.l, "cmpd": "1850", "auta": "1800-1850"})
		if ok != tc.valid {
			t.Fatal(tc, ok)
		}
	}
	d, ok := kamisDate(map[string]any{"create_date4": "первая половина XVII века", "create_date1": "1601", "create_date2": "1634"})
	if !ok || d.First != 1600 || d.Last != 1650 {
		t.Fatal(d, ok)
	}
	if _, ok = kamisDate(map[string]any{"create_date4": "1973", "create_date1": "1973", "create_date2": "1973"}); ok {
		t.Fatal("post-cutoff")
	}
	if _, ok = kamisDate(map[string]any{"uchet": "1850", "create_date1": "1850", "create_date2": "1850"}); ok {
		t.Fatal("invented missing literal")
	}
}
func TestContinuationIdentityMatching(t *testing.T) {
	b, d := 1830, 1903
	a := knownAuthor{QID: "Q134741", Name: "Camille Pissarro", Birth: &b, Death: &d}
	index := map[string][]knownAuthor{authorityKey(a.Name): {a}}
	if _, ok := matchAuthor(index, "Pissarro, Camille", "1830/1903"); !ok {
		t.Fatal("exact reversed name")
	}
	if _, ok := matchAuthor(index, "Pissarro", "1830-1903"); ok {
		t.Fatal("surname")
	}
	if _, ok := matchAuthor(index, "Camille Pissarro", "1831/1903"); ok {
		t.Fatal("lifespan conflict")
	}
	index[authorityKey(a.Name)] = append(index[authorityKey(a.Name)], knownAuthor{QID: "Q1"})
	if _, ok := matchAuthor(index, "Camille Pissarro", ""); ok {
		t.Fatal("ambiguous")
	}
	if !creatorDateConflict(a, creationDate{1750, 1800, "range"}, "painting") {
		t.Fatal("impossible source century")
	}
	if creatorDateConflict(a, creationDate{1850, 1925, "range"}, "painting") {
		t.Fatal("overlap is not a fabricated narrow date")
	}
}
