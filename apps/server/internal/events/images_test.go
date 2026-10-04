package events

import (
	"encoding/json"
	"testing"
)

func TestEventIllustrationRequiresReviewedIdentity(t *testing.T) {
	if len(selectedImages) == 0 {
		t.Fatal("no selected event illustrations")
	}
	for _, selected := range selectedImages {
		event := Event{ID: selected.EventID, SourceID: selected.SourceID}
		attachImage(&event)
		if event.Image == nil || event.Image.SourceURL != selected.SourceURL {
			t.Fatal("selected illustration missing")
		}
		event.SourceID = "Q1"
		attachImage(&event)
		if event.Image != nil {
			t.Fatal("illustration attached to mismatched event")
		}
	}
	event := Event{ID: "unreviewed", Image: &Image{ImageURL: "https://unreviewed.invalid/a.jpg"}}
	attachImage(&event)
	if event.Image != nil {
		t.Fatal("unreviewed imported image retained")
	}
}

func TestEventImageRejectsEscapedAssetPaths(t *testing.T) {
	var selected imageSelection
	for _, row := range selectedImages {
		selected = row
		break
	}
	for _, path := range []string{"/images/events/selected-20261001/../other.jpg", "/images/events/selected-20261001/another-event.jpg", "https://unreviewed.invalid/a.jpg"} {
		t.Run(path, func(t *testing.T) {
			row := selected
			row.ImageURL = path
			raw, err := json.Marshal([]imageSelection{row})
			if err != nil {
				t.Fatal(err)
			}
			defer func() {
				if recover() == nil {
					t.Fatal("unsafe selection accepted")
				}
			}()
			readImageSelection(raw)
		})
	}
}
