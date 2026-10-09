package catalog

import (
	"context"
	"fmt"
	"testing"
	"time"
)

func TestFacetCacheIsolationRevisionExpiryAndBounds(t *testing.T) {
	now := time.Now()
	c := &facetCache{entries: map[string]facetCacheEntry{}, now: func() time.Time { return now }}
	ctx := WithCatalogueRevision(context.Background(), "10")
	key := facetCacheKey(ctx, "museum:the-met")
	facets := emptyMuseumFacets()
	facets.Artists = append(facets.Artists, FacetOption{Slug: "rembrandt", Name: "Rembrandt"})
	c.put(key, facets)
	var first, second MuseumFacets
	if !c.get(key, &first) {
		t.Fatal("missing entry")
	}
	first.Artists[0].Name = "mutated"
	if !c.get(key, &second) || second.Artists[0].Name != "Rembrandt" {
		t.Fatal("caller mutated cached value")
	}
	if c.get(facetCacheKey(WithCatalogueRevision(ctx, "11"), "museum:the-met"), &second) {
		t.Fatal("old revision reused")
	}
	if c.get(facetCacheKey(context.Background(), "museum:the-met"), &second) {
		t.Fatal("cached without revision")
	}
	now = now.Add(time.Minute)
	if c.get(key, &second) {
		t.Fatal("expired facet returned")
	}
	for i := 0; i < 100; i++ {
		c.put(fmt.Sprint(i), facets)
	}
	if len(c.entries) > 64 || c.bytes > 2<<20 {
		t.Fatal("facet cache unbounded")
	}
	if publicRead(context.Background()) || !publicRead(WithPublicRead(context.Background())) {
		t.Fatal("audit evidence projection changed")
	}
}
