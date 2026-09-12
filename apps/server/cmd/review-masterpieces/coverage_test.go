package main

import (
	"strings"
	"testing"
	"time"
)

func coverageFixture() coverageEntry {
	var pick coveragePick
	for _, p := range coveragePicks {
		if p.Source == "nga" && p.Object == "5" {
			pick = p
		}
	}
	raw := map[string]any{"openaccess": "1", "viewtype": "primary", "depictstmsobjectid": "5", "uuid": "00007f61-4922-417b-8f27-893ea328206c", "iiifurl": "https://api.nga.gov/iiif/00007f61-4922-417b-8f27-893ea328206c"}
	return coverageEntry{Pick: pick, Candidate: candidate{ID: "work-5", Object: "5", Scheme: schemeFor("nga"), Artist: pick.Artist, SourceID: "source", Institution: "museum", Fingerprint: "fingerprint"}, Retrieved: time.Now().UTC(), ImageURL: str(raw, "iiifurl") + "/full/!600,600/0/default.jpg", Raw: raw, Rights: "licensed", Policy: ngaPolicy, LicenseURL: ngaPolicy}
}
func TestCoverageRightsAndSelection(t *testing.T) {
	if e := validateCoverageEntry(coverageFixture()); e != nil {
		t.Fatal(e)
	}
	for name, change := range map[string]func(*coverageEntry){
		"no image grant":    func(x *coverageEntry) { x.Raw["openaccess"] = "0" },
		"secondary image":   func(x *coverageEntry) { x.Raw["viewtype"] = "alternate" },
		"different object":  func(x *coverageEntry) { x.Raw["depictstmsobjectid"] = "9" },
		"different image":   func(x *coverageEntry) { x.Raw["uuid"] = "00007f61-4922-417b-8f27-893ea328206d" },
		"invented curation": func(x *coverageEntry) { x.Pick.Reason = "Museum says masterpiece" },
		"stale":             func(x *coverageEntry) { x.Retrieved = time.Now().Add(-25 * time.Hour) },
		"future":            func(x *coverageEntry) { x.Retrieved = time.Now().Add(time.Hour) },
		"mislabelled cc0":   func(x *coverageEntry) { x.Rights = "cc0" },
		"wrong artist":      func(x *coverageEntry) { x.Candidate.Artist = "Someone else" },
		"wrong source":      func(x *coverageEntry) { x.Candidate.Scheme = schemeFor("met") },
	} {
		t.Run(name, func(t *testing.T) {
			x := coverageFixture()
			change(&x)
			if validateCoverageEntry(x) == nil {
				t.Fatal("accepted unsafe entry")
			}
		})
	}
}
func wdClaim(v any) any {
	return map[string]any{"rank": "normal", "mainsnak": map[string]any{"snaktype": "value", "datavalue": map[string]any{"value": v}}}
}
func commonsFixture() coverageEntry {
	var pick coveragePick
	for _, p := range coveragePicks {
		if p.Source == "commons-met" && p.Object == "437442" {
			pick = p
		}
	}
	entity := map[string]any{"id": "Q19912134", "claims": map[string]any{"P170": []any{wdClaim(map[string]any{"id": "Q172911"})}, "P195": []any{wdClaim(map[string]any{"id": "Q160236"})}, "P217": []any{wdClaim("1972.145.2")}, "P18": []any{wdClaim("Repin.jpg")}}}
	page := "https://www.metmuseum.org/art/collection/search/437442"
	imageURL := "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/Repin.jpg/960px-Repin.jpg"
	meta := map[string]any{}
	for k, v := range map[string]string{"LicenseShortName": "Public domain", "UsageTerms": "Public domain", "Copyrighted": "False", "Restrictions": "", "Categories": "PD-Art (PD-old-auto-expired)", "Credit": page} {
		meta[k] = map[string]any{"value": v}
	}
	info := map[string]any{"thumburl": imageURL, "descriptionurl": "https://commons.wikimedia.org/wiki/File:Repin.jpg", "extmetadata": meta}
	return coverageEntry{Pick: pick, Candidate: candidate{ID: "work-1", Object: pick.Object, Artist: pick.Artist, Scheme: schemeFor(pick.Source), SourceID: "source", Institution: "museum", Fingerprint: "fingerprint"}, Accession: "1972.145.2", Page: page, ImageURL: imageURL, ImagePage: str(info, "descriptionurl"), Rights: "public_domain", Policy: commonsPolicy, LicenseURL: commonsPolicy, Provider: "Wikimedia Commons", Retrieved: time.Now().UTC(), Raw: map[string]any{"wikidata": entity, "commons": info, "file_title": "File:Repin.jpg"}}
}
func TestCommonsExactIdentityAndRights(t *testing.T) {
	if e := validateCoverageEntry(commonsFixture()); e != nil {
		t.Fatal(e)
	}
	for name, change := range map[string]func(*coverageEntry){
		"restriction": func(x *coverageEntry) {
			obj(obj(obj(x.Raw["commons"])["extmetadata"])["Restrictions"])["value"] = "Permission needed"
		},
		"copyright": func(x *coverageEntry) {
			obj(obj(obj(x.Raw["commons"])["extmetadata"])["Copyrighted"])["value"] = "true"
		},
		"wrong credit": func(x *coverageEntry) {
			obj(obj(obj(x.Raw["commons"])["extmetadata"])["Credit"])["value"] = "Different work"
		},
		"wrong file": func(x *coverageEntry) { x.Raw["file_title"] = "File:Other.jpg" },
		"wrong licence page": func(x *coverageEntry) {
			x.ImagePage = strings.ReplaceAll(x.ImagePage, "Repin.jpg", "Other.jpg")
			obj(x.Raw["commons"])["descriptionurl"] = x.ImagePage
		},
		"wrong inventory": func(x *coverageEntry) { x.Accession = "different" },
		"qualified creator": func(x *coverageEntry) {
			cs := obj(obj(x.Raw["wikidata"])["claims"])["P170"].([]any)
			obj(cs[0])["qualifiers"] = map[string]any{"P1480": []any{"attributed to"}}
		},
		"multiple image authority": func(x *coverageEntry) {
			obj(obj(x.Raw["wikidata"])["claims"])["P18"] = []any{wdClaim("Repin.jpg"), wdClaim("Other.jpg")}
		},
	} {
		t.Run(name, func(t *testing.T) {
			x := commonsFixture()
			change(&x)
			if validateCoverageEntry(x) == nil {
				t.Fatal("accepted unsafe Commons record")
			}
		})
	}
}

func commonsCC0Fixture() coverageEntry {
	x := commonsFixture()
	info := obj(x.Raw["commons"])
	meta := obj(info["extmetadata"])
	for k, v := range map[string]string{"LicenseShortName": "CC0", "License": "cc0", "UsageTerms": "Creative Commons Zero, Public Domain Dedication", "Copyrighted": "True", "Categories": "CC-Zero|Images from Metropolitan Museum of Art|Artworks digital representation of 2D work", "Credit": "Met donation: //commons.wikimedia.org/wiki/Commons:Met"} {
		meta[k] = map[string]any{"value": v}
	}
	x.Candidate.Title = "Garshin"
	x.Raw["commons_revision"] = map[string]any{"timestamp": "2026-09-10T00:00:00Z", "slots": map[string]any{"main": map[string]any{"*": "{{Artwork\n |source = " + x.Page + "{{Template:TheMet}}\n |accession number = 1972.145.2\n |wikidata = Q19912134\n |title = Garshin\n |permission = {{Cc-zero}}\n}}"}}}
	x.Rights = "cc0"
	x.Policy = "https://commons.wikimedia.org/wiki/Commons:Met"
	x.LicenseURL = "https://creativecommons.org/publicdomain/zero/1.0/"
	return x
}

func TestCommonsCC0Donation(t *testing.T) {
	if e := validateCoverageEntry(commonsCC0Fixture()); e != nil {
		t.Fatal(e)
	}
	for name, change := range map[string]func(*coverageEntry){
		"no waiver": func(x *coverageEntry) { obj(obj(obj(x.Raw["commons"])["extmetadata"])["License"])["value"] = "unknown" },
		"restriction": func(x *coverageEntry) {
			obj(obj(obj(x.Raw["commons"])["extmetadata"])["Restrictions"])["value"] = "Permission needed"
		},
		"not museum donation": func(x *coverageEntry) {
			obj(obj(obj(x.Raw["commons"])["extmetadata"])["Credit"])["value"] = "Someone uploaded this"
		},
		"depicts conflict": func(x *coverageEntry) {
			m := obj(obj(obj(x.Raw["commons"])["extmetadata"])["Categories"])
			m["value"] = str(m, "value") + "|Artworks with digital representation of different depicts"
		},
		"no source revision": func(x *coverageEntry) { delete(x.Raw, "commons_revision") },
		"wrong inventory": func(x *coverageEntry) {
			m := obj(obj(obj(x.Raw["commons_revision"])["slots"])["main"])
			m["*"] = strings.ReplaceAll(str(m, "*"), "1972.145.2", "wrong")
		},
		"different object": func(x *coverageEntry) {
			m := obj(obj(obj(x.Raw["commons_revision"])["slots"])["main"])
			m["*"] = strings.ReplaceAll(str(m, "*"), x.Page, x.Page+"0")
		},
		"mislabelled public domain": func(x *coverageEntry) { x.Rights = "public_domain" },
	} {
		t.Run(name, func(t *testing.T) {
			x := commonsCC0Fixture()
			change(&x)
			if validateCoverageEntry(x) == nil {
				t.Fatal("accepted unsafe CC0 donation")
			}
		})
	}
}

func TestCommonsLiveFieldsOnly(t *testing.T) {
	for _, w := range []string{"<!--\n |source = expected\n-->", " |source = expected\n |source = other"} {
		if commonsField(w, "source") != "" {
			t.Fatal("accepted ambiguous/commented field")
		}
	}
}
