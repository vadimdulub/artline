package books

import "context"

// Count within precisely the same visibility, year and filter scope as List.
// Only unused dimensions are offered: replacing an existing OR selection could
// broaden the result and would invalidate these counts. Author membership uses
// the same label-or-linked-name rule as the list predicate.
const suggestionsQuery = `WITH matching AS MATERIALIZED (
 SELECT b.id,b.author_label,d.languages,d.countries,d.regions ` + predicate + `
), memberships AS (
 SELECT id,'language' AS key,unnest(languages) AS value FROM matching WHERE coalesce(cardinality($8::text[]),0)=0
 UNION ALL SELECT id,'country',unnest(countries) FROM matching WHERE coalesce(cardinality($9::text[]),0)=0
 UNION ALL SELECT id,'region',unnest(regions) FROM matching WHERE coalesce(cardinality($10::text[]),0)=0
 UNION ALL SELECT id,'author',author_label FROM matching WHERE coalesce(cardinality($5::text[]),0)=0
 UNION ALL SELECT m.id,'author',c.name FROM matching m
 JOIN book_creator_links l ON l.book_id=m.id JOIN book_creators c ON c.id=l.creator_id
 WHERE coalesce(cardinality($5::text[]),0)=0
), counts AS (
 SELECT key,value,count(DISTINCT id)::int AS count FROM memberships WHERE value<>''
 GROUP BY key,value HAVING count(DISTINCT id)<$11
)
SELECT c.key,c.value,coalesce(t.name,c.value),c.count FROM counts c
LEFT JOIN book_discovery_terms t ON t.kind=c.key AND t.key=c.value
ORDER BY (c.count<=100) DESC,CASE WHEN c.count<=100 THEN -c.count ELSE c.count END,c.key,c.value LIMIT 3`

func (r *Repository) suggestions(ctx context.Context, args []any, total int) ([]SuggestedFilter, error) {
	result := []SuggestedFilter{}
	rows, err := r.db.Query(ctx, suggestionsQuery, append(args, total)...)
	if err != nil {
		return result, err
	}
	defer rows.Close()
	for rows.Next() {
		var suggestion SuggestedFilter
		if err := rows.Scan(&suggestion.Key, &suggestion.Value, &suggestion.Name, &suggestion.Count); err != nil {
			return result, err
		}
		result = append(result, suggestion)
	}
	return result, rows.Err()
}
