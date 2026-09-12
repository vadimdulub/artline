package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestReviewedAthensFacts(t *testing.T) {
	for _, f := range athensFacts {
		t.Run(f.Slug, func(t *testing.T) {
			path := filepath.Join("../../../..", "content/imports/popular-europe-session-20260911/athens-objects", f.Slug+".html")
			b, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			sha, _, err := hashFile(path)
			if err != nil || sha != f.SHA {
				t.Fatal("reviewed source changed", err)
			}
			s := string(b)
			if err = verifyAthensFact(s, f); err != nil {
				t.Fatal(err)
			}
			for _, field := range []string{"artist", "title", "original-title", "title-date", "media", "dimensions", "info-exhibition-Building"} {
				bad := strings.ReplaceAll(s, `class="artwork__`+field, `class="unreviewed__`+field)
				if err = verifyAthensFact(bad, f); err == nil {
					t.Fatal("accepted missing/changed", field)
				}
			}
			bad := f
			bad.Year = 1971
			bad.Date = "1971"
			if verifyAthensFact(s, bad) == nil {
				t.Fatal("accepted changed/post-cutoff date")
			}
			bad = f
			bad.Slug = "another-object"
			if verifyAthensFact(s, bad) == nil {
				t.Fatal("accepted different canonical object")
			}
		})
	}
}

func TestAthensFieldAmbiguity(t *testing.T) {
	s := `<div class="artwork__title"><h2>One &amp; Two</h2></div>`
	if athensField(s, "title") != "One & Two" {
		t.Fatal("entity normalization")
	}
	if athensField(s+s, "title") != "" {
		t.Fatal("ambiguous primary field accepted")
	}
}
