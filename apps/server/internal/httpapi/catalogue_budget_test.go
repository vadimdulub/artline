package httpapi

import (
	"context"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

func TestCatalogueAdmissionBoundsAndCancellation(t *testing.T) {
	entered, release, finished := make(chan struct{}), make(chan struct{}), make(chan struct{})
	var calls atomic.Int32
	h := catalogueAdmission(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if calls.Add(1) == 1 {
			close(entered)
			<-release
		}
		w.WriteHeader(200)
	}), 1, 0, time.Millisecond)
	go func() {
		h.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/api/v1/artists/rembrandt", nil))
		close(finished)
	}()
	<-entered
	w := httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest("GET", "/api/v1/artists/monet", nil))
	if w.Code != 503 || w.Header().Get("Retry-After") != "1" || calls.Load() != 1 {
		t.Fatal("unbounded admission", w.Code, calls.Load())
	}
	// Account/session reads are independent of the catalogue gate.
	w = httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest("GET", "/api/v1/auth/session", nil))
	if w.Code != 200 {
		t.Fatal("member route blocked")
	}
	close(release)
	<-finished
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	w = httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest("GET", "/api/v1/museums", nil).WithContext(ctx))
	if w.Code != 503 || calls.Load() != 2 {
		t.Fatal("cancelled read executed")
	}
	w = httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest("GET", "/api/v1/museums", nil))
	if w.Code != 200 || calls.Load() != 3 {
		t.Fatal("slot leaked")
	}
}

func TestCatalogueBudgetAndCacheHitBypass(t *testing.T) {
	for _, path := range []string{"/api/v1/artists/rembrandt", "/api/v1/museums/the-met", "/api/v1/atlas", "/api/v1/auth/session"} {
		h := catalogueReadBudget(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			deadline, ok := r.Context().Deadline()
			if path == "/api/v1/auth/session" {
				if ok {
					t.Error("member deadline changed")
				}
				return
			}
			max := 8 * time.Second
			if path == "/api/v1/atlas" {
				max = 25 * time.Second
			}
			if !ok || time.Until(deadline) > max || time.Until(deadline) < max-time.Second {
				t.Error("missing read budget", path)
			}
		}))
		h.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", path, nil))
	}
	cache := newCatalogueCache(func(context.Context) (string, error) { return "1", nil })
	var reads atomic.Int32
	h := (&API{}).cacheCatalogue(cache, catalogueAdmission(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		reads.Add(1)
		writeJSON(w, 200, map[string]bool{"ok": true})
	}), 1, 0, time.Millisecond))
	for i := 0; i < 2; i++ {
		w := cacheRequest(h, "/api/v1/artists/rembrandt", "")
		if w.Code != 200 {
			t.Fatal(w.Code)
		}
		if i == 1 && (w.Header().Get("X-Artline-Cache") != "HIT" || w.Header().Get("Server-Timing") != "") {
			t.Fatal("hit went through admission")
		}
	}
	if reads.Load() != 1 {
		t.Fatal("record response not reused")
	}
}

func TestCatalogueAdmissionQueueTimeoutReleasesSlot(t *testing.T) {
	entered, release, finished := make(chan struct{}), make(chan struct{}), make(chan struct{})
	var calls atomic.Int32
	h := catalogueAdmission(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if calls.Add(1) == 1 {
			close(entered)
			<-release
		}
		w.WriteHeader(200)
	}), 1, 1, 3*time.Millisecond)
	go func() {
		h.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/api/v1/artists/a", nil))
		close(finished)
	}()
	<-entered
	for i := 0; i < 2; i++ {
		w := httptest.NewRecorder()
		h.ServeHTTP(w, httptest.NewRequest("GET", "/api/v1/artists/b", nil))
		if w.Code != 503 || calls.Load() != 1 {
			t.Fatal("queued timeout executed or leaked", w.Code, calls.Load())
		}
	}
	close(release)
	<-finished
	w := httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest("GET", "/api/v1/artists/c", nil))
	if w.Code != 200 || calls.Load() != 2 {
		t.Fatal("admission did not recover")
	}
}

func TestPublicRecordCacheAllowlist(t *testing.T) {
	for _, path := range []string{"/api/v1/artists", "/api/v1/museums", "/api/v1/artists/source_name", "/api/v1/artists/rembrandt/works", "/api/v1/artists/rembrandt/identity", "/api/v1/museums/the-met/works/00000000-0000-0000-0000-000000000001", "/api/v1/seo/sitemaps/artworks/abc"} {
		if !cacheableCataloguePath(path) {
			t.Error("public route omitted", path)
		}
	}
	for _, path := range []string{"/api/v1/auth/session", "/api/v1/member/account", "/api/v1/member/bookmarks", "/api/v1/member/bookmarks/state", "/api/v1/artists/a/private", "/api/v1/museums/a/identity", "/api/v1/museums/a/works/invalid", "/api/v1/seo/sitemaps/artworks/nope"} {
		if cacheableCataloguePath(path) {
			t.Error("unsafe route allowed", path)
		}
	}
}
