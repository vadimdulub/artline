package member

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"net/http"
	"regexp"
	"strings"
	"time"
)

var bookmarkID = regexp.MustCompile(`^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$`)
var bookmarkSlug = regexp.MustCompile(`^[a-z0-9]+(?:[-_][a-z0-9]+)*$`)
var bookmarkKinds = []string{"artist", "artwork", "book", "event"}
var ErrBookmarkMissing = errors.New("bookmark target not found")
var ErrBookmarkLimit = errors.New("local bookmark limit reached")

type BookmarkRef struct {
	Kind string `json:"kind"`
	ID   string `json:"id"`
}
type Bookmark struct {
	BookmarkRef
	Title        string         `json:"title"`
	Subtitle     string         `json:"subtitle"`
	Href         string         `json:"href"`
	MediaURL     *string        `json:"media_url"`
	AltText      *string        `json:"alt_text"`
	RightsStatus *string        `json:"rights_status"`
	SavedAt      time.Time      `json:"saved_at"`
	Image        *BookmarkImage `json:"image,omitempty"`
}

// Preserve the selected reproduction's own label and credit, separately from
// artwork rights statuses and from the date of the book or historical event.
type BookmarkImage struct {
	ImageURL   string `json:"imageUrl"`
	SourceURL  string `json:"sourceUrl"`
	Label      string `json:"label"`
	Credit     string `json:"credit"`
	License    string `json:"license"`
	LicenseURL string `json:"licenseUrl"`
}
type BookmarkCursor struct {
	SavedAt time.Time `json:"t"`
	Kind    string    `json:"k"`
	ID      string    `json:"i"`
	Filter  string    `json:"f"`
}
type BookmarkPage struct {
	Items      []Bookmark `json:"items"`
	NextCursor string     `json:"next_cursor"`
}
type BookmarkStore interface {
	List(context.Context, string, string, BookmarkCursor, int) ([]Bookmark, error)
	States(context.Context, string, []BookmarkRef) ([]BookmarkRef, error)
	Set(context.Context, string, BookmarkRef, bool) error
}

func validBookmark(ref BookmarkRef) bool {
	switch ref.Kind {
	case "artist", "artwork":
		return bookmarkID.MatchString(ref.ID)
	case "book", "event":
		return len(ref.ID) <= 160 && bookmarkSlug.MatchString(ref.ID)
	}
	return false
}
func validBookmarkKind(kind string) bool {
	for _, candidate := range bookmarkKinds {
		if kind == candidate {
			return true
		}
	}
	return false
}

func (h *Handler) RegisterBookmarks(mux *http.ServeMux, store BookmarkStore) {
	mux.HandleFunc("GET /api/v1/member/bookmarks", h.memberOnly(func(w http.ResponseWriter, r *http.Request, user User) {
		kind := r.URL.Query().Get("kind")
		if kind != "" && !validBookmarkKind(kind) {
			accessError(w, 400, "INVALID_FILTER", "Choose artists, artworks, books, events, or all bookmarks.")
			return
		}
		cursor := BookmarkCursor{}
		if raw := r.URL.Query().Get("cursor"); raw != "" {
			if len(raw) > 512 {
				accessError(w, 400, "INVALID_CURSOR", "Start again from your newest bookmarks.")
				return
			}
			data, err := base64.RawURLEncoding.DecodeString(raw)
			if err != nil || json.Unmarshal(data, &cursor) != nil || cursor.Filter != kind || cursor.SavedAt.IsZero() || !validBookmark(BookmarkRef{cursor.Kind, cursor.ID}) {
				accessError(w, 400, "INVALID_CURSOR", "Start again from your newest bookmarks.")
				return
			}
		}
		items, err := store.List(r.Context(), user.ID, kind, cursor, 31)
		if err != nil {
			bookmarkError(w, err)
			return
		}
		page := BookmarkPage{Items: items}
		if page.Items == nil {
			page.Items = []Bookmark{}
		}
		if len(items) > 30 {
			page.Items = items[:30]
			last := items[29]
			raw, _ := json.Marshal(BookmarkCursor{last.SavedAt, last.Kind, last.ID, kind})
			page.NextCursor = base64.RawURLEncoding.EncodeToString(raw)
		}
		bookmarkJSON(w, page)
	}))
	mux.HandleFunc("GET /api/v1/member/bookmarks/state", h.memberOnly(func(w http.ResponseWriter, r *http.Request, user User) {
		refs := []BookmarkRef{}
		for _, kind := range bookmarkKinds {
			for _, id := range r.URL.Query()[kind] {
				ref := BookmarkRef{kind, strings.ToLower(id)}
				if !validBookmark(ref) {
					accessError(w, 400, "INVALID_BOOKMARK", "Invalid bookmark reference.")
					return
				}
				refs = append(refs, ref)
			}
		}
		if len(refs) == 0 || len(refs) > 100 {
			accessError(w, 400, "INVALID_BOOKMARKS", "Request between 1 and 100 bookmark states.")
			return
		}
		saved, err := store.States(r.Context(), user.ID, refs)
		if err != nil {
			bookmarkError(w, err)
			return
		}
		if saved == nil {
			saved = []BookmarkRef{}
		}
		bookmarkJSON(w, map[string]any{"saved": saved})
	}))
	for _, method := range []string{http.MethodPut, http.MethodDelete} {
		mux.HandleFunc(method+" /api/v1/member/bookmarks/{kind}/{id}", h.memberOnly(func(w http.ResponseWriter, r *http.Request, user User) {
			ref := BookmarkRef{r.PathValue("kind"), strings.ToLower(r.PathValue("id"))}
			if !validBookmark(ref) {
				accessError(w, 400, "INVALID_BOOKMARK", "Invalid bookmark reference.")
				return
			}
			saved := r.Method == http.MethodPut
			if err := store.Set(r.Context(), user.ID, ref, saved); err != nil {
				bookmarkError(w, err)
				return
			}
			bookmarkJSON(w, map[string]any{"kind": ref.Kind, "id": ref.ID, "saved": saved})
		}))
	}
}
func (h *Handler) memberOnly(next func(http.ResponseWriter, *http.Request, User)) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "private, no-store")
		w.Header().Set("X-Robots-Tag", "noindex")
		if r.Method == http.MethodHead {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		if r.Method != http.MethodGet && (r.Header.Get("Origin") != h.config.Origin || r.Header.Get("Sec-Fetch-Site") == "cross-site") {
			accessError(w, 403, "SAME_ORIGIN_REQUIRED", "This request must come from Artline.")
			return
		}
		user, ok := h.authorize(w, r)
		if !ok {
			return
		}
		ctx, cancel := context.WithTimeout(r.Context(), 8*time.Second)
		defer cancel()
		next(w, r.WithContext(ctx), user)
	}
}
func bookmarkJSON(w http.ResponseWriter, value any) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(value)
}
func bookmarkError(w http.ResponseWriter, err error) {
	if errors.Is(err, ErrBookmarkMissing) {
		accessError(w, 404, "RECORD_UNAVAILABLE", "This record is no longer available.")
		return
	}
	if errors.Is(err, ErrBookmarkLimit) {
		accessError(w, 409, "LOCAL_BOOKMARK_LIMIT", "The local preview holds up to 1,000 bookmarks.")
		return
	}
	accessError(w, 503, "BOOKMARKS_UNAVAILABLE", "Your bookmarks are temporarily unavailable. Please try again.")
}
