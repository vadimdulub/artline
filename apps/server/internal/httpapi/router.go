package httpapi

import (
	"crypto/subtle"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

type API struct {
	config config.Config
	db     *pgxpool.Pool
	repo   *catalog.Repository
}

func New(cfg config.Config, db *pgxpool.Pool) http.Handler {
	api := &API{config: cfg, db: db, repo: catalog.NewRepository(db)}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", api.health)
	mux.HandleFunc("GET /ready", api.ready)
	mux.HandleFunc("GET /api/v1/timeline", api.timeline)
	mux.HandleFunc("GET /api/v1/timeline/facets", api.timelineFacets)
	mux.HandleFunc("GET /api/v1/painters/options", api.painterOptions)
	mux.HandleFunc("GET /api/v1/artists/{slug}", api.artist)
	mux.HandleFunc("GET /api/v1/artists/{slug}/works", api.artistWorks)
	mux.HandleFunc("GET /api/v1/artists/{slug}/works/{id}", api.artistArtwork)
	mux.HandleFunc("GET /api/v1/museums", api.museums)
	mux.HandleFunc("GET /api/v1/museums/{slug}", api.museum)
	mux.HandleFunc("GET /api/v1/museums/{slug}/works", api.museumWorks)
	mux.HandleFunc("GET /api/v1/museums/{slug}/works/{id}", api.museumArtwork)
	mux.Handle("PATCH /api/v1/museums/{slug}/must-see", api.requireEditor(http.HandlerFunc(api.saveMustSee)))
	mux.HandleFunc("GET /api/v1/catalogue/artists", api.catalogueArtists)
	mux.Handle("GET /api/v1/catalogue/artists/{id}", api.requireEditor(http.HandlerFunc(api.catalogueArtist)))
	mux.Handle("POST /api/v1/catalogue/artists", api.requireEditor(http.HandlerFunc(api.createArtist)))
	mux.Handle("PATCH /api/v1/catalogue/artists/{id}", api.requireEditor(http.HandlerFunc(api.updateArtist)))
	mux.Handle("DELETE /api/v1/catalogue/artists/{id}", api.requireEditor(http.HandlerFunc(api.archiveArtist)))
	mux.Handle("POST /api/v1/catalogue/artists/{id}/restore", api.requireEditor(http.HandlerFunc(api.restoreArtist)))
	mux.Handle("GET /api/v1/coverage/summary", api.requireEditor(http.HandlerFunc(api.coverage)))
	mux.Handle("POST /api/v1/publish/validate", api.requireEditor(http.HandlerFunc(api.validatePublication)))
	mux.Handle("POST /api/v1/publish/artists/{id}", api.requireEditor(http.HandlerFunc(api.publishArtist)))
	mux.Handle("POST /api/v1/unpublish/artists/{id}", api.requireEditor(http.HandlerFunc(api.unpublishArtist)))

	return api.recoverPanic(api.requestLog(api.cors(mux)))
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
	status := strings.TrimSpace(r.URL.Query().Get("status"))
	if !allowed(status, "", "draft", "review", "published") {
		writeError(w, http.StatusBadRequest, "INVALID_STATUS", "Status must be draft, review, or published.")
		return
	}
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	if !preview {
		if status != "" && status != "published" {
			writeError(w, 401, "EDITOR_AUTH_REQUIRED", "Sign in to preview research records.")
			return
		}
		status = "published"
	}
	q := r.URL.Query()
	choices := map[string][]string{}
	for key, valid := range map[string]func(string) bool{"country": countryPattern.MatchString, "movement": museumSlugPattern.MatchString, "painter": museumSlugPattern.MatchString, "work_type": validWorkType} {
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
	ctx, cancel := contextWithTimeout(r, 8*time.Second)
	defer cancel()
	response, err := api.repo.Timeline(ctx, catalog.TimelineFilter{
		StartYear:   start,
		EndYear:     end,
		Query:       strings.TrimSpace(r.URL.Query().Get("q")),
		Countries:   choices["country"],
		Movements:   choices["movement"],
		Painters:    choices["painter"],
		Status:      status,
		Regions:     regions,
		WorkTypes:   choices["work_type"],
		PopularOnly: popular,
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
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	popular, err := parsePopular(r.URL.Query()["popular"])
	if err != nil {
		writeError(w, 400, "INVALID_POPULAR", err.Error())
		return
	}
	facets, err := api.repo.DiscoveryFacets(r.Context(), preview, popular)
	if err != nil {
		slog.Error("timeline facet query failed", "error", err)
		writeError(w, http.StatusInternalServerError, "FACET_QUERY_FAILED", "Timeline filters could not be loaded.")
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, http.StatusOK, facets)
}

func (api *API) artist(w http.ResponseWriter, r *http.Request) {
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return
	}
	slug := catalog.NormalizeSlug(r.PathValue("slug"))
	if slug == "" {
		writeError(w, http.StatusBadRequest, "INVALID_SLUG", "Artist slug is required.")
		return
	}
	artist, err := api.repo.ArtistBySlug(r.Context(), slug, preview)
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
	status := strings.TrimSpace(r.URL.Query().Get("status"))
	if !allowed(status, "", "draft", "review", "published", "archived") {
		writeError(w, http.StatusBadRequest, "INVALID_STATUS", "Unknown catalogue status.")
		return
	}
	status, includeArchived, ok := api.catalogueReadScope(w, r, status)
	if !ok {
		return
	}
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
	artists, err := api.repo.Catalogue(r.Context(), status, strings.TrimSpace(r.URL.Query().Get("q")), limit+1, offset, sort, includeArchived)
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

func (api *API) catalogueReadScope(w http.ResponseWriter, r *http.Request, status string) (string, bool, bool) {
	preview, ok := api.previewAllowed(w, r)
	if !ok {
		return "", false, false
	}
	if api.isEditor(r) {
		return status, true, true
	}
	if status == "archived" || (!preview && status != "" && status != "published") {
		writeError(w, http.StatusUnauthorized, "EDITOR_AUTH_REQUIRED", "Sign in to browse this record status.")
		return "", false, false
	}
	if !preview {
		status = "published"
	}
	return status, false, true
}

func (api *API) createArtist(w http.ResponseWriter, r *http.Request) {
	input, ok := decodeArtistInput(w, r, false)
	if !ok {
		return
	}
	artist, err := api.repo.CreateArtist(r.Context(), input)
	if err != nil {
		slog.Error("create artist failed", "error", err)
		writeError(w, http.StatusConflict, "ARTIST_CREATE_FAILED", "The painter could not be created. Check that the slug is unique.")
		return
	}
	writeJSON(w, http.StatusCreated, artist)
}

func (api *API) updateArtist(w http.ResponseWriter, r *http.Request) {
	input, ok := decodeArtistInput(w, r, true)
	if !ok {
		return
	}
	artist, err := api.repo.UpdateArtist(r.Context(), r.PathValue("id"), input)
	if errors.Is(err, catalog.ErrRevisionConflict) {
		writeError(w, http.StatusConflict, "REVISION_CONFLICT", "This painter changed after you opened it. Reload before saving.")
		return
	}
	if errors.Is(err, catalog.ErrNotFound) {
		writeError(w, http.StatusNotFound, "ARTIST_NOT_FOUND", "This painter is not in the catalogue.")
		return
	}
	if err != nil {
		slog.Error("update artist failed", "error", err)
		writeError(w, http.StatusBadRequest, "ARTIST_UPDATE_FAILED", "The painter could not be updated.")
		return
	}
	writeJSON(w, http.StatusOK, artist)
}

func (api *API) archiveArtist(w http.ResponseWriter, r *http.Request) {
	api.setArtistArchived(w, r, true)
}

func (api *API) restoreArtist(w http.ResponseWriter, r *http.Request) {
	api.setArtistArchived(w, r, false)
}

func (api *API) setArtistArchived(w http.ResponseWriter, r *http.Request, archived bool) {
	var request revisionRequest
	if !decodeJSON(w, r, &request) {
		return
	}
	if request.ExpectedRevision < 1 {
		writeError(w, 422, "EXPECTED_REVISION_REQUIRED", "Reload the record before changing its archive state.")
		return
	}
	artist, err := api.repo.SetArchived(r.Context(), r.PathValue("id"), archived, request.ExpectedRevision)
	if errors.Is(err, catalog.ErrRevisionConflict) {
		writeError(w, 409, "REVISION_CONFLICT", "This record changed. Reload before archiving or restoring it.")
		return
	}
	if errors.Is(err, catalog.ErrNotFound) {
		writeError(w, http.StatusNotFound, "ARTIST_NOT_FOUND", "This painter is not in the catalogue.")
		return
	}
	if err != nil {
		slog.Error("archive state update failed", "error", err)
		writeError(w, http.StatusInternalServerError, "ARCHIVE_UPDATE_FAILED", "The archive state could not be changed.")
		return
	}
	writeJSON(w, http.StatusOK, artist)
}

func (api *API) coverage(w http.ResponseWriter, r *http.Request) {
	summary, err := api.repo.Coverage(r.Context())
	if err != nil {
		slog.Error("coverage query failed", "error", err)
		writeError(w, http.StatusInternalServerError, "COVERAGE_QUERY_FAILED", "Coverage could not be calculated.")
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	writeJSON(w, http.StatusOK, summary)
}

type validationRequest struct {
	ArtistID string `json:"artist_id"`
}

type revisionRequest struct {
	ExpectedRevision int `json:"expected_revision"`
}

func (api *API) validatePublication(w http.ResponseWriter, r *http.Request) {
	var request validationRequest
	if !decodeJSON(w, r, &request) {
		return
	}
	if !regexp.MustCompile(`^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$`).MatchString(request.ArtistID) {
		writeError(w, http.StatusUnprocessableEntity, "ARTIST_ID_REQUIRED", "artist_id must be a valid record identifier.")
		return
	}
	report, err := api.repo.ValidateArtistForPublication(r.Context(), request.ArtistID)
	if errors.Is(err, catalog.ErrNotFound) {
		writeError(w, http.StatusNotFound, "ARTIST_NOT_FOUND", "This painter is not in the catalogue.")
		return
	}
	if err != nil {
		slog.Error("publication validation failed", "error", err)
		writeError(w, http.StatusInternalServerError, "PUBLICATION_VALIDATION_FAILED", "Publication checks could not be completed.")
		return
	}
	writeJSON(w, http.StatusOK, report)
}

func (api *API) publishArtist(w http.ResponseWriter, r *http.Request) {
	var request revisionRequest
	if !decodeJSON(w, r, &request) {
		return
	}
	report, err := api.repo.ValidateArtistForPublication(r.Context(), r.PathValue("id"))
	if errors.Is(err, catalog.ErrNotFound) {
		writeError(w, http.StatusNotFound, "ARTIST_NOT_FOUND", "This painter is not in the catalogue.")
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "PUBLICATION_VALIDATION_FAILED", "Publication checks could not be completed.")
		return
	}
	if !report.Ready {
		writeJSON(w, http.StatusUnprocessableEntity, report)
		return
	}
	artist, err := api.repo.SetPublished(r.Context(), r.PathValue("id"), request.ExpectedRevision, true)
	api.writePublicationResult(w, artist, err)
}

func (api *API) unpublishArtist(w http.ResponseWriter, r *http.Request) {
	var request revisionRequest
	if !decodeJSON(w, r, &request) {
		return
	}
	artist, err := api.repo.SetPublished(r.Context(), r.PathValue("id"), request.ExpectedRevision, false)
	api.writePublicationResult(w, artist, err)
}

func (api *API) writePublicationResult(w http.ResponseWriter, artist catalog.CatalogueArtist, err error) {
	var invalid *catalog.PublicationError
	if errors.As(err, &invalid) {
		writeJSON(w, 422, invalid.Report)
		return
	}
	if errors.Is(err, catalog.ErrRevisionConflict) {
		writeError(w, http.StatusConflict, "REVISION_CONFLICT", "This painter changed after you opened it. Reload before changing publication state.")
		return
	}
	if errors.Is(err, catalog.ErrNotFound) {
		writeError(w, http.StatusNotFound, "ARTIST_NOT_FOUND", "This painter is not in the catalogue.")
		return
	}
	if err != nil {
		slog.Error("publication state update failed", "error", err)
		writeError(w, http.StatusInternalServerError, "PUBLICATION_UPDATE_FAILED", "Publication state could not be changed.")
		return
	}
	writeJSON(w, http.StatusOK, artist)
}

func decodeArtistInput(w http.ResponseWriter, r *http.Request, update bool) (catalog.ArtistInput, bool) {
	var input catalog.ArtistInput
	if !decodeJSON(w, r, &input) {
		return input, false
	}
	input.Slug = catalog.NormalizeSlug(input.Slug)
	input.DisplayName = strings.TrimSpace(input.DisplayName)
	input.SortName = strings.TrimSpace(input.SortName)
	input.EntityType = strings.TrimSpace(input.EntityType)
	input.TimelineDisplay = strings.TrimSpace(input.TimelineDisplay)
	input.TimelineBasis = strings.TrimSpace(input.TimelineBasis)
	input.Status = strings.TrimSpace(input.Status)
	if input.SortName == "" {
		input.SortName = input.DisplayName
	}
	if input.EntityType == "" {
		input.EntityType = "person"
	}
	if input.TimelineBasis == "" {
		input.TimelineBasis = "life"
	}
	if input.Status == "" {
		input.Status = "draft"
	}
	if !regexp.MustCompile(`^[a-z0-9]+(-[a-z0-9]+)*$`).MatchString(input.Slug) || len(input.Slug) > 100 || input.DisplayName == "" || len(input.DisplayName) > 200 || input.TimelineDisplay == "" {
		writeError(w, http.StatusUnprocessableEntity, "REQUIRED_FIELDS", "Slug, display name, and timeline display are required.")
		return input, false
	}
	if input.TimelineStartYear < 1 || input.TimelineEndYear > 2100 || input.TimelineStartYear > 2000 || input.TimelineEndYear < 1100 || input.TimelineStartYear > input.TimelineEndYear {
		writeError(w, http.StatusUnprocessableEntity, "INVALID_TIMELINE_RANGE", "Life or activity dates must be ordered and overlap 1100–2000. Do not truncate dates to fit the timeline.")
		return input, false
	}
	if !allowed(input.EntityType, "person", "anonymous_master", "workshop", "collective") || !allowed(input.TimelineBasis, "life", "activity", "mixed", "estimated") {
		writeError(w, http.StatusUnprocessableEntity, "INVALID_CLASSIFICATION", "Entity type or timeline basis is invalid.")
		return input, false
	}
	if !allowed(input.Status, "draft", "review") {
		writeError(w, http.StatusUnprocessableEntity, "PUBLISH_REQUIRES_VALIDATION", "Create and edit routes may only save draft or review records.")
		return input, false
	}
	if update && input.ExpectedRevision < 1 {
		writeError(w, http.StatusUnprocessableEntity, "EXPECTED_REVISION_REQUIRED", "expected_revision is required when updating a painter.")
		return input, false
	}
	return input, true
}

func decodeJSON(w http.ResponseWriter, r *http.Request, destination any) bool {
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(destination); err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_JSON", "Request body must be valid JSON with known fields.")
		return false
	}
	if decoder.Decode(&struct{}{}) != io.EOF {
		writeError(w, 400, "INVALID_JSON", "Send exactly one JSON object.")
		return false
	}
	return true
}

func (api *API) requireEditor(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if api.config.EditorToken == "" {
			writeError(w, http.StatusServiceUnavailable, "EDITOR_AUTH_NOT_CONFIGURED", "Editor writes are disabled until ARTLINE_EDITOR_TOKEN is configured.")
			return
		}
		if !api.isEditor(r) {
			writeError(w, http.StatusUnauthorized, "EDITOR_AUTH_REQUIRED", "A valid editor token is required.")
			return
		}
		if id := r.PathValue("id"); id != "" && !regexp.MustCompile(`^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$`).MatchString(id) {
			writeError(w, 400, "INVALID_ID", "Invalid record identifier.")
			return
		}
		w.Header().Set("Cache-Control", "private, no-store")
		next.ServeHTTP(w, r)
	})
}

func (api *API) isEditor(r *http.Request) bool {
	prefix, provided, ok := strings.Cut(r.Header.Get("Authorization"), " ")
	return ok && prefix == "Bearer" && api.config.EditorToken != "" && subtle.ConstantTimeCompare([]byte(provided), []byte(api.config.EditorToken)) == 1
}
func (api *API) previewAllowed(w http.ResponseWriter, r *http.Request) (bool, bool) {
	w.Header().Set("Cache-Control", "private, no-store")
	publicPreview := api.config.PublicResearchPreview && (r.Method == http.MethodGet || r.Method == http.MethodHead)
	preview := publicPreview || r.URL.Query().Get("preview") == "1"
	if preview && !publicPreview && !api.isEditor(r) {
		writeError(w, 401, "EDITOR_AUTH_REQUIRED", "Sign in to preview research records.")
		return false, false
	}
	return preview, true
}
func (api *API) catalogueArtist(w http.ResponseWriter, r *http.Request) {
	var slug string
	if err := api.db.QueryRow(r.Context(), "SELECT slug FROM artists WHERE id=$1", r.PathValue("id")).Scan(&slug); err != nil {
		writeError(w, 404, "ARTIST_NOT_FOUND", "Painter not found.")
		return
	}
	artist, err := api.repo.ArtistBySlug(r.Context(), slug, true)
	if err != nil {
		writeError(w, 404, "ARTIST_NOT_FOUND", "Painter not found or archived.")
		return
	}
	writeJSON(w, 200, artist)
}

func (api *API) cors(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if origin != "" && strings.TrimSuffix(origin, "/") == strings.TrimSuffix(api.config.FrontendOrigin, "/") {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Vary", "Origin")
			w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
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
