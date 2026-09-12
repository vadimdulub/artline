package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestPinakothekReviewedSnapshots(t *testing.T) {
	for accession, facts := range pinakothekFacts {
		t.Run(accession, func(t *testing.T) {
			file := filepath.Join("../../../..", "content/imports/popular-europe-session-20260911/pages", facts.File)
			b, err := os.ReadFile(file)
			if os.IsNotExist(err) {
				t.Skip("private research snapshot absent")
			}
			if err != nil {
				t.Fatal(err)
			}
			if hash(b) != facts.SHA {
				t.Fatal("source snapshot changed")
			}
			source := string(b)
			if _, err = pinakothekImage(source, facts, accession); err != nil {
				t.Fatal(err)
			}
			for name, bad := range map[string]string{
				"licence removed":   strings.ReplaceAll(source, pinakothekLicense, "https://example.com/all-rights-reserved"),
				"wrong inventory":   strings.Replace(source, "Inventarnummer", "Not an inventory", 1),
				"wrong collection":  strings.ReplaceAll(source, "Bestand", "Other"),
				"wrong title":       strings.ReplaceAll(source, "artwork__title", "different-title"),
				"different picture": strings.ReplaceAll(source, "-"+accession+"_", "-999999_"),
			} {
				if _, err = pinakothekImage(bad, facts, accession); err == nil {
					t.Errorf("accepted %s", name)
				}
			}
		})
	}
}
