package main

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestNivaagaardPinnedImages(t *testing.T) {
	policy, err := os.ReadFile(filepath.Join("../../../..", nivaDir, "public-domain.html"))
	if err != nil {
		t.Fatal(err)
	}
	for i, f := range nivaImageFacts {
		t.Run(f.Acc, func(t *testing.T) {
			b, err := os.ReadFile(filepath.Join("../../../..", nivaDir, f.Slug+".html"))
			if err != nil {
				t.Fatal(err)
			}
			u, err := nivaImage(string(b), f)
			if err != nil {
				t.Fatal(err)
			}
			fixture := func() coverageEntry {
				return coverageEntry{Pick: nivaImagePicks[i], Candidate: candidate{ID: "test", Object: f.Acc, Artist: f.Artist, Title: f.Title, Scheme: schemeFor("popular-nivaagaard"), Fingerprint: "fp", SourceID: "source", Institution: "museum"}, Accession: f.Acc, Page: "https://nivaagaard.dk/en/the-collection/" + f.Slug + "/", ImagePage: "https://nivaagaard.dk/en/the-collection/" + f.Slug + "/", ImageURL: u, Provider: "The Nivaagaard Collection", Rights: "public_domain", License: "Public domain", LicenseURL: nivaPD, Policy: nivaPolicy, Credit: nivaCredit(f), Retrieved: time.Now().UTC(), Raw: map[string]any{"html": string(b), "policy_html": string(policy)}}
			}
			if err = validateCoverageEntry(fixture()); err != nil {
				t.Fatal(err)
			}
			for _, mutate := range []func(*coverageEntry){
				func(x *coverageEntry) { x.Accession = "0002NMK" },
				func(x *coverageEntry) { x.Candidate.Title = "different portrait" },
				func(x *coverageEntry) { x.Candidate.Artist = "Workshop of " + f.Artist },
				func(x *coverageEntry) { x.Raw["html"] = string(b) + "changed" },
				func(x *coverageEntry) { x.Raw["policy_html"] = "public domain" },
				func(x *coverageEntry) { x.ImageURL += "?crop=1" },
				func(x *coverageEntry) { x.Credit = "missing full credit" },
				func(x *coverageEntry) { x.License = "CC0" },
				func(x *coverageEntry) { x.Retrieved = time.Now().Add(-25 * time.Hour) },
			} {
				x := fixture()
				mutate(&x)
				if validateCoverageEntry(x) == nil {
					t.Fatal("changed evidence accepted")
				}
			}
		})
	}
}
