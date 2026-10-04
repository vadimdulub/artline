package books

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
)

type portraitSelection struct {
	CreatorID        string `json:"creatorId"`
	CreatorSourceURL string `json:"creatorSourceUrl"`
	Cover
}

// Only this versioned, reviewed selection can attach an image to a creator.
// Imported JSON never determines portrait visibility or overrides its identity.
//
//go:embed portrait-selection.json
var portraitData []byte

var selectedPortraits = readPortraitSelection(portraitData)

func readPortraitSelection(raw []byte) map[string]portraitSelection {
	var rows []portraitSelection
	if err := json.Unmarshal(raw, &rows); err != nil {
		panic(fmt.Sprintf("invalid author portrait manifest: %v", err))
	}
	result := make(map[string]portraitSelection, len(rows))
	identity := regexp.MustCompile(`^Q[1-9][0-9]*$`)
	for _, row := range rows {
		if !identity.MatchString(row.CreatorID) || row.CreatorSourceURL != "https://www.wikidata.org/wiki/"+row.CreatorID || !selectedImagePath(row.ImageURL, "authors", row.CreatorID) || row.Label == "" || row.Credit == "" || row.License != "Public domain" || row.LicenseURL != "https://creativecommons.org/publicdomain/mark/1.0/" || row.CheckedAt == "" || !strings.HasPrefix(row.SourceURL, "https://commons.wikimedia.org/wiki/File:") {
			panic("incomplete or unsafe author portrait: " + row.CreatorID)
		}
		if _, exists := result[row.CreatorID]; exists {
			panic("duplicate author portrait: " + row.CreatorID)
		}
		result[row.CreatorID] = row
	}
	return result
}

func attachPortrait(creator *Creator) {
	creator.Portrait = nil
	if selected, ok := selectedPortraits[creator.ID]; ok && selected.CreatorSourceURL == creator.SourceURL && creator.Kind != "collective" && creator.Kind != "unknown" {
		portrait := selected.Cover
		creator.Portrait = &portrait
	}
}
