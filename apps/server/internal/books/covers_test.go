package books

import "testing"

func TestCoversStayBoundToReviewedBookIdentity(t *testing.T) {
	if len(selectedCovers) == 0 {
		t.Fatal("no selected covers")
	}
	var selection coverSelection
	for _, value := range selectedCovers {
		selection = value
		break
	}
	items := []Book{
		{ID: selection.BookID, SourceID: selection.SourceID},
		{ID: selection.BookID, SourceID: "different-source"},
		{ID: "unreviewed", SourceID: selection.SourceID, Cover: &Cover{ImageURL: "https://unreviewed.invalid/image.jpg"}},
	}
	attachCovers(items)
	if items[0].Cover == nil || items[0].Cover.SourceURL != selection.SourceURL {
		t.Fatal("selected identity lost its source")
	}
	if items[1].Cover != nil || items[2].Cover != nil {
		t.Fatal("unreviewed or mismatched image leaked into response")
	}
}

func TestCoverManifestRejectsUnsafeImages(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("unsafe image manifest accepted")
		}
	}()
	readCoverSelection([]byte(`[{"bookId":"test","sourceId":"Q1","imageUrl":"javascript:alert(1)"}]`))
}
