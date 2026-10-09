package catalog

import (
	"context"
	"errors"

	"github.com/jackc/pgx/v5"
)

// ArtistIdentity supports a single artwork page without loading the painter's
// collection summaries, representative works, biography or influence graph.
type ArtistIdentity struct {
	ID          string `json:"id"`
	Slug        string `json:"slug"`
	DisplayName string `json:"display_name"`
	EntityType  string `json:"entity_type"`
}

const artistIdentityQuery = `SELECT id::text,slug,display_name,entity_type FROM artists WHERE
 (slug=$1 OR id=(SELECT entity_id FROM slug_redirects WHERE entity_type='artist' AND old_slug=$1))
 AND status<>'archived'`

func (r *Repository) ArtistIdentity(ctx context.Context, slug string) (ArtistIdentity, error) {
	var artist ArtistIdentity
	err := r.db.QueryRow(ctx, artistIdentityQuery, slug).Scan(&artist.ID, &artist.Slug, &artist.DisplayName, &artist.EntityType)
	if errors.Is(err, pgx.ErrNoRows) {
		return artist, ErrNotFound
	}
	return artist, err
}
