package books

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/vadimdulub/artline/apps/server/internal/timeline"
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
 WHERE (NOT $5 OR c.id=ANY(b.woman_author_ids))
 AND (coalesce(cardinality($4::text[]),0)=0 OR c.name=ANY($4))
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
	args := []any{f.Start, f.End, strings.TrimSpace(f.Query), f.Authors, f.Women, f.Top100, f.Languages, f.Countries, f.Regions}
	var firstYear, lastYear *int
	if err := r.db.QueryRow(ctx, authorTimelineScope+`SELECT count(*),count(*) FILTER (WHERE start_year IS NULL),(SELECT count(*) FROM classified),min(start_year),max(end_year) FROM matching`, args...).Scan(&result.Total, &result.UndatedTotal, &result.SelectionTotal, &firstYear, &lastYear); err != nil {
		return result, fmt.Errorf("count authors: %w", err)
	}
	result.MatchedRange = timeline.FitExtent(firstYear, lastYear, f.Start, f.End)
	individualLimit := timeline.IndividualLimit
	if f.Top100 {
		individualLimit = HighlightsLimit
	}
	if result.Total > individualLimit || (result.Total > 0 && result.UndatedTotal == result.Total) {
		result.Mode = "density"
	}
	c, _ := decodeCursor(f.After)
	rows, err := r.db.Query(ctx, authorTimelineScope+`SELECT c.record,a.start_year,a.end_year,coalesce(a.approximate,true),a.book_count,a.credits
 FROM (SELECT * FROM matching WHERE (coalesce(start_year,2147483647),id)>($10,$11) ORDER BY coalesce(start_year,2147483647),id LIMIT $12) a
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
		attachPortrait(&a.Creator)
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
	return result, nil
}
