package httpapi

import (
	"errors"
	"log/slog"
	"net/http"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

func (api *API) artistConnections(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	if len(q["direction"]) != 1 || len(q["cursor"]) > 1 || !allowed(q.Get("direction"), "incoming", "outgoing") || len(q.Get("cursor")) > 4096 {
		writeError(w, 400, "INVALID_CONNECTIONS_FILTER", "Choose a connection direction and return to the first page.")
		return
	}
	slug := sourceArtistSlug(r.PathValue("slug"))
	if !validArtistSlug(slug) {
		writeError(w, 404, "ARTIST_NOT_FOUND", "This artist is not available.")
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	page, err := api.repo.ArtistConnectionPage(ctx, slug, q.Get("direction"), q.Get("cursor"))
	switch {
	case errors.Is(err, catalog.ErrNotFound):
		writeError(w, 404, "ARTIST_NOT_FOUND", "This artist is not available.")
	case errors.Is(err, catalog.ErrConnectionsFilter):
		writeError(w, 400, "INVALID_CONNECTIONS_FILTER", "Return to the first connections page.")
	case err != nil:
		slog.Error("artist connections failed", "error", err)
		writeError(w, 500, "CONNECTIONS_FAILED", "Connections could not be loaded. Try again.")
	default:
		writeJSON(w, 200, page)
	}
}
