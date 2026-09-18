package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestAtlasValidationAndEditorBoundary(t *testing.T) {
	handler := New(config.Config{EditorToken: "test-editor"}, nil)
	for _, tc := range []struct {
		method, url, body, token string
		status                   int
	}{
		{"GET", "/api/v1/atlas/presets", "", "", 200},
		{"GET", "/api/v1/atlas?selection=true", "", "", 200},
		{"GET", "/api/v1/atlas?selection=oops", "", "", 400},
		{"GET", "/api/v1/atlas?selection=true&pick_artwork=invalid", "", "", 400},
		{"GET", "/api/v1/atlas?selection=true&pick_book=bad%27id", "", "", 400},
		{"POST", "/api/v1/atlas/drafts", "{}", "test-editor", 404},
		{"GET", "/api/v1/atlas?preview=1", "", "", 401},
		{"GET", "/api/v1/atlas?start=1900", "", "", 400},
		{"GET", "/api/v1/atlas?start=0&end=2000", "", "", 400},
		{"GET", "/api/v1/atlas?start=2020&end=2000", "", "", 400},
		{"GET", "/api/v1/atlas?type=idea", "", "", 400},
		{"GET", "/api/v1/atlas?type=book&type=book", "", "", 400},
		{"GET", "/api/v1/atlas?region=Russia", "", "", 400},
		{"GET", "/api/v1/atlas?preset=made-up", "", "", 400},
		{"GET", "/api/v1/atlas?window=century", "", "", 400},
		{"GET", "/api/v1/atlas?after_book=invalid", "", "", 400},
		{"GET", "/api/v1/atlas?limit=61", "", "", 400},
		{"GET", "/api/v1/atlas?highlights=true&highlights=false", "", "", 400},
		{"GET", "/api/v1/atlas/artworks/invalid", "", "", 400},
		{"GET", "/api/v1/atlas?selection=true&book_top100=yes", "", "", 400},
		{"GET", "/api/v1/atlas?selection=true&book_top100=true&book_top100=false", "", "", 400},
		{"GET", "/api/v1/atlas?selection=true&artwork_women=1", "", "", 400},
		{"GET", "/api/v1/atlas?selection=true&event_q=" + strings.Repeat("x", 201), "", "", 400},
		{"GET", "/api/v1/atlas", "", "", 200},
	} {
		req := httptest.NewRequest(tc.method, tc.url, strings.NewReader(tc.body))
		if tc.token != "" {
			req.Header.Set("Authorization", "Bearer "+tc.token)
		}
		out := httptest.NewRecorder()
		handler.ServeHTTP(out, req)
		if out.Code != tc.status {
			t.Fatalf("%s %s: got %d want %d: %s", tc.method, tc.url, out.Code, tc.status, out.Body.String())
		}
	}
}
