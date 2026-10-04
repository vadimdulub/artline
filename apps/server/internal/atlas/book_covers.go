package atlas

import (
	"context"

	"github.com/vadimdulub/artline/apps/server/internal/books"
)

// Enrich only the returned, visibility-checked page with selected covers.
// One indexed identity lookup avoids fetching each full book separately.
func (r *Repository) attachBookCovers(ctx context.Context, items []Item) error {
	if len(items) == 0 {
		return nil
	}
	ids := make([]string, len(items))
	positions := make(map[string]int, len(items))
	for i, item := range items {
		ids[i], positions[item.ID] = item.ID, i
	}
	rows, err := r.db.Query(ctx, `SELECT id,source_id FROM book_records WHERE id=ANY($1::text[])`, ids)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var id, sourceID string
		if err := rows.Scan(&id, &sourceID); err != nil {
			return err
		}
		items[positions[id]].Cover = books.SelectedCover(id, sourceID)
	}
	return rows.Err()
}
