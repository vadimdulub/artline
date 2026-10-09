package httpapi

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/atlas"
	"github.com/vadimdulub/artline/apps/server/internal/books"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/events"
	"github.com/vadimdulub/artline/apps/server/internal/member"
)

type API struct {
	config    config.Config
	db        *pgxpool.Pool
	repo      *catalog.Repository
	bookRepo  *books.Repository
	eventRepo *events.Repository
	atlasRepo *atlas.Repository
}

func New(cfg config.Config, db *pgxpool.Pool) http.Handler {
	api := &API{config: cfg, db: db, repo: catalog.NewRepository(db), bookRepo: books.NewRepository(db), eventRepo: events.NewRepository(db), atlasRepo: atlas.NewRepository(db)}
	mux := http.NewServeMux()
	memberOrigin := cfg.AuthOrigin
	if cfg.LocalDebug {
		memberOrigin = cfg.FrontendOrigin
	}
	member.New(member.Config{ClientID: cfg.GoogleClientID, ClientSecret: cfg.GoogleClientSecret, CookieKey: cfg.AuthCookieKey, Origin: memberOrigin, LocalDebug: cfg.LocalDebug}, member.PostgresStore{DB: db}).Register(mux)
	mux.HandleFunc("GET /health", api.health)
	mux.HandleFunc("GET /ready", api.ready)
	mux.HandleFunc("GET /api/v1/timeline", api.timeline)
	mux.HandleFunc("GET /api/v1/books", api.books)
	mux.HandleFunc("GET /api/v1/books/authors", api.bookAuthors)
	mux.HandleFunc("GET /api/v1/books/facets", api.bookFacets)
	mux.HandleFunc("GET /api/v1/books/{id}", api.book)
	mux.HandleFunc("GET /api/v1/events", api.events)
	mux.HandleFunc("GET /api/v1/events/facets", api.eventFacets)
	mux.HandleFunc("GET /api/v1/events/{id}", api.event)
	mux.HandleFunc("GET /api/v1/atlas", api.atlasTimeline)
	mux.HandleFunc("GET /api/v1/atlas/presets", api.atlasPresets)
	mux.HandleFunc("GET /api/v1/atlas/geography", api.atlasGeography)
	mux.HandleFunc("GET /api/v1/atlas/creators", api.atlasCreators)
	mux.HandleFunc("GET /api/v1/atlas/artworks/{id}", api.atlasArtwork)
	mux.HandleFunc("GET /api/v1/timeline/facets", api.timelineFacets)
	mux.HandleFunc("GET /api/v1/painters/options", api.painterOptions)
	mux.HandleFunc("GET /api/v1/artists", api.artistDirectory)
	mux.HandleFunc("GET /api/v1/artworks", api.artworkDirectory)
	mux.HandleFunc("GET /api/v1/artists/{slug}", api.artist)
	mux.HandleFunc("GET /api/v1/seo/sitemaps", api.sitemapShards)
	mux.HandleFunc("GET /api/v1/seo/sitemaps/{kind}/{prefix}", api.sitemapEntries)
	mux.HandleFunc("GET /api/v1/seo/artists", api.discoveryArtists)
	mux.HandleFunc("GET /api/v1/artists/{slug}/works", api.artistWorks)
	mux.HandleFunc("GET /api/v1/artists/{slug}/works/{id}", api.artistArtwork)
	mux.HandleFunc("GET /api/v1/museums", api.museums)
	mux.HandleFunc("GET /api/v1/museums/{slug}", api.museum)
	mux.HandleFunc("GET /api/v1/museums/{slug}/works", api.museumWorks)
	mux.HandleFunc("GET /api/v1/museums/{slug}/works/{id}", api.museumArtwork)
	mux.HandleFunc("GET /api/v1/catalogue/artists", api.catalogueArtists)

	var catalogue http.Handler = catalogueAdmission(mux, 4, 16, 500*time.Millisecond)
	if db != nil {
		cache := newCatalogueCache(func(ctx context.Context) (string, error) {
			var snapshot string
			err := db.QueryRow(ctx, "SELECT sum(revision)::text FROM public.catalogue_cache_revisions HAVING count(*)=64").Scan(&snapshot)
			return snapshot, err
		})
		catalogue = api.cacheCatalogue(cache, catalogue)
	}
	handler := api.recoverPanic(api.requestLog(api.cors(catalogueReadBudget(catalogue))))
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Robots-Tag", "noindex")
		w.Header().Set("Cache-Control", "private, no-store")
		handler.ServeHTTP(w, r.WithContext(catalog.WithPublicRead(r.Context())))
	})
}

func (api *API) health(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (api *API) ready(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := contextWithTimeout(r, 2*time.Second)
	defer cancel()
	if err := api.db.Ping(ctx); err != nil {
		writeError(w, http.StatusServiceUnavailable, "DATABASE_UNAVAILABLE", "PostgreSQL is not ready.")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ready"})
}

func (api *API) timeline(w http.ResponseWriter, r *http.Request) {
	start, err := integerQuery(r, "start", 1100, 1100, 2000)
	if err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_START_YEAR", err.Error())
		return
	}
	end, err := integerQuery(r, "end", 2000, 1100, 2000)
	if err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_END_YEAR", err.Error())
		return
	}
	if start > end {
		writeError(w, http.StatusBadRequest, "INVALID_RANGE", "Start year must be before or equal to end year.")
		return
	}
	q := r.URL.Query()
	choices := map[string][]string{}
	for key, valid := range map[string]func(string) bool{"country": countryPattern.MatchString, "movement": museumSlugPattern.MatchString, "painter": validArtistSlug, "work_type": validWorkType} {
		choices[key], err = parseChoices(q[key], valid, key == "country")
		if err != nil {
			writeError(w, 400, "INVALID_FILTER", err.Error())
			return
		}
	}
	if len(q.Get("q")) > 200 {
		writeError(w, 400, "INVALID_QUERY", "Use at most 200 characters.")
		return
	}
	regions, err := parseRegions(r.URL.Query()["region"])
	if err != nil {
		writeError(w, 400, "INVALID_REGIONS", err.Error())
		return
	}
	popular, err := parsePopular(r.URL.Query()["popular"])
	if err != nil {
		writeError(w, 400, "INVALID_POPULAR", err.Error())
		return
	}
	women, err := parseWomen(r.URL.Query()["women"])
	if err != nil {
		writeError(w, 400, "INVALID_WOMEN", err.Error())
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	response, err := api.repo.Timeline(ctx, catalog.TimelineFilter{
		StartYear:   start,
		EndYear:     end,
		Query:       strings.TrimSpace(r.URL.Query().Get("q")),
		Countries:   choices["country"],
		Movements:   choices["movement"],
		Painters:    choices["painter"],
		Regions:     regions,
		WorkTypes:   choices["work_type"],
		PopularOnly: popular,
		WomenOnly:   women,
	})
	if err != nil {
		slog.Error("timeline query failed", "error", err)
		writeError(w, http.StatusInternalServerError, "TIMELINE_QUERY_FAILED", "The timeline could not be loaded.")
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, http.StatusOK, response)
}

func (api *API) timelineFacets(w http.ResponseWriter, r *http.Request) {
	popular, err := parsePopular(r.URL.Query()["popular"])
	if err != nil {
		writeError(w, 400, "INVALID_POPULAR", err.Error())
		return
	}
	women, err := parseWomen(r.URL.Query()["women"])
	if err != nil {
		writeError(w, 400, "INVALID_WOMEN", err.Error())
		return
	}
	facets, err := api.repo.DiscoveryFacets(r.Context(), popular, women)
	if err != nil {
		slog.Error("timeline facet query failed", "error", err)
		writeError(w, http.StatusInternalServerError, "FACET_QUERY_FAILED", "Timeline filters could not be loaded.")
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, http.StatusOK, facets)
}

func (api *API) artist(w http.ResponseWriter, r *http.Request) {
	slug := artistLookupSlug(r.PathValue("slug"))
	if slug == "" {
		writeError(w, http.StatusBadRequest, "INVALID_SLUG", "Artist slug is required.")
		return
	}
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	artist, err := api.repo.ArtistBySlug(ctx, slug)
	if errors.Is(err, catalog.ErrNotFound) {
		writeError(w, http.StatusNotFound, "ARTIST_NOT_FOUND", "This painter is not in the catalogue.")
		return
	}
	if err != nil {
		slog.Error("artist query failed", "slug", slug, "error", err)
		writeError(w, http.StatusInternalServerError, "ARTIST_QUERY_FAILED", "The painter could not be loaded.")
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, http.StatusOK, artist)
}

func (api *API) catalogueArtists(w http.ResponseWriter, r *http.Request) {
	if len(r.URL.Query().Get("q")) > 200 {
		writeError(w, 400, "INVALID_QUERY", "Use at most 200 characters.")
		return
	}
	limit, err := integerQuery(r, "limit", 100, 1, 200)
	if err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_LIMIT", err.Error())
		return
	}
	offset, err := integerQuery(r, "offset", 0, 0, 100000)
	if err != nil {
		writeError(w, 400, "INVALID_OFFSET", err.Error())
		return
	}
	sort := r.URL.Query().Get("sort")
	if !allowed(sort, "", "name", "date", "updated") {
		writeError(w, 400, "INVALID_SORT", "Unknown sort field.")
		return
	}
	artists, err := api.repo.Catalogue(r.Context(), strings.TrimSpace(r.URL.Query().Get("q")), limit+1, offset, sort)
	if err != nil {
		slog.Error("catalogue query failed", "error", err)
		writeError(w, http.StatusInternalServerError, "CATALOGUE_QUERY_FAILED", "The catalogue could not be loaded.")
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	more := len(artists) > limit
	if more {
		artists = artists[:limit]
	}
	writeJSON(w, http.StatusOK, map[string]any{"items": artists, "has_more": more})
}

func (api *API) cors(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if origin != "" && strings.TrimSuffix(origin, "/") == strings.TrimSuffix(api.config.FrontendOrigin, "/") {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Vary", "Origin")
			w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
		}
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func (api *API) requestLog(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		started := time.Now()
		next.ServeHTTP(w, r)
		slog.Info("request", "method", r.Method, "path", r.URL.Path, "duration_ms", time.Since(started).Milliseconds())
	})
}

func (api *API) recoverPanic(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if recovered := recover(); recovered != nil {
				slog.Error("request panic", "value", recovered)
				writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "The request could not be completed.")
			}
		}()
		next.ServeHTTP(w, r)
	})
}

func integerQuery(r *http.Request, key string, fallback, minimum, maximum int) (int, error) {
	raw := strings.TrimSpace(r.URL.Query().Get(key))
	if raw == "" {
		return fallback, nil
	}
	value, err := strconv.Atoi(raw)
	if err != nil || value < minimum || value > maximum {
		return 0, fmt.Errorf("%s must be a number from %d through %d", key, minimum, maximum)
	}
	return value, nil
}

func allowed(value string, values ...string) bool {
	for _, candidate := range values {
		if value == candidate {
			return true
		}
	}
	return false
}

type errorResponse struct {
	Error struct {
		Code    string `json:"code"`
		Message string `json:"message"`
	} `json:"error"`
}

func writeError(w http.ResponseWriter, status int, code, message string) {
	var response errorResponse
	response.Error.Code = code
	response.Error.Message = message
	writeJSON(w, status, response)
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(value); err != nil {
		slog.Error("encode response", "error", err)
	}
}
