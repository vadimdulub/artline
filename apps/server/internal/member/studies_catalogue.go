package member

import (
	"context"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/books"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"github.com/vadimdulub/artline/apps/server/internal/events"
)

type PostgresStudyCatalogue struct{ DB *pgxpool.Pool }
type studySearchCursor struct {
	Title string
	ID    string
	Scope string
}

func (p PostgresStudyCatalogue) Search(ctx context.Context, owner string, f StudySearch) (StudySearchPage, error) {
	out := StudySearchPage{Items: []StudyRecord{}}
	filter := f
	filter.Cursor = ""
	raw, _ := json.Marshal([]any{owner, filter})
	scope := fmt.Sprintf("%x", sha256.Sum256(raw))[:24]
	c := studySearchCursor{}
	if f.Cursor != "" {
		b, err := base64.RawURLEncoding.DecodeString(f.Cursor)
		if err != nil || json.Unmarshal(b, &c) != nil || c.Scope != scope || len(c.Title) > 2000 || !validBookmark(BookmarkRef{f.Kind, c.ID}) {
			return out, studyCursorError()
		}
	}
	args := []any{pgx.QueryExecModeCacheDescribe}
	bind := func(v any) string { args = append(args, v); return fmt.Sprintf("$%d", len(args)-1) }
	table, id, title, start, end := "artworks a", "a.id", "a.normalized_title", "a.creation_year_start", "a.creation_year_end"
	if f.Kind == "book" {
		table, id, title, start, end = "book_records a", "a.id", "lower(a.title)", "a.start_year", "a.end_year"
	}
	if f.Kind == "event" {
		table, id, title, start, end = "event_records a", "a.id", "lower(a.title)", "a.start_year", "a.end_year"
	}
	where := []string{"a.status<>'archived'"}
	if f.Kind == "artwork" {
		where = append(where, "artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)<>'excluded'")
	}
	if f.Kind == "book" {
		where = append(where, "(a.end_year<=2000 OR a.start_year IS NULL)")
	}
	if f.Query != "" {
		column := "a.title"
		if f.Kind != "artwork" {
			column = "a.search_text"
		}
		where = append(where, column+" ILIKE '%'||"+bind(f.Query)+"||'%'")
	}
	if f.Creator != "" {
		param := bind(f.Creator)
		if f.Kind == "artwork" {
			// Resolve matching creators before artwork enrichment; the reverse FK
			// index gives a bounded artist-to-artwork path for this optional filter.
			where = append(where, "a.id IN (SELECT aa.artwork_id FROM artists ar JOIN artwork_artists aa ON aa.artist_id=ar.id WHERE ar.status<>'archived' AND ar.display_name ILIKE '%'||"+param+"||'%')")
		} else if f.Kind == "book" {
			where = append(where, "a.author_label ILIKE '%'||"+param+"||'%'")
		} else {
			where = append(where, "a.kind ILIKE '%'||"+param+"||'%'")
		}
	}
	if f.Dates == "undated" {
		where = append(where, start+" IS NULL AND "+end+" IS NULL")
	}
	if f.From != nil {
		where = append(where, "coalesce("+end+","+start+")>="+bind(*f.From))
	}
	if f.To != nil {
		where = append(where, "coalesce("+start+","+end+")<="+bind(*f.To))
	}
	if f.ImageOnly && f.Kind == "artwork" {
		where = append(where, `EXISTS(SELECT 1 FROM media_assets image WHERE image.id=a.primary_media_id AND image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$')`)
	}
	if f.Bookmarked {
		if f.LocalSaved != nil {
			cast := "::text[]"
			if f.Kind == "artwork" {
				cast = "::uuid[]"
			}
			where = append(where, id+"=ANY("+bind(f.LocalSaved)+cast+")")
		} else {
			where = append(where, id+" IN (SELECT "+f.Kind+"_id FROM member_"+f.Kind+"_bookmarks WHERE member_id="+bind(owner)+")")
		}
	}
	// Materialize only matching native keys for text searches, then page them.
	query := "WITH candidates AS "
	if f.Query != "" || f.Creator != "" {
		query += "MATERIALIZED "
	}
	query += "(SELECT " + id + " AS id," + title + " AS title FROM " + table + " WHERE " + strings.Join(where, " AND ") + ") SELECT id::text,title FROM candidates"
	// Ordinary artwork browsing uses the existing primary-key order. Older
	// read-only catalogues may not have the newer alphabetical projection;
	// never scan/sort every wide artwork row merely to show the first 24.
	byID := f.Kind == "artwork" && f.Query == "" && f.Creator == ""
	if f.Cursor != "" {
		cast := ""
		if f.Kind == "artwork" {
			cast = "::uuid"
		}
		if byID {
			query += " WHERE candidates.id>" + bind(c.ID) + cast
		} else {
			query += " WHERE (title,id)>(" + bind(c.Title) + "," + bind(c.ID) + cast + ")"
		}
	}
	if byID {
		query += " ORDER BY candidates.id LIMIT 25"
	} else {
		query += " ORDER BY candidates.title,candidates.id LIMIT 25"
	}
	rows, err := p.DB.Query(ctx, query, args...)
	if err != nil {
		return out, err
	}
	refs := []BookmarkRef{}
	titles := []string{}
	for rows.Next() {
		var id, title string
		if err = rows.Scan(&id, &title); err != nil {
			break
		}
		refs = append(refs, BookmarkRef{f.Kind, id})
		titles = append(titles, title)
	}
	rows.Close()
	if err != nil {
		return out, err
	}
	if err = rows.Err(); err != nil {
		return out, err
	}
	if len(refs) > 24 {
		b, _ := json.Marshal(studySearchCursor{titles[23], refs[23].ID, scope})
		out.NextCursor = base64.RawURLEncoding.EncodeToString(b)
		refs = refs[:24]
	}
	out.Items, err = p.Lookup(ctx, refs)
	return out, err
}

func stringValue(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}

// Prefer unambiguous displayed year intervals to conflicting machine dates.
// Never connect separate stages (e.g. painting and a later added border), or
// turn open-ended/qualified prose into an exact year.
var studyYearParts = regexp.MustCompile(`\b([1-9][0-9]{3})(?:\s*[–—-]\s*([0-9]{2,4}))?\b`)

func studyIntervals(label string, start, end *int) ([]StudyInterval, string) {
	out := []StudyInterval{}
	lower := strings.ToLower(label)
	if strings.Contains(lower, "unverified") || strings.Contains(lower, "under review") || strings.Contains(lower, "unknown") || strings.Contains(lower, "later") || strings.Contains(lower, "before") || strings.Contains(lower, "after") || strings.Contains(lower, "century") || strings.Contains(lower, " or ") {
		return out, "The recorded date is qualified; it has not been converted to an exact interval."
	}
	parts := studyYearParts.FindAllStringSubmatch(label, -1)
	if len(parts) > 0 && !strings.Contains(lower, "bce") && !strings.Contains(lower, "bc") {
		for _, m := range parts {
			a, _ := strconv.Atoi(m[1])
			b := a
			if m[2] != "" {
				b, _ = strconv.Atoi(m[2])
				if len(m[2]) < 4 {
					power := 1
					for range len(m[2]) {
						power *= 10
					}
					b = (a/power)*power + b
					if b < a {
						b += power
					}
				}
			}
			if a <= b && b <= 2000 {
				out = append(out, StudyInterval{a, b})
			}
		}
		if len(out) > 0 {
			note := "Intervals follow the displayed catalogue date. Approximate dates retain their original label."
			if start != nil && (*start != out[0].Start || end != nil && *end != out[len(out)-1].End) {
				note += fmt.Sprintf(" Numeric catalogue dates (%d–%d) differ; the displayed label is retained.", *start, func() int {
					if end != nil {
						return *end
					}
					return *start
				}())
			}
			return out, note
		}
	}
	if start != nil && end != nil && *start != 0 && *end != 0 && *start <= *end {
		return []StudyInterval{{*start, *end}}, "Interval follows the recorded catalogue dates; the original date label is preserved."
	}
	return out, "Date not established as a closed interval. Kept in the study for review."
}
func studyImage(image *BookmarkImage) *BookmarkImage {
	if image == nil {
		return nil
	}
	u, err := url.Parse(image.ImageURL)
	if err != nil || u.User != nil || (!strings.HasPrefix(image.ImageURL, "/assets/") && !strings.HasPrefix(image.ImageURL, "/images/") && !(u.Scheme == "https" && (u.Host == "upload.wikimedia.org" || u.Host == "thumb.wikimedia.org"))) {
		return nil
	}
	return image
}
func (p PostgresStudyCatalogue) Lookup(ctx context.Context, refs []BookmarkRef) ([]StudyRecord, error) {
	out := []StudyRecord{}
	if len(refs) == 0 {
		return out, nil
	}
	if len(refs) > 24 {
		return out, studyInputError("Choose up to 24 records.")
	}
	ids := map[string][]string{}
	for _, ref := range refs {
		if !studyKind(ref.Kind) || !validBookmark(ref) {
			return out, ErrBookmarkMissing
		}
		ids[ref.Kind] = append(ids[ref.Kind], ref.ID)
	}
	byKey := map[string]StudyRecord{}
	now := time.Now().UTC()
	works, err := catalog.NewRepository(p.DB).StudyArtworks(ctx, ids["artwork"])
	if err != nil {
		return out, err
	}
	for _, a := range works {
		creators := []string{}
		for _, c := range a.Creators {
			name := c.Name
			if c.Role != "" && c.Role != "artist" && c.Role != "primary" && c.Role != "creator" {
				name += " (" + strings.ReplaceAll(c.Role, "_", " ") + ")"
			}
			creators = append(creators, name)
		}
		if len(creators) == 0 {
			creators = append(creators, stringValue(a.UnlinkedCreatorLabel))
		}
		intervals, note := studyIntervals(a.DateDisplay, a.CreationYearStart, a.CreationYearEnd)
		r := StudyRecord{BookmarkRef: BookmarkRef{"artwork", a.ID}, Title: a.Title, Creator: strings.Join(creators, ", "), Date: a.DateDisplay, Intervals: intervals, DateNote: note, Medium: stringValue(a.MediumText), Dimensions: stringValue(a.DimensionsText), Href: "/artworks?" + url.Values{"work": {a.ID}}.Encode(), Sources: []StudySource{}, CapturedAt: now}
		if len(a.Creators) > 0 {
			r.Href = "/artists/" + a.Creators[0].Slug + "/works/" + a.ID
		}
		if a.Holding != nil {
			r.Holding = a.Holding.Name
		}
		for _, c := range a.Citations {
			if _, err := studyURL(c.SourceURL); err == nil {
				r.Sources = append(r.Sources, StudySource{c.SourceName, c.SourceURL})
			}
		}
		if len(r.Sources) == 0 && a.SourcePageURL != nil {
			if _, err := studyURL(*a.SourcePageURL); err == nil {
				r.Sources = append(r.Sources, StudySource{"Image source", *a.SourcePageURL})
			}
		}
		if a.MediaURL != nil {
			license := stringValue(a.LicenseLabel)
			if license == "" {
				license = stringValue(a.RightsStatus)
			}
			r.Image = studyImage(&BookmarkImage{ImageURL: *a.MediaURL, SourceURL: stringValue(a.SourcePageURL), Label: a.Title, Credit: stringValue(a.AttributionText), License: license, LicenseURL: stringValue(a.LicenseURL)})
		}
		byKey[studyKey(r)] = r
	}
	eventImages := []events.Event{}
	for _, kind := range []string{"book", "event"} {
		if len(ids[kind]) == 0 {
			continue
		}
		scope := ""
		if kind == "book" {
			scope = " AND (end_year<=2000 OR start_year IS NULL)"
		}
		rows, err := p.DB.Query(ctx, `SELECT record FROM `+kind+`_records WHERE id=ANY($1::text[]) AND status<>'archived'`+scope, ids[kind])
		if err != nil {
			return out, err
		}
		for rows.Next() {
			var raw []byte
			if err = rows.Scan(&raw); err != nil {
				break
			}
			r := StudyRecord{BookmarkRef: BookmarkRef{Kind: kind}, CapturedAt: now, Sources: []StudySource{}}
			if kind == "book" {
				var b books.Book
				if err = json.Unmarshal(raw, &b); err != nil {
					break
				}
				r.ID = b.ID
				r.Title = b.Title
				r.Creator = b.Author
				r.Date = b.Years
				r.Intervals, r.DateNote = studyIntervals(b.Years, b.StartYear, b.EndYear)
				r.DateNote += " " + b.DateBasis
				r.Sources = append(r.Sources, StudySource{"Book source", b.SourceURL})
				for _, source := range b.DateSources {
					r.Sources = append(r.Sources, StudySource{source.Name, source.URL})
				}
				if image := books.SelectedCover(b.ID, b.SourceID); image != nil {
					r.Image = studyImage(&BookmarkImage{ImageURL: image.ImageURL, SourceURL: image.SourceURL, Label: image.Label, Credit: image.Credit, License: image.License, LicenseURL: image.LicenseURL})
				}
			} else {
				var e events.Event
				if err = json.Unmarshal(raw, &e); err != nil {
					break
				}
				r.ID = e.ID
				r.Title = e.Title
				r.Creator = e.Kind
				r.Date = e.Years
				r.Intervals, r.DateNote = studyIntervals(e.Years, e.StartYear, e.EndYear)
				r.DateNote += " " + e.DateBasis
				r.Sources = append(r.Sources, StudySource{"Event source", e.SourceURL})
				for _, source := range e.Sources {
					r.Sources = append(r.Sources, StudySource{source.Name, source.URL})
				}
				eventImages = append(eventImages, e)
			}
			r.Href = "/" + kind + "s?" + url.Values{kind: {r.ID}}.Encode()
			byKey[studyKey(r)] = r
		}
		rows.Close()
		if err != nil {
			return out, err
		}
		if err = rows.Err(); err != nil {
			return out, err
		}
	}
	if err := events.ResolveImages(ctx, p.DB, eventImages); err != nil {
		return out, err
	}
	for _, event := range eventImages {
		key := "event:" + event.ID
		record := byKey[key]
		record.Image = studyImage(bookmarkEventImage(event.Image))
		byKey[key] = record
	}
	for _, ref := range refs {
		if r, ok := byKey[ref.Kind+":"+ref.ID]; ok {
			out = append(out, r)
		}
	}
	return out, nil
}
