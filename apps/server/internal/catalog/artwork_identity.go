package catalog

import (
	"context"
	"errors"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
)

// CanonicalArtworkID preserves links to individually reconciled duplicates.
// Only an explicit artwork redirect can leave an archived record; an archive
// without one stays unavailable. Callers still apply their visibility and
// museum/artist membership policies to the returned active work.
func (r *Repository) CanonicalArtworkID(ctx context.Context, id string) (string, error) {
	var parsed pgtype.UUID
	if err := parsed.Scan(id); err != nil || !parsed.Valid {
		return "", ErrNotFound
	}
	var canonical string
	err := r.db.QueryRow(ctx, `WITH RECURSIVE resolved AS (
 SELECT a.id,a.slug,a.status,0 AS depth,ARRAY[a.id] AS visited
 FROM artworks a WHERE a.id=$1::uuid
 UNION ALL
 SELECT a.id,a.slug,a.status,previous.depth+1,previous.visited||a.id
 FROM resolved previous
 JOIN slug_redirects redirect ON redirect.entity_type='artwork' AND redirect.old_slug=previous.slug
 JOIN artworks a ON a.id=redirect.entity_id
 WHERE previous.status='archived' AND previous.depth<8 AND NOT a.id=ANY(previous.visited)
 ) SELECT id::text FROM resolved WHERE status<>'archived' ORDER BY depth LIMIT 1`, id).Scan(&canonical)
	if errors.Is(err, pgx.ErrNoRows) {
		return "", ErrNotFound
	}
	return canonical, err
}
