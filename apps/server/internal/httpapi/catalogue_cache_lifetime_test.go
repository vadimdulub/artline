package httpapi

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestCatalogueDayCacheAndRevisionInvalidation(t *testing.T) {
	now, revision, reads := time.Now(), "one", 0
	cache := newCatalogueCache(func(context.Context) (string, error) { return revision, nil })
	cache.now = func() time.Time { return now }
	handler := (&API{}).cacheCatalogue(cache, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		reads++
		writeJSON(w, 200, map[string]int{"read": reads})
	}))
	for _, path := range []string{"/api/v1/artists", "/api/v1/books", "/api/v1/atlas", "/api/v1/exhibitions"} {
		first := cacheRequest(handler, path, "")
		now = now.Add(23 * time.Hour)
		hit := cacheRequest(handler, path, "")
		if hit.Header().Get("X-Artline-Cache") != "HIT" || first.Body.String() != hit.Body.String() {
			t.Fatalf("default catalogue did not retain its day cache: %s", path)
		}
		revision += "next"
		changed := cacheRequest(handler, path, "")
		if changed.Header().Get("X-Artline-Cache") != "MISS" || changed.Body.String() == first.Body.String() {
			t.Fatal("content update reused the old response")
		}
	}
}

func TestCatalogueDisplayClaimsKeepShortExpiry(t *testing.T) {
	for _, tc := range []struct {
		path, body string
		want       time.Duration
	}{
		{"/api/v1/museums", `{"items":[{"on_view_count":0}]}`, 24 * time.Hour},
		{"/api/v1/museums", `{"items":[{"on_view_count":1}]}`, time.Minute},
		{"/api/v1/museums?display=on_view", `{"items":[]}`, time.Minute},
		{"/api/v1/museums/the-met/works", `{"items":[]}`, time.Minute},
		{"/api/v1/museums/the-met", `{}`, time.Minute},
	} {
		if got := catalogueResponseLifetime(httptest.NewRequest("GET", tc.path, nil), []byte(tc.body)); got != tc.want {
			t.Fatalf("%s lifetime %v, want %v", tc.path, got, tc.want)
		}
	}
}
