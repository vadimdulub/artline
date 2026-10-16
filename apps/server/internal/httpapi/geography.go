package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/geography"
	"log/slog"
	"net/http"
	"regexp"
	"time"
)

var mapUUID = regexp.MustCompile(`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`)
var mapRecordID = regexp.MustCompile(`^[a-zA-Z0-9_-]{1,100}$`)

func (api *API) mapLocations(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	kind := q.Get("kind")
	ids := q["id"]
	if kind != "artist" && kind != "artwork" && kind != "book" && kind != "event" {
		writeError(w, 400, "INVALID_MAP_KIND", "Choose artist, artwork, book or event.")
		return
	}
	if len(ids) == 0 || len(ids) > geography.MaxIDs {
		writeError(w, 400, "INVALID_MAP_IDS", "Use between 1 and 80 IDs.")
		return
	}
	seen := map[string]bool{}
	for _, id := range ids {
		valid := mapRecordID.MatchString(id)
		if kind == "artist" || kind == "artwork" {
			valid = mapUUID.MatchString(id)
		}
		if !valid || seen[id] {
			writeError(w, 400, "INVALID_MAP_IDS", "Use valid, unique catalogue IDs.")
			return
		}
		seen[id] = true
	}
	start, err := integerQuery(r, "start", -12000, -12000, 2100)
	if err != nil {
		writeError(w, 400, "INVALID_RANGE", err.Error())
		return
	}
	end, err := integerQuery(r, "end", 2000, -12000, 2100)
	if err != nil || start > end {
		writeError(w, 400, "INVALID_RANGE", "Choose a valid year range.")
		return
	}
	ctx, cancel := contextWithTimeout(r, 5*time.Second)
	defer cancel()
	result, err := geography.Lookup(ctx, api.db, kind, ids, start, end)
	if err != nil {
		slog.Error("map locations failed", "error", err)
		writeError(w, 500, "MAP_QUERY_FAILED", "Place evidence could not be loaded.")
		return
	}
	writeJSON(w, 200, result)
}
