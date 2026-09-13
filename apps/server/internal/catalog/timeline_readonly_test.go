package catalog

import (
	"context"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Reuse one database session beyond PostgreSQL's initial custom-plan executions.
// The request deadline also catches the large heap reads that made the live
// popular timeline fail despite fast count-only and first-page smoke checks.
func TestTimelineReadOnlyRepeatedRequests(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("ARTLINE_READONLY_DATABASE_URL is not set")
	}
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly, IsoLevel: pgx.RepeatableRead})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	repo := &Repository{db: tx}
	var baseline TimelineResponse
	for attempt := 0; attempt < 8; attempt++ {
		requestCtx, cancel := context.WithTimeout(ctx, 8*time.Second)
		start := time.Now()
		view, err := repo.Timeline(requestCtx, TimelineFilter{StartYear: 1100, EndYear: 2000, PopularOnly: true})
		cancel()
		if err != nil {
			t.Fatal(err)
		}
		if attempt == 0 {
			baseline = view
		}
		if len(view.Items) > 300 || view.Total != baseline.Total || len(view.Items) != len(baseline.Items) {
			t.Fatal("repeated timeline changed its bounded results")
		}
		for index, item := range view.Items {
			if item.ID != baseline.Items[index].ID || item.ArtworkCount != baseline.Items[index].ArtworkCount {
				t.Fatal("repeated timeline changed painter order or artwork counts")
			}
		}
		t.Logf("request %d: %d painters in %s", attempt+1, view.Total, time.Since(start))
	}
}

// Explicitly opt-in to existing catalogue reads. This does not use testdb,
// create databases, insert fixtures, or run migrations.
func TestTimelineReadOnlyCountsAndSuggestions(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("ARTLINE_READONLY_DATABASE_URL is not set")
	}
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly, IsoLevel: pgx.RepeatableRead})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	repo := &Repository{db: tx}
	for _, filter := range []TimelineFilter{
		{StartYear: 1100, EndYear: 2000},
		{StartYear: 1900, EndYear: 1949},
		{StartYear: 1900, EndYear: 1909},
		{StartYear: 1999, EndYear: 2000},
		{StartYear: 1100, EndYear: 2000, Countries: []string{"FR", "IT"}},
		{StartYear: 1100, EndYear: 2000, PopularOnly: true},
	} {
		view, err := repo.Timeline(ctx, filter)
		if err != nil {
			t.Fatal(err)
		}
		if len(view.Items) > 300 || len(view.Periods) > 90 || len(view.SuggestedFilters) > 3 {
			t.Fatal("unbounded timeline response")
		}
		if len(view.Items) > 0 {
			ids := make([]string, 0, len(view.Items))
			for _, item := range view.Items {
				ids = append(ids, item.ID)
			}
			// Compare the optimized exclusion lookup with the original positive
			// artwork join, including duplicate attribution roles and zero works.
			rows, err := tx.Query(ctx, `SELECT aa.artist_id::text,count(DISTINCT aa.artwork_id)
 FROM artwork_artists aa JOIN artworks aw ON aw.id=aa.artwork_id
 WHERE aa.artist_id=ANY($1::uuid[]) AND aw.status<>'archived'
 AND ($2<>'published' OR aw.status='published') GROUP BY aa.artist_id`, ids, filter.Status)
			if err != nil {
				t.Fatal(err)
			}
			expected := map[string]int{}
			for rows.Next() {
				var id string
				var count int
				if err := rows.Scan(&id, &count); err != nil {
					t.Fatal(err)
				}
				expected[id] = count
			}
			if err := rows.Err(); err != nil {
				t.Fatal(err)
			}
			rows.Close()
			for _, item := range view.Items {
				if item.ArtworkCount != expected[item.ID] {
					t.Fatalf("%s: artwork count=%d expected=%d", item.Slug, item.ArtworkCount, expected[item.ID])
				}
			}
		}
		for _, period := range view.Periods {
			if period.StartYear >= period.EndYear {
				t.Fatalf("period cannot be selected exactly: %+v", period)
			}
			child := filter
			child.StartYear, child.EndYear = period.StartYear, period.EndYear
			opened, err := repo.Timeline(ctx, child)
			if err != nil {
				t.Fatal(err)
			}
			if opened.Total != period.Count {
				t.Fatalf("%d–%d: column=%d opened=%d", period.StartYear, period.EndYear, period.Count, opened.Total)
			}
		}
		for _, suggestion := range view.SuggestedFilters {
			child := filter
			switch suggestion.Key {
			case "country":
				if len(filter.Countries) > 0 {
					t.Fatal("suggestion would replace existing country filters")
				}
				child.Countries = []string{suggestion.Value}
			case "movement":
				child.Movements = []string{suggestion.Value}
			default:
				t.Fatalf("unsupported suggestion: %s", suggestion.Key)
			}
			opened, err := repo.Timeline(ctx, child)
			if err != nil {
				t.Fatal(err)
			}
			if opened.Total != suggestion.Count || opened.Total <= 0 || opened.Total >= view.Total {
				t.Fatalf("incorrect suggestion %+v, opened=%d current=%d", suggestion, opened.Total, view.Total)
			}
		}
		t.Logf("verified %d–%d: %d painters, %d periods, %d suggestions", filter.StartYear, filter.EndYear, view.Total, len(view.Periods), len(view.SuggestedFilters))
	}
	args := []any{1100, 2000, "", "", []string{}, []string{}, []string{}, []string{}, false, []string{}, 50}
	for name, query := range map[string]string{"density": timelineDensityQuery, "suggestions": timelineSuggestionsQuery} {
		planArgs := append([]any(nil), args...)
		if name == "suggestions" {
			planArgs[10] = 20000
		}
		var plan string
		if err := tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+query, planArgs...).Scan(&plan); err != nil {
			t.Fatal(err)
		}
		t.Logf("%s local plan: %s", name, plan)
	}
	// An in-query 20,000-painter fixture tests the overlap aggregation at planning
	// scale without inserting rows into the catalogue or creating a test database.
	_, periodSQL, _ := strings.Cut(timelineDensityQuery, "), periods AS (")
	synthetic := `WITH matching AS MATERIALIZED (
	 SELECT 1050+(n*37)%900 AS timeline_start_year,1100+(n*37)%900 AS timeline_end_year,
	 'Fixture movement'::text AS movement,'#888888'::text AS color FROM generate_series(1,20000) n
	), periods AS (` + strings.ReplaceAll(periodSQL, "$11", "$3")
	var plan string
	if err := tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+synthetic, 1100, 2000, 50).Scan(&plan); err != nil {
		t.Fatal(err)
	}
	t.Logf("20,000-painter synthetic plan: %s", plan)
}
