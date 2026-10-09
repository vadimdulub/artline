package catalog

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
)

// One indexed artist lookup, followed by one artwork primary-key lookup. Never
// rank a painter's full collection (or the global catalogue) during a page load.
const artistKeyArtworkQuery = `SELECT to_jsonb(aw)||jsonb_build_object(
 'attribution_role',k.attribution_role,'representative_order',aa.representative_order)
 FROM artist_key_artworks k
 JOIN artworks aw ON aw.id=k.artwork_id
 JOIN artwork_artists aa ON aa.artwork_id=k.artwork_id AND aa.artist_id=k.artist_id
   AND aa.attribution_role=k.attribution_role
 WHERE k.artist_id=$1 AND aw.status<>'archived'
 AND artline_creation_scope(aw.creation_year_start,aw.creation_year_end,aw.date_precision)='eligible'`

func (r *Repository) artistKeyArtwork(ctx context.Context, artistID string) (*Artwork, error) {
	var data []byte
	err := r.db.QueryRow(ctx, artistKeyArtworkQuery, artistID).Scan(&data)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("query artist key artwork: %w", err)
	}
	works := make([]Artwork, 1)
	if err = json.Unmarshal(data, &works[0]); err != nil {
		return nil, err
	}
	if err = r.enrichChronologyPage(ctx, works); err != nil {
		return nil, err
	}
	return &works[0], nil
}
