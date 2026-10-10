package member

import (
	"context"
	"errors"
	"sort"
	"sync"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/books"
	"github.com/vadimdulub/artline/apps/server/internal/events"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type PostgresBookmarks struct{ DB *pgxpool.Pool }

// Each branch starts at one member's indexed bookmarks. Only the bounded page
// is enriched; no global artwork collection, count, or offset scan is needed.
const bookmarkPageSQL = `WITH picked AS MATERIALIZED (
 SELECT * FROM (
  (SELECT 'artist'::text AS kind,b.artist_id::text AS id,b.created_at AS saved_at
   FROM member_artist_bookmarks b JOIN artists a ON a.id=b.artist_id
   WHERE b.member_id=$1 AND ($2='' OR $2='artist') AND a.status<>'archived'
    AND ($3::timestamptz IS NULL OR (b.created_at,'artist'::text,b.artist_id)<($3,$4::text,CASE WHEN $4='artist' THEN $5::text::uuid END))
   ORDER BY b.created_at DESC,b.artist_id DESC LIMIT $6)
  UNION ALL
  (SELECT 'artwork'::text,b.artwork_id::text,b.created_at
   FROM member_artwork_bookmarks b JOIN artworks a ON a.id=b.artwork_id
   WHERE b.member_id=$1 AND ($2='' OR $2='artwork') AND a.status<>'archived'
    AND ($3::timestamptz IS NULL OR (b.created_at,'artwork'::text,b.artwork_id)<($3,$4::text,CASE WHEN $4='artwork' THEN $5::text::uuid END))
   ORDER BY b.created_at DESC,b.artwork_id DESC LIMIT $6)
  UNION ALL
  (SELECT 'book'::text,b.book_id,b.created_at
   FROM member_book_bookmarks b JOIN book_records a ON a.id=b.book_id
   WHERE b.member_id=$1 AND ($2='' OR $2='book') AND a.status<>'archived'
    AND (a.end_year<=2000 OR a.start_year IS NULL)
    AND ($3::timestamptz IS NULL OR (b.created_at,'book'::text,b.book_id)<($3,$4::text,$5::text))
   ORDER BY b.created_at DESC,b.book_id DESC LIMIT $6)
  UNION ALL
  (SELECT 'event'::text,b.event_id,b.created_at
   FROM member_event_bookmarks b JOIN event_records a ON a.id=b.event_id
   WHERE b.member_id=$1 AND ($2='' OR $2='event') AND a.status<>'archived'
    AND ($3::timestamptz IS NULL OR (b.created_at,'event'::text,b.event_id)<($3,$4::text,$5::text))
   ORDER BY b.created_at DESC,b.event_id DESC LIMIT $6)
 ) candidates ORDER BY saved_at DESC,kind DESC,id DESC LIMIT $6
) `
const bookmarkDetailsSQL = `SELECT p.kind,p.id,p.saved_at,
 coalesce(a.display_name,w.title,b.title,e.title),
 coalesce(a.timeline_display,w.date_display,b.author_label,e.record->>'years',''),
 CASE WHEN p.kind='artist' THEN '/artists/'||a.slug
      WHEN p.kind='book' THEN '/books?book='||b.id
      WHEN p.kind='event' THEN '/events?event='||e.id
      WHEN creator.slug IS NOT NULL THEN '/artists/'||creator.slug||'/works/'||w.id::text
      ELSE '/all?itemType=artwork&item='||w.id::text END,
 ma.storage_path,ma.alt_text,ma.rights_status,coalesce(b.source_id,e.source_id,'')
 FROM picked p
 LEFT JOIN artists a ON a.id=CASE WHEN p.kind='artist' THEN p.id::uuid END
 LEFT JOIN artworks w ON w.id=CASE WHEN p.kind='artwork' THEN p.id::uuid END
 LEFT JOIN book_records b ON p.kind='book' AND b.id=p.id
 LEFT JOIN event_records e ON p.kind='event' AND e.id=p.id
 LEFT JOIN media_assets ma ON ma.id=w.primary_media_id
 LEFT JOIN LATERAL (
  SELECT ar.slug FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id
  WHERE aa.artwork_id=CASE WHEN p.kind='artwork' THEN p.id::uuid END AND ar.status<>'archived'
  ORDER BY (aa.attribution_role='primary') DESC,ar.slug LIMIT 1
 ) creator ON true
 WHERE (p.kind='artist' AND a.status<>'archived') OR (p.kind='artwork' AND w.status<>'archived')
    OR (p.kind='book' AND b.status<>'archived' AND (b.end_year<=2000 OR b.start_year IS NULL))
    OR (p.kind='event' AND e.status<>'archived')
 ORDER BY p.saved_at DESC,p.kind DESC,p.id DESC`

func scanBookmark(row interface{ Scan(...any) error }) (Bookmark, error) {
	var item Bookmark
	var sourceID string
	err := row.Scan(&item.Kind, &item.ID, &item.SavedAt, &item.Title, &item.Subtitle, &item.Href, &item.MediaURL, &item.AltText, &item.RightsStatus, &sourceID)
	if err == nil {
		if item.Kind == "book" {
			if image := books.SelectedCover(item.ID, sourceID); image != nil {
				item.Image = &BookmarkImage{image.ImageURL, image.SourceURL, image.Label, image.Credit, image.License, image.LicenseURL}
			}
		} else if item.Kind == "event" {
			if image := events.SelectedImage(item.ID, sourceID); image != nil {
				item.Image = &BookmarkImage{image.ImageURL, image.SourceURL, image.Label, image.Credit, image.License, image.LicenseURL}
			}
		}
	}
	return item, err
}
func (s PostgresBookmarks) List(ctx context.Context, memberID, kind string, cursor BookmarkCursor, limit int) ([]Bookmark, error) {
	var stamp *time.Time
	var id *string
	if !cursor.SavedAt.IsZero() {
		stamp = &cursor.SavedAt
		id = &cursor.ID
	}
	rows, err := s.DB.Query(ctx, bookmarkPageSQL+bookmarkDetailsSQL, memberID, kind, stamp, cursor.Kind, id, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := []Bookmark{}
	for rows.Next() {
		item, err := scanBookmark(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}
func (s PostgresBookmarks) Lookup(ctx context.Context, ref BookmarkRef) (Bookmark, error) {
	item, err := scanBookmark(s.DB.QueryRow(ctx, `WITH picked AS (SELECT $1::text AS kind,$2::text AS id,now() AS saved_at) `+bookmarkDetailsSQL, ref.Kind, ref.ID))
	if errors.Is(err, pgx.ErrNoRows) {
		err = ErrBookmarkMissing
	}
	return item, err
}

// Only this fixed allowlist supplies SQL identifiers and predicates.
func bookmarkTarget(kind string) (table, column, target, cast, scope string) {
	switch kind {
	case "artist":
		return "member_artist_bookmarks", "artist_id", "artists", "uuid", ""
	case "artwork":
		return "member_artwork_bookmarks", "artwork_id", "artworks", "uuid", ""
	case "book":
		return "member_book_bookmarks", "book_id", "book_records", "text", " AND (a.end_year<=2000 OR a.start_year IS NULL)"
	case "event":
		return "member_event_bookmarks", "event_id", "event_records", "text", ""
	}
	return
}
func (s PostgresBookmarks) Set(ctx context.Context, memberID string, ref BookmarkRef, saved bool) error {
	table, column, target, _, scope := bookmarkTarget(ref.Kind)
	if table == "" || !validBookmark(ref) {
		return ErrBookmarkMissing
	}
	if !saved {
		_, err := s.DB.Exec(ctx, `DELETE FROM `+table+` WHERE member_id=$1 AND `+column+`=$2`, memberID, ref.ID)
		return err
	}
	var exists bool
	err := s.DB.QueryRow(ctx, `WITH target AS (SELECT a.id FROM `+target+` a WHERE a.id=$2 AND a.status<>'archived'`+scope+`), inserted AS (
  INSERT INTO `+table+`(member_id,`+column+`) SELECT $1,id FROM target ON CONFLICT DO NOTHING
 ) SELECT EXISTS(SELECT 1 FROM target)`, memberID, ref.ID).Scan(&exists)
	if err == nil && !exists {
		return ErrBookmarkMissing
	}
	return err
}
func (s PostgresBookmarks) States(ctx context.Context, memberID string, refs []BookmarkRef) ([]BookmarkRef, error) {
	saved := []BookmarkRef{}
	for _, kind := range bookmarkKinds {
		ids := []string{}
		for _, ref := range refs {
			if ref.Kind == kind {
				ids = append(ids, ref.ID)
			}
		}
		if len(ids) == 0 {
			continue
		}
		table, column, target, cast, scope := bookmarkTarget(kind)
		rows, err := s.DB.Query(ctx, `SELECT b.`+column+`::text FROM `+table+` b JOIN `+target+` a ON a.id=b.`+column+` WHERE b.member_id=$1 AND b.`+column+`=ANY($2::`+cast+`[]) AND a.status<>'archived'`+scope, memberID, ids)
		if err != nil {
			return nil, err
		}
		for rows.Next() {
			var id string
			if err = rows.Scan(&id); err != nil {
				rows.Close()
				return nil, err
			}
			saved = append(saved, BookmarkRef{kind, id})
		}
		err = rows.Err()
		rows.Close()
		if err != nil {
			return nil, err
		}
	}
	return saved, nil
}

// Local previews keep only ephemeral bookmarks. Catalogue lookups are read-only;
// no synthetic member, session, or bookmark rows are written to the real database.
type LocalBookmarks struct {
	mu     sync.Mutex
	items  map[BookmarkRef]Bookmark
	lookup func(context.Context, BookmarkRef) (Bookmark, error)
}

func NewLocalBookmarks(lookup func(context.Context, BookmarkRef) (Bookmark, error)) *LocalBookmarks {
	return &LocalBookmarks{items: map[BookmarkRef]Bookmark{}, lookup: lookup}
}
func (s *LocalBookmarks) Set(ctx context.Context, _ string, ref BookmarkRef, saved bool) error {
	if !saved {
		s.mu.Lock()
		delete(s.items, ref)
		s.mu.Unlock()
		return nil
	}
	item, err := s.lookup(ctx, ref)
	if err != nil {
		return err
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.items[ref]; ok {
		return nil
	}
	if len(s.items) >= 1000 {
		return ErrBookmarkLimit
	}
	s.items[ref] = item
	return nil
}
func (s *LocalBookmarks) States(_ context.Context, _ string, refs []BookmarkRef) ([]BookmarkRef, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	saved := []BookmarkRef{}
	for _, ref := range refs {
		if _, ok := s.items[ref]; ok {
			saved = append(saved, ref)
		}
	}
	return saved, nil
}
func bookmarkBefore(a, b Bookmark) bool {
	if !a.SavedAt.Equal(b.SavedAt) {
		return a.SavedAt.After(b.SavedAt)
	}
	if a.Kind != b.Kind {
		return a.Kind > b.Kind
	}
	return a.ID > b.ID
}
func (s *LocalBookmarks) List(_ context.Context, _ string, kind string, cursor BookmarkCursor, limit int) ([]Bookmark, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	items := []Bookmark{}
	after := Bookmark{BookmarkRef: BookmarkRef{cursor.Kind, cursor.ID}, SavedAt: cursor.SavedAt}
	for _, item := range s.items {
		if kind != "" && item.Kind != kind {
			continue
		}
		if !cursor.SavedAt.IsZero() && !bookmarkBefore(after, item) {
			continue
		}
		items = append(items, item)
	}
	sort.Slice(items, func(i, j int) bool { return bookmarkBefore(items[i], items[j]) })
	if len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}
