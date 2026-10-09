package books

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/timeline"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"
)

const authorTimelineLegacyScope = `WITH eligible_books AS MATERIALIZED (
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

func TestAuthorTimelinePerformanceReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_BOOKS_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("opt-in read-only performance comparison")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.MaxConns = 1
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	args := []any{Bounds.Start, Bounds.End, "", []string{}, false, false, []string{}, []string{}, []string{}}
	query := authorTimelineLegacyScope + `SELECT count(*),count(*) FILTER (WHERE start_year IS NULL),(SELECT count(*) FROM classified),min(start_year),max(end_year) FROM matching`
	dir := os.Getenv("ARTLINE_PERFORMANCE_DIR")
	if dir == "" {
		t.Fatal("provide a private plan output directory")
	}
	if err = os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(dir, "books-count-before.sql"), []byte(query), 0600); err != nil {
		t.Fatal(err)
	}
	var plan []byte
	if err = db.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+query, args...).Scan(&plan); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(dir, "books-count-before.json"), plan, 0600); err != nil {
		t.Fatal(err)
	}
	var p []map[string]any
	if err = json.Unmarshal(plan, &p); err != nil {
		t.Fatal(err)
	}
	t.Logf("book author count: %v ms; JIT: %v", p[0]["Execution Time"], p[0]["JIT"])
	repo := NewRepository(db)
	for i, f := range []Filter{
		{Range: Bounds, Limit: 30},
		{Range: Bounds, Limit: 30, Top100: true},
		{Range: Bounds, Limit: 30, Women: true},
		{Range: Range{1900, 1909}, Limit: 30, Languages: []string{"Q7737"}},
		{Range: Bounds, Limit: 30, Authors: []string{"Homer"}},
		{Range: Bounds, Limit: 30, Query: "no-match-perf-20261009"},
		{Range: Bounds, Limit: 30, After: encodeCursor(Book{ID: "!"})},
	} {
		beforeStart := time.Now()
		before, err := repo.authorTimelineLegacy(ctx, f)
		beforeDuration := time.Since(beforeStart)
		if err != nil {
			t.Fatal(err)
		}
		afterStart := time.Now()
		after, err := repo.authorTimeline(ctx, f)
		afterDuration := time.Since(afterStart)
		if err != nil {
			t.Fatal(err)
		}
		if !reflect.DeepEqual(before, after) {
			t.Fatalf("case %d response differs\nbefore=%+v\nafter=%+v", i, before, after)
		}
		t.Logf("case %d identical: total=%d; before=%s after=%s", i, after.Total, beforeDuration, afterDuration)
		if after.HasMore {
			f.After = after.NextCursor
			before, err = repo.authorTimelineLegacy(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			after, err = repo.authorTimeline(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			if !reflect.DeepEqual(before, after) {
				t.Fatalf("case %d cursor response differs", i)
			}
		}
	}
	c, _ := decodeCursor("")
	if err = db.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+authorTimelineQuery, append(args, c.Year, c.ID, 31)...).Scan(&plan); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(dir, "books-combined-after.json"), plan, 0600); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(dir, "books-combined-after.sql"), []byte(authorTimelineQuery), 0600); err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(plan, &p); err != nil {
		t.Fatal(err)
	}
	t.Logf("combined count and page: %v ms; JIT: %v", p[0]["Execution Time"], p[0]["JIT"])

}

func (r *Repository) authorTimelineLegacy(ctx context.Context, f Filter) (Response, error) {
	result := metadata(f.Range)
	result.View, result.Authors = "authors", []TimelineAuthor{}
	args := []any{f.Start, f.End, strings.TrimSpace(f.Query), f.Authors, f.Women, f.Top100, f.Languages, f.Countries, f.Regions}
	var firstYear, lastYear *int
	if err := r.db.QueryRow(ctx, authorTimelineLegacyScope+`SELECT count(*),count(*) FILTER (WHERE start_year IS NULL),(SELECT count(*) FROM classified),min(start_year),max(end_year) FROM matching`, args...).Scan(&result.Total, &result.UndatedTotal, &result.SelectionTotal, &firstYear, &lastYear); err != nil {
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
	rows, err := r.db.Query(ctx, authorTimelineLegacyScope+`SELECT c.record,a.start_year,a.end_year,coalesce(a.approximate,true),a.book_count,a.credits
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
