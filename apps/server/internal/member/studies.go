package member

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"slices"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"
)

const studyRecordLimit = 200

var ErrStudyMissing = errors.New("study not found")
var ErrStudyLimit = errors.New("study limit reached")

type studyInputError string

func (e studyInputError) Error() string { return string(e) }

type StudyInterval struct {
	Start int `json:"start"`
	End   int `json:"end"`
}
type StudySource struct {
	Name string `json:"name"`
	URL  string `json:"url"`
}

// Catalogue references are dated snapshots. Personal records never enter the catalogue.
type StudyRecord struct {
	BookmarkRef
	Title      string          `json:"title"`
	Creator    string          `json:"creator"`
	Date       string          `json:"date"`
	Intervals  []StudyInterval `json:"intervals"`
	DateNote   string          `json:"date_note"`
	Medium     string          `json:"medium"`
	Dimensions string          `json:"dimensions"`
	Holding    string          `json:"holding"`
	Href       string          `json:"href"`
	Sources    []StudySource   `json:"sources"`
	Image      *BookmarkImage  `json:"image,omitempty"`
	Personal   bool            `json:"personal"`
	Note       string          `json:"note"`
	CapturedAt time.Time       `json:"captured_at"`
}
type Study struct {
	ShareToken string        `json:"share_token,omitempty"`
	ID         string        `json:"id"`
	Title      string        `json:"title"`
	Role       string        `json:"role"`
	UpdatedAt  time.Time     `json:"updated_at"`
	Records    []StudyRecord `json:"records"`
}
type StudySummary struct {
	Public    bool      `json:"public"`
	ID        string    `json:"id"`
	Title     string    `json:"title"`
	Role      string    `json:"role"`
	UpdatedAt time.Time `json:"updated_at"`
	Count     int       `json:"count"`
}
type StudyStore interface {
	List(context.Context, string, StudyListFilter) (StudyListPage, error)
	Create(context.Context, string, Study) error
	Get(context.Context, string, string) (Study, error)
	GetShared(context.Context, string) (Study, error)
	Update(context.Context, string, string, func(*Study) error) (Study, error)
	Delete(context.Context, string, string) error
}
type StudyCatalogue interface {
	Search(context.Context, string, StudySearch) (StudySearchPage, error)
	Lookup(context.Context, []BookmarkRef) ([]StudyRecord, error)
}
type StudySearch struct {
	Kind, Query, Creator, Dates, Cursor string
	From, To                            *int
	ImageOnly, Bookmarked               bool
	// In local debug, saved IDs come from the in-memory bookmark store.
	LocalSaved []string
}
type StudySearchPage struct {
	Items      []StudyRecord `json:"items"`
	NextCursor string        `json:"next_cursor"`
}
type StudyView struct {
	ShareToken string   `json:"share_token,omitempty"`
	Keys       []string `json:"keys"`
	StudySummary
	Items      []StudyRecord  `json:"items"`
	Matched    int            `json:"matched"`
	Counts     map[string]int `json:"counts"`
	Range      *StudyInterval `json:"range"`
	NextCursor string         `json:"next_cursor"`
	Artworks   []StudyRecord  `json:"artworks"`
}

func studyID() string {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	b[6] = (b[6] & 15) | 64
	b[8] = (b[8] & 63) | 128
	h := hex.EncodeToString(b)
	return h[:8] + "-" + h[8:12] + "-" + h[12:16] + "-" + h[16:20] + "-" + h[20:]
}
func studySummary(s Study) StudySummary {
	return StudySummary{ID: s.ID, Title: s.Title, Role: s.Role, UpdatedAt: s.UpdatedAt, Count: len(s.Records), Public: s.ShareToken != ""}
}
func studyKind(s string) bool       { return s == "artwork" || s == "book" || s == "event" }
func studyKey(r StudyRecord) string { return r.Kind + ":" + r.ID }
func studyURL(raw string) (string, error) {
	u, err := url.Parse(strings.TrimSpace(raw))
	if err != nil || len(raw) > 2048 || u.Hostname() == "" || u.User != nil || (u.Scheme != "https" && u.Scheme != "http") {
		return "", studyInputError("Enter a complete http or https link without login credentials.")
	}
	return u.String(), nil
}
func studyDateYear(year int) string {
	if year < 0 {
		return strconv.Itoa(-year) + " BCE"
	}
	return strconv.Itoa(year)
}
func studyYears(q url.Values) (*int, *int, error) {
	var values [2]*int
	for i, k := range []string{"from", "to"} {
		if q.Get(k) != "" {
			n, err := strconv.Atoi(q.Get(k))
			if err != nil || n == 0 || n < -12000 || n > 2000 {
				return nil, nil, studyInputError("Use whole years from 12000 BCE (−12000) to 2000; there is no year zero.")
			}
			values[i] = &n
		}
	}
	if values[0] != nil && values[1] != nil && *values[0] > *values[1] {
		return nil, nil, studyInputError("From must be earlier than or equal to To.")
	}
	return values[0], values[1], nil
}
func studyOverlap(r StudyRecord, from, to *int) bool {
	if from == nil && to == nil {
		return true
	}
	for _, v := range r.Intervals {
		if (from == nil || v.End >= *from) && (to == nil || v.Start <= *to) {
			return true
		}
	}
	return false
}
func studyRead(w http.ResponseWriter, r *http.Request, out any) bool {
	r.Body = http.MaxBytesReader(w, r.Body, 32768)
	d := json.NewDecoder(r.Body)
	d.DisallowUnknownFields()
	if err := d.Decode(out); err != nil {
		accessError(w, 400, "INVALID_STUDY", "Check the information and try again.")
		return false
	}
	if d.Decode(&struct{}{}) != io.EOF {
		accessError(w, 400, "INVALID_STUDY", "Send one request at a time.")
		return false
	}
	return true
}
func studyError(w http.ResponseWriter, err error) {
	var input studyInputError
	switch {
	case errors.As(err, &input):
		accessError(w, 400, "INVALID_STUDY", string(input))
	case errors.Is(err, ErrStudyMissing), errors.Is(err, ErrBookmarkMissing):
		accessError(w, 404, "STUDY_UNAVAILABLE", "This study or record is no longer available.")
	case errors.Is(err, ErrStudyLimit):
		accessError(w, 409, "STUDY_LIMIT", "A study holds up to 200 records. You can create up to 1,000 studies.")
	default:
		accessError(w, 503, "STUDIES_UNAVAILABLE", "Studies could not be saved or loaded. Please try again.")
	}
}

func (h *Handler) RegisterStudies(mux *http.ServeMux, store StudyStore, catalogue StudyCatalogue, bookmarks BookmarkStore) {
	h.registerSharedStudies(mux, store)
	register := func(method, path string, fn func(http.ResponseWriter, *http.Request, User) error) {
		mux.HandleFunc(method+" /api/v1/member/studies"+path, h.memberOnly(func(w http.ResponseWriter, r *http.Request, u User) {
			if id := r.PathValue("id"); id != "" && !bookmarkID.MatchString(id) {
				studyError(w, ErrStudyMissing)
				return
			}
			if err := fn(w, r, u); err != nil {
				studyError(w, err)
			}
		}))
	}
	register("GET", "", func(w http.ResponseWriter, r *http.Request, u User) error {
		filter, err := studyListFilter(r.URL.Query())
		if err != nil {
			return err
		}
		page, err := store.List(r.Context(), u.ID, filter)
		if err != nil {
			return err
		}
		bookmarkJSON(w, page)
		return nil
	})
	register("POST", "", func(w http.ResponseWriter, r *http.Request, u User) error {
		var body struct {
			Title string `json:"title"`
			Role  string `json:"role"`
		}
		if !studyRead(w, r, &body) {
			return nil
		}
		body.Title = strings.TrimSpace(body.Title)
		if body.Title == "" || utf8.RuneCountInString(body.Title) > 180 {
			return studyInputError("Give your study a title (up to 180 characters).")
		}
		if body.Role != "" && body.Role != "research" {
			return studyInputError("Studies are for research.")
		}
		s := Study{ID: studyID(), Title: body.Title, Role: "research", UpdatedAt: time.Now().UTC(), Records: []StudyRecord{}}
		if err := store.Create(r.Context(), u.ID, s); err != nil {
			return err
		}
		bookmarkJSON(w, studySummary(s))
		return nil
	})
	register("GET", "/search", func(w http.ResponseWriter, r *http.Request, u User) error {
		q := r.URL.Query()
		from, to, err := studyYears(q)
		if err != nil {
			return err
		}
		f := StudySearch{Kind: q.Get("kind"), Query: strings.TrimSpace(q.Get("q")), Creator: strings.TrimSpace(q.Get("creator")), Dates: q.Get("dates"), Cursor: q.Get("cursor"), From: from, To: to, ImageOnly: q.Get("image") == "true", Bookmarked: q.Get("saved") == "true"}
		if !studyKind(f.Kind) || len(f.Query) > 200 || len(f.Creator) > 200 || len(f.Cursor) > 4096 || (f.Dates != "" && f.Dates != "undated") {
			return studyInputError("Check your search filters.")
		}
		if h.config.LocalDebug && f.Bookmarked {
			saved, err := bookmarks.List(r.Context(), u.ID, f.Kind, BookmarkCursor{}, 1000)
			if err != nil {
				return err
			}
			f.LocalSaved = []string{}
			for _, v := range saved {
				f.LocalSaved = append(f.LocalSaved, v.ID)
			}
		}
		page, err := catalogue.Search(r.Context(), u.ID, f)
		if err != nil {
			return err
		}
		bookmarkJSON(w, page)
		return nil
	})
	register("GET", "/{id}", func(w http.ResponseWriter, r *http.Request, u User) error {
		s, err := store.Get(r.Context(), u.ID, r.PathValue("id"))
		if err != nil {
			return err
		}
		view, err := studyView(s, r.URL.Query())
		if err != nil {
			return err
		}
		view.ShareToken = s.ShareToken
		bookmarkJSON(w, view)
		return nil
	})
	register("PATCH", "/{id}", func(w http.ResponseWriter, r *http.Request, u User) error {
		var body struct {
			Public *bool   `json:"public"`
			Title  *string `json:"title"`
			Role   *string `json:"role"`
		}
		if !studyRead(w, r, &body) {
			return nil
		}
		s, err := store.Update(r.Context(), u.ID, r.PathValue("id"), func(s *Study) error {
			if body.Title != nil {
				title := strings.TrimSpace(*body.Title)
				if title == "" || utf8.RuneCountInString(title) > 180 {
					return studyInputError("Enter a title of up to 180 characters.")
				}
				s.Title = title
			}
			if body.Role != nil {
				if *body.Role != "research" {
					return studyInputError("Studies are for research.")
				}
				s.Role = *body.Role
			}
			if body.Public != nil {
				if !*body.Public {
					s.ShareToken = ""
				} else if s.ShareToken == "" {
					s.ShareToken = studyID()
				}
			}
			return nil
		})
		if err != nil {
			return err
		}
		bookmarkJSON(w, studySummary(s))
		return nil
	})
	register("DELETE", "/{id}", func(w http.ResponseWriter, r *http.Request, u User) error {
		if err := store.Delete(r.Context(), u.ID, r.PathValue("id")); err != nil {
			return err
		}
		bookmarkJSON(w, map[string]bool{"deleted": true})
		return nil
	})
	register("POST", "/{id}/records", func(w http.ResponseWriter, r *http.Request, u User) error {
		// Authorize ownership before performing any catalogue work.
		if _, err := store.Get(r.Context(), u.ID, r.PathValue("id")); err != nil {
			return err
		}
		var body struct {
			Refs []BookmarkRef `json:"refs"`
			Link *struct {
				Kind    string `json:"kind"`
				URL     string `json:"url"`
				Title   string `json:"title"`
				Creator string `json:"creator"`
				Year    *int   `json:"year"`
				EndYear *int   `json:"end_year"`
			} `json:"link"`
		}
		if !studyRead(w, r, &body) {
			return nil
		}
		records := []StudyRecord{}
		if body.Link != nil {
			b := body.Link
			if len(body.Refs) > 0 || !studyKind(b.Kind) || len(b.Title) > 500 || len(b.Creator) > 300 {
				return studyInputError("Choose a record type and check the title and creator.")
			}
			link := ""
			if strings.TrimSpace(b.URL) != "" {
				var err error
				link, err = studyURL(b.URL)
				if err != nil {
					return err
				}
			}
			title := strings.TrimSpace(b.Title)
			if title == "" && link != "" {
				parsed, _ := url.Parse(link)
				title = parsed.Hostname()
			}
			if title == "" {
				return studyInputError("Give your record a title.")
			}
			if b.Year == nil {
				return studyInputError("Enter a year, or a start and end year for a date range.")
			}
			end := *b.Year
			if b.EndYear != nil {
				end = *b.EndYear
			}
			if *b.Year == 0 || end == 0 || *b.Year < -12000 || end > 2000 || *b.Year > end || (b.Kind == "artwork" && end > 1970) {
				return studyInputError("Use years from −12000 to 2000 (artworks up to 1970), without year zero. The end year must be on or after the start year.")
			}
			date := studyDateYear(*b.Year)
			if end != *b.Year {
				date += "–" + studyDateYear(end)
			}
			sources := []StudySource{}
			if link != "" {
				sources = append(sources, StudySource{"Your source", link})
			}
			record := StudyRecord{BookmarkRef: BookmarkRef{b.Kind, studyID()}, Title: title, Creator: strings.TrimSpace(b.Creator), Date: date, Intervals: []StudyInterval{{*b.Year, end}}, Href: link, Sources: sources, Personal: true, DateNote: "Personal reference. Details and dates are supplied by you.", CapturedAt: time.Now().UTC()}
			records = append(records, record)
		} else {
			if len(body.Refs) < 1 || len(body.Refs) > 24 {
				return studyInputError("Choose between 1 and 24 records.")
			}
			for _, ref := range body.Refs {
				if !studyKind(ref.Kind) || !validBookmark(ref) {
					return studyInputError("Choose an available catalogue record.")
				}
			}
			var err error
			records, err = catalogue.Lookup(r.Context(), body.Refs)
			if err != nil {
				return err
			}
			if len(records) != len(body.Refs) {
				return ErrBookmarkMissing
			}
		}
		s, err := store.Update(r.Context(), u.ID, r.PathValue("id"), func(s *Study) error {
			for _, record := range records {
				if slices.ContainsFunc(s.Records, func(v StudyRecord) bool {
					return studyKey(v) == studyKey(record) || (v.Personal && record.Personal && v.Kind == record.Kind && record.Href != "" && v.Href == record.Href)
				}) {
					continue
				}
				if len(s.Records) >= studyRecordLimit {
					return ErrStudyLimit
				}
				s.Records = append(s.Records, record)
			}
			return nil
		})
		if err != nil {
			return err
		}
		bookmarkJSON(w, studySummary(s))
		return nil
	})
	for _, method := range []string{"PUT", "DELETE"} {
		register(method, "/{id}/records/{kind}/{record}", func(w http.ResponseWriter, r *http.Request, u User) error {
			var body struct {
				Note string `json:"note"`
			}
			if r.Method == "PUT" {
				if !studyRead(w, r, &body) {
					return nil
				}
				if len(body.Note) > 4000 {
					return studyInputError("Keep notes under 4,000 characters.")
				}
			}
			s, err := store.Update(r.Context(), u.ID, r.PathValue("id"), func(s *Study) error {
				i := slices.IndexFunc(s.Records, func(v StudyRecord) bool { return v.Kind == r.PathValue("kind") && v.ID == r.PathValue("record") })
				if i < 0 {
					return ErrStudyMissing
				}
				if r.Method == "DELETE" {
					s.Records = slices.Delete(s.Records, i, i+1)
				} else {
					s.Records[i].Note = body.Note
				}
				return nil
			})
			if err != nil {
				return err
			}
			bookmarkJSON(w, studySummary(s))
			return nil
		})
	}
	register("GET", "/{id}/export", func(w http.ResponseWriter, r *http.Request, u User) error {
		s, err := store.Get(r.Context(), u.ID, r.PathValue("id"))
		if err != nil {
			return err
		}
		return studyExport(w, s, r.URL.Query().Get("format"))
	})
}

func studyView(s Study, q url.Values) (StudyView, error) {
	v := StudyView{StudySummary: studySummary(s), Items: []StudyRecord{}, Artworks: []StudyRecord{}, Counts: map[string]int{"artwork": 0, "book": 0, "event": 0}}
	from, to, err := studyYears(q)
	if err != nil {
		return v, err
	}
	query := strings.ToLower(strings.TrimSpace(q.Get("q")))
	if len(query) > 200 {
		return v, studyInputError("Keep searches under 200 characters.")
	}
	kinds := q["kind"]
	for _, k := range kinds {
		if !studyKind(k) && k != "none" {
			return v, studyInputError("Choose artworks, books or events.")
		}
	}
	items := []StudyRecord{}
	for _, record := range s.Records {
		v.Keys = append(v.Keys, studyKey(record))
		v.Counts[record.Kind]++
		if record.Kind == "artwork" {
			option := record
			option.Image = nil
			option.Sources = nil
			option.Note = ""
			v.Artworks = append(v.Artworks, option)
		}
		if len(kinds) > 0 && !slices.Contains(kinds, record.Kind) {
			continue
		}
		if query != "" && !strings.Contains(strings.ToLower(record.Title+" "+record.Creator+" "+record.Note), query) {
			continue
		}
		if !studyOverlap(record, from, to) {
			continue
		}
		items = append(items, record)
		for _, i := range record.Intervals {
			if v.Range == nil {
				v.Range = &StudyInterval{i.Start, i.End}
			} else {
				v.Range.Start = min(v.Range.Start, i.Start)
				v.Range.End = max(v.Range.End, i.End)
			}
		}
	}
	if v.Range != nil {
		if from != nil {
			v.Range.Start = *from
		}
		if to != nil {
			v.Range.End = *to
		}
	}
	sort.SliceStable(items, func(i, j int) bool {
		if q.Get("view") == "gallery" && items[i].Kind != items[j].Kind {
			priority := map[string]int{"artwork": 0, "book": 1, "event": 2}
			return priority[items[i].Kind] < priority[items[j].Kind]
		}
		year := func(r StudyRecord) int {
			if len(r.Intervals) > 0 {
				return r.Intervals[0].Start
			}
			return 10000
		}
		a, b := year(items[i]), year(items[j])
		if a != b {
			return a < b
		}
		return studyKey(items[i]) < studyKey(items[j])
	})
	v.Matched = len(items)
	offset := 0
	if cursor := q.Get("cursor"); cursor != "" { // A bounded private set; cursor is the previous stable record key.
		if len(cursor) > 200 {
			return v, studyInputError("Reset the study page.")
		}
		i := slices.IndexFunc(items, func(r StudyRecord) bool { return studyKey(r) == cursor })
		if i < 0 {
			return v, studyInputError("The study changed. Reset the study page.")
		}
		offset = i + 1
	}
	end := min(offset+50, len(items))
	v.Items = items[offset:end]
	if end < len(items) {
		v.NextCursor = studyKey(items[end-1])
	}
	// Two independent compare picks, regardless of the current filter/page.
	if picks := q["compare"]; len(picks) > 0 {
		if len(picks) > 2 {
			return v, studyInputError("Choose two artworks.")
		}
		v.Artworks = []StudyRecord{}
		for _, key := range picks {
			for _, record := range s.Records {
				if record.Kind == "artwork" && studyKey(record) == key {
					v.Artworks = append(v.Artworks, record)
				}
			}
		}
	}
	return v, nil
}

// Kept here to make validation errors explicit without exposing SQL details.
func studyCursorError() error {
	return studyInputError(fmt.Sprint("The search changed. Start from the first page."))
}
