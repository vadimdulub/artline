package httpapi

import (
	"net/http"
	"strings"
	"time"
)

func (api *API) painterOptions(w http.ResponseWriter, r *http.Request) {
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	q := r.URL.Query()
	query, museum := strings.TrimSpace(q.Get("q")), q.Get("museum")
	selected, err := parseChoices(q["selected"], museumSlugPattern.MatchString, false)
	if err != nil || len(query) > 200 || (museum != "" && (len(museum) > 100 || !museumSlugPattern.MatchString(museum))) {
		writeError(w, 400, "INVALID_FILTER", "Check the painter search and selected values.")
		return
	}
	popular, err := parsePopular(q["popular"])
	if err != nil {
		writeError(w, 400, "INVALID_POPULAR", err.Error())
		return
	}
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	result, err := api.repo.PainterOptions(ctx, query, museum, selected, preview, popular)
	if err != nil {
		api.museumError(w, err)
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, 200, result)
}
