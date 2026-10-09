package catalog

import (
	"context"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"regexp"
)

type ArtworkDirectoryFilter struct {
	Query, Cursor      string
	Undated, ImageOnly bool
	Limit              int
}
type ArtworkDirectoryItem struct {
	ID           string     `json:"id"`
	Title        string     `json:"title"`
	DateDisplay  string     `json:"date_display"`
	Creator      string     `json:"creator"`
	Status       string     `json:"status"`
	MediaURL     *string    `json:"media_url"`
	AltText      *string    `json:"alt_text"`
	RightsStatus *string    `json:"rights_status"`
	Museum       *MuseumRef `json:"museum"`
}
type ArtworkDirectoryPage struct {
	Items      []ArtworkDirectoryItem `json:"items"`
	Total      int                    `json:"total"`
	NextCursor string                 `json:"next_cursor"`
}
type artworkDirectoryCursor struct{ Title, ID, Scope string }

var artworkDirectoryUUID = regexp.MustCompile(`^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$`)

// Catalogue browsing includes undated, unassigned and unillustrated records.
// Historical editorial status does not change visibility or date eligibility.
const artworkDirectoryWhere = ` FROM artworks aw WHERE aw.status<>'archived'
  AND ($1='' OR aw.title ILIKE '%'||$1||'%')
 AND (NOT $2 OR (aw.creation_year_start IS NULL AND aw.creation_year_end IS NULL))
 AND (NOT $3 OR (aw.primary_media_id IS NOT NULL AND EXISTS(SELECT 1 FROM media_assets image WHERE image.id=aw.primary_media_id
 AND image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$')))`

const artworkDirectoryPageSQL = `WITH page AS MATERIALIZED (
 SELECT aw.id,aw.normalized_title` + artworkDirectoryWhere + `
 AND (NOT $4 OR (aw.normalized_title,aw.id)>($5,$6::uuid))
 ORDER BY aw.normalized_title,aw.id LIMIT $7
 ) SELECT p.normalized_title,jsonb_build_object('id',aw.id,'title',aw.title,
 'date_display',aw.date_display,'status',aw.status,'media_url',ma.storage_path,
 'alt_text',ma.alt_text,'rights_status',ma.rights_status,
 'creator',coalesce((SELECT string_agg(names.name,', ' ORDER BY names.name) FROM
 (SELECT DISTINCT a.display_name AS name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id
 WHERE aa.artwork_id=aw.id AND a.status<>'archived' ) names),aw.unlinked_creator_label,''),
 'museum',CASE WHEN i.id IS NOT NULL THEN jsonb_build_object('id',i.id,'slug',i.slug,'name',i.name) END)
 FROM page p JOIN artworks aw ON aw.id=p.id LEFT JOIN media_assets ma ON ma.id=aw.primary_media_id
 LEFT JOIN institutions i ON i.id=aw.current_institution_id AND i.status<>'archived'
 ORDER BY p.normalized_title,p.id`

func (r *Repository) BrowseArtworks(ctx context.Context, f ArtworkDirectoryFilter) (ArtworkDirectoryPage, error) {
	out := ArtworkDirectoryPage{Items: []ArtworkDirectoryItem{}}
	if len(f.Query) > 200 || len(f.Cursor) > 4096 || f.Limit < 1 || f.Limit > 60 {
		return out, ErrChronologyFilter
	}
	scopeFilter := f
	scopeFilter.Cursor = ""
	raw, _ := json.Marshal([]any{scopeFilter})
	scope := fmt.Sprintf("%x", sha256.Sum256(raw))[:24]
	c := artworkDirectoryCursor{ID: "00000000-0000-0000-0000-000000000000"}
	if f.Cursor != "" {
		raw, err := base64.RawURLEncoding.DecodeString(f.Cursor)
		if err != nil || json.Unmarshal(raw, &c) != nil || c.Scope != scope || !artworkDirectoryUUID.MatchString(c.ID) || len(c.Title) > 2000 {
			return out, ErrChronologyFilter
		}
	}
	args := []any{f.Query, f.Undated, f.ImageOnly}
	// Catalogue-wide totals are updated in the same transaction as artwork edits.
	// Keep read-only local catalogues usable before this additive migration.
	var totalsTable *string
	if f.Query == "" && !f.ImageOnly {
		if err := r.db.QueryRow(ctx, "SELECT to_regclass('artwork_directory_totals')::text").Scan(&totalsTable); err != nil {
			return out, err
		}
	}
	if totalsTable != nil {
		if err := r.db.QueryRow(ctx, `SELECT coalesce(sum(total),0) FROM artwork_directory_totals
		 WHERE status<>'archived' AND (NOT $1 OR undated)`, museumQueryArgs(f.Undated)...).Scan(&out.Total); err != nil {
			return out, err
		}
	} else if err := r.db.QueryRow(ctx, "SELECT count(*)"+artworkDirectoryWhere, museumQueryArgs(args...)...).Scan(&out.Total); err != nil {
		return out, err
	}
	args = append(args, f.Cursor != "", c.Title, c.ID, f.Limit+1)
	rows, err := r.db.Query(ctx, artworkDirectoryPageSQL, museumQueryArgs(args...)...)
	if err != nil {
		return out, err
	}
	defer rows.Close()
	last := artworkDirectoryCursor{Scope: scope}
	for rows.Next() {
		var title string
		var raw []byte
		var item ArtworkDirectoryItem
		if err = rows.Scan(&title, &raw); err != nil {
			return out, err
		}
		if len(out.Items) == f.Limit {
			raw, _ = json.Marshal(last)
			out.NextCursor = base64.RawURLEncoding.EncodeToString(raw)
			break
		}
		if err = json.Unmarshal(raw, &item); err != nil {
			return out, err
		}
		out.Items = append(out.Items, item)
		last = artworkDirectoryCursor{title, item.ID, scope}
	}
	return out, rows.Err()
}
