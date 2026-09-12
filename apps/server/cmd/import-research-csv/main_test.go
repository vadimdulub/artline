package main

import (
	"encoding/csv"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestCreatorReview(t *testing.T) {
	for _, n := range []string{"Unknown", "Autore non registrato", "anonyme;Rubens (d'après)", "tekijä ei tiedossa", "Unidentified (Italian)"} {
		if got := creatorDecision(n); got != "excluded_unidentified_creator" {
			t.Errorf("%q: %s", n, got)
		}
	}
	for _, n := range []string{"Japan", "British School", "Allori Alessandro (bottega)", "Master of Delft", "A;B", "George Smith Ltd", "Haven, Lambert van (Tilskrevet)", "Reni Guido (scuola)", "Figueroa Pedro - Atribuido", "Pittore Lombardo (sec. Xvii)", "Various artists", "Ming Dynasty"} {
		if got := creatorDecision(n); got != "deferred_creator_attribution" {
			t.Errorf("%q: %s", n, got)
		}
	}
	for _, n := range []string{"Henner Jean-Jacques (1829-1905)", "Mary Vaux Walcott, born Philadelphia, PA 1860-died St. Andrews, New Brunswick, Canada 1940", "Edward Hopper", "Painter: Philip Guston", "Artist Name"} {
		if got := creatorDecision(n); got != "named_candidate" {
			t.Errorf("%q: %s", n, got)
		}
	}
}
func TestDateReview(t *testing.T) {
	for input, want := range map[string]string{"1970": "staged_needs_source_identity_and_type", "1969-1971": "staged_needs_date_review", "c. 1970": "staged_needs_date_review", "unknown": "staged_needs_date_review", "1850-1800": "staged_needs_date_review", "1971": "excluded_after_1970", "1971-1973": "excluded_after_1970"} {
		if got := dateDecision(input); got != want {
			t.Errorf("%s: %s", input, got)
		}
	}
}
func TestDeltaPreservesMultiplicityAndEvidence(t *testing.T) {
	d := t.TempDir()
	old := []string{"Artist Name", "Old work", "1900", "Museum", "France", "false"}
	added := []string{"Artist Name", "Untitled, \"study\"\nsecond line", "c. 1970", "Museum", "France", "true"}
	write := func(name string, rows [][]string) string {
		p := filepath.Join(d, name)
		f, e := os.Create(p)
		if e != nil {
			t.Fatal(e)
		}
		w := csv.NewWriter(f)
		w.Write(header)
		w.WriteAll(rows)
		f.Close()
		return p
	}
	base := write("base.csv", [][]string{old})
	input := write("expanded.csv", [][]string{old, added, added})
	b, _ := os.ReadFile(input)
	u := "https://storage.googleapis.com/artline-508319-images/research/" + digest(b) + ".csv"
	out := filepath.Join(d, "review")
	if e := prepare(input, base, u, out); e != nil {
		t.Fatal(e)
	}
	b, _ = os.ReadFile(filepath.Join(out, "review.json"))
	var rep report
	json.Unmarshal(b, &rep)
	if rep.Counts["added_rows"] != 2 || rep.Counts["staged_distinct_csv_rows"] != 1 || rep.Counts["repeated_added_rows"] != 1 {
		t.Fatal(rep.Counts)
	}
	b, _ = os.ReadFile(filepath.Join(out, "chunk-001.json"))
	var rows []struct {
		Raw struct {
			CSV entry `json:"csv"`
		} `json:"raw"`
	}
	if e := json.Unmarshal(b, &rows); e != nil {
		t.Fatal(e)
	}
	if len(rows) != 1 || len(rows[0].Raw.CSV.Rows) != 2 || rows[0].Raw.CSV.Cells[1] != added[1] {
		t.Fatal(rows)
	}
	if e := prepare(input, base, u, out); e == nil {
		t.Fatal("overwrote evidence")
	}
	missing := write("missing.csv", [][]string{added})
	b, _ = os.ReadFile(missing)
	if e := prepare(missing, base, "https://storage.googleapis.com/artline-508319-images/research/"+digest(b)+".csv", filepath.Join(d, "bad")); e == nil {
		t.Fatal("accepted incomplete baseline")
	}
}
