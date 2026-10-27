package exhibitions

import (
	"context"
	"errors"

	"github.com/jackc/pgx/v5"
)

// CanonicalID follows only explicit, individually reviewed identity aliases.
// An ordinary archived event or a programme/tour parent never implies an alias.
func (r *Repository) CanonicalID(ctx context.Context, id string) (string, error) {
	if !ValidID(id) {
		return "", ErrNotFound
	}
	if r.db == nil {
		return "", ErrUnavailable
	}
	var canonical string
	err := r.db.QueryRow(ctx, `WITH RECURSIVE identity AS (
 SELECT id,status,canonical_exhibition_id,0 AS depth,ARRAY[id] AS visited
 FROM exhibitions WHERE id=$1::uuid
 UNION ALL
 SELECT e.id,e.status,e.canonical_exhibition_id,previous.depth+1,previous.visited||e.id
 FROM identity previous JOIN exhibitions e ON e.id=previous.canonical_exhibition_id
 WHERE previous.status='archived' AND previous.depth<8 AND NOT e.id=ANY(previous.visited)
 ) SELECT id::text FROM identity WHERE status<>'archived' ORDER BY depth LIMIT 1`, id).Scan(&canonical)
	if errors.Is(err, pgx.ErrNoRows) {
		return "", ErrNotFound
	}
	return canonical, err
}
