package main

import (
	"os"
	"testing"
	"time"
)

func TestAthensIconExactMediaCrosswalk(t *testing.T) {
	b, err := os.ReadFile("../../../../" + athensIconAPIPath)
	if err != nil {
		t.Fatal(err)
	}
	mb, err := os.ReadFile("../../../../" + athensIconMuseumPath)
	if err != nil {
		t.Fatal(err)
	}
	i, err := athensIconInfo(string(b))
	if err != nil {
		t.Fatal(err)
	}
	fixture := func() coverageEntry {
		return coverageEntry{Pick: athensIconPick, Candidate: candidate{ID: "de1c163d-25b8-4772-9de7-f0987ae92525", Object: "33", Artist: athensIconPick.Artist, Title: "Crucifixion", Scheme: schemeFor(athensIconPick.Source), SourceID: "source", Institution: "museum", Fingerprint: "fp"}, Accession: "ΒΧΜ 01354", Page: athensIconPage, ImageURL: str(i, "thumburl"), ImagePage: str(i, "descriptionurl"), Provider: "Wikimedia Commons", Rights: "cc_by_sa", License: "CC BY-SA 4.0", LicenseURL: athensIconLicense, Policy: commonsPolicy, Credit: athensIconCredit, Retrieved: time.Now().UTC(), Raw: map[string]any{"commons_api_json": string(b), "museum_html": string(mb)}}
	}
	if err = validateCoverageEntry(fixture()); err != nil {
		t.Fatal(err)
	}
	for _, mutate := range []func(*coverageEntry){
		func(x *coverageEntry) { x.Candidate.ID = "other" },
		func(x *coverageEntry) { x.Pick.Artist = "Invented painter" },
		func(x *coverageEntry) { x.Accession = "ΒΧΜ 01544" },
		func(x *coverageEntry) { x.ImageURL += "&crop=1" },
		func(x *coverageEntry) { x.Credit = "No photographer credit" },
		func(x *coverageEntry) { x.License = "CC0" },
		func(x *coverageEntry) { x.Rights = "public_domain" },
		func(x *coverageEntry) { x.Raw["museum_html"] = "changed" },
		func(x *coverageEntry) { x.Raw["commons_api_json"] = string(b) + " " },
	} {
		x := fixture()
		mutate(&x)
		if validateCoverageEntry(x) == nil {
			t.Fatal("incorrect image crosswalk accepted")
		}
	}
}
