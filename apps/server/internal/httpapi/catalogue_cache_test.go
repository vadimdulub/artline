package httpapi

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/atlas"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

func cacheRequest(handler http.Handler, path, auth string) *httptest.ResponseRecorder {
	r := httptest.NewRequest("GET", path, nil)
	r.Header.Set("Authorization", auth)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, r)
	return w
}

func TestCatalogueCacheVisibilityAndInvalidation(t *testing.T) {
	snapshot := "1:2:"
	cache := newCatalogueCache(func(context.Context) (string, error) { return snapshot, nil })
	api := &API{config: config.Config{EditorToken: "secret"}}
	reads := 0
	handler := api.cacheCatalogue(cache, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		reads++
		preview, _ := api.previewAllowed(w, r)
		writeJSON(w, 200, map[string]any{"preview": preview, "read": reads})
	}))
	first := cacheRequest(handler, "/api/v1/atlas?start=1300&end=1650&fit=true", "")
	hit := cacheRequest(handler, "/api/v1/atlas?end=1650&start=1300", "")
	if first.Body.String() != hit.Body.String() || reads != 1 || hit.Header().Get("X-Artline-Cache") != "HIT" || hit.Header().Get("Cache-Control") != "private, no-store" {
		t.Fatal("equivalent queries should share a private cached response")
	}
	preview := cacheRequest(handler, "/api/v1/atlas?preview=1", "Bearer secret")
	if !strings.Contains(preview.Body.String(), `"preview":true`) {
		t.Fatal("editor preview missing")
	}
	denied := cacheRequest(handler, "/api/v1/atlas?preview=1", "")
	if denied.Code != 401 || reads != 2 {
		t.Fatal("cached preview bypassed authorization")
	}
	// Identical URL, different server visibility policy: never reuse public data.
	api.config.PublicResearchPreview = true
	publicPreview := cacheRequest(handler, "/api/v1/atlas?end=1650&start=1300", "")
	if !strings.Contains(publicPreview.Body.String(), `"preview":true`) || reads != 3 {
		t.Fatal("visibility scopes shared an entry")
	}
	published := cacheRequest(handler, "/api/v1/atlas?preview=0", "")
	if !strings.Contains(published.Body.String(), `"preview":false`) {
		t.Fatal("published-only ignored")
	}
	snapshot = "2:3:"
	cacheRequest(handler, "/api/v1/atlas?end=1650&start=1300", "")
	if reads != 5 {
		t.Fatal("new PostgreSQL snapshot must invalidate old results")
	}
}

func TestCatalogueCacheBoundsAndExpiry(t *testing.T) {
	cache := newCatalogueCache(nil)
	now := time.Now()
	cache.now = func() time.Time { return now }
	cache.maxBytes = 6
	keys := [][32]byte{sha256.Sum256([]byte("a")), sha256.Sum256([]byte("b")), sha256.Sum256([]byte("c"))}
	for _, key := range keys {
		cache.acquire(key)
		cache.finish(key, []byte("abc"))
	}
	if cache.bytes != 6 || len(cache.entries) != 2 || cache.entries[keys[0]] != nil {
		t.Fatal("LRU byte limit exceeded")
	}
	now = now.Add(time.Minute)
	if body, _, owner := cache.acquire(keys[1]); body != nil || !owner {
		t.Fatal("expired entry returned")
	}
	cache.finish(keys[1], nil)
	cache.maxBytes = catalogueCacheBytes
	for i := 0; i < 150; i++ {
		key := sha256.Sum256([]byte(fmt.Sprint(i)))
		cache.acquire(key)
		cache.finish(key, []byte("x"))
	}
	if len(cache.entries) != 128 {
		t.Fatal("entry count unbounded")
	}
}

func TestCatalogueCacheDoesNotStoreUnsafeResponses(t *testing.T) {
	for _, kind := range []string{"error", "cookie", "large", "snapshot", "member", "write"} {
		t.Run(kind, func(t *testing.T) {
			cache := newCatalogueCache(func(context.Context) (string, error) {
				if kind == "snapshot" {
					return "", errors.New("unavailable")
				}
				return "1:2:", nil
			})
			reads := 0
			handler := (&API{}).cacheCatalogue(cache, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				reads++
				w.Header().Set("Content-Type", "application/json")
				if kind == "cookie" {
					w.Header().Set("Set-Cookie", "session=value")
				}
				if kind == "error" {
					w.WriteHeader(500)
				}
				body := "{}"
				if kind == "large" {
					body = strings.Repeat("x", catalogueCacheEntryBytes+1)
				}
				_, _ = w.Write([]byte(body))
			}))
			path, method := "/api/v1/atlas", "GET"
			if kind == "member" {
				path = "/api/v1/member/session"
			}
			if kind == "write" {
				method = "POST"
			}
			for i := 0; i < 2; i++ {
				handler.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(method, path, nil))
			}
			if reads != 2 || len(cache.entries) != 0 || len(cache.pending) != 0 {
				t.Fatal("unsafe response cached or request left pending")
			}
		})
	}
}

func TestCatalogueCacheCoalescesConcurrentRequests(t *testing.T) {
	cache := newCatalogueCache(func(context.Context) (string, error) { return "1:2:", nil })
	var reads atomic.Int32
	entered, release := make(chan struct{}), make(chan struct{})
	handler := (&API{}).cacheCatalogue(cache, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if reads.Add(1) == 1 {
			close(entered)
		}
		<-release
		writeJSON(w, 200, map[string]bool{"ok": true})
	}))
	var wg sync.WaitGroup
	for i := 0; i < 12; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			w := cacheRequest(handler, "/api/v1/atlas", "")
			if w.Code != 200 || !strings.Contains(w.Body.String(), `"ok":true`) {
				t.Error("missing response")
			}
		}()
	}
	<-entered
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	handler.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/api/v1/atlas", nil).WithContext(ctx))
	close(release)
	wg.Wait()
	if reads.Load() != 1 || len(cache.pending) != 0 {
		t.Fatal("duplicate concurrent query or leaked waiter")
	}
}

func TestPublicAtlasPresetsPreserveServerEvidence(t *testing.T) {
	presets := atlas.Presets()
	before, _ := json.Marshal(presets)
	public := publicAtlasPresets(presets)
	after, _ := json.Marshal(presets)
	compact, _ := json.Marshal(public)
	if string(before) != string(after) {
		t.Fatal("source evidence was mutated")
	}
	if len(compact) >= len(before)*3/4 {
		t.Fatalf("metadata not reduced: %d -> %d", len(before), len(compact))
	}
	for i, p := range public {
		if p.ID != presets[i].ID || p.Context != presets[i].Context || p.StartingScope != presets[i].StartingScope {
			t.Fatal("menu data changed")
		}
		if p.Focus != nil && (p.Focus.Related != nil || p.Focus.Context != nil || p.Focus.ArtworkIdentities != nil) {
			t.Fatal("internal links leaked")
		}
	}
	t.Logf("preset metadata: %d -> %d bytes", len(before), len(compact))
}
