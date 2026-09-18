package books

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
)

type TimelineAuthor struct {
	Creator
	StartYear   *int     `json:"startYear"`
	EndYear     *int     `json:"endYear"`
	Lifespan    string   `json:"lifespan"`
	Approximate bool     `json:"approximate"`
	BookCount   int      `json:"bookCount"`
	Credits     []string `json:"credits"`
}

// Parse only the complete, documented date-label grammar produced by the book
// import. Ranges/alternatives stay uncertain; their outer limits are used for
// overlap queries and dashed marks, never presented as exact birth/death years.
// Unsupported labels stay unplaced. Missing death is NOT evidence of living.
const lifeDateTerm = `(c[.] )?[1-9][0-9]{0,3}( BCE)?(–[1-9][0-9]{0,3}( BCE)?)?`
const lifeDatePattern = `^` + lifeDateTerm + `( or ` + lifeDateTerm + `)*$`
const authorTimelineScope = `WITH eligible_books AS MATERIALIZED (
 SELECT b.id,b.author_label,d.languages,d.countries,d.regions,d.woman_author_ids ` + scopePredicate + `
), links AS MATERIALIZED (
 SELECT b.id AS book_id,c.id AS author_id,l.credit
 FROM eligible_books b JOIN book_creator_links l ON l.book_id=b.id JOIN book_creators c ON c.id=l.creator_id
 WHERE (NOT $6 OR c.id=ANY(b.woman_author_ids))
 AND (coalesce(cardinality($5::text[]),0)=0 OR c.name=ANY($5))
), author_ids AS (
 SELECT author_id,count(DISTINCT book_id)::int AS book_count,array_agg(DISTINCT credit ORDER BY credit) AS credits FROM links GROUP BY author_id
), dates AS (
 SELECT c.id,c.name,c.record->>'kind' AS kind,c.record->>'birth' AS birth,c.record->>'death' AS death,a.book_count,a.credits,
 life.birth_start,life.birth_end,life.death_start,life.death_end
 FROM author_ids a JOIN book_creators c ON c.id=a.author_id
 LEFT JOIN LATERAL (
  SELECT min(y) FILTER (WHERE part='birth') AS birth_start,max(y) FILTER (WHERE part='birth') AS birth_end,
         min(y) FILTER (WHERE part='death') AS death_start,max(y) FILTER (WHERE part='death') AS death_end
  FROM (SELECT part,(token[1])::int * CASE WHEN token[2]=' BCE' THEN -1 ELSE 1 END AS y
   FROM (VALUES ('birth',c.record->>'birth'),('death',c.record->>'death')) labels(part,label)
   CROSS JOIN LATERAL regexp_matches(CASE WHEN label ~ '` + lifeDatePattern + `' THEN label ELSE '' END,'([0-9]+)( BCE)?','g') AS token
  ) parsed
 ) life ON c.record->>'kind'<>'collective'
), classified AS MATERIALIZED (
 SELECT *,CASE WHEN coalesce(birth_start,death_start) BETWEEN -5000 AND 2026 AND coalesce(death_end,birth_end) BETWEEN -5000 AND 2026
  AND coalesce(birth_start,death_start)<=coalesce(death_end,birth_end) THEN coalesce(birth_start,death_start) END AS start_year,
 CASE WHEN coalesce(birth_start,death_start) BETWEEN -5000 AND 2026 AND coalesce(death_end,birth_end) BETWEEN -5000 AND 2026
  AND coalesce(birth_start,death_start)<=coalesce(death_end,birth_end) THEN coalesce(death_end,birth_end) END AS end_year,
 (kind<>'person' OR birth IS NULL OR death IS NULL OR birth !~ '^[1-9][0-9]*( BCE)?$' OR death !~ '^[1-9][0-9]*( BCE)?$') AS approximate
 FROM dates
), matching AS MATERIALIZED (
 SELECT * FROM classified WHERE (start_year <= $2 AND end_year >= $1) OR (start_year IS NULL AND $1=-5000 AND $2=2000)
) `

const authorSuggestionsQuery = authorTimelineScope + `, memberships AS (
 SELECT a.id,'language' AS key,unnest(b.languages) AS value FROM matching a JOIN links l ON l.author_id=a.id JOIN eligible_books b ON b.id=l.book_id WHERE coalesce(cardinality($8::text[]),0)=0
 UNION ALL SELECT a.id,'country',unnest(b.countries) FROM matching a JOIN links l ON l.author_id=a.id JOIN eligible_books b ON b.id=l.book_id WHERE coalesce(cardinality($9::text[]),0)=0
 UNION ALL SELECT a.id,'region',unnest(b.regions) FROM matching a JOIN links l ON l.author_id=a.id JOIN eligible_books b ON b.id=l.book_id WHERE coalesce(cardinality($10::text[]),0)=0
 UNION ALL SELECT id,'author',name FROM matching WHERE coalesce(cardinality($5::text[]),0)=0
), counts AS (
 SELECT key,value,count(DISTINCT id)::int AS count FROM memberships WHERE value<>'' GROUP BY key,value HAVING count(DISTINCT id)<$11
)
SELECT c.key,c.value,coalesce(t.name,c.value),c.count FROM counts c LEFT JOIN book_discovery_terms t ON t.kind=c.key AND t.key=c.value
ORDER BY (c.count<=100) DESC,CASE WHEN c.count<=100 THEN -c.count ELSE c.count END,c.key,c.value LIMIT 3`

func authorLifeLabel(c Creator) string {
	if c.Kind == "collective" {
		return "Collective authorship · no single lifespan"
	}
	if c.Birth != nil && c.Death != nil {
		return *c.Birth + "–" + *c.Death
	}
	if c.Birth != nil {
		return "Born " + *c.Birth + " · death not recorded"
	}
	if c.Death != nil {
		return "Birth not recorded · died " + *c.Death
	}
	return "Lifespan not established"
}

func (r *Repository) authorTimeline(ctx context.Context, f Filter) (Response, error) {
	result := metadata(f.Range)
	result.View, result.Authors = "authors", []TimelineAuthor{}
	args := []any{f.Start, f.End, f.Preview, strings.TrimSpace(f.Query), f.Authors, f.Women, f.Top100, f.Languages, f.Countries, f.Regions}
	if err := r.db.QueryRow(ctx, authorTimelineScope+`SELECT count(*),count(*) FILTER (WHERE start_year IS NULL),(SELECT count(*) FROM classified) FROM matching`, args...).Scan(&result.Total, &result.UndatedTotal, &result.SelectionTotal); err != nil {
		return result, fmt.Errorf("count authors: %w", err)
	}
	c, _ := decodeCursor(f.After)
	rows, err := r.db.Query(ctx, authorTimelineScope+`SELECT c.record,a.start_year,a.end_year,coalesce(a.approximate,true),a.book_count,a.credits
 FROM (SELECT * FROM matching WHERE (coalesce(start_year,2147483647),id)>($11,$12) ORDER BY coalesce(start_year,2147483647),id LIMIT $13) a
 JOIN book_creators c ON c.id=a.id ORDER BY coalesce(a.start_year,2147483647),a.id`, append(args, c.Year, c.ID, f.Limit+1)...)
	if err != nil {
		return result, err
	}
	for rows.Next() {
		var a TimelineAuthor
		var raw []byte
		if err = rows.Scan(&raw, &a.StartYear, &a.EndYear, &a.Approximate, &a.BookCount, &a.Credits); err != nil {
			rows.Close()
			return result, err
		}
		if err = json.Unmarshal(raw, &a.Creator); err != nil {
			rows.Close()
			return result, err
		}
		a.Lifespan = authorLifeLabel(a.Creator)
		result.Authors = append(result.Authors, a)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return result, err
	}
	if len(result.Authors) > f.Limit {
		result.Authors = result.Authors[:f.Limit]
		result.HasMore = true
		last := result.Authors[len(result.Authors)-1]
		result.NextCursor = encodeCursor(Book{ID: last.ID, StartYear: last.StartYear})
	}
	if result.Total-result.UndatedTotal <= 100 {
		return result, nil
	}
	result.Mode = "density"
	starts, ends := []int{}, []int{}
	for _, p := range densityPeriods(f.Range) {
		starts = append(starts, p.Start)
		ends = append(ends, p.End)
	}
	rows, err = r.db.Query(ctx, authorTimelineScope+`SELECT p.start_year,p.end_year,count(*) FROM unnest($11::int[],$12::int[]) p(start_year,end_year)
 JOIN matching a ON a.start_year<=p.end_year AND a.end_year>=p.start_year GROUP BY p.start_year,p.end_year ORDER BY p.start_year`, append(args, starts, ends)...)
	if err != nil {
		return result, err
	}
	for rows.Next() {
		var p DensityPeriod
		if err = rows.Scan(&p.Start, &p.End, &p.Count); err != nil {
			rows.Close()
			return result, err
		}
		result.Density = append(result.Density, p)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return result, err
	}
	rows, err = r.db.Query(ctx, authorSuggestionsQuery, append(args, result.Total)...)
	if err != nil {
		return result, err
	}
	defer rows.Close()
	for rows.Next() {
		var s SuggestedFilter
		if err = rows.Scan(&s.Key, &s.Value, &s.Name, &s.Count); err != nil {
			return result, err
		}
		result.SuggestedFilters = append(result.SuggestedFilters, s)
	}
	return result, rows.Err()
}
