package events

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
)

type Image struct {
	ImageURL   string `json:"imageUrl"`
	SourceURL  string `json:"sourceUrl"`
	Label      string `json:"label"`
	Credit     string `json:"credit"`
	License    string `json:"license"`
	LicenseURL string `json:"licenseUrl"`
	CheckedAt  string `json:"checkedAt"`
}

type imageSelection struct {
	EventID  string `json:"eventId"`
	SourceID string `json:"sourceId"`
	Image
}

// Attach reviewed illustrations only after SQL has established record visibility.
// The label distinguishes contemporary records, later depictions and maps.
//
//go:embed image-selection.json
var imageData []byte
var selectedImages = readImageSelection(imageData)

func readImageSelection(raw []byte) map[string]imageSelection {
	var rows []imageSelection
	if err := json.Unmarshal(raw, &rows); err != nil {
		panic(fmt.Sprintf("invalid event image manifest: %v", err))
	}
	result := make(map[string]imageSelection, len(rows))
	for _, row := range rows {
		path := regexp.MustCompile(`^/images/events/selected-[0-9]{8}/` + regexp.QuoteMeta(row.EventID) + `\.jpg$`)
		if !regexp.MustCompile(`^[a-z0-9-]+$`).MatchString(row.EventID) || !regexp.MustCompile(`^Q[1-9][0-9]*$`).MatchString(row.SourceID) || !path.MatchString(row.ImageURL) || row.Label == "" || row.Credit == "" || row.CheckedAt == "" || row.License != "Public domain" || row.LicenseURL != "https://creativecommons.org/publicdomain/mark/1.0/" || !strings.HasPrefix(row.SourceURL, "https://commons.wikimedia.org/wiki/File:") {
			panic("incomplete or unsafe event illustration: " + row.EventID)
		}
		if _, exists := result[row.EventID]; exists {
			panic("duplicate event illustration: " + row.EventID)
		}
		result[row.EventID] = row
	}
	return result
}

func attachImage(event *Event) {
	event.Image = nil
	if selected, ok := selectedImages[event.ID]; ok && selected.SourceID == event.SourceID {
		image := selected.Image
		event.Image = &image
	}
}
