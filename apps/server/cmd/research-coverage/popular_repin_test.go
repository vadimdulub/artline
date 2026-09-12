package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestRepinReviewedNotices(t *testing.T) {
	for _, f := range repinFacts {
		t.Run(f.ID, func(t *testing.T) {
			path := filepath.Join("../../../..", "content/imports/popular-europe-session-20260911/repin-notices", f.ID+".html")
			b, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			sha, _, err := hashFile(path)
			if err != nil || sha != f.SHA {
				t.Fatal("source pin", err)
			}
			s := string(b)
			if err = verifyRepinFact(s, f); err != nil {
				t.Fatal(err)
			}
			for _, token := range []string{`class="work__author"`, `class="work__desc"`, `class="work__title"`, `title="Period"`, `title="Material"`, `title="Size"`, `title="Inventory number"`} {
				if verifyRepinFact(strings.ReplaceAll(s, token, `data-unreviewed="x"`), f) == nil {
					t.Fatal("accepted absent field", token)
				}
			}
			bad := f
			bad.Acc = "another-object"
			if verifyRepinFact(s, bad) == nil {
				t.Fatal("accepted wrong inventory")
			}
		})
	}
}
