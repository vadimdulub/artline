package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestRemovedEditorEndpointsAreUnavailable(t *testing.T) {
	{
		handler := New(config.Config{}, nil)
		for _, route := range []struct{ method, path string }{
			{"GET", "/api/v1/catalogue/artists/00000000-0000-0000-0000-000000000001"}, {"GET", "/api/v1/coverage/summary"},
			{"POST", "/api/v1/catalogue/artists"}, {"PATCH", "/api/v1/catalogue/artists/invalid"},
			{"DELETE", "/api/v1/catalogue/artists/invalid"}, {"POST", "/api/v1/catalogue/artists/invalid/restore"},
			{"PATCH", "/api/v1/museums/the-met/must-see"},
			{"POST", "/api/v1/publish/validate"}, {"POST", "/api/v1/publish/artists/invalid"}, {"POST", "/api/v1/unpublish/artists/invalid"},
		} {
			for _, auth := range []string{"", "test-editor-secret", "Bearer wrong", "Bearer test-editor-secret"} {
				request := httptest.NewRequest(route.method, route.path, strings.NewReader("{}"))
				request.Header.Set("Authorization", auth)
				response := httptest.NewRecorder()
				handler.ServeHTTP(response, request)
				if response.Code != 404 && response.Code != 405 {
					t.Fatalf("%s %s with %q: got %d", route.method, route.path, auth, response.Code)
				}
			}
		}
	}
}

func TestValidationBeforeDatabaseAccess(t *testing.T) {
	handler := New(config.Config{LocalDebug: true}, nil)
	for _, tc := range []struct {
		method, path, body string
		status             int
	}{
		{"GET", "/api/v1/timeline?start=2000&end=1100", "", 400},
		{"GET", "/api/v1/timeline?country=invalid", "", 400},
		{"GET", "/api/v1/timeline?painter=monet&painter=bad__slug", "", 400},
		{"GET", "/api/v1/painters/options?selected=bad__slug", "", 400},
		{"GET", "/api/v1/museums/the-met/works?artist=monet&artist=bad__slug", "", 400},
		{"GET", "/api/v1/timeline?work_type=imaginary", "", 400},
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
		{"GET", "/api/v1/museums?selection=owner", "", 400},
		{"GET", "/api/v1/museums?limit=500000", "", 400},
		{"GET", "/api/v1/museums/the-met/works?start=1900&end=1700", "", 400},
		{"GET", "/api/v1/museums/the-met/works?unknown_date=1&start=1700", "", 400},
		{"GET", "/api/v1/museums/the-met/works?venue=invalid", "", 400},
		{"GET", "/api/v1/museums/the-met/works/invalid", "", 404},
	} {
		request := httptest.NewRequest(tc.method, tc.path, strings.NewReader(tc.body))
		request.RemoteAddr = "127.0.0.1:1234"
		request.Header.Set("Authorization", "Bearer test-editor-secret")
		response := httptest.NewRecorder()
		handler.ServeHTTP(response, request)
		if response.Code != tc.status {
			t.Errorf("%s: want %d got %d: %s", tc.path, tc.status, response.Code, response.Body.String())
		}
	}
}
