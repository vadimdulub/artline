package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"log/slog"
	"net/http"
	"strings"
	"time"
)

func artistDirectoryFilter(r *http.Request) (catalog.ArtistDirectoryFilter, error) {
	q := r.URL.Query()
	f := catalog.ArtistDirectoryFilter{Query: strings.TrimSpace(q.Get("q")), Country: q.Get("country"), Movement: q.Get("movement"), Sort: q.Get("sort"), Cursor: q.Get("cursor")}
	for _, key := range []string{"q", "country", "movement", "sort", "cursor", "popular", "women", "limit"} {
		if len(q[key]) > 1 {
			return f, catalog.ErrChronologyFilter
		}
	}
	if f.Sort == "" {
		f.Sort = "popular"
	}
	if len(f.Query) > 200 || (f.Country != "" && !countryPattern.MatchString(f.Country)) || (f.Movement != "" && !validArtistSlug(f.Movement)) || !allowed(f.Sort, "popular", "name") || !allowed(q.Get("popular"), "", "true", "false") || !allowed(q.Get("women"), "", "true", "false") {
		return f, catalog.ErrChronologyFilter
	}
	f.Popular = q.Get("popular") == "true"
	f.Women = q.Get("women") == "true"
	var err error
	f.Limit, err = integerQuery(r, "limit", 24, 1, 60)
	if err != nil || len(f.Cursor) > 2048 {
		return f, catalog.ErrChronologyFilter
	}
	return f, nil
}
func (api *API) artistDirectory(w http.ResponseWriter, r *http.Request) {
	f, err := artistDirectoryFilter(r)
	if err != nil {
		writeError(w, 400, "INVALID_ARTIST_FILTER", "Check the artist filters or return to the first page.")
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	page, err := api.repo.BrowseArtists(ctx, f)
	if err == catalog.ErrChronologyFilter {
		writeError(w, 400, "INVALID_ARTIST_CURSOR", "These filters need a new first page.")
		return
	}
	if err != nil {
		slog.Error("artist directory failed", "error", err)
		writeError(w, 500, "ARTIST_DIRECTORY_FAILED", "The artist directory could not be loaded. Try again.")
		return
	}
	w.Header().Set("Cache-Control", "private, no-store")
	writeJSON(w, 200, page)
}
