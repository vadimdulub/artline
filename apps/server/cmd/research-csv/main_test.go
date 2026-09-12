package main

import (
	"bytes"
	"encoding/csv"
	"os"
	"path/filepath"
	"testing"
)

func minimalDataset() dataset {
	return dataset{CheckedOn: "2026-09-12", Painters: []row{{"painter_key": "p", "name": "Painter", "source_url": "https://museum.example/artist"}}, Institutions: map[string]row{"m": {"institution_name": "Museum"}}, Artworks: []row{{"artwork_key": "a", "painter_key": "p", "institution_key": "m", "creator_display": "Painter", "title_original": "Work", "object_url": "https://museum.example/work", "date_precision": "exact", "creation_year_start": "1900", "creation_year_end": "1900", "verification_status": "verified_candidate"}}}
}

func TestPrepareRejectsUnsafeFacts(t *testing.T) {
	for _, tc := range []struct {
		name string
		edit func(*dataset)
	}{
		{"missing painter", func(d *dataset) { d.Artworks[0]["painter_key"] = "missing" }},
		{"after cutoff", func(d *dataset) { d.Artworks[0]["creation_year_end"] = "1971" }},
		{"exact range", func(d *dataset) { d.Artworks[0]["creation_year_end"] = "1901" }},
		{"fabricated circa bounds", func(d *dataset) { d.Artworks[0]["date_precision"] = "circa" }},
		{"unverified", func(d *dataset) { d.Artworks[0]["verification_status"] = "" }},
		{"unsafe source", func(d *dataset) { d.Artworks[0]["object_url"] = "file:///etc/passwd" }},
		{"duplicate object", func(d *dataset) {
			r := row{}
			for k, v := range d.Artworks[0] {
				r[k] = v
			}
			r["artwork_key"] = "other"
			d.Artworks = append(d.Artworks, r)
		}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			d := minimalDataset()
			tc.edit(&d)
			if prepare(&d) == nil {
				t.Fatal("accepted invalid facts")
			}
		})
	}
}

func TestSharedCollectionDifferentObjects(t *testing.T) {
	d := minimalDataset()
	a := d.Artworks[0]
	a["source_url"] = a["object_url"]
	delete(a, "object_url")
	a["source_locator"] = "first object"
	b := row{}
	for k, v := range a {
		b[k] = v
	}
	b["artwork_key"] = "b"
	b["source_locator"] = "second object"
	d.Artworks = append(d.Artworks, b)
	if e := prepare(&d); e != nil {
		t.Fatal(e)
	}
}

func TestCSVPreservesUnicodeQuotesAndIdentifiers(t *testing.T) {
	input := []row{{"title": "Αρμονία, \"Light\"\nsecond line", "accession": "00135"}}
	b, e := csvBytes([]string{"title", "accession"}, input)
	if e != nil {
		t.Fatal(e)
	}
	r := csv.NewReader(bytes.NewReader(b))
	records, e := r.ReadAll()
	if e != nil {
		t.Fatal(e)
	}
	if len(records) != 2 || records[1][0] != input[0]["title"] || records[1][1] != "00135" {
		t.Fatalf("corrupted CSV: %#v", records)
	}
}

func TestNeverOverwriteExistingEvidence(t *testing.T) {
	path := filepath.Join(t.TempDir(), "evidence.csv")
	if e := exclusiveWrite(path, []byte("original")); e != nil {
		t.Fatal(e)
	}
	if e := exclusiveWrite(path, []byte("replacement")); e == nil {
		t.Fatal("overwrote evidence")
	}
	b, e := os.ReadFile(path)
	if e != nil || string(b) != "original" {
		t.Fatal("existing evidence changed")
	}
}
