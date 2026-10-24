package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestExhibitionGalleryRoutesAndValidation(t *testing.T) {
	handler := New(config.Config{}, nil)
	for _, tc := range []struct {
		path   string
		status int
	}{
		{"/api/v1/exhibitions?collection=expanded", 503},
		{"/api/v1/exhibitions?collection=archive", 503},
		{"/api/v1/exhibitions?person=bad", 400},
		{"/api/v1/exhibitions?after=bad", 400},
		{"/api/v1/exhibitions?limit=101", 400},
		{"/api/v1/exhibitions?country=" + strings.Repeat("a", 201), 400},
		{"/api/v1/exhibitions?city=" + strings.Repeat("a", 201), 400},
		{"/api/v1/exhibitions/invalid", 404},
		{"/api/v1/exhibitions/artworks/invalid", 404},
		{"/api/v1/exhibitions/artworks/entries", 404},
		{"/api/v1/exhibitions/artworks/invalid/exhibitions", 404},
		{"/api/v1/exhibitions/71ff8e00-4566-5c73-834b-eeb9f8cc5033/entries?participation=published", 400},
		{"/api/v1/exhibitions/artworks/26d15c6c-431c-5aa7-b234-7b60b85516ea/exhibitions?after=bad", 400},
		{"/api/v1/exhibitions/71ff8e00-4566-5c73-834b-eeb9f8cc5033/other", 404},
	} {
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, httptest.NewRequest("GET", tc.path, nil))
		if w.Code != tc.status {
			t.Errorf("%s: %d, want %d", tc.path, w.Code, tc.status)
		}
	}
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, httptest.NewRequest("POST", "/api/v1/exhibitions/artworks/26d15c6c-431c-5aa7-b234-7b60b85516ea", nil))
	if w.Code != 405 {
		t.Fatalf("read route accepted POST: %d", w.Code)
	}
}
