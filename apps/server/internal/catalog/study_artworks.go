package catalog

import (
	"context"
	"encoding/json"
)

// StudyArtworks enriches only requested IDs, in a constant number of queries.
// It retains active uncertain/undated works and excludes definitely post-1970 works.
func (r *Repository) StudyArtworks(ctx context.Context, ids []string) ([]AtlasArtwork, error) {
	out := []AtlasArtwork{}
	if len(ids) == 0 {
		return out, nil
	}
	if len(ids) > 24 {
		return nil, ErrChronologyFilter
	}
	rows, err := r.db.Query(ctx, `SELECT to_jsonb(a)||jsonb_build_object('media_url',m.storage_path,'alt_text',m.alt_text,'rights_status',m.rights_status,'attribution_text',m.attribution_text,'source_page_url',m.source_page_url,'license_label',m.license_label,'license_url',m.license_url)
 FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY($1::uuid[]) AND a.status<>'archived' AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)<>'excluded'`, ids)
	if err != nil {
		return nil, err
	}
	works := []Artwork{}
	for rows.Next() {
		var b []byte
		var a Artwork
		if err = rows.Scan(&b); err != nil {
			break
		}
		if err = json.Unmarshal(b, &a); err != nil {
			break
		}
		works = append(works, a)
	}
	rows.Close()
	if err != nil {
		return nil, err
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}
	if err = r.enrichArtworks(ctx, works); err != nil {
		return nil, err
	}
	byID := map[string]int{}
	for _, a := range works {
		byID[a.ID] = len(out)
		out = append(out, AtlasArtwork{Artwork: a, Creators: []AtlasCreator{}})
	}
	rows, err = r.db.Query(ctx, `SELECT aa.artwork_id::text,ar.id::text,ar.slug,ar.display_name,ar.timeline_display,aa.attribution_role FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY($1::uuid[]) AND ar.status<>'archived' ORDER BY ar.sort_name,ar.id,aa.attribution_role`, ids)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	for rows.Next() {
		var id string
		var c AtlasCreator
		if err = rows.Scan(&id, &c.ID, &c.Slug, &c.Name, &c.Years, &c.Role); err != nil {
			return nil, err
		}
		if i, ok := byID[id]; ok {
			out[i].Creators = append(out[i].Creators, c)
		}
	}
	return out, rows.Err()
}
