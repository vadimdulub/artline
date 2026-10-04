package catalog

import (
	_ "embed"
	"encoding/json"
	"slices"
)

// Source-attributed reference material supplements (never overwrites) database
// biographies. A visible artist must match both stable ID and canonical slug.
// Publication/access decisions remain in ArtistBySlug before this lookup.
type ReferenceBiography struct {
	Text        string `json:"text"`
	SourceURL   string `json:"source_url"`
	RevisionURL string `json:"revision_url"`
	LicenseURL  string `json:"license_url"`
	Attribution string `json:"attribution"`
	Changes     string `json:"changes"`
}
type biographyEntry struct {
	ReferenceBiography
	ArtistID            string   `json:"artist_id"`
	AdditionalArtistIDs []string `json:"additional_artist_ids,omitempty"`
	QID                 string   `json:"qid"`
}

//go:embed biographies.json
var biographyJSON []byte
var referenceBiographies = func() map[string]biographyEntry {
	var entries map[string]biographyEntry
	if err := json.Unmarshal(biographyJSON, &entries); err != nil {
		panic("invalid biography source bundle: " + err.Error())
	}
	return entries
}()

func referenceBiography(id, slug string) *ReferenceBiography {
	entry, ok := referenceBiographies[slug]
	if !ok || (entry.ArtistID != id && !slices.Contains(entry.AdditionalArtistIDs, id)) {
		return nil
	}
	biography := entry.ReferenceBiography
	return &biography
}
