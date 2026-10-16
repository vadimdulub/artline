package httpapi

import (
	"errors"
	"log/slog"
	"net/http"
	"strconv"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/exhibitions"
)

func (api *API) exhibitions(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	limit, err := integerQuery(r, "limit", 40, 1, 100)
	if err != nil {
		writeError(w, 400, "INVALID_EXHIBITION_FILTER", err.Error())
		return
	}
	f := exhibitions.Filter{Query: q.Get("q"), Institution: q.Get("institution"), Artist: q.Get("artist"), Artwork: q.Get("artwork"), Source: q.Get("source"), Format: q.Get("format"), State: q.Get("state"), After: q.Get("after"), Limit: limit, Collection: q.Get("collection"), Theme: q.Get("theme"), Person: q.Get("person")}
	for key, target := range map[string]**int{"start": &f.Start, "end": &f.End} {
		if q.Get(key) != "" {
			v, e := strconv.Atoi(q.Get(key))
			if e != nil {
				writeError(w, 400, "INVALID_EXHIBITION_FILTER", "Use a valid year.")
				return
			}
			*target = &v
		}
	}
	if err = f.Validate(); err != nil {
		writeError(w, 400, "INVALID_EXHIBITION_FILTER", err.Error())
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	out, err := api.exhibitionRepo.List(ctx, f)
	if err != nil {
		api.exhibitionError(w, err)
		return
	}
	writeJSON(w, 200, out)
}

func (api *API) exhibition(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	out, err := api.exhibitionRepo.ByID(ctx, r.PathValue("id"))
	if err != nil {
		api.exhibitionError(w, err)
		return
	}
	writeJSON(w, 200, out)
}

func (api *API) exhibitionEntries(w http.ResponseWriter, r *http.Request) {
	limit, err := integerQuery(r, "limit", 50, 1, 100)
	after := r.URL.Query().Get("after")
	participation := r.URL.Query().Get("participation")
	if (participation != "" && participation != "exhibited") || err != nil || (after != "" && !exhibitions.ValidID(after)) {
		writeError(w, 400, "INVALID_EXHIBITION_PAGE", "Use a valid entry cursor and a limit from 1 to 100.")
		return
	}
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	out, err := api.exhibitionRepo.Entries(ctx, r.PathValue("id"), after, limit, participation)
	if err != nil {
		api.exhibitionError(w, err)
		return
	}
	writeJSON(w, 200, out)
}

func (api *API) exhibitionError(w http.ResponseWriter, err error) {
	if errors.Is(err, exhibitions.ErrNotFound) {
		writeError(w, 404, "EXHIBITION_NOT_FOUND", "This exhibition is not in the catalogue.")
		return
	}
	slog.Error("exhibition query failed", "error", err)
	writeError(w, 503, "EXHIBITIONS_UNAVAILABLE", "Exhibitions could not be loaded. Please try again.")
}

func (api *API) exhibitionArtwork(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	out, err := api.exhibitionRepo.Artwork(ctx, r.PathValue("id"))
	if err != nil {
		api.exhibitionError(w, err)
		return
	}
	writeJSON(w, 200, out)
}
func (api *API) exhibitionArtworkAppearances(w http.ResponseWriter, r *http.Request) {
	limit, err := integerQuery(r, "limit", 40, 1, 100)
	after := r.URL.Query().Get("after")
	if err != nil || (after != "" && !exhibitions.ValidID(after)) {
		writeError(w, 400, "INVALID_EXHIBITION_PAGE", "Use a valid entry cursor and a limit from 1 to 100.")
		return
	}
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	out, err := api.exhibitionRepo.ArtworkAppearances(ctx, r.PathValue("id"), after, limit)
	if err != nil {
		api.exhibitionError(w, err)
		return
	}
	writeJSON(w, 200, out)
}

// A shared three-segment route avoids ServeMux's ambiguous wildcard intersection
// between /{exhibition}/entries and /artworks/{object}.
func (api *API) exhibitionSubresource(w http.ResponseWriter, r *http.Request) {
	if r.PathValue("id") == "artworks" {
		r.SetPathValue("id", r.PathValue("action"))
		api.exhibitionArtwork(w, r)
		return
	}
	if r.PathValue("action") == "entries" {
		api.exhibitionEntries(w, r)
		return
	}
	writeError(w, 404, "EXHIBITION_NOT_FOUND", "This exhibition resource is not in the catalogue.")
}
