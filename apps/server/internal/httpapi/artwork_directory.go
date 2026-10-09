package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"log/slog"
	"net/http"
	"strings"
	"time"
)

func artworkDirectoryFilter(r *http.Request) (catalog.ArtworkDirectoryFilter, error) {
	q := r.URL.Query()
	f := catalog.ArtworkDirectoryFilter{Query: strings.TrimSpace(q.Get("q")), Cursor: q.Get("cursor")}
	for _, key := range []string{"q", "cursor", "undated", "image_only", "limit"} {
		if len(q[key]) > 1 {
			return f, catalog.ErrChronologyFilter
		}
	}
	if len(f.Query) > 200 || len(f.Cursor) > 4096 || !allowed(q.Get("undated"), "", "true", "false") || !allowed(q.Get("image_only"), "", "true", "false") {
		return f, catalog.ErrChronologyFilter
	}
	f.Undated = q.Get("undated") == "true"
	f.ImageOnly = q.Get("image_only") == "true"
	var err error
	f.Limit, err = integerQuery(r, "limit", 24, 1, 60)
	return f, err
}
func (api *API) artworkDirectory(w http.ResponseWriter, r *http.Request) {
	f, err := artworkDirectoryFilter(r)
	if err != nil {
		writeError(w, 400, "INVALID_ARTWORK_FILTER", "Check the artwork filters or return to the first page.")
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	page, err := api.repo.BrowseArtworks(ctx, f)
	if err == catalog.ErrChronologyFilter {
		writeError(w, 400, "INVALID_ARTWORK_CURSOR", "These filters need a new first page.")
		return
	}
	if err != nil {
		slog.Error("artwork directory failed", "error", err)
		writeError(w, 500, "ARTWORK_DIRECTORY_FAILED", "The artwork catalogue could not be loaded. Try again.")
		return
	}
	writeJSON(w, 200, page)
}
