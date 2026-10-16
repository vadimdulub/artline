package member

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
	"unicode/utf8"
)

var ErrMuseumAccess = errors.New("museum staff access required")
var ErrPublicationConflict = errors.New("publication changed")
var ErrPublicationMissing = errors.New("publication not found")

type StudioMuseum struct {
	ID       string `json:"id"`
	Slug     string `json:"slug"`
	Name     string `json:"name"`
	Website  string `json:"website_url"`
	Managed  bool   `json:"managed"`
	Eligible bool   `json:"eligible"`
}
type MuseumDocument struct {
	ImageID     string             `json:"image_id"`
	Artworks    []MuseumArtworkRef `json:"artworks"`
	BodyFormat  string             `json:"body_format"`
	Title       string             `json:"title"`
	Summary     string             `json:"summary"`
	Body        string             `json:"body"`
	Creator     string             `json:"creator"`
	DateLabel   string             `json:"date_label"`
	YearStart   *int               `json:"year_start"`
	YearEnd     *int               `json:"year_end"`
	Medium      string             `json:"medium"`
	Dimensions  string             `json:"dimensions"`
	Inventory   string             `json:"inventory"`
	StartDate   string             `json:"start_date"`
	EndDate     string             `json:"end_date"`
	Venue       string             `json:"venue"`
	Language    string             `json:"language"`
	ImageURL    string             `json:"image_url"`
	ImageAlt    string             `json:"image_alt"`
	ImageCredit string             `json:"image_credit"`
	SourceURL   string             `json:"source_url"`
	VisitURL    string             `json:"visit_url"`
	Address     string             `json:"address"`
	Hours       string             `json:"hours"`
}
type MuseumPublication struct {
	Artworks   []MuseumArtworkChoice `json:"resolved_artworks,omitempty"`
	ID         string                `json:"id"`
	Kind       string                `json:"kind"`
	Document   MuseumDocument        `json:"document"`
	Version    int                   `json:"version,omitempty"`
	Published  bool                  `json:"published"`
	HasChanges bool                  `json:"has_changes,omitempty"`
	UpdatedAt  time.Time             `json:"updated_at"`
}
type PublicationPage struct {
	Items      []MuseumPublication `json:"items"`
	NextCursor string              `json:"next_cursor"`
}
type PublicationWrite struct {
	Kind     string         `json:"kind"`
	Document MuseumDocument `json:"document"`
	Version  int            `json:"version"`
	Action   string         `json:"action"`
}
type MuseumStudioStore interface {
	Artworks(context.Context, string, []string, bool) ([]MuseumPublication, error)
	SaveUpload(context.Context, User, string, MuseumUpload) error
	Upload(context.Context, string, string) (MuseumUpload, error)
	ImagePublished(context.Context, string, string) (bool, error)
	Museums(context.Context, User, string) ([]StudioMuseum, error)
	Museum(context.Context, string) (StudioMuseum, error)
	Claim(context.Context, User, string) error
	Access(context.Context, User, string) error
	List(context.Context, string, bool, string, string, string) ([]MuseumPublication, error)
	Get(context.Context, string, string, bool) (MuseumPublication, error)
	Write(context.Context, User, string, string, PublicationWrite) (MuseumPublication, error)
}

func museumKind(s string) bool {
	return s == "artwork" || s == "exhibition" || s == "guide" || s == "profile"
}
func museumDomain(user User) string {
	domain := strings.ToLower(strings.TrimSpace(user.HostedDomain))
	_, emailDomain, ok := strings.Cut(strings.ToLower(user.Email), "@")
	if !ok || domain == "" || domain != emailDomain || strings.ContainsAny(domain, "/@ :") {
		return ""
	}
	return domain
}
func validateMuseumDocument(kind string, d MuseumDocument) string {
	if message := validateMuseumArtworks(kind, d.Artworks); message != "" {
		return message
	}
	if d.BodyFormat != "" && d.BodyFormat != "markdown" {
		return "Choose a supported text format."
	}
	if d.ImageID != "" && (!bookmarkID.MatchString(d.ImageID) || d.ImageURL != "") {
		return "Choose one uploaded image or an image URL."
	}
	if strings.TrimSpace(d.Title) == "" || utf8.RuneCountInString(d.Title) > 240 {
		return "Add a title of up to 240 characters."
	}
	if utf8.RuneCountInString(d.Summary) > 1000 || utf8.RuneCountInString(d.Body) > 20000 {
		return "Use up to 1,000 characters for the introduction and 20,000 for the text."
	}
	for _, v := range []string{d.Creator, d.DateLabel, d.Medium, d.Dimensions, d.Inventory, d.Venue, d.Language, d.ImageAlt, d.ImageCredit, d.Address, d.Hours} {
		if utf8.RuneCountInString(v) > 1000 {
			return "A field is too long. Use up to 1,000 characters."
		}
	}
	for _, v := range []string{d.ImageURL, d.SourceURL, d.VisitURL} {
		if v == "" {
			continue
		}
		u, err := url.Parse(v)
		if err != nil || len(v) > 2048 || u.Scheme != "https" || u.Hostname() == "" || u.User != nil {
			return "Use a complete HTTPS link."
		}
	}
	if (d.ImageURL != "" || d.ImageID != "") && (strings.TrimSpace(d.ImageCredit) == "" || strings.TrimSpace(d.ImageAlt) == "") {
		return "Add an image description and image credit."
	}
	if kind == "artwork" {
		if strings.TrimSpace(d.DateLabel) == "" {
			return "Add the recorded artwork date, or state that the date is unknown."
		}
		for _, v := range []*int{d.YearStart, d.YearEnd} {
			if v != nil && (*v < -10000 || *v > 3000) {
				return "Artwork years must be between −10000 and 3000."
			}
		}
		if d.YearEnd != nil && (d.YearStart == nil || *d.YearEnd < *d.YearStart) {
			return "The end year must be on or after the start year."
		}
	}
	if kind == "exhibition" {
		start, err := time.Parse("2006-01-02", d.StartDate)
		if err != nil {
			return "Add a valid exhibition opening date."
		}
		if d.EndDate != "" {
			end, err := time.Parse("2006-01-02", d.EndDate)
			if err != nil || end.Before(start) {
				return "The closing date must be on or after the opening date."
			}
		}
	}
	return ""
}
func museumStudioError(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, ErrMuseumArtwork):
		accessError(w, 400, "ARTWORK_UNAVAILABLE", "A selected artwork is unavailable or still a draft. Publish it before publishing this guide or exhibition.")
	case errors.Is(err, ErrMuseumAccess):
		accessError(w, 403, "MUSEUM_ACCESS", "Use a verified museum work account with an approved domain to manage this museum.")
	case errors.Is(err, ErrPublicationConflict):
		accessError(w, 409, "PUBLICATION_CONFLICT", "This record changed in another window. Close the editor and reload before editing again.")
	case errors.Is(err, ErrPublicationMissing):
		accessError(w, 404, "NOT_FOUND", "This museum publication could not be found.")
	default:
		accessError(w, 503, "STUDIO_UNAVAILABLE", "Museum publishing is temporarily unavailable. Please try again.")
	}
}
func museumPublicRead(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "private, no-store")
		slug := r.PathValue("slug")
		if len(slug) > 100 || !bookmarkSlug.MatchString(slug) {
			museumStudioError(w, ErrPublicationMissing)
			return
		}
		ctx, cancel := context.WithTimeout(r.Context(), 8*time.Second)
		defer cancel()
		next(w, r.WithContext(ctx))
	}
}

func (h *Handler) RegisterMuseumStudio(mux *http.ServeMux, store MuseumStudioStore, options ...MuseumStudioOptions) {
	var opt MuseumStudioOptions
	if len(options) > 0 {
		opt = options[0]
	}
	h.registerMuseumArtworkPicker(mux, store, opt.Catalogue)
	h.registerMuseumUploads(mux, store, opt.Blobs)
	mux.HandleFunc("GET /api/v1/member/museum-studio", h.memberOnly(func(w http.ResponseWriter, r *http.Request, u User) {
		q := strings.TrimSpace(r.URL.Query().Get("q"))
		if len(q) > 200 {
			accessError(w, 400, "INVALID_QUERY", "Use up to 200 characters.")
			return
		}
		items, err := store.Museums(r.Context(), u, q)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		bookmarkJSON(w, map[string]any{"items": items, "local_debug": h.config.LocalDebug, "work_identity": museumDomain(u) != ""})
	}))
	mux.HandleFunc("POST /api/v1/member/museum-studio/{slug}/claim", h.memberOnly(func(w http.ResponseWriter, r *http.Request, u User) {
		err := store.Claim(r.Context(), u, r.PathValue("slug"))
		if err != nil {
			museumStudioError(w, err)
			return
		}
		bookmarkJSON(w, map[string]bool{"verified": true})
	}))
	mux.HandleFunc("GET /api/v1/member/museum-studio/{slug}", h.memberOnly(func(w http.ResponseWriter, r *http.Request, u User) {
		slug := r.PathValue("slug")
		if err := store.Access(r.Context(), u, slug); err != nil {
			museumStudioError(w, err)
			return
		}
		m, err := store.Museum(r.Context(), slug)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		bookmarkJSON(w, m)
	}))
	list := func(w http.ResponseWriter, r *http.Request, public bool) {
		q := r.URL.Query()
		kind, query, cursor := q.Get("kind"), strings.TrimSpace(q.Get("q")), q.Get("cursor")
		if !museumKind(kind) || len(query) > 200 || (cursor != "" && !bookmarkID.MatchString(cursor)) {
			accessError(w, 400, "INVALID_FILTER", "Choose a content type and a valid page.")
			return
		}
		items, err := store.List(r.Context(), r.PathValue("slug"), public, kind, query, cursor)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		page := PublicationPage{Items: items}
		if len(items) > 24 {
			page.NextCursor = items[23].ID
			page.Items = items[:24]
		}
		if page.Items == nil {
			page.Items = []MuseumPublication{}
		}
		bookmarkJSON(w, page)
	}
	mux.HandleFunc("GET /api/v1/member/museum-studio/{slug}/content", h.memberOnly(func(w http.ResponseWriter, r *http.Request, u User) {
		if err := store.Access(r.Context(), u, r.PathValue("slug")); err != nil {
			museumStudioError(w, err)
			return
		}
		list(w, r, false)
	}))
	write := h.memberOnly(func(w http.ResponseWriter, r *http.Request, u User) {
		slug, id := r.PathValue("slug"), r.PathValue("id")
		if id != "" && !bookmarkID.MatchString(id) {
			accessError(w, 400, "INVALID_ID", "Choose a valid publication.")
			return
		}
		if err := store.Access(r.Context(), u, slug); err != nil {
			museumStudioError(w, err)
			return
		}
		var input PublicationWrite
		decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 262144))
		decoder.DisallowUnknownFields()
		if err := decoder.Decode(&input); err != nil {
			accessError(w, 400, "INVALID_INPUT", "Check the publication fields and size.")
			return
		}
		if err := decoder.Decode(&struct{}{}); err != io.EOF {
			accessError(w, 400, "INVALID_INPUT", "Send one publication.")
			return
		}
		if !museumKind(input.Kind) || (input.Action != "save" && input.Action != "publish" && input.Action != "unpublish") || input.Version < 0 || (id == "" && input.Version != 0) {
			accessError(w, 400, "INVALID_INPUT", "Choose a valid content type and publishing action.")
			return
		}
		if message := validateMuseumDocument(input.Kind, input.Document); message != "" {
			accessError(w, 400, "INVALID_DOCUMENT", message)
			return
		}
		if input.Document.ImageID != "" {
			if _, err := store.Upload(r.Context(), slug, input.Document.ImageID); err != nil {
				accessError(w, 400, "INVALID_IMAGE", "Upload an image for this museum before saving.")
				return
			}
		}
		if len(input.Document.Artworks) > 0 && input.Action != "unpublish" {
			choices, err := resolveMuseumArtworks(r.Context(), store, opt.Catalogue, slug, input.Document.Artworks, false)
			if err != nil {
				museumStudioError(w, err)
				return
			}
			for _, choice := range choices {
				if !choice.Available || input.Action == "publish" && !choice.Published {
					museumStudioError(w, ErrMuseumArtwork)
					return
				}
			}
		}
		item, err := store.Write(r.Context(), u, slug, id, input)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		bookmarkJSON(w, item)
	})
	mux.HandleFunc("POST /api/v1/member/museum-studio/{slug}/content", write)
	mux.HandleFunc("PUT /api/v1/member/museum-studio/{slug}/content/{id}", write)
	// Museum publications are public only after explicit publication; never reuse catalogue status rules.
	mux.HandleFunc("GET /api/v1/museum-publications/{slug}", museumPublicRead(func(w http.ResponseWriter, r *http.Request) { list(w, r, true) }))
	mux.HandleFunc("GET /api/v1/museum-publications/{slug}/museum", museumPublicRead(func(w http.ResponseWriter, r *http.Request) {
		slug := r.PathValue("slug")
		found := false
		for _, kind := range []string{"profile", "artwork", "exhibition", "guide"} {
			rows, err := store.List(r.Context(), slug, true, kind, "", "")
			if err != nil {
				museumStudioError(w, err)
				return
			}
			if len(rows) > 0 {
				found = true
				break
			}
		}
		if !found {
			museumStudioError(w, ErrPublicationMissing)
			return
		}
		museum, err := store.Museum(r.Context(), slug)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		bookmarkJSON(w, museum)
	}))
	mux.HandleFunc("GET /api/v1/museum-publications/{slug}/{id}", museumPublicRead(func(w http.ResponseWriter, r *http.Request) {
		if !bookmarkID.MatchString(r.PathValue("id")) {
			museumStudioError(w, ErrPublicationMissing)
			return
		}
		item, err := store.Get(r.Context(), r.PathValue("slug"), r.PathValue("id"), true)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		item.Artworks, err = resolveMuseumArtworks(r.Context(), store, opt.Catalogue, r.PathValue("slug"), item.Document.Artworks, true)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		bookmarkJSON(w, item)
	}))
}
