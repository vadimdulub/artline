package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"net/http/httptest"
	"testing"
)

func TestEventsRequireAuthorizedPreviewAndHistoricalBounds(t *testing.T) {
	handler := New(config.Config{}, nil)
	for _, tc := range []struct {
		url    string
		status int
	}{
		{"/api/v1/events?preview=1", 401}, {"/api/v1/events/event-q6534?preview=1", 401}, {"/api/v1/events/facets?preview=1", 401},
		{"/api/v1/events?end=2001", 400}, {"/api/v1/events?start=-12001", 400}, {"/api/v1/events?start=0", 400}, {"/api/v1/events?limit=101", 400},
		{"/api/v1/events?after=invalid", 400}, {"/api/v1/events?topic=", 400}, {"/api/v1/events?top100=1", 400}, {"/api/v1/events?top100=true&top100=false", 400},
		{"/api/v1/events/facets?top100=oops", 400}, {"/api/v1/events/facets", 503}, {"/api/v1/events", 503}, {"/api/v1/events/event-q6534", 503},
	} {
		out := httptest.NewRecorder()
		handler.ServeHTTP(out, httptest.NewRequest("GET", tc.url, nil))
		if out.Code != tc.status {
			t.Fatalf("%s: got %d, wanted %d", tc.url, out.Code, tc.status)
		}
	}
}
