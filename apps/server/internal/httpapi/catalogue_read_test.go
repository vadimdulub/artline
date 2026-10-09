package httpapi

import (
	"net/http/httptest"
	"testing"

	"github.com/vadimdulub/artline/apps/server/internal/config"
)

func TestPublicCatalogueRejectsUnboundedRequests(t *testing.T) {
	handler := New(config.Config{}, nil)
	for _, query := range []string{"?limit=201", "?offset=100001", "?sort=unknown"} {
		r := httptest.NewRequest("GET", "/api/v1/catalogue/artists"+query, nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, r)
		if w.Code != 400 {
			t.Fatalf("%s returned %d, want validation before database access", query, w.Code)
		}
	}
}
