package httpapi

import (
	"net/http"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

// Discovery always uses published records, irrespective of public preview or
// editor credentials. These endpoints never call previewAllowed.
func (api *API) sitemapShards(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	items, err := api.repo.SitemapShards(ctx)
	if err != nil {
		writeError(w, 503, "SITEMAP_UNAVAILABLE", "The sitemap is temporarily unavailable.")
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, 200, map[string]any{"items": items})
}

func (api *API) sitemapEntries(w http.ResponseWriter, r *http.Request) {
	kind, prefix := r.PathValue("kind"), r.PathValue("prefix")
	if !catalog.ValidSitemapShard(kind, prefix) {
		writeError(w, 400, "INVALID_SITEMAP", "Invalid sitemap range.")
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	items, err := api.repo.SitemapEntries(ctx, kind, prefix)
	if err != nil {
		writeError(w, 503, "SITEMAP_UNAVAILABLE", "The sitemap is temporarily unavailable.")
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, 200, map[string]any{"items": items})
}

func (api *API) publishedArtists(w http.ResponseWriter, r *http.Request) {
	after := r.URL.Query().Get("after")
	if len(after) > 200 || (after != "" && !validArtistSlug(after)) {
		writeError(w, 400, "INVALID_CURSOR", "Invalid artist cursor.")
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	page, err := api.repo.PublishedArtistDirectory(ctx, after)
	if err != nil {
		writeError(w, 503, "DIRECTORY_UNAVAILABLE", "The artist directory is temporarily unavailable.")
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, 200, page)
}
