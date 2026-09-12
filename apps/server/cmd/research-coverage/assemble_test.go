package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestNGADates(t *testing.T) {
	for _, tt := range []struct{ literal, start, end, want string }{
		{"", "1390", "1441", "date_literal_requires_review"}, {"c. 1434/1436", "1434", "1436", "eligible"},
		{"1970", "1970", "1970", "eligible"}, {"1971", "1971", "1971", "after_1970"},
		{"1969/1972", "1969", "1972", "date_crosses_1970"}, {"before 1870", "1800", "1870", "date_literal_requires_review"},
		{"1860 or 1870", "1860", "1870", "date_literal_requires_review"}, {"1640", "1645", "1645", "date_literal_numeric_conflict"},
		{"late 1640s", "1647", "1649", "eligible"}, {"1898/02", "1898", "1902", "date_outside_atlas_or_invalid"},
		{"c. 1500", "1470", "1530", "date_literal_numeric_conflict"},
	} {
		_, got := ngaDate(map[string]string{"displaydate": tt.literal, "beginyear": tt.start, "endyear": tt.end})
		if got != tt.want {
			t.Errorf("%q: %s != %s", tt.literal, got, tt.want)
		}
	}
}
func TestCSVQuotedNewlinesAndPipe(t *testing.T) {
	path := filepath.Join(t.TempDir(), "source.csv")
	if e := os.WriteFile(path, []byte("Identifiant|Nom_officiel\nM1|\"Museum\nGallery\"\n"), 0600); e != nil {
		t.Fatal(e)
	}
	count := 0
	e := csvRows(path, '|', func(r map[string]string) error {
		count++
		if r["identifiant"] != "M1" || r["nom_officiel"] != "Museum\nGallery" {
			t.Fatal(r)
		}
		return nil
	})
	if e != nil || count != 1 {
		t.Fatal(count, e)
	}
}
