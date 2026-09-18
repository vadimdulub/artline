package httpapi

import (
	"errors"
	"log/slog"
	"net/http"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/books"
)

func (api *API) books(w http.ResponseWriter, r *http.Request) {
	start, err := integerQuery(r, "start", books.Bounds.Start, books.Bounds.Start, books.Bounds.End)
	if err != nil {
		writeError(w, 400, "INVALID_START_YEAR", err.Error())
		return
	}
	end, err := integerQuery(r, "end", books.Bounds.End, books.Bounds.Start, books.Bounds.End)
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
	q := r.URL.Query()
	women, top100, ok := bookDiscoverySelection(w, r)
	if !ok {
		return
	}
	filter := books.Filter{Range: books.Range{Start: start, End: end}, View: q.Get("view"), Query: q.Get("q"), Authors: q["author"], Languages: q["language"], Countries: q["country"], Regions: q["region"], Women: women, Top100: top100, After: q.Get("after"), Limit: limit, Preview: preview}
	if err := filter.Validate(); err != nil {
		writeError(w, 400, "INVALID_BOOK_FILTER", err.Error())
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	result, err := api.bookRepo.List(ctx, filter)
	if err != nil {
		api.bookError(w, err)
		return
	}
	writeJSON(w, 200, result)
}
func (api *API) book(w http.ResponseWriter, r *http.Request) {
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	result, err := api.bookRepo.ByID(ctx, r.PathValue("id"), preview)
	if err != nil {
		api.bookError(w, err)
		return
	}
	writeJSON(w, 200, result)
}
func (api *API) bookAuthors(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if len(query) > 200 {
		writeError(w, 400, "INVALID_QUERY", "Use at most 200 characters.")
		return
	}
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	women, top100, ok := bookDiscoverySelection(w, r)
	if !ok {
		return
	}
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	result, err := api.bookRepo.Authors(ctx, query, preview, women, top100)
	if err != nil {
		api.bookError(w, err)
		return
	}
	writeJSON(w, 200, result)
}

func bookDiscoverySelection(w http.ResponseWriter, r *http.Request) (bool, bool, bool) {
	women, err := parseWomen(r.URL.Query()["women"])
	if err != nil {
		writeError(w, 400, "INVALID_WOMEN", err.Error())
		return false, false, false
	}
	values := r.URL.Query()["top100"]
	if len(values) > 1 || (len(values) == 1 && values[0] != "true" && values[0] != "false") {
		writeError(w, 400, "INVALID_TOP100", "Use top100=true or top100=false once.")
		return false, false, false
	}
	return women, len(values) == 1 && values[0] == "true", true
}

func (api *API) bookFacets(w http.ResponseWriter, r *http.Request) {
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	women, top100, ok := bookDiscoverySelection(w, r)
	if !ok {
		return
	}
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	result, err := api.bookRepo.Facets(ctx, preview, women, top100)
	if err != nil {
		api.bookError(w, err)
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, 200, result)
}
func (api *API) bookError(w http.ResponseWriter, err error) {
	if errors.Is(err, books.ErrNotFound) {
		writeError(w, 404, "BOOK_NOT_FOUND", "This book is not in the current selection.")
		return
	}
	slog.Error("book catalogue query failed", "error", err)
	writeError(w, 503, "BOOKS_UNAVAILABLE", "The book catalogue could not be loaded. Please try again.")
}
