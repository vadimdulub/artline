package catalog

import (
	"context"
	"fmt"
	"strings"
)

const museumEditorialHighlightLimit = 24

type museumHighlightSet struct {
	IDs    []string `json:"ids"`
	Source string   `json:"source"`
}

// An Artlines browsing selection is distinct from a museum's documented list.
// Nothing is persisted as a museum designation, holding or display claim.
func (r *Repository) museumHighlights(ctx context.Context, slug string) (museumHighlightSet, error) {
	key := facetCacheKey(ctx, "museum-highlights:"+slug)
	out := museumHighlightSet{IDs: []string{}, Source: "museum"}
	if r.facets.get(key, &out) {
		return out, nil
	}
	rows, err := r.db.Query(ctx, museumScopedCTE+`SELECT w.id::text FROM institutions i
 JOIN selections s ON s.institution_id=i.id JOIN works w ON w.id=s.artwork_id
 WHERE i.slug=$1 AND `+museumVisible+` AND `+museumMembership+`
 GROUP BY w.id ORDER BY min(s.position),w.id LIMIT 24`, museumQueryArgs(slug)...)
	if err != nil {
		return out, err
	}
	for rows.Next() {
		var id string
		if err = rows.Scan(&id); err != nil {
			break
		}
		out.IDs = append(out.IDs, id)
	}
	rows.Close()
	if err != nil {
		return out, err
	}
	if err = rows.Err(); err != nil {
		return out, err
	}
	if len(out.IDs) == 0 {
		out.Source = "artlines"
		where := ` FROM institutions i JOIN works w ON ` + museumMembership + ` WHERE i.slug=$1 AND ` + museumVisible
		image := `EXISTS(SELECT 1 FROM media_assets image WHERE image.id=w.primary_media_id AND image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$')`
		for rank, filter := range []struct{ condition, native string }{
			{image, "aw.primary_media_id IS NOT NULL"},
			{"NOT " + image, "true"},
		} {
			remaining := museumEditorialHighlightLimit - len(out.IDs)
			if remaining == 0 {
				break
			}
			// Missing-image candidates are needed only when the collection has
			// fewer than 24 illustrated works. Each membership seeks separately.
			branches := museumOrderedCandidates(where, rank, filter.condition, filter.native, "true", fmt.Sprint(remaining))
			rows, err = r.db.Query(ctx, museumScopedCTE+`, candidates AS MATERIALIZED (`+strings.Join(branches, " UNION ALL ")+`)
 SELECT id::text FROM candidates ORDER BY normalized_title,id LIMIT `+fmt.Sprint(remaining), museumQueryArgs(slug)...)
			if err != nil {
				return out, err
			}
			for rows.Next() {
				var id string
				if err = rows.Scan(&id); err != nil {
					break
				}
				out.IDs = append(out.IDs, id)
			}
			rows.Close()
			if err != nil {
				return out, err
			}
			if err = rows.Err(); err != nil {
				return out, err
			}
		}
	}
	r.facets.put(key, out)
	return out, nil
}
