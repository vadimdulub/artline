package main

import (
	"os"
	"testing"
	"time"
)

func TestPoldiCommonsExactCrosswalk(t *testing.T) {
	for i, f := range poldiImageFacts {
		t.Run(f.Acc, func(t *testing.T) {
			b, e := os.ReadFile("../../../../content/imports/popular-resume-20260911-1852/poldi-commons/" + f.APIName + ".json")
			if e != nil {
				t.Fatal(e)
			}
			mb, e := os.ReadFile("../../../../content/imports/popular-resume-20260911-1852/poldi/" + f.MuseumName + ".html")
			if e != nil {
				t.Fatal(e)
			}
			info, e := poldiImageInfo(string(b), f)
			if e != nil {
				t.Fatal(e)
			}
			fixture := func() coverageEntry {
				return coverageEntry{Pick: poldiImagePicks[i], Candidate: candidate{ID: "test", Object: f.Acc, Artist: f.Artist, Title: f.Title, Scheme: schemeFor("popular-poldi"), SourceID: "source", Institution: "museum", Fingerprint: "fp"}, Accession: f.Acc, Page: "https://museopoldipezzoli.it/en/scopri/collezioni/capolavori/opera/" + f.Slug + "/", ImagePage: str(info, "descriptionurl"), ImageURL: str(info, "thumburl"), Provider: "Wikimedia Commons", Rights: "public_domain", License: "Public domain", LicenseURL: nivaPD, Policy: commonsPolicy, Credit: poldiImageCredit(f), Retrieved: time.Now().UTC(), Raw: map[string]any{"commons_api_json": string(b), "museum_html": string(mb)}}
			}
			if e = validateCoverageEntry(fixture()); e != nil {
				t.Fatal(e)
			}
			for _, m := range []func(*coverageEntry){func(x *coverageEntry) { x.Accession = "other" }, func(x *coverageEntry) { x.Candidate.Title = "different" }, func(x *coverageEntry) { x.Raw["commons_api_json"] = string(b) + "changed" }, func(x *coverageEntry) { x.Raw["museum_html"] = "changed" }, func(x *coverageEntry) { x.ImageURL += "&crop=true" }, func(x *coverageEntry) { x.Provider = "Museum permission" }, func(x *coverageEntry) { x.License = "CC0" }, func(x *coverageEntry) { x.Credit = "missing credit" }} {
				x := fixture()
				m(&x)
				if validateCoverageEntry(x) == nil {
					t.Fatal("accepted incorrect crosswalk")
				}
			}
		})
	}
}
