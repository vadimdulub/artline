package catalog

import (
	"context"
	"encoding/json"
	"errors"
	"github.com/jackc/pgx/v5"
)

type AtlasCreator struct {
	ID    string `json:"id"`
	Slug  string `json:"slug"`
	Name  string `json:"name"`
	Years string `json:"years"`
	Role  string `json:"role"`
}
type AtlasArtwork struct {
	Artwork
	Creators []AtlasCreator `json:"creators"`
}

// The caller applies atlas eligibility. This method independently checks native
// visibility and enriches one UUID, never the global museum artwork relation.
func (r *Repository) AtlasArtwork(ctx context.Context, id string, preview bool) (AtlasArtwork, error) {
	out := AtlasArtwork{Creators: []AtlasCreator{}}
	var raw []byte
	err := r.db.QueryRow(ctx, `SELECT to_jsonb(a)||jsonb_build_object('media_url',CASE WHEN m.verified_at IS NOT NULL AND m.rights_status IN ('public_domain','cc0','cc_by','cc_by_sa','licensed') AND nullif(trim(m.alt_text),'') IS NOT NULL THEN m.storage_path END,'alt_text',m.alt_text,'rights_status',m.rights_status,'attribution_text',m.attribution_text,'source_page_url',m.source_page_url,'license_label',m.license_label,'license_url',m.license_url) FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=$1 AND a.status<>'archived' AND ($2 OR a.status='published')`, id, preview).Scan(&raw)
	if errors.Is(err, pgx.ErrNoRows) {
		return out, ErrNotFound
	}
	if err != nil {
		return out, err
	}
	if err = json.Unmarshal(raw, &out.Artwork); err != nil {
		return out, err
	}
	works := []Artwork{out.Artwork}
	if err = r.enrichArtworks(ctx, works, preview); err != nil {
		return out, err
	}
	out.Artwork = works[0]
	rows, err := r.db.Query(ctx, `SELECT ar.id::text,ar.slug,ar.display_name,ar.timeline_display,aa.attribution_role FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=$1 AND ar.status<>'archived' AND ($2 OR ar.status='published') ORDER BY ar.sort_name,ar.id,aa.attribution_role`, id, preview)
	if err != nil {
		return out, err
	}
	defer rows.Close()
	for rows.Next() {
		var c AtlasCreator
		if err = rows.Scan(&c.ID, &c.Slug, &c.Name, &c.Years, &c.Role); err != nil {
			return out, err
		}
		out.Creators = append(out.Creators, c)
	}
	return out, rows.Err()
}
