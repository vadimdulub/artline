package books

import "testing"

func TestPortraitRequiresReviewedCreatorIdentity(t *testing.T) {
	if len(selectedPortraits) == 0 {
		t.Fatal("no selected portraits")
	}
	for _, selected := range selectedPortraits {
		creator := Creator{ID: selected.CreatorID, SourceURL: selected.CreatorSourceURL, Kind: "person"}
		attachPortrait(&creator)
		if creator.Portrait == nil || creator.Portrait.SourceURL != selected.SourceURL {
			t.Fatal("selected portrait missing")
		}
		creator.SourceURL = "https://www.wikidata.org/wiki/Q1"
		attachPortrait(&creator)
		if creator.Portrait != nil {
			t.Fatal("mismatched identity retained portrait")
		}
		creator.SourceURL, creator.Kind = selected.CreatorSourceURL, "collective"
		attachPortrait(&creator)
		if creator.Portrait != nil {
			t.Fatal("collective creator received individual portrait")
		}
	}
	creator := Creator{ID: "unreviewed", Portrait: &Cover{ImageURL: "https://unreviewed.invalid/a.jpg"}}
	attachPortrait(&creator)
	if creator.Portrait != nil {
		t.Fatal("raw imported portrait leaked")
	}
}

func TestPortraitManifestRejectsUnselectedImage(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("invalid portrait accepted")
		}
	}()
	readPortraitSelection([]byte(`[{"creatorId":"Q1","creatorSourceUrl":"https://www.wikidata.org/wiki/Q1","imageUrl":"https://unreviewed.invalid/a.jpg"}]`))
}
