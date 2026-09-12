package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestEditorEndpointsDenyAnonymousAndRawTokens(t *testing.T) {
	for _, publicPreview := range []bool{false, true} {
		handler := New(config.Config{EditorToken: "test-editor-secret", PublicResearchPreview: publicPreview}, nil)
		for _, route := range []struct{ method, path string }{
			{"GET", "/api/v1/catalogue/artists/00000000-0000-0000-0000-000000000001"}, {"GET", "/api/v1/coverage/summary"},
			{"POST", "/api/v1/catalogue/artists"}, {"PATCH", "/api/v1/catalogue/artists/invalid"},
			{"DELETE", "/api/v1/catalogue/artists/invalid"}, {"POST", "/api/v1/catalogue/artists/invalid/restore"},
			{"PATCH", "/api/v1/museums/the-met/must-see"},
			{"POST", "/api/v1/publish/validate"}, {"POST", "/api/v1/publish/artists/invalid"}, {"POST", "/api/v1/unpublish/artists/invalid"},
		} {
			for _, auth := range []string{"", "test-editor-secret", "Bearer wrong"} {
				request := httptest.NewRequest(route.method, route.path, strings.NewReader("{}"))
				request.Header.Set("Authorization", auth)
				response := httptest.NewRecorder()
				handler.ServeHTTP(response, request)
				if response.Code != 401 {
					t.Fatalf("%s %s with %q: got %d", route.method, route.path, auth, response.Code)
				}
			}
		}
	}
}

func TestResearchPreviewVisibility(t *testing.T) {
	for _, tc := range []struct {
		name, method, query, auth string
		public, preview, allowed  bool
	}{
		{"published default", "GET", "", "", false, false, true},
		{"private preview denied", "GET", "?preview=1", "", false, false, false},
		{"editor preview", "GET", "?preview=1", "Bearer test-editor-secret", false, true, true},
		{"public default", "GET", "", "", true, true, true},
		{"public explicit", "GET", "?preview=1", "", true, true, true},
		{"public head", "HEAD", "", "", true, true, true},
		{"public cannot grant write access", "POST", "?preview=1", "", true, false, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			api := &API{config: config.Config{EditorToken: "test-editor-secret", PublicResearchPreview: tc.public}}
			r := httptest.NewRequest(tc.method, "/api/v1/timeline"+tc.query, nil)
			r.Header.Set("Authorization", tc.auth)
			w := httptest.NewRecorder()
			preview, allowed := api.previewAllowed(w, r)
			if preview != tc.preview || allowed != tc.allowed {
				t.Fatalf("preview=%v allowed=%v, want %v %v", preview, allowed, tc.preview, tc.allowed)
			}
			if !allowed && w.Code != 401 {
				t.Fatalf("denied with %d", w.Code)
			}
			if w.Header().Get("Cache-Control") != "private, no-store" {
				t.Fatal("preview response must not be shared-cached")
			}
		})
	}
}
func TestValidationBeforeDatabaseAccess(t *testing.T) {
	handler := New(config.Config{EditorToken: "test-editor-secret"}, nil)
	for _, tc := range []struct {
		method, path, body string
		status             int
	}{
		{"GET", "/api/v1/timeline?start=2000&end=1100", "", 400},
		{"GET", "/api/v1/timeline?country=invalid", "", 400},
		{"GET", "/api/v1/timeline?painter=monet&painter=bad_slug", "", 400},
		{"GET", "/api/v1/painters/options?selected=bad_slug", "", 400},
		{"GET", "/api/v1/museums/the-met/works?artist=monet&artist=bad_slug", "", 400},
		{"GET", "/api/v1/timeline?work_type=sculpture", "", 400},
		{"GET", "/api/v1/timeline?popular=yes", "", 400},
		{"GET", "/api/v1/timeline/facets?popular=true&popular=false", "", 400},
		{"GET", "/api/v1/timeline?region=northern_europe", "", 400},
		{"GET", "/api/v1/museums?region=northern_europe", "", 400},
		{"GET", "/api/v1/artists/giotto/works?year=1300.5", "", 400},
		{"GET", "/api/v1/artists/giotto/works?year=1300&undated=1", "", 400},
		{"GET", "/api/v1/artists/giotto/works?undated=yes", "", 400},
		{"GET", "/api/v1/artists/giotto/works?limit=100000", "", 400},
		{"GET", "/api/v1/artists/giotto/works/not-an-id", "", 404},
		{"GET", "/api/v1/museums?country=invalid", "", 400},
		{"GET", "/api/v1/museums?display=always", "", 400},
		{"GET", "/api/v1/museums?limit=500000", "", 400},
		{"GET", "/api/v1/museums/the-met/works?start=1900&end=1700", "", 400},
		{"GET", "/api/v1/museums/the-met/works?unknown_date=1&start=1700", "", 400},
		{"GET", "/api/v1/museums/the-met/works?venue=invalid", "", 400},
		{"GET", "/api/v1/museums/the-met/works/invalid", "", 404},
		{"PATCH", "/api/v1/museums/the-met/must-see", "{}", 422},
		{"PATCH", "/api/v1/catalogue/artists/not-a-uuid", "{}", 400},
		{"POST", "/api/v1/catalogue/artists", "{} {}", 400},
		{"POST", "/api/v1/catalogue/artists", `{"slug":"Bad slug","display_name":"Painter","timeline_display":"1800–1900","timeline_start_year":1800,"timeline_end_year":1900}`, 422},
	} {
		request := httptest.NewRequest(tc.method, tc.path, strings.NewReader(tc.body))
		request.Header.Set("Authorization", "Bearer test-editor-secret")
		response := httptest.NewRecorder()
		handler.ServeHTTP(response, request)
		if response.Code != tc.status {
			t.Errorf("%s: want %d got %d: %s", tc.path, tc.status, response.Code, response.Body.String())
		}
	}
	for _, path := range []string{"/api/v1/timeline?preview=1", "/api/v1/artists/giotto?preview=1", "/api/v1/timeline?status=review", "/api/v1/museums?preview=1", "/api/v1/museums/the-met?preview=1", "/api/v1/museums/the-met/works?preview=1"} {
		response := httptest.NewRecorder()
		handler.ServeHTTP(response, httptest.NewRequest("GET", path, nil))
		if response.Code != 401 {
			t.Errorf("anonymous preview %s returned %d", path, response.Code)
		}
	}
}
