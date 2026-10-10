package member

import (
	"context"
	"errors"
	"sort"
	"sync"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type PostgresBookmarks struct{ DB *pgxpool.Pool }

// Each branch starts at one member's indexed bookmarks. Only the bounded page
// is enriched; no global artwork collection, count, or offset scan is needed.
const bookmarkPageSQL = `WITH picked AS MATERIALIZED (
 SELECT * FROM (
  (SELECT 'artist'::text AS kind,b.artist_id AS id,b.created_at AS saved_at
   FROM member_artist_bookmarks b JOIN artists a ON a.id=b.artist_id
   WHERE b.member_id=$1 AND ($2='' OR $2='artist') AND a.status<>'archived'
    AND ($3::timestamptz IS NULL OR (b.created_at,'artist'::text,b.artist_id)<($3,$4::text,$5::uuid))
   ORDER BY b.created_at DESC,b.artist_id DESC LIMIT $6)
  UNION ALL
  (SELECT 'artwork'::text,b.artwork_id,b.created_at
   FROM member_artwork_bookmarks b JOIN artworks a ON a.id=b.artwork_id
   WHERE b.member_id=$1 AND ($2='' OR $2='artwork') AND a.status<>'archived'
    AND ($3::timestamptz IS NULL OR (b.created_at,'artwork'::text,b.artwork_id)<($3,$4::text,$5::uuid))
   ORDER BY b.created_at DESC,b.artwork_id DESC LIMIT $6)
 ) candidates ORDER BY saved_at DESC,kind DESC,id DESC LIMIT $6
) `
const bookmarkDetailsSQL = `SELECT p.kind,p.id::text,p.saved_at,
 coalesce(a.display_name,w.title),coalesce(a.timeline_display,w.date_display,''),
 CASE WHEN p.kind='artist' THEN '/artists/'||a.slug
      WHEN creator.slug IS NOT NULL THEN '/artists/'||creator.slug||'/works/'||w.id::text
      ELSE '/all?itemType=artwork&item='||w.id::text END,
 ma.storage_path,ma.alt_text,ma.rights_status
 FROM picked p
 LEFT JOIN artists a ON p.kind='artist' AND a.id=p.id
 LEFT JOIN artworks w ON p.kind='artwork' AND w.id=p.id
 LEFT JOIN media_assets ma ON ma.id=w.primary_media_id
 LEFT JOIN LATERAL (
  SELECT ar.slug FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id
  WHERE p.kind='artwork' AND aa.artwork_id=p.id AND ar.status<>'archived'
  ORDER BY (aa.attribution_role='primary') DESC,ar.slug LIMIT 1
 ) creator ON true
 WHERE (p.kind='artist' AND a.status<>'archived') OR (p.kind='artwork' AND w.status<>'archived')
 ORDER BY p.saved_at DESC,p.kind DESC,p.id DESC`

func scanBookmark(row interface{ Scan(...any) error }) (Bookmark, error) {
	var item Bookmark
	err := row.Scan(&item.Kind, &item.ID, &item.SavedAt, &item.Title, &item.Subtitle, &item.Href, &item.MediaURL, &item.AltText, &item.RightsStatus)
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
	item, err := scanBookmark(s.DB.QueryRow(ctx, `WITH picked AS (SELECT $1::text AS kind,$2::uuid AS id,now() AS saved_at) `+bookmarkDetailsSQL, ref.Kind, ref.ID))
	if errors.Is(err, pgx.ErrNoRows) {
		err = ErrBookmarkMissing
	}
	return item, err
}
func (s PostgresBookmarks) Set(ctx context.Context, memberID string, ref BookmarkRef, saved bool) error {
	table, column, target := "member_artist_bookmarks", "artist_id", "artists"
	if ref.Kind == "artwork" {
		table, column, target = "member_artwork_bookmarks", "artwork_id", "artworks"
	}
	if !saved {
		_, err := s.DB.Exec(ctx, `DELETE FROM `+table+` WHERE member_id=$1 AND `+column+`=$2`, memberID, ref.ID)
		return err
	}
	var exists bool
	err := s.DB.QueryRow(ctx, `WITH target AS (SELECT id FROM `+target+` WHERE id=$2 AND status<>'archived'), inserted AS (
  INSERT INTO `+table+`(member_id,`+column+`) SELECT $1,id FROM target ON CONFLICT DO NOTHING
 ) SELECT EXISTS(SELECT 1 FROM target)`, memberID, ref.ID).Scan(&exists)
	if err == nil && !exists {
		return ErrBookmarkMissing
	}
	return err
}
func (s PostgresBookmarks) States(ctx context.Context, memberID string, refs []BookmarkRef) ([]BookmarkRef, error) {
	saved := []BookmarkRef{}
	for _, kind := range []string{"artist", "artwork"} {
		ids := []string{}
		for _, ref := range refs {
			if ref.Kind == kind {
				ids = append(ids, ref.ID)
			}
		}
		if len(ids) == 0 {
			continue
		}
		table, column, target := "member_artist_bookmarks", "artist_id", "artists"
		if kind == "artwork" {
			table, column, target = "member_artwork_bookmarks", "artwork_id", "artworks"
		}
		rows, err := s.DB.Query(ctx, `SELECT b.`+column+`::text FROM `+table+` b JOIN `+target+` a ON a.id=b.`+column+` WHERE b.member_id=$1 AND b.`+column+`=ANY($2::uuid[]) AND a.status<>'archived'`, memberID, ids)
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
