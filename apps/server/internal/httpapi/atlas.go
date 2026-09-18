package httpapi

import (
	"errors"
	"github.com/vadimdulub/artline/apps/server/internal/atlas"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"log/slog"
	"net/http"
	"net/url"
	"regexp"
	"time"
)

func (api *API) atlasPresets(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"presets": atlas.Presets(), "types": atlas.Definitions, "regions": atlas.Regions, "continents": atlas.Continents, "bounds": atlas.Bounds, "defaultPreset": ""})
}
func (api *API) atlasTimeline(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	for _, key := range []string{"start", "end", "preset", "window", "q", "highlights", "region", "limit", "after_artwork", "after_book", "after_event", "selection"} {
		if len(q[key]) > 1 {
			writeError(w, 400, "INVALID_ATLAS_FILTER", "Use each atlas filter once.")
			return
		}
	}
	rangeValue := atlas.Bounds
	id := q.Get("preset")
	if id != "" {
		p, ok := atlas.FindPreset(id)
		if !ok {
			writeError(w, 400, "INVALID_PRESET", "Choose one of the listed historical lenses.")
			return
		}
		rangeValue = p.Context
		if q.Get("window") == "period" {
			rangeValue = p.Period
		}
	}
	if q.Get("window") != "" && q.Get("window") != "period" && q.Get("window") != "context" {
		writeError(w, 400, "INVALID_WINDOW", "Choose the main period or before and after.")
		return
	}
	if q.Has("start") != q.Has("end") {
		writeError(w, 400, "INVALID_RANGE", "Enter both start and end years.")
		return
	}
	start, err := integerQuery(r, "start", rangeValue.Start, atlas.Bounds.Start, atlas.Bounds.End)
	if err != nil {
		writeError(w, 400, "INVALID_RANGE", err.Error())
		return
	}
	end, err := integerQuery(r, "end", rangeValue.End, atlas.Bounds.Start, atlas.Bounds.End)
	if err != nil {
		writeError(w, 400, "INVALID_RANGE", err.Error())
		return
	}
	limit, err := integerQuery(r, "limit", 60, 1, 60)
	if err != nil {
		writeError(w, 400, "INVALID_LIMIT", err.Error())
		return
	}
	highlights := q.Get("highlights")
	if highlights != "" && highlights != "true" && highlights != "false" {
		writeError(w, 400, "INVALID_HIGHLIGHTS", "Use highlights=true or highlights=false.")
		return
	}
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	f := atlas.Filter{Range: atlas.Range{Start: start, End: end}, Query: q.Get("q"), Region: q.Get("region"), Countries: q["country"], Continents: q["continent"], Types: q["type"], Highlights: highlights != "false", Preview: preview, Limit: limit, After: map[string]string{}}
	if value := q.Get("selection"); value != "" && value != "true" && value != "false" {
		writeError(w, 400, "INVALID_SELECTION", "Use selection=true or selection=false.")
		return
	}
	f.Selection = q.Get("selection") == "true" || (q.Get("selection") == "" && len(q["type"]) == 0 && !q.Has("preset") && !q.Has("start") && !q.Has("q"))
	f.Entities = map[string]url.Values{}
	for kind, fields := range atlas.EntityFields {
		values := url.Values{}
		for _, field := range fields {
			if v, ok := q[kind+"_"+field]; ok {
				values[field] = v
			}
		}
		if len(values) > 0 {
			f.Entities[kind] = values
		}
	}
	f.Picks = map[string][]string{}
	for _, kind := range atlas.Definitions {
		if ids := q["pick_"+kind.Key]; len(ids) > 0 {
			f.Picks[kind.Key] = ids
		}
	}
	for _, kind := range atlas.Definitions {
		if v := q.Get("after_" + kind.Key); v != "" {
			f.After[kind.Key] = v
		}
	}
	if err = f.Validate(); err != nil {
		writeError(w, 400, "INVALID_ATLAS_FILTER", "Choose valid types and ordered years from 12000 BCE to 2000; there is no year zero. A page link must match its filters.")
		return
	}
	ctx, cancel := contextWithTimeout(r, 10*time.Second)
	defer cancel()
	out, err := api.atlasRepo.List(ctx, f)
	if err != nil {
		api.atlasError(w, err)
		return
	}
	writeJSON(w, 200, out)
}
func (api *API) atlasArtwork(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	if !regexp.MustCompile(`^[a-fA-F0-9]{8}(-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$`).MatchString(id) {
		writeError(w, 400, "INVALID_ID", "Invalid artwork identifier.")
		return
	}
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	visible, err := api.atlasRepo.ArtworkVisible(ctx, id, preview)
	if err != nil {
		api.atlasError(w, err)
		return
	}
	if !visible {
		api.atlasError(w, atlas.ErrNotFound)
		return
	}
	out, err := api.repo.AtlasArtwork(ctx, id, preview)
	if err != nil {
		api.atlasError(w, err)
		return
	}
	writeJSON(w, 200, out)
}
func (api *API) atlasError(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, atlas.ErrFilter):
		writeError(w, 400, "INVALID_ATLAS_FILTER", "The filter or page link is invalid. Reset the view and try again.")
	case errors.Is(err, atlas.ErrNotFound) || errors.Is(err, catalog.ErrNotFound):
		writeError(w, 404, "NOT_FOUND", "This record is not available.")
	default:
		slog.Error("atlas request failed", "error", err)
		writeError(w, 503, "ATLAS_UNAVAILABLE", "This part of the atlas could not be loaded. Please try again.")
	}
}

func (api *API) atlasGeography(w http.ResponseWriter, r *http.Request) {
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	countries, err := api.atlasRepo.Countries(ctx, preview)
	if err != nil {
		api.atlasError(w, err)
		return
	}
	writeJSON(w, 200, map[string]any{"countries": countries})
}
