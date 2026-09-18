package books

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"net/url"
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
		if err != nil || image.Scheme != "https" || (image.Host != "upload.wikimedia.org" && image.Host != "thumb.wikimedia.org") || image.User != nil || row.BookID == "" || row.SourceID == "" || row.Credit == "" || row.Label == "" || row.License == "" || row.CheckedAt == "" || !strings.HasPrefix(row.SourceURL, "https://commons.wikimedia.org/wiki/File:") || !strings.HasPrefix(row.LicenseURL, "https://creativecommons.org/") {
			panic(fmt.Sprintf("incomplete or unsafe book cover selection: %s", row.BookID))
		}
		if _, exists := result[row.BookID]; exists {
			panic("duplicate book cover: " + row.BookID)
		}
		result[row.BookID] = row
	}
	return result
}

func attachCovers(items []Book) {
	for i := range items {
		// Never accept raw imported cover metadata without selection review.
		items[i].Cover = nil
		if selected, ok := selectedCovers[items[i].ID]; ok && selected.SourceID == items[i].SourceID {
			cover := selected.Cover
			items[i].Cover = &cover
		}
	}
}
