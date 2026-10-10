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

func TestReviewedImageVersionsPreserveIdentityAndPathBoundary(t *testing.T) {
	if !selectedImagePath("/images/books/selected-20261010-publisher-3/wd-q480.jpg", "books", "wd-q480") {
		t.Fatal("reviewed image version rejected")
	}
	for _, path := range []string{
		"/images/books/selected-20261010-publisher-3/wd-q481.jpg",
		"/images/books/selected-20261010/../wd-q480.jpg",
		"/images/books/selected-20261010-../wd-q480.jpg",
		"/images/events/selected-20261010-publisher-3/wd-q480.jpg",
	} {
		if selectedImagePath(path, "books", "wd-q480") {
			t.Fatalf("unsafe or mismatched image version accepted: %s", path)
		}
	}
}

func TestPublisherCoverRequiresPreparedImageAndReviewedLicense(t *testing.T) {
	page := "https://standardebooks.org/ebooks/leo-tolstoy/war-and-peace/louise-maude_aylmer-maude"
	if !reviewedCoverSource(page, "CC0", true) {
		t.Fatal("reviewed local publisher cover rejected")
	}
	for _, tc := range []struct {
		url, license string
		local        bool
	}{
		{page, "unknown", true},
		{page, "CC0", false},
		{"https://standardebooks.org.invalid/ebooks/author/book", "CC0", true},
		{"https://user@standardebooks.org/ebooks/author/book", "CC0", true},
		{"https://standardebooks.org/ebooks", "CC0", true},
		{page + "?unreviewed=1", "CC0", true},
	} {
		if reviewedCoverSource(tc.url, tc.license, tc.local) {
			t.Fatalf("unsafe or unreviewed publisher selection accepted: %+v", tc)
		}
	}
}
