package catalog

import (
	"context"
	"fmt"
	"strconv"

	"github.com/jackc/pgx/v5"
	"github.com/vadimdulub/artline/apps/server/internal/timeline"
)

// One predicate serves counts, nodes, periods and filter suggestions.
const timelinePredicate = `
 FROM artists a
 LEFT JOIN artist_movements am ON am.artist_id=a.id AND am.role='primary'
 LEFT JOIN movements m ON m.id=am.movement_id AND m.status<>'archived'
 WHERE a.status<>'archived'
 AND a.timeline_start_year <= $2 AND a.timeline_end_year >= $1
 AND ($3='' OR a.display_name ILIKE '%'||$3||'%' OR a.sort_name ILIKE '%'||$3||'%'
   OR EXISTS (SELECT 1 FROM artist_aliases x WHERE x.artist_id=a.id AND x.alias ILIKE '%'||$3||'%')
   OR EXISTS (SELECT 1 FROM artist_movements x JOIN movements y ON y.id=x.movement_id WHERE x.artist_id=a.id AND y.status<>'archived' AND y.name ILIKE '%'||$3||'%')
   OR EXISTS (SELECT 1 FROM artist_countries x JOIN countries y ON y.code=x.country_code WHERE x.artist_id=a.id AND y.name ILIKE '%'||$3||'%')
   OR EXISTS (SELECT 1 FROM artist_places x JOIN places y ON y.id=x.place_id WHERE x.artist_id=a.id AND y.name ILIKE '%'||$3||'%')
   OR EXISTS (SELECT 1 FROM artwork_artists x JOIN artworks y ON y.id=x.artwork_id WHERE x.artist_id=a.id AND y.status<>'archived' AND y.title ILIKE '%'||$3||'%'))
 AND (cardinality($4::text[])=0 OR EXISTS (SELECT 1 FROM artist_countries x WHERE x.artist_id=a.id AND x.country_code::text=ANY($4)))
 AND (cardinality($5::text[])=0 OR EXISTS (SELECT 1 FROM artist_movements x JOIN movements y ON y.id=x.movement_id WHERE x.artist_id=a.id AND y.status<>'archived' AND y.slug=ANY($5)))
 AND (coalesce(cardinality($6::text[]),0)=0 OR EXISTS (SELECT 1 FROM artist_countries x JOIN countries y ON y.code=x.country_code WHERE x.artist_id=a.id AND y.region_code=ANY($6::text[])))
 AND (cardinality($7::text[])=0 OR EXISTS (SELECT 1 FROM artwork_artists x JOIN artworks y ON y.id=x.artwork_id WHERE x.artist_id=a.id AND y.work_type=ANY($7) AND y.status<>'archived'))
 AND (NOT $8 OR EXISTS (SELECT 1 FROM artist_discovery_selection ds WHERE ds.artist_id=a.id AND ds.is_popular))
 AND (cardinality($9::text[])=0 OR a.slug=ANY($9))
 AND (NOT $10 OR EXISTS (SELECT 1 FROM artist_gender_evidence ge WHERE ge.artist_id=a.id AND ge.is_woman))
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
var timelineSuggestionsQuery = `WITH matching AS MATERIALIZED (
 SELECT a.id ` + timelinePredicate + `
), suggestions AS (
 SELECT 'country' AS key,trim(c.code::text) AS value,c.name,count(DISTINCT a.id)::int AS count
 FROM matching a JOIN artist_countries ac ON ac.artist_id=a.id JOIN countries c ON c.code=ac.country_code
 WHERE cardinality($4::text[])=0
 GROUP BY c.code,c.name HAVING count(DISTINCT a.id) < $11
 UNION ALL
 SELECT 'movement',m.slug,m.name,count(DISTINCT a.id)::int
 FROM matching a JOIN artist_movements am ON am.artist_id=a.id JOIN movements m ON m.id=am.movement_id
 WHERE cardinality($5::text[])=0 AND m.status<>'archived'
 GROUP BY m.slug,m.name HAVING count(DISTINCT a.id) < $11
)
SELECT key,value,name,count FROM suggestions
ORDER BY (count <= ` + strconv.Itoa(timeline.IndividualLimit) + `) DESC,CASE WHEN count <= ` + strconv.Itoa(timeline.IndividualLimit) + ` THEN -count ELSE count END,key,value LIMIT 3`

// Count scoped artwork IDs and exclude archives through the status index,
// without fetching every linked artwork heap row.
const timelineArtworkCountsQuery = `SELECT aa.artist_id::text,count(DISTINCT aa.artwork_id)
 FROM artwork_artists aa WHERE aa.artist_id=ANY($1::uuid[])
 AND NOT EXISTS(SELECT 1 FROM artworks aw WHERE aw.id=aa.artwork_id AND aw.status='archived')
 GROUP BY aa.artist_id`

func (r *Repository) Timeline(ctx context.Context, filter TimelineFilter) (TimelineResponse, error) {
	result := TimelineResponse{Mode: "individual", Items: []TimelineArtist{}, Bins: []TimelineBin{}, Periods: []TimelinePeriod{}, PopularOnly: filter.PopularOnly, WomenOnly: filter.WomenOnly, SuggestedFilters: []TimelineSuggestedFilter{}}
	result.Range.Start, result.Range.End = filter.StartYear, filter.EndYear
	// Filter selectivity varies widely. Bind values without retaining a named
	// statement that can switch to an unsuitable generic plan after repeated use.
	args := []any{pgx.QueryExecModeCacheDescribe, filter.StartYear, filter.EndYear, filter.Query, filterChoices(filter.Countries, filter.Country), filterChoices(filter.Movements, filter.Movement), filter.Regions, filterChoices(filter.WorkTypes, filter.WorkType), filter.PopularOnly, filterChoices(filter.Painters, ""), filter.WomenOnly}
	var firstYear, lastYear *int
	if err := r.db.QueryRow(ctx, "SELECT count(*),min(a.timeline_start_year),max(a.timeline_end_year)"+timelinePredicate, args...).Scan(&result.Total, &firstYear, &lastYear); err != nil {
		return result, fmt.Errorf("count timeline: %w", err)
	}
	result.MatchedRange = timeline.FitExtent(firstYear, lastYear, filter.StartYear, filter.EndYear)
	if result.Total > timeline.IndividualLimit {
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
 ARRAY(SELECT DISTINCT trim(x.country_code::text) FROM artist_countries x WHERE x.artist_id=a.id ORDER BY 1)
 ` + timelinePredicate + ` ORDER BY a.timeline_start_year,a.sort_name,a.id LIMIT ` + strconv.Itoa(timeline.IndividualLimit)
	rows, err := r.db.Query(ctx, query, args...)
	if err != nil {
		return result, fmt.Errorf("timeline nodes: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var item TimelineArtist
		if err := rows.Scan(&item.ID, &item.Slug, &item.Name, &item.StartYear, &item.EndYear, &item.DateDisplay, &item.Status, &item.Movement.Slug, &item.Movement.Name, &item.Movement.Color, &item.Countries); err != nil {
			return result, err
		}
		result.Items = append(result.Items, item)
	}
	if err := rows.Err(); err != nil {
		return result, err
	}
	rows.Close()
	if len(result.Items) == 0 {
		return result, nil
	}
	ids := make([]string, 0, len(result.Items))
	positions := make(map[string]int, len(result.Items))
	for index, item := range result.Items {
		ids = append(ids, item.ID)
		positions[item.ID] = index
	}
	counts, err := r.db.Query(ctx, timelineArtworkCountsQuery, pgx.QueryExecModeCacheDescribe, ids)
	if err != nil {
		return result, fmt.Errorf("timeline artwork counts: %w", err)
	}
	defer counts.Close()
	for counts.Next() {
		var id string
		var count int
		if err := counts.Scan(&id, &count); err != nil {
			return result, err
		}
		if index, ok := positions[id]; ok {
			result.Items[index].ArtworkCount = count
		}
	}
	return result, counts.Err()
}
