package books

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"net/url"
	"regexp"
	"strings"
)

// Cover is a selected, source-linked reproduction, independent of work dates.
// Missing or unverified reproductions use original typography in the drawer.
type Cover struct {
	ImageURL   string `json:"imageUrl"`
	SourceURL  string `json:"sourceUrl"`
	Label      string `json:"label"`
	Credit     string `json:"credit"`
	License    string `json:"license"`
	LicenseURL string `json:"licenseUrl"`
	CheckedAt  string `json:"checkedAt"`
}

type coverSelection struct {
	BookID   string `json:"bookId"`
	SourceID string `json:"sourceId"`
	Cover
}

// The versioned manifest contains only explicitly selected reproductions, not
// the research candidates. Rebuilding replaces the immutable selection; a
// withdrawn file must be removed from this manifest. Publication remains SQL's
// responsibility: attach only after a book passes catalogue visibility checks.
//
//go:embed cover-selection.json
var coverData []byte

var selectedCovers = readCoverSelection(coverData)

func readCoverSelection(raw []byte) map[string]coverSelection {
	var rows []coverSelection
	if err := json.Unmarshal(raw, &rows); err != nil {
		panic(fmt.Sprintf("invalid book cover manifest: %v", err))
	}
	result := make(map[string]coverSelection, len(rows))
	for _, row := range rows {
		image, err := url.Parse(row.ImageURL)
		local := selectedImagePath(row.ImageURL, "books", row.BookID)
		remote := err == nil && image.Scheme == "https" && (image.Host == "upload.wikimedia.org" || image.Host == "thumb.wikimedia.org") && image.User == nil
		if (!local && !remote) || row.BookID == "" || row.SourceID == "" || row.Credit == "" || row.Label == "" || row.License == "" || row.CheckedAt == "" || !reviewedCoverSource(row.SourceURL, row.License, local) || !strings.HasPrefix(row.LicenseURL, "https://creativecommons.org/") {
			panic(fmt.Sprintf("incomplete or unsafe book cover selection: %s", row.BookID))
		}
		if _, exists := result[row.BookID]; exists {
			panic("duplicate book cover: " + row.BookID)
		}
		result[row.BookID] = row
	}
	return result
}

func reviewedCoverSource(source, license string, local bool) bool {
	if strings.HasPrefix(source, "https://commons.wikimedia.org/wiki/File:") {
		return true
	}
	// Publisher editions are selected with exact work identity, the publisher's
	// CC0 dedication and a separate check of the underlying cover artwork.
	u, err := url.Parse(source)
	return local && license == "CC0" && err == nil && u.Scheme == "https" && u.Host == "standardebooks.org" && u.User == nil && u.RawQuery == "" && u.Fragment == "" && strings.HasPrefix(u.Path, "/ebooks/") && len(strings.Split(strings.Trim(u.Path, "/"), "/")) >= 3
}

func selectedImagePath(path, category, id string) bool {
	if !regexp.MustCompile(`^[A-Za-z0-9-]+$`).MatchString(id) {
		return false
	}
	return regexp.MustCompile(`^/images/` + regexp.QuoteMeta(category) + `/selected-[0-9]{8}(?:-[a-z0-9-]+)?/` + regexp.QuoteMeta(id) + `\.jpg$`).MatchString(path)
}

func attachCovers(items []Book) {
	for i := range items {
		// Never accept raw imported cover metadata without selection review.
		items[i].Cover = SelectedCover(items[i].ID, items[i].SourceID)
	}
}

// SelectedCover returns a copy of a reviewed reproduction for an already
// visible book. Both identifiers must match the immutable selection manifest.
func SelectedCover(id, sourceID string) *Cover {
	if selected, ok := selectedCovers[id]; ok && selected.SourceID == sourceID {
		cover := selected.Cover
		return &cover
	}
	return nil
}
