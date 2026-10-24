package httpapi

import (
	"net/http/httptest"
	"testing"
)

func TestArtworkDirectoryFilter(t *testing.T) {
	for _, q := range []string{"limit=0", "limit=61", "undated=yes", "image_only=1", "q=a&q=b"} {
		if _, err := artworkDirectoryFilter(httptest.NewRequest("GET", "/api/v1/artworks?"+q, nil)); err == nil {
			t.Errorf("accepted %s", q)
		}
	}
	f, err := artworkDirectoryFilter(httptest.NewRequest("GET", "/api/v1/artworks", nil))
	if err != nil || f.Limit != 24 || !f.ImageOnly || f.Undated {
		t.Fatal("default must include pictures", f, err)
	}
}

func TestArtworkDirectoryIgnoresLegacyStatus(t *testing.T) {
	for _, status := range []string{"draft", "review", "published", "archived"} {
		f, err := artworkDirectoryFilter(httptest.NewRequest("GET", "/api/v1/artworks?status="+status, nil))
		if err != nil || f.Limit != 24 {
			t.Fatalf("legacy status %q must not narrow the active catalogue", status)
		}
	}
}

func TestArtworkDirectoryPictureDefaultAndOptOut(t *testing.T) {
	for _, query := range []string{"", "image_only=true", "image_only=false"} {
		f, err := artworkDirectoryFilter(httptest.NewRequest("GET", "/api/v1/artworks?"+query, nil))
		if err != nil || f.ImageOnly != (query != "image_only=false") {
			t.Fatalf("picture option %q: %+v %v", query, f, err)
		}
	}
}
