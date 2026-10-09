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

	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

const catalogueCacheBytes = 16 << 20
const catalogueCacheEntryBytes = 1 << 20

type catalogueCacheEntry struct {
	key     [32]byte
	body    []byte
	expires time.Time
}

// Cache only bounded public catalogue reads. Member/auth paths are excluded;
// browser responses remain private and every lookup checks the current revision.
func cacheableCataloguePath(path string) bool {
	switch path {
	case "/api/v1/artists", "/api/v1/museums", "/api/v1/seo/artists", "/api/v1/seo/sitemaps", "/api/v1/artworks", "/api/v1/timeline", "/api/v1/timeline/facets", "/api/v1/painters/options",
		"/api/v1/books", "/api/v1/books/authors", "/api/v1/books/facets",
		"/api/v1/events", "/api/v1/events/facets", "/api/v1/atlas",
		"/api/v1/atlas/presets", "/api/v1/atlas/geography", "/api/v1/atlas/creators":
		return true
	}
	parts := strings.Split(strings.TrimPrefix(path, "/api/v1/"), "/")
	if strings.HasPrefix(path, "/api/v1/") {
		if len(parts) >= 2 && (parts[0] == "artists" || parts[0] == "museums") && validArtistSlug(parts[1]) {
			if len(parts) == 3 && parts[0] == "artists" && parts[2] == "identity" {
				return true
			}
			if len(parts) == 2 || (len(parts) == 3 && parts[2] == "works") || (len(parts) == 4 && parts[2] == "works" && museumIDPattern.MatchString(parts[3])) {
				return true
			}
		}
		if len(parts) == 4 && parts[0] == "seo" && parts[1] == "sitemaps" && catalog.ValidSitemapShard(parts[2], parts[3]) {
			return true
		}
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
		w.Header().Set("Cache-Control", "private, no-store")
		if r.Method != http.MethodGet || !cacheableCataloguePath(r.URL.Path) || len(r.URL.RawQuery) > 8192 {
			next.ServeHTTP(w, r)
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
		// Transactional catalogue triggers invalidate imports and edits on every
		// instance. Cluster maintenance and member sessions leave this revision
		// unchanged. The one-minute TTL also bounds time-derived display states.
		r = r.WithContext(catalog.WithCatalogueRevision(r.Context(), snapshot))
		query := r.URL.Query()
		query.Del("fit")     // Client interaction state; no handler filters by it.
		query.Del("preview") // Legacy visibility parameters no longer change reads.
		query.Del("status")
		key := sha256.Sum256([]byte(fmt.Sprintf("%s\n%s\n%s", snapshot, r.URL.Path, query.Encode())))
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
					catalogueBusy(w)
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
