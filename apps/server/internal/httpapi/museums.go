package httpapi

import (
	"errors"
	"log/slog"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

var museumSlugPattern = regexp.MustCompile(`^[a-z0-9]+(?:-[a-z0-9]+)*$`)
var museumIDPattern = regexp.MustCompile(`^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$`)

func museumFilter(r *http.Request) (catalog.MuseumFilter, error) {
	q := r.URL.Query()
	f := catalog.MuseumFilter{Query: strings.TrimSpace(q.Get("q")), Selection: q.Get("selection"), Display: q.Get("display"), Sort: q.Get("sort"), Cursor: q.Get("cursor")}
	var err error
	for _, spec := range []struct {
		key   string
		dest  *[]string
		valid func(string) bool
	}{
		{"artist", &f.Artists, validArtistSlug}, {"movement", &f.Movements, museumSlugPattern.MatchString},
		{"venue", &f.Venues, museumIDPattern.MatchString}, {"work_type", &f.WorkTypes, validWorkType},
	} {
		*spec.dest, err = parseChoices(q[spec.key], spec.valid, false)
		if err != nil {
			return f, catalog.ErrMuseumFilter
		}
	}
	f.Regions, err = parseRegions(q["region"])
	if err != nil {
		return f, err
	}
	f.Countries, err = parseRegions(q["country"])
	if err != nil {
		return f, err
	}
	for i, country := range f.Countries {
		if len(country) != 2 {
			return f, catalog.ErrMuseumFilter
		}
		f.Countries[i] = strings.ToUpper(country)
	}
	f.Limit, err = integerQuery(r, "limit", 24, 1, 60)
	if err != nil {
		return f, err
	}
	if len(f.Query) > 200 || len(f.Cursor) > 2048 || !allowed(f.Selection, "", "museum") || !allowed(f.Display, "", "on_view") || !allowed(f.Sort, "", "images", "year", "title", "curated") {
		return f, catalog.ErrMuseumFilter
	}
	if f.Artist != "" && !validArtistSlug(f.Artist) {
		return f, catalog.ErrMuseumFilter
	}
	if f.Movement != "" && (len(f.Movement) > 100 || !museumSlugPattern.MatchString(f.Movement)) {
		return f, catalog.ErrMuseumFilter
	}
	if f.Venue != "" && !museumIDPattern.MatchString(f.Venue) {
		return f, catalog.ErrMuseumFilter
	}
	if f.WorkType != "" && !validWorkType(f.WorkType) {
		return f, catalog.ErrMuseumFilter
	}
	for _, name := range []string{"unknown_date", "image_only"} {
		if !allowed(q.Get(name), "", "0", "1") {
			return f, catalog.ErrMuseumFilter
		}
	}
	f.UnknownDate = q.Get("unknown_date") == "1"
	f.ImageOnly = q.Get("image_only") == "1"
	for _, name := range []string{"start", "end"} {
		if value := q.Get(name); value != "" {
			year, e := strconv.Atoi(value)
			if e != nil || year < -10000 || year > 3000 {
				return f, catalog.ErrMuseumFilter
			}
			if name == "start" {
				f.Start = &year
			} else {
				f.End = &year
			}
		}
	}
	if f.Start != nil && f.End != nil && *f.Start > *f.End {
		return f, catalog.ErrMuseumFilter
	}
	if f.UnknownDate && (f.Start != nil || f.End != nil) {
		return f, catalog.ErrMuseumFilter
	}
	return f, nil
}
func (api *API) museumError(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, catalog.ErrNotFound):
		writeError(w, 404, "MUSEUM_RECORD_NOT_FOUND", "This museum or artwork is not available in the catalogue.")
	case errors.Is(err, catalog.ErrMuseumFilter):
		writeError(w, 400, "INVALID_MUSEUM_FILTER", "Check your filters or return to the first page.")
	default:
		slog.Error("museum request failed", "error", err)
		writeError(w, 500, "MUSEUM_REQUEST_FAILED", "The museum catalogue could not be loaded. Please try again.")
	}
}
func (api *API) museums(w http.ResponseWriter, r *http.Request) {
	f, err := museumFilter(r)
	if err != nil {
		api.museumError(w, catalog.ErrMuseumFilter)
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	result, err := api.repo.Museums(ctx, f)
	if err != nil {
		api.museumError(w, err)
		return
	}
	writeJSON(w, 200, result)
}
func (api *API) museum(w http.ResponseWriter, r *http.Request) {
	slug := r.PathValue("slug")
	if len(slug) > 100 || !museumSlugPattern.MatchString(slug) {
		api.museumError(w, catalog.ErrNotFound)
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	result, err := api.repo.Museum(ctx, slug)
	if err != nil {
		api.museumError(w, err)
		return
	}
	writeJSON(w, 200, result)
}
func (api *API) museumWorks(w http.ResponseWriter, r *http.Request) {
	f, err := museumFilter(r)
	if err != nil {
		api.museumError(w, catalog.ErrMuseumFilter)
		return
	}
	slug := r.PathValue("slug")
	if len(slug) > 100 || !museumSlugPattern.MatchString(slug) {
		api.museumError(w, catalog.ErrNotFound)
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	result, err := api.repo.MuseumWorks(ctx, slug, f)
	if err != nil {
		api.museumError(w, err)
		return
	}
	writeJSON(w, 200, result)
}
func (api *API) museumArtwork(w http.ResponseWriter, r *http.Request) {
	if !museumIDPattern.MatchString(r.PathValue("id")) {
		api.museumError(w, catalog.ErrNotFound)
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	result, err := api.repo.MuseumArtwork(ctx, r.PathValue("slug"), r.PathValue("id"))
	if err != nil {
		api.museumError(w, err)
		return
	}
	writeJSON(w, 200, result)
}
