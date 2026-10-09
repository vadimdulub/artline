package atlas

import (
	"context"
	"fmt"
	"strings"
)

// Role-qualified identities stay distinct until the catalogue reconciles them.
func validateCreators(values []string) error {
	if len(values) > 32 {
		return ErrFilter
	}
	seen := map[string]bool{}
	for _, value := range values {
		kind, id, ok := strings.Cut(value, ":")
		if !ok || (kind != "painter" && kind != "author") || len(id) > 200 || !recordIDPattern.MatchString(id) || seen[value] {
			return ErrFilter
		}
		seen[value] = true
	}
	return nil
}
func creatorPredicate(kind string, values []string, args *[]any) string {
	if len(values) == 0 || kind == "event" {
		return "true"
	}
	role := "painter"
	if kind == "book" {
		role = "author"
	}
	ids := []string{}
	for _, value := range values {
		if id, ok := strings.CutPrefix(value, role+":"); ok {
			ids = append(ids, id)
		}
	}
	if len(ids) == 0 {
		return "false"
	}
	*args = append(*args, ids)
	p := fmt.Sprintf("$%d::text[]", len(*args)-1)
	if kind == "book" {
		return `b.id IN (SELECT l.book_id FROM book_creator_links l WHERE l.creator_id=ANY(` + p + `))`
	}
	return `a.id IN (SELECT aa.artwork_id FROM artists ar JOIN artwork_artists aa ON aa.artist_id=ar.id WHERE ar.slug=ANY(` + p + `) AND ar.status<>'archived' )`
}

type CreatorChoices struct {
	Items    []Region `json:"items"`
	Selected []Region `json:"selected"`
	HasMore  bool     `json:"has_more"`
}

// Search is bounded independently of selected labels. No collection is sent to the browser.
func (r *Repository) Creators(ctx context.Context, query string, selected []string) (CreatorChoices, error) {
	out := CreatorChoices{Items: []Region{}, Selected: []Region{}}
	if len(query) > 200 {
		return out, ErrFilter
	}
	if err := validateCreators(selected); err != nil {
		return out, err
	}
	if r.db == nil {
		return out, fmt.Errorf("atlas unavailable")
	}
	const candidates = `WITH candidates AS (
 SELECT 'painter:'||ar.slug AS slug,ar.display_name||' · Painter' AS name,lower(ar.display_name) AS sort_name FROM artists ar
 WHERE ar.status<>'archived'
 UNION ALL SELECT 'author:'||c.id,c.name||' · Author',lower(c.name) FROM book_creators c
 WHERE EXISTS(SELECT 1 FROM book_creator_links l JOIN book_records b ON b.id=l.book_id WHERE l.creator_id=c.id AND b.status<>'archived'  AND b.end_year<=2000)) `
	rows, err := r.db.Query(ctx, candidates+`SELECT slug,name,false AS selected FROM (SELECT * FROM candidates WHERE $1='' OR strpos(sort_name,lower($1))>0 ORDER BY sort_name,slug LIMIT 31) found
 UNION ALL SELECT slug,name,true FROM candidates WHERE slug=ANY($2::text[])`, strings.TrimSpace(query), selected)
	if err != nil {
		return out, err
	}
	defer rows.Close()
	for rows.Next() {
		var item Region
		var chosen bool
		if err := rows.Scan(&item.Key, &item.Name, &chosen); err != nil {
			return out, err
		}
		if chosen {
			out.Selected = append(out.Selected, item)
		} else {
			out.Items = append(out.Items, item)
		}
	}
	if err := rows.Err(); err != nil {
		return out, err
	}
	if len(out.Items) > 30 {
		out.Items = out.Items[:30]
		out.HasMore = true
	}
	return out, nil
}
