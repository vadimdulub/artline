package httpapi

import (
	"bytes"
	"container/list"
	"context"
	"crypto/sha256"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"
)

const catalogueCacheBytes = 16 << 20
const catalogueCacheEntryBytes = 1 << 20

type catalogueCacheEntry struct {
	key     [32]byte
	body    []byte
	expires time.Time
}

// Only bounded discovery reads are cached. Details, SEO, member and editor
// routes retain their existing behavior and all browser responses stay private.
func cacheableCataloguePath(path string) bool {
	switch path {
	case "/api/v1/timeline", "/api/v1/timeline/facets", "/api/v1/painters/options",
		"/api/v1/books", "/api/v1/books/authors", "/api/v1/books/facets",
		"/api/v1/events", "/api/v1/events/facets", "/api/v1/atlas",
		"/api/v1/atlas/presets", "/api/v1/atlas/geography", "/api/v1/atlas/creators":
		return true
	}
	return false
}

type catalogueCache struct {
	mu       sync.Mutex
	entries  map[[32]byte]*list.Element
	pending  map[[32]byte]chan struct{}
	lru      *list.List
	bytes    int
	maxBytes int
	now      func() time.Time
	snapshot func(context.Context) (string, error)
}

func newCatalogueCache(snapshot func(context.Context) (string, error)) *catalogueCache {
	return &catalogueCache{entries: map[[32]byte]*list.Element{}, pending: map[[32]byte]chan struct{}{}, lru: list.New(), maxBytes: catalogueCacheBytes, now: time.Now, snapshot: snapshot}
}

func (c *catalogueCache) acquire(key [32]byte) ([]byte, <-chan struct{}, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if element := c.entries[key]; element != nil {
		entry := element.Value.(catalogueCacheEntry)
		if c.now().Before(entry.expires) {
			c.lru.MoveToFront(element)
			return entry.body, nil, false
		}
		c.remove(element)
	}
	if pending := c.pending[key]; pending != nil {
		return nil, pending, false
	}
	c.pending[key] = make(chan struct{})
	return nil, nil, true
}

func (c *catalogueCache) remove(element *list.Element) {
	entry := element.Value.(catalogueCacheEntry)
	c.bytes -= len(entry.body)
	delete(c.entries, entry.key)
	c.lru.Remove(element)
}

func (c *catalogueCache) finish(key [32]byte, body []byte) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if len(body) > 0 && len(body) <= catalogueCacheEntryBytes && len(body) <= c.maxBytes {
		for c.lru.Len() >= 128 || c.bytes+len(body) > c.maxBytes {
			c.remove(c.lru.Back())
		}
		entry := catalogueCacheEntry{key: key, body: bytes.Clone(body), expires: c.now().Add(time.Minute)}
		c.entries[key] = c.lru.PushFront(entry)
		c.bytes += len(body)
	}
	close(c.pending[key])
	delete(c.pending, key)
}

type catalogueCapture struct {
	http.ResponseWriter
	status   int
	body     bytes.Buffer
	tooLarge bool
}

func (w *catalogueCapture) WriteHeader(status int) {
	if w.status != 0 {
		return
	}
	w.status = status
	w.ResponseWriter.WriteHeader(status)
}

func (w *catalogueCapture) Write(body []byte) (int, error) {
	if w.status == 0 {
		w.WriteHeader(http.StatusOK)
	}
	if !w.tooLarge && w.body.Len()+len(body) <= catalogueCacheEntryBytes {
		w.body.Write(body)
	} else {
		w.tooLarge = true
		w.body.Reset()
	}
	return w.ResponseWriter.Write(body)
}

func (api *API) cacheCatalogue(cache *catalogueCache, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet || !cacheableCataloguePath(r.URL.Path) || len(r.URL.RawQuery) > 8192 {
			next.ServeHTTP(w, r)
			return
		}
		// Recheck access before every lookup; published and research responses
		// cannot share an entry, even when their filters otherwise match.
		preview, allowed := api.previewAllowed(w, r)
		if !allowed {
			return
		}
		ctx, cancel := context.WithTimeout(r.Context(), time.Second)
		snapshot, err := cache.snapshot(ctx)
		cancel()
		if err != nil {
			w.Header().Set("X-Artline-Cache", "BYPASS")
			next.ServeHTTP(w, r)
			return
		}
		// A fresh PostgreSQL visibility snapshot invalidates results after any
		// committed write, including SQL imports and edits on other instances.
		// This is a read-only metadata query, not a scan of catalogue tables.
		query := r.URL.Query()
		query.Del("fit") // Client interaction state; no handler filters by it.
		key := sha256.Sum256([]byte(fmt.Sprintf("%t\n%s\n%s\n%s", preview, snapshot, r.URL.Path, query.Encode())))
		for {
			body, pending, owner := cache.acquire(key)
			if body != nil {
				w.Header().Set("Content-Type", "application/json; charset=utf-8")
				w.Header().Set("X-Artline-Cache", "HIT")
				_, _ = w.Write(body)
				return
			}
			if !owner {
				select {
				case <-pending:
					continue
				case <-r.Context().Done():
					return
				}
			}
			var stored []byte
			defer func() { cache.finish(key, stored) }()
			w.Header().Set("X-Artline-Cache", "MISS")
			capture := &catalogueCapture{ResponseWriter: w}
			next.ServeHTTP(capture, r)
			if capture.status == http.StatusOK && !capture.tooLarge && r.Context().Err() == nil &&
				strings.HasPrefix(w.Header().Get("Content-Type"), "application/json") && w.Header().Get("Set-Cookie") == "" {
				stored = capture.body.Bytes()
			}
			return
		}
	})
}
