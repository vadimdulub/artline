package httpapi

import (
	"errors"
	"log/slog"
	"net/http"
	"strconv"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

func artistWorksFilter(r *http.Request) (catalog.ArtistWorksFilter, error) {
	q := r.URL.Query()
	f := catalog.ArtistWorksFilter{Cursor: q.Get("cursor"), Undated: q.Get("undated") == "1"}
	var err error
	f.Limit, err = integerQuery(r, "limit", 24, 1, 60)
	if err != nil || len(f.Cursor) > 2048 || !allowed(q.Get("undated"), "", "0", "1") {
		return f, catalog.ErrChronologyFilter
	}
	if raw := q.Get("year"); raw != "" {
		year, e := strconv.Atoi(raw)
		if e != nil || year < -10000 || year > 3000 || f.Undated {
			return f, catalog.ErrChronologyFilter
		}
		f.Year = &year
	}
	return f, nil
}

func (api *API) artistChronologyError(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, catalog.ErrNotFound):
		writeError(w, 404, "ARTWORK_NOT_FOUND", "This painter or artwork is not available in the catalogue.")
	case errors.Is(err, catalog.ErrChronologyFilter):
		writeError(w, 400, "INVALID_CHRONOLOGY_FILTER", "Check the artwork year or return to the first page.")
	default:
		slog.Error("artwork chronology failed", "error", err)
		writeError(w, 500, "CHRONOLOGY_FAILED", "The artwork chronology could not be loaded. Try again.")
	}
}
func (api *API) artistWorks(w http.ResponseWriter, r *http.Request) {
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	f, err := artistWorksFilter(r)
	if err != nil {
		api.artistChronologyError(w, err)
		return
	}
	slug := r.PathValue("slug")
	if len(slug) > 100 || !museumSlugPattern.MatchString(slug) {
		api.artistChronologyError(w, catalog.ErrNotFound)
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	page, err := api.repo.ArtistWorks(ctx, slug, f, preview)
	if err != nil {
		api.artistChronologyError(w, err)
		return
	}
	w.Header().Set("Cache-Control", "private, no-store")
	writeJSON(w, 200, page)
}
func (api *API) artistArtwork(w http.ResponseWriter, r *http.Request) {
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	slug, id := r.PathValue("slug"), r.PathValue("id")
	if len(slug) > 100 || !museumSlugPattern.MatchString(slug) || !museumIDPattern.MatchString(id) {
		api.artistChronologyError(w, catalog.ErrNotFound)
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	work, err := api.repo.ArtistArtwork(ctx, slug, id, preview)
	if err != nil {
		api.artistChronologyError(w, err)
		return
	}
	w.Header().Set("Cache-Control", "private, no-store")
	writeJSON(w, 200, work)
}
