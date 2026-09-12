package httpapi

import (
	"net/http/httptest"
	"testing"

	"github.com/vadimdulub/artline/apps/server/internal/config"
)

func TestCatalogueReadScope(t *testing.T) {
	for _, tc := range []struct {
		name, status, query, authorization, wantStatus string
		public, wantArchived, wantAllowed              bool
	}{
		{name: "anonymous published default", wantStatus: "published", wantAllowed: true},
		{name: "anonymous cannot request review", status: "review"},
		{name: "private preview requires editor", query: "?preview=1"},
		{name: "public research list", public: true, wantAllowed: true},
		{name: "public research status", public: true, status: "review", wantStatus: "review", wantAllowed: true},
		{name: "public cannot see archives", public: true, status: "archived"},
		{name: "wrong token cannot see archives", public: true, status: "archived", authorization: "Bearer wrong"},
		{name: "editor can see archives", status: "archived", authorization: "Bearer test-editor-secret", wantStatus: "archived", wantArchived: true, wantAllowed: true},
		{name: "editor can see all statuses", authorization: "Bearer test-editor-secret", wantArchived: true, wantAllowed: true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			api := &API{config: config.Config{EditorToken: "test-editor-secret", PublicResearchPreview: tc.public}}
			r := httptest.NewRequest("GET", "/api/v1/catalogue/artists"+tc.query, nil)
			r.Header.Set("Authorization", tc.authorization)
			w := httptest.NewRecorder()
			status, archived, allowed := api.catalogueReadScope(w, r, tc.status)
			if status != tc.wantStatus || archived != tc.wantArchived || allowed != tc.wantAllowed {
				t.Fatalf("got status=%q archived=%v allowed=%v; want %q %v %v", status, archived, allowed, tc.wantStatus, tc.wantArchived, tc.wantAllowed)
			}
			if !allowed && w.Code != 401 {
				t.Fatalf("denied request returned %d", w.Code)
			}
		})
	}
}

func TestPublicCatalogueRejectsUnboundedRequests(t *testing.T) {
	handler := New(config.Config{PublicResearchPreview: true}, nil)
	for _, query := range []string{"?limit=201", "?offset=100001", "?sort=unknown", "?status=unknown"} {
		r := httptest.NewRequest("GET", "/api/v1/catalogue/artists"+query, nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, r)
		if w.Code != 400 {
			t.Fatalf("%s returned %d, want validation before database access", query, w.Code)
		}
	}
}
