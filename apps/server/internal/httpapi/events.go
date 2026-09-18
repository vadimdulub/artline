package httpapi

import (
	"errors"
	"github.com/vadimdulub/artline/apps/server/internal/events"
	"log/slog"
	"net/http"
	"time"
)

func (api *API) eventTop100(w http.ResponseWriter, r *http.Request) (bool, bool) {
	values := r.URL.Query()["top100"]
	if len(values) > 1 || (len(values) == 1 && values[0] != "true" && values[0] != "false") {
		writeError(w, 400, "INVALID_TOP100", "Use top100=true or top100=false once.")
		return false, false
	}
	return len(values) == 1 && values[0] == "true", true
}
func (api *API) events(w http.ResponseWriter, r *http.Request) {
	start, err := integerQuery(r, "start", events.Bounds.Start, events.Bounds.Start, events.Bounds.End)
	if err != nil {
		writeError(w, 400, "INVALID_START_YEAR", err.Error())
		return
	}
	end, err := integerQuery(r, "end", events.Bounds.End, events.Bounds.Start, events.Bounds.End)
	if err != nil {
		writeError(w, 400, "INVALID_END_YEAR", err.Error())
		return
	}
	limit, err := integerQuery(r, "limit", 100, 1, 100)
	if err != nil {
		writeError(w, 400, "INVALID_LIMIT", err.Error())
		return
	}
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	top, ok := api.eventTop100(w, r)
	if !ok {
		return
	}
	q := r.URL.Query()
	f := events.Filter{Range: events.Range{Start: start, End: end}, Query: q.Get("q"), After: q.Get("after"), Topics: q["topic"], Countries: q["country"], Regions: q["region"], Kinds: q["kind"], Top100: top, Preview: preview, Limit: limit}
	if err = f.Validate(); err != nil {
		writeError(w, 400, "INVALID_EVENT_FILTER", err.Error())
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	out, err := api.eventRepo.List(ctx, f)
	if err != nil {
		api.eventError(w, err)
		return
	}
	writeJSON(w, 200, out)
}
func (api *API) event(w http.ResponseWriter, r *http.Request) {
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	out, err := api.eventRepo.ByID(ctx, r.PathValue("id"), preview)
	if err != nil {
		api.eventError(w, err)
		return
	}
	writeJSON(w, 200, out)
}
func (api *API) eventFacets(w http.ResponseWriter, r *http.Request) {
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	top, ok := api.eventTop100(w, r)
	if !ok {
		return
	}
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	out, err := api.eventRepo.Facets(ctx, preview, top)
	if err != nil {
		api.eventError(w, err)
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, 200, out)
}
func (api *API) eventError(w http.ResponseWriter, err error) {
	if errors.Is(err, events.ErrNotFound) {
		writeError(w, 404, "EVENT_NOT_FOUND", "This event is not in the current selection.")
		return
	}
	slog.Error("events query failed", "error", err)
	writeError(w, 503, "EVENTS_UNAVAILABLE", "Events could not be loaded. Please try again.")
}
