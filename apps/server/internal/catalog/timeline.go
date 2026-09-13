package catalog

import (
	"context"
	"fmt"
)

// One predicate serves counts, nodes, periods and filter suggestions.
const timelinePredicate = `
 FROM artists a
 LEFT JOIN artist_movements am ON am.artist_id=a.id AND am.role='primary'
 LEFT JOIN movements m ON m.id=am.movement_id AND m.status<>'archived' AND ($3<>'published' OR m.status='published')
 WHERE a.status<>'archived'
 AND a.timeline_start_year <= $2 AND a.timeline_end_year >= $1
 AND ($3='' OR a.status=$3)
 AND ($4='' OR a.display_name ILIKE '%'||$4||'%' OR a.sort_name ILIKE '%'||$4||'%'
   OR EXISTS (SELECT 1 FROM artist_aliases x WHERE x.artist_id=a.id AND x.alias ILIKE '%'||$4||'%')
   OR EXISTS (SELECT 1 FROM artist_movements x JOIN movements y ON y.id=x.movement_id WHERE x.artist_id=a.id AND y.status<>'archived' AND ($3<>'published' OR y.status='published') AND y.name ILIKE '%'||$4||'%')
   OR EXISTS (SELECT 1 FROM artist_countries x JOIN countries y ON y.code=x.country_code WHERE x.artist_id=a.id AND y.name ILIKE '%'||$4||'%')
   OR EXISTS (SELECT 1 FROM artist_places x JOIN places y ON y.id=x.place_id WHERE x.artist_id=a.id AND y.name ILIKE '%'||$4||'%')
   OR EXISTS (SELECT 1 FROM artwork_artists x JOIN artworks y ON y.id=x.artwork_id WHERE x.artist_id=a.id AND y.status<>'archived' AND ($3<>'published' OR y.status='published') AND y.title ILIKE '%'||$4||'%'))
 AND (cardinality($5::text[])=0 OR EXISTS (SELECT 1 FROM artist_countries x WHERE x.artist_id=a.id AND x.country_code::text=ANY($5)))
 AND (cardinality($6::text[])=0 OR EXISTS (SELECT 1 FROM artist_movements x JOIN movements y ON y.id=x.movement_id WHERE x.artist_id=a.id AND y.status<>'archived' AND ($3<>'published' OR y.status='published') AND y.slug=ANY($6)))
 AND (coalesce(cardinality($7::text[]),0)=0 OR EXISTS (SELECT 1 FROM artist_countries x JOIN countries y ON y.code=x.country_code WHERE x.artist_id=a.id AND y.region_code=ANY($7::text[])))
 AND (cardinality($8::text[])=0 OR EXISTS (SELECT 1 FROM artwork_artists x JOIN artworks y ON y.id=x.artwork_id WHERE x.artist_id=a.id AND y.work_type=ANY($8) AND y.status<>'archived' AND ($3<>'published' OR y.status='published')))
 AND (NOT $9 OR EXISTS (SELECT 1 FROM artist_discovery_selection ds WHERE ds.artist_id=a.id AND ds.is_popular))
 AND (cardinality($10::text[])=0 OR a.slug=ANY($10))
`

// Every period counts the same overlapping life/activity intervals as selecting
// its dates. Neighbouring periods may contain the same painter. Merge a trailing
// single year into its preceding period to match the UI's two-year minimum.
const timelineDensityQuery = `WITH matching AS MATERIALIZED (
 SELECT a.timeline_start_year,a.timeline_end_year,
 coalesce(m.name,'Unclassified') AS movement,coalesce(m.color_hex,'#8b8880') AS color
 ` + timelinePredicate + `
), periods AS (
 SELECT year AS start_year,CASE WHEN year+$11 >= $2 THEN $2 ELSE year+$11-1 END AS end_year
 FROM generate_series($1::int,$2::int-1,$11::int) AS year
)
SELECT p.start_year,p.end_year,a.movement,a.color,count(*)
FROM periods p JOIN matching a ON a.timeline_start_year <= p.end_year AND a.timeline_end_year >= p.start_year
GROUP BY p.start_year,p.end_year,a.movement,a.color ORDER BY p.start_year,a.movement`

// Only suggest an unused filter dimension: replacing an existing OR selection
// could broaden the result, invalidating counts calculated from this scope.
const timelineSuggestionsQuery = `WITH matching AS MATERIALIZED (
 SELECT a.id ` + timelinePredicate + `
), suggestions AS (
 SELECT 'country' AS key,trim(c.code::text) AS value,c.name,count(DISTINCT a.id)::int AS count
 FROM matching a JOIN artist_countries ac ON ac.artist_id=a.id JOIN countries c ON c.code=ac.country_code
 WHERE cardinality($5::text[])=0
 GROUP BY c.code,c.name HAVING count(DISTINCT a.id) < $11
 UNION ALL
 SELECT 'movement',m.slug,m.name,count(DISTINCT a.id)::int
 FROM matching a JOIN artist_movements am ON am.artist_id=a.id JOIN movements m ON m.id=am.movement_id
 WHERE cardinality($6::text[])=0 AND m.status<>'archived' AND ($3<>'published' OR m.status='published')
 GROUP BY m.slug,m.name HAVING count(DISTINCT a.id) < $11
)
SELECT key,value,name,count FROM suggestions
ORDER BY (count <= 300) DESC,CASE WHEN count <= 300 THEN -count ELSE count END,key,value LIMIT 3`

func (r *Repository) Timeline(ctx context.Context, filter TimelineFilter) (TimelineResponse, error) {
	result := TimelineResponse{Mode: "individual", Items: []TimelineArtist{}, Bins: []TimelineBin{}, Periods: []TimelinePeriod{}, PopularOnly: filter.PopularOnly, SuggestedFilters: []TimelineSuggestedFilter{}}
	result.Range.Start, result.Range.End = filter.StartYear, filter.EndYear
	args := []any{filter.StartYear, filter.EndYear, filter.Status, filter.Query, filterChoices(filter.Countries, filter.Country), filterChoices(filter.Movements, filter.Movement), filter.Regions, filterChoices(filter.WorkTypes, filter.WorkType), filter.PopularOnly, filterChoices(filter.Painters, "")}
	if err := r.db.QueryRow(ctx, "SELECT count(*)"+timelinePredicate, args...).Scan(&result.Total); err != nil {
		return result, fmt.Errorf("count timeline: %w", err)
	}
	if result.Total > 300 {
		result.Mode = "density"
		width := 10
		if filter.EndYear-filter.StartYear > 200 {
			width = 25
		}
		if filter.EndYear-filter.StartYear > 500 {
			width = 50
		}
		rows, err := r.db.Query(ctx, timelineDensityQuery, append(args, width)...)
		if err != nil {
			return result, fmt.Errorf("timeline density: %w", err)
		}
		defer rows.Close()
		for rows.Next() {
			var bin TimelineBin
			if err := rows.Scan(&bin.StartYear, &bin.EndYear, &bin.Movement, &bin.Color, &bin.Count); err != nil {
				return result, err
			}
			result.Bins = append(result.Bins, bin)
			last := len(result.Periods) - 1
			if last < 0 || result.Periods[last].StartYear != bin.StartYear {
				result.Periods = append(result.Periods, TimelinePeriod{StartYear: bin.StartYear, EndYear: bin.EndYear, Count: bin.Count})
			} else {
				result.Periods[last].Count += bin.Count
			}
		}
		if err := rows.Err(); err != nil {
			return result, err
		}
		rows.Close()
		suggestions, err := r.db.Query(ctx, timelineSuggestionsQuery, append(args, result.Total)...)
		if err != nil {
			return result, fmt.Errorf("timeline suggestions: %w", err)
		}
		defer suggestions.Close()
		for suggestions.Next() {
			var suggestion TimelineSuggestedFilter
			if err := suggestions.Scan(&suggestion.Key, &suggestion.Value, &suggestion.Name, &suggestion.Count); err != nil {
				return result, err
			}
			result.SuggestedFilters = append(result.SuggestedFilters, suggestion)
		}
		return result, suggestions.Err()
	}
	query := `SELECT a.id::text,a.slug,a.display_name,a.timeline_start_year,a.timeline_end_year,a.timeline_display,a.status,
 coalesce(m.slug,'unclassified'),coalesce(m.name,'Unclassified'),coalesce(m.color_hex,'#8b8880'),
 ARRAY(SELECT DISTINCT trim(x.country_code::text) FROM artist_countries x WHERE x.artist_id=a.id ORDER BY 1),
 (SELECT count(DISTINCT x.artwork_id) FROM artwork_artists x JOIN artworks y ON y.id=x.artwork_id WHERE x.artist_id=a.id AND y.status<>'archived' AND ($3<>'published' OR y.status='published'))
 ` + timelinePredicate + ` ORDER BY a.timeline_start_year,a.sort_name,a.id LIMIT 300`
	rows, err := r.db.Query(ctx, query, args...)
	if err != nil {
		return result, fmt.Errorf("timeline nodes: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var item TimelineArtist
		if err := rows.Scan(&item.ID, &item.Slug, &item.Name, &item.StartYear, &item.EndYear, &item.DateDisplay, &item.Status, &item.Movement.Slug, &item.Movement.Name, &item.Movement.Color, &item.Countries, &item.ArtworkCount); err != nil {
			return result, err
		}
		result.Items = append(result.Items, item)
	}
	return result, rows.Err()
}
