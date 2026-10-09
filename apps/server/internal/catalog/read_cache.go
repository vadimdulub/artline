package catalog

import (
	"context"
	"encoding/json"
	"sync"
	"time"
)

type publicReadKey struct{}
type catalogueRevisionKey struct{}

// Public views render citation labels/URLs, not internal citation notes. The
// underlying evidence and direct repository/audit reads remain unchanged.
func WithPublicRead(ctx context.Context) context.Context {
	return context.WithValue(ctx, publicReadKey{}, true)
}

func publicRead(ctx context.Context) bool {
	value, _ := ctx.Value(publicReadKey{}).(bool)
	return value
}

// A revision is supplied only after a fresh successful database snapshot read.
// Missing snapshots bypass both HTTP and facet caches, never reuse stale data.
func WithCatalogueRevision(ctx context.Context, revision string) context.Context {
	return context.WithValue(ctx, catalogueRevisionKey{}, revision)
}

type facetCacheEntry struct {
	body    []byte
	expires time.Time
}

type facetCache struct {
	mu      sync.Mutex
	entries map[string]facetCacheEntry
	bytes   int
	now     func() time.Time
}

func facetCacheKey(ctx context.Context, scope string) string {
	revision, _ := ctx.Value(catalogueRevisionKey{}).(string)
	if revision == "" {
		return ""
	}
	return revision + "\n" + scope
}

func (c *facetCache) get(key string, dest any) bool {
	if c == nil || key == "" {
		return false
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	e, ok := c.entries[key]
	if !ok {
		return false
	}
	if !c.now().Before(e.expires) {
		delete(c.entries, key)
		c.bytes -= len(e.body)
		return false
	}
	// Decoding gives every caller its own slices, including cached empty lists.
	return json.Unmarshal(e.body, dest) == nil
}

func (c *facetCache) put(key string, value any) {
	if c == nil || key == "" {
		return
	}
	body, err := json.Marshal(value)
	if err != nil || len(body) > 128<<10 {
		return
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	if old, ok := c.entries[key]; ok {
		c.bytes -= len(old.body)
		delete(c.entries, key)
	}
	// This tiny cache holds at most 64 facet sets / 2 MiB. Evict the oldest
	// expiry first; old-revision entries consume no unbounded extra space.
	for len(c.entries) >= 64 || c.bytes+len(body) > 2<<20 {
		var oldest string
		var expiry time.Time
		for k, entry := range c.entries {
			if expiry.IsZero() || entry.expires.Before(expiry) {
				oldest, expiry = k, entry.expires
			}
		}
		c.bytes -= len(c.entries[oldest].body)
		delete(c.entries, oldest)
	}
	c.entries[key] = facetCacheEntry{body: body, expires: c.now().Add(time.Minute)}
	c.bytes += len(body)
}
