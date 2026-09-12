package main

import (
	"testing"
	"time"
)

func chicagoFixture() coverageEntry {
	p := chicagoPicks[0]
	m := map[string]any{"id": float64(16633), "title": "The Seine at Port-Marly, Piles of Sand", "main_reference_number": "1933.443", "artist_title": p.Artist, "artist_id": float64(35805), "artist_ids": []any{float64(35805)}, "date_start": float64(1875), "date_end": float64(1875), "date_display": "1875", "artwork_type_title": "Painting", "is_public_domain": true, "image_id": "12345678-1234-1234-1234-123456789abc", "_iiif_base": "https://www.artic.edu/iiif/2"}
	u := "https://www.artic.edu/artworks/16633"
	return coverageEntry{Pick: p, Candidate: candidate{ID: "test", Object: p.Object, Artist: p.Artist, Title: str(m, "title"), Scheme: schemeFor("chicago"), Fingerprint: "fp", SourceID: "s", Institution: "i"}, Accession: "1933.443", Page: u, ImagePage: u, Raw: m, Retrieved: time.Now().UTC(), ImageURL: "https://www.artic.edu/iiif/2/12345678-1234-1234-1234-123456789abc/full/843,/0/default.jpg", Policy: chicagoPolicy, Rights: "public_domain", LicenseURL: "https://creativecommons.org/publicdomain/mark/1.0/"}
}

func TestChicagoImageIdentityAndPermission(t *testing.T) {
	if e := validateCoverageEntry(chicagoFixture()); e != nil {
		t.Fatal(e)
	}
	for _, mutate := range []func(*coverageEntry){
		func(x *coverageEntry) { x.Raw["is_public_domain"] = false },
		func(x *coverageEntry) { x.Raw["copyright_notice"] = "All rights reserved" },
		func(x *coverageEntry) { x.Raw["artist_ids"] = []any{float64(35805), float64(123)} },
		func(x *coverageEntry) { x.Raw["id"] = float64(123) },
		func(x *coverageEntry) { x.Raw["date_end"] = float64(1971) },
		func(x *coverageEntry) { x.Raw["date_display"] = "" },
		func(x *coverageEntry) { x.ImageURL = "https://example.org/image.jpg" },
	} {
		x := chicagoFixture()
		mutate(&x)
		if e := validateCoverageEntry(x); e == nil {
			t.Fatal("unsafe image accepted")
		}
	}
}
