package catalog

import "context"

type PainterOptions struct {
	Items    []FacetOption `json:"items"`
	Selected []FacetOption `json:"selected"`
	HasMore  bool          `json:"has_more"`
}

// At most 30 search results and 32 explicitly selected identities leave the API.
// Museum requests use the same scoped membership/visibility policy as artwork lists.
func (r *Repository) PainterOptions(ctx context.Context, query, museum string, selected []string, preview, popular bool) (PainterOptions, error) {
	out := PainterOptions{Items: []FacetOption{}, Selected: []FacetOption{}}
	cte, membership := "", ""
	if museum != "" {
		cte = museumScopedCTE
		membership = ` AND EXISTS(SELECT 1 FROM institutions i JOIN works w ON ` + museumMembership + ` JOIN artwork_artists aa ON aa.artwork_id=w.id WHERE i.slug=$2 AND ` + museumVisible + ` AND aa.artist_id=a.id)`
	}
	rows, err := r.db.Query(ctx, cte+`SELECT a.slug,a.display_name FROM artists a
 LEFT JOIN artist_discovery_selection ds ON ds.artist_id=a.id
 WHERE a.status<>'archived' AND ($1 OR a.status='published') AND ($2::text IS NOT NULL)
 AND (NOT $4 OR coalesce(ds.is_popular,false))
 AND ($3='' OR a.display_name ILIKE '%'||$3||'%' OR EXISTS(SELECT 1 FROM artist_aliases x WHERE x.artist_id=a.id AND x.alias ILIKE '%'||$3||'%'))`+membership+`
 ORDER BY coalesce(ds.is_popular,false) DESC,ds.popularity_rank NULLS LAST,a.sort_name,a.id LIMIT 31`, preview, museum, query, popular)
	if err != nil {
		return out, err
	}
	for rows.Next() {
		var option FacetOption
		if err = rows.Scan(&option.Slug, &option.Name); err != nil {
			break
		}
		out.Items = append(out.Items, option)
	}
	rows.Close()
	if err != nil {
		return out, err
	}
	if err = rows.Err(); err != nil {
		return out, err
	}
	if len(out.Items) > 30 {
		out.HasMore = true
		out.Items = out.Items[:30]
	}
	rows, err = r.db.Query(ctx, `SELECT slug,display_name FROM artists WHERE slug=ANY($1::text[]) AND status<>'archived' AND ($2 OR status='published') ORDER BY sort_name,id LIMIT 32`, filterChoices(selected, ""), preview)
	if err != nil {
		return out, err
	}
	defer rows.Close()
	for rows.Next() {
		var option FacetOption
		if err = rows.Scan(&option.Slug, &option.Name); err != nil {
			return out, err
		}
		out.Selected = append(out.Selected, option)
	}
	return out, rows.Err()
}
