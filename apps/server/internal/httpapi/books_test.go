package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"net/http/httptest"
	"testing"
)

func TestBooksRequireAuthorizedPreviewAndValidBounds(t *testing.T) {
	handler := New(config.Config{}, nil)
	for _, tc := range []struct {
		url    string
		status int
	}{
		{"/api/v1/books?preview=1", 401}, {"/api/v1/books/odyssey?preview=1", 401}, {"/api/v1/books/authors?preview=1", 401},
		{"/api/v1/books?start=0", 400}, {"/api/v1/books?limit=101", 400}, {"/api/v1/books?after=invalid", 400},
		{"/api/v1/books?view=wrong", 400}, {"/api/v1/books?view=authors&preview=1", 401}, {"/api/v1/books?view=authors", 503},
		{"/api/v1/books?women=yes", 400}, {"/api/v1/books?top100=1", 400}, {"/api/v1/books?top100=true&top100=false", 400}, {"/api/v1/books?language=", 400},
		{"/api/v1/books/facets?preview=1", 401}, {"/api/v1/books/facets?top100=no", 400}, {"/api/v1/books/authors?women=1", 400},
		{"/api/v1/books/facets", 503},
		{"/api/v1/books", 503}, {"/api/v1/books/odyssey", 503},
	} {
		response := httptest.NewRecorder()
		handler.ServeHTTP(response, httptest.NewRequest("GET", tc.url, nil))
		if response.Code != tc.status {
			t.Fatalf("%s: %d %s", tc.url, response.Code, response.Body.String())
		}
	}
}
