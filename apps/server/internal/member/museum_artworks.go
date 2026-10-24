package member

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"strings"
	"unicode/utf8"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

const maxMuseumArtworks = 48

var ErrMuseumArtwork = errors.New("selected artwork unavailable")

type MuseumArtworkRef struct {
	Kind string `json:"kind"`
	ID   string `json:"id"`
	Note string `json:"note"`
}
type MuseumArtworkChoice struct {
	MuseumArtworkRef
	Title     string `json:"title"`
	Creator   string `json:"creator"`
	Date      string `json:"date"`
	ImageURL  string `json:"image_url"`
	ImageAlt  string `json:"image_alt"`
	Credit    string `json:"credit"`
	Href      string `json:"href"`
	Available bool   `json:"available"`
	Published bool   `json:"published"`
}
type MuseumArtworkPage struct {
	Items      []MuseumArtworkChoice `json:"items"`
	NextCursor string                `json:"next_cursor"`
}
type MuseumArtworkCatalogue interface {
	Search(context.Context, string, string, string, string, bool) (MuseumArtworkPage, error)
	Lookup(context.Context, []string) ([]MuseumArtworkChoice, error)
}
type PostgresMuseumArtworks struct{ DB *pgxpool.Pool }

func (p PostgresMuseumArtworks) Search(ctx context.Context, slug, scope, q, cursor string, images bool) (MuseumArtworkPage, error) {
	out := MuseumArtworkPage{Items: []MuseumArtworkChoice{}}
	if scope == "all" {
		page, err := (PostgresStudyCatalogue{DB: p.DB}).Search(ctx, "", StudySearch{Kind: "artwork", Query: q, Cursor: cursor, ImageOnly: images})
		if err != nil {
			return out, err
		}
		out.NextCursor = page.NextCursor
		for _, record := range page.Items {
			out.Items = append(out.Items, choiceFromStudy(record))
		}
		return out, nil
	}
	page, err := catalog.NewRepository(p.DB).MuseumWorks(ctx, slug, catalog.MuseumFilter{Query: q, Cursor: cursor, ImageOnly: images, Limit: 24, Sort: "images"})
	if errors.Is(err, catalog.ErrNotFound) {
		return out, nil
	}
	if err != nil {
		return out, err
	}
	out.NextCursor = page.NextCursor
	ids := []string{}
	for _, item := range page.Items {
		ids = append(ids, item.ID)
	}
	out.Items, err = p.Lookup(ctx, ids)
	return out, err
}
func choiceFromStudy(record StudyRecord) MuseumArtworkChoice {
	choice := MuseumArtworkChoice{MuseumArtworkRef: MuseumArtworkRef{Kind: "catalogue", ID: record.ID}, Title: record.Title, Creator: record.Creator, Date: record.Date, Href: record.Href, Available: true, Published: true}
	if record.Image != nil {
		choice.ImageURL = record.Image.ImageURL
		choice.ImageAlt = record.Image.Label
		choice.Credit = strings.TrimSpace(record.Image.Credit)
		if record.Image.License != "" && !strings.Contains(choice.Credit, record.Image.License) {
			choice.Credit = strings.TrimSpace(choice.Credit + " " + record.Image.License)
		}
	}
	return choice
}
func (p PostgresMuseumArtworks) Lookup(ctx context.Context, ids []string) ([]MuseumArtworkChoice, error) {
	out := []MuseumArtworkChoice{}
	for offset := 0; offset < len(ids); offset += 24 {
		refs := []BookmarkRef{}
		for _, id := range ids[offset:min(offset+24, len(ids))] {
			refs = append(refs, BookmarkRef{Kind: "artwork", ID: id})
		}
		rows, err := (PostgresStudyCatalogue{DB: p.DB}).Lookup(ctx, refs)
		if err != nil {
			return nil, err
		}
		for _, record := range rows {
			out = append(out, choiceFromStudy(record))
		}
	}
	return out, nil
}
func choiceFromPublication(slug string, p MuseumPublication) MuseumArtworkChoice {
	return MuseumArtworkChoice{MuseumArtworkRef: MuseumArtworkRef{Kind: "museum", ID: p.ID}, Title: p.Document.Title, Creator: p.Document.Creator, Date: p.Document.DateLabel, ImageURL: museumDocumentImageURL(slug, p.Document), ImageAlt: p.Document.ImageAlt, Credit: p.Document.ImageCredit, Href: "/museums/" + slug + "/publications/" + p.ID, Available: true, Published: p.Published}
}
func validateMuseumArtworks(kind string, refs []MuseumArtworkRef) string {
	if len(refs) > maxMuseumArtworks {
		return "Choose up to 48 artworks per guide or exhibition."
	}
	if len(refs) > 0 && kind != "guide" && kind != "exhibition" {
		return "Artworks can be arranged in guides and exhibitions."
	}
	seen := map[string]bool{}
	for _, ref := range refs {
		key := ref.Kind + ":" + ref.ID
		if (ref.Kind != "catalogue" && ref.Kind != "museum") || !bookmarkID.MatchString(ref.ID) || seen[key] {
			return "Choose distinct, valid artworks from the picker."
		}
		seen[key] = true
		if utf8.RuneCountInString(ref.Note) > 1000 {
			return "Use up to 1,000 characters beside each artwork."
		}
	}
	return ""
}
func resolveMuseumArtworks(ctx context.Context, store MuseumStudioStore, cat MuseumArtworkCatalogue, slug string, refs []MuseumArtworkRef, public bool) ([]MuseumArtworkChoice, error) {
	out := []MuseumArtworkChoice{}
	if len(refs) == 0 {
		return out, nil
	}
	catalogueIDs, museumIDs := []string{}, []string{}
	for _, ref := range refs {
		if ref.Kind == "catalogue" {
			catalogueIDs = append(catalogueIDs, ref.ID)
		} else {
			museumIDs = append(museumIDs, ref.ID)
		}
	}
	byID := map[string]MuseumArtworkChoice{}
	if len(catalogueIDs) > 0 {
		if cat == nil {
			return nil, ErrMuseumArtwork
		}
		items, err := cat.Lookup(ctx, catalogueIDs)
		if err != nil {
			return nil, err
		}
		for _, item := range items {
			byID["catalogue:"+item.ID] = item
		}
	}
	if len(museumIDs) > 0 {
		items, err := store.Artworks(ctx, slug, museumIDs, public)
		if err != nil {
			return nil, err
		}
		for _, item := range items {
			byID["museum:"+item.ID] = choiceFromPublication(slug, item)
		}
	}
	for _, ref := range refs {
		item, ok := byID[ref.Kind+":"+ref.ID]
		if !ok {
			item = MuseumArtworkChoice{Title: "Artwork unavailable"}
		}
		item.MuseumArtworkRef = ref
		out = append(out, item)
	}
	return out, nil
}
func (h *Handler) registerMuseumArtworkPicker(mux *http.ServeMux, store MuseumStudioStore, cat MuseumArtworkCatalogue) {
	mux.HandleFunc("GET /api/v1/member/museum-studio/{slug}/artworks", h.memberOnly(func(w http.ResponseWriter, r *http.Request, u User) {
		slug := r.PathValue("slug")
		if err := store.Access(r.Context(), u, slug); err != nil {
			museumStudioError(w, err)
			return
		}
		q := r.URL.Query()
		scope := q.Get("scope")
		if scope == "" {
			scope = "collection"
		}
		if (scope != "collection" && scope != "all" && scope != "museum") || len(q.Get("q")) > 200 || len(q.Get("cursor")) > 4096 {
			accessError(w, 400, "INVALID_FILTER", "Choose a collection and a search of up to 200 characters.")
			return
		}
		var page MuseumArtworkPage
		var err error
		if scope == "museum" {
			cursor := q.Get("cursor")
			if cursor != "" && !bookmarkID.MatchString(cursor) {
				accessError(w, 400, "INVALID_CURSOR", "Choose a valid page.")
				return
			}
			var items []MuseumPublication
			items, err = store.List(r.Context(), slug, false, "artwork", q.Get("q"), cursor)
			page.Items = []MuseumArtworkChoice{}
			if len(items) > 24 {
				page.NextCursor = items[23].ID
				items = items[:24]
			}
			for _, item := range items {
				page.Items = append(page.Items, choiceFromPublication(slug, item))
			}
		} else if cat != nil {
			page, err = cat.Search(r.Context(), slug, scope, q.Get("q"), q.Get("cursor"), q.Get("images") != "0")
		} else {
			err = ErrMuseumArtwork
		}
		if err != nil {
			var input studyInputError
			if errors.Is(err, catalog.ErrMuseumFilter) || errors.As(err, &input) {
				accessError(w, 400, "INVALID_CURSOR", "The search changed. Start again from the first page.")
			} else {
				museumStudioError(w, err)
			}
			return
		}
		bookmarkJSON(w, page)
	}))
	mux.HandleFunc("POST /api/v1/member/museum-studio/{slug}/artworks/resolve", h.memberOnly(func(w http.ResponseWriter, r *http.Request, u User) {
		slug := r.PathValue("slug")
		if err := store.Access(r.Context(), u, slug); err != nil {
			museumStudioError(w, err)
			return
		}
		var refs []MuseumArtworkRef
		d := json.NewDecoder(http.MaxBytesReader(w, r.Body, 262144))
		d.DisallowUnknownFields()
		if err := d.Decode(&refs); err != nil {
			accessError(w, 400, "INVALID_SELECTION", "Choose artworks from the picker.")
			return
		}
		if message := validateMuseumArtworks("guide", refs); message != "" {
			accessError(w, 400, "INVALID_SELECTION", message)
			return
		}
		items, err := resolveMuseumArtworks(r.Context(), store, cat, slug, refs, false)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		bookmarkJSON(w, map[string]any{"items": items})
	}))
	mux.HandleFunc("GET /api/v1/member/museum-studio/{slug}/content/{id}", h.memberOnly(func(w http.ResponseWriter, r *http.Request, u User) {
		slug, id := r.PathValue("slug"), r.PathValue("id")
		if !bookmarkID.MatchString(id) {
			museumStudioError(w, ErrPublicationMissing)
			return
		}
		if err := store.Access(r.Context(), u, slug); err != nil {
			museumStudioError(w, err)
			return
		}
		item, err := store.Get(r.Context(), slug, id, false)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		bookmarkJSON(w, item)
	}))
}
