package events

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"net/url"
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
		if !regexp.MustCompile(`^[a-z0-9-]+$`).MatchString(row.EventID) || !regexp.MustCompile(`^(Q[1-9][0-9]*|artline-[a-z0-9-]+)$`).MatchString(row.SourceID) || !path.MatchString(row.ImageURL) || row.Label == "" || row.Credit == "" || row.CheckedAt == "" || !reviewedImageLicense(row.License, row.LicenseURL) || !strings.HasPrefix(row.SourceURL, "https://commons.wikimedia.org/wiki/File:") {
			panic("incomplete or unsafe event illustration: " + row.EventID)
		}
		if _, exists := result[row.EventID]; exists {
			panic("duplicate event illustration: " + row.EventID)
		}
		result[row.EventID] = row
	}
	return result
}

// Image permission is distinct from the event's historical status. Preserve the
// selected file's actual license, including attribution and share-alike terms.
func reviewedImageLicense(label, link string) bool {
	if label == "Public domain" {
		return link == "https://creativecommons.org/publicdomain/mark/1.0/"
	}
	if label == "CC0" {
		return link == "https://creativecommons.org/publicdomain/zero/1.0/"
	}
	parts := regexp.MustCompile(`^CC (BY(?:-SA)?) ([1-4]\.0|2\.5)(?: ([a-z]{2,3}))?$`).FindStringSubmatch(label)
	if parts == nil {
		return false
	}
	u, err := url.Parse(link)
	if err != nil || u.Scheme != "https" || u.Host != "creativecommons.org" || u.User != nil || u.RawQuery != "" || u.Fragment != "" {
		return false
	}
	want := "/licenses/" + strings.ToLower(parts[1]) + "/" + parts[2] + "/"
	if parts[3] != "" {
		want += parts[3] + "/"
	}
	return u.Path == want
}

func attachImage(event *Event) {
	event.Image = nil
	if selected, ok := selectedImages[event.ID]; ok && selected.SourceID == event.SourceID {
		image := selected.Image
		event.Image = &image
	}
}
