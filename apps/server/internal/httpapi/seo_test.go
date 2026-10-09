package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"net/http/httptest"
	"testing"
)

func TestSEORejectsInvalidRangesBeforeDatabaseAccess(t *testing.T) {
	handler := New(config.Config{}, nil)
	for _, path := range []string{"/api/v1/seo/sitemaps/unknown/abc", "/api/v1/seo/sitemaps/artworks/ffff", "/api/v1/seo/sitemaps/artworks/XYZ", "/api/v1/seo/artists?after=invalid!"} {
		r := httptest.NewRequest("GET", path, nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, r)
		if w.Code != 400 {
			t.Errorf("%s: got %d", path, w.Code)
		}
		if w.Header().Get("X-Robots-Tag") != "noindex" {
			t.Errorf("API must not be indexed")
		}
	}
}
