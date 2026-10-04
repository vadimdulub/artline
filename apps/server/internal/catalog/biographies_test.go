package catalog

import (
	"encoding/json"
	"net/url"
	"regexp"
	"strings"
	"testing"
)

func TestReferenceBiographiesHaveIdentityAndAttribution(t *testing.T) {
	var entries map[string]struct {
		biographyEntry
		Rank       int `json:"rank"`
		RevisionID int `json:"revision_id"`
	}
	if err := json.Unmarshal(biographyJSON, &entries); err != nil {
		t.Fatal(err)
	}
	if len(entries) != 1000 {
		t.Fatalf("expected the 1,000-artist cohort; got %d", len(entries))
	}
	ranks := map[int]bool{}
	identities := map[string]bool{}
	for slug, entry := range entries {
		if entry.Rank < 1 || entry.Rank > 1000 || ranks[entry.Rank] {
			t.Errorf("invalid cohort rank: %s", slug)
		}
		ranks[entry.Rank] = true
		if len(entry.ArtistID) != 36 || !regexp.MustCompile(`^Q[1-9][0-9]*$`).MatchString(entry.QID) || len(strings.TrimSpace(entry.Text)) < 80 {
			t.Errorf("missing identity or text: %s", slug)
		}
		source, err := url.Parse(entry.SourceURL)
		if err != nil || source.Scheme != "https" || source.Host != "en.wikipedia.org" || !strings.HasPrefix(source.Path, "/wiki/") {
			t.Errorf("invalid source: %s", slug)
		}
		if entry.RevisionID == 0 || !strings.HasPrefix(entry.RevisionURL, "https://en.wikipedia.org/w/index.php?oldid=") || entry.Attribution != "Wikipedia contributors" || entry.LicenseURL != "https://creativecommons.org/licenses/by-sa/4.0/" || entry.Changes == "" {
			t.Errorf("missing attribution: %s", slug)
		}
		if referenceBiography(entry.ArtistID, slug) == nil || referenceBiography("different-artist", slug) != nil {
			t.Error("artist identity guard failed", slug)
		}
		for _, id := range append([]string{entry.ArtistID}, entry.AdditionalArtistIDs...) {
			if len(id) != 36 || identities[id] || referenceBiography(id, slug) == nil || referenceBiography(id, "wrong-slug") != nil {
				t.Error("additional artist identity guard failed", slug, id)
			}
			identities[id] = true
		}
	}
}

func TestDomenichinoReviewedProductionIdentity(t *testing.T) {
	biography := referenceBiography("e43108bb-3d3b-4aae-a7aa-f1321ecf5a29", "le-dominiquin-round2-033f8b250c97")
	if biography == nil || biography.SourceURL != "https://en.wikipedia.org/wiki/Domenichino" {
		t.Fatal("reviewed production identity must resolve to Domenichino")
	}
}
