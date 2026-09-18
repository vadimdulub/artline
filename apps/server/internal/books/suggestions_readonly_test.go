package books

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Audit the real collection in enforced read-only sessions, with no fixtures.
func TestReadOnlySuggestions(t *testing.T) {
	dsn := os.Getenv("ARTLINE_BOOKS_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue audit not requested")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	repo := NewRepository(db)
	for _, filter := range []Filter{
		{Range: Bounds},
		{Range: Bounds, Languages: []string{"Q7737"}},
		{Range: Range{1850, 1899}, Languages: []string{"Q7737"}},
		{Range: Range{1950, 1959}},
		{Range: Bounds, Countries: []string{"Q159"}},
		{Range: Bounds, Languages: []string{"Q7737", "Q1860"}, Countries: []string{"Q159", "Q15180"}},
		{Range: Bounds, Women: true},
		{Range: Bounds, Top100: true},
		{Range: Bounds, Query: "novel"},
		{Range: Bounds, Authors: []string{"Leo Tolstoy"}},
	} {
		filter.Limit, filter.Preview = 100, true
		view, err := repo.List(ctx, filter)
		if err != nil {
			t.Fatal(err)
		}
		if len(view.SuggestedFilters) > 3 || len(view.Items) > 100 {
			t.Fatal("unbounded response")
		}
		for _, suggestion := range view.SuggestedFilters {
			child := filter
			var choices *[]string
			switch suggestion.Key {
			case "language":
				choices = &child.Languages
			case "country":
				choices = &child.Countries
			case "region":
				choices = &child.Regions
			case "author":
				choices = &child.Authors
			default:
				t.Fatalf("unsupported suggestion: %+v", suggestion)
			}
			if len(*choices) > 0 {
				t.Fatalf("suggestion replaces an active filter: %+v", suggestion)
			}
			*choices = []string{suggestion.Value}
			opened, err := repo.List(ctx, child)
			if err != nil {
				t.Fatal(err)
			}
			if opened.Total != suggestion.Count || opened.Total <= 0 || opened.Total >= view.Total {
				t.Fatalf("suggestion count=%d opened=%d parent=%d: %+v", suggestion.Count, opened.Total, view.Total, suggestion)
			}
		}
		if view.Mode == "density" && len(view.SuggestedFilters) == 0 {
			t.Fatalf("no way to narrow crowded view: %+v", filter)
		}
		t.Logf("range=%+v languages=%v countries=%v: %d books, %d suggestions", filter.Range, filter.Languages, filter.Countries, view.Total, len(view.SuggestedFilters))
	}
	public, err := repo.List(ctx, Filter{Range: Bounds, Limit: 100})
	if err != nil || len(public.SuggestedFilters) > 0 {
		t.Fatalf("unpublished suggestions exposed: %v", err)
	}
	for _, languages := range [][]string{nil, {"Q7737"}} {
		var plan string
		args := []any{Bounds.Start, Bounds.End, true, "", []string{}, false, false, languages, []string{}, []string{}, 10000}
		if err := db.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+suggestionsQuery, args...).Scan(&plan); err != nil {
			t.Fatal(err)
		}
		t.Logf("suggestions plan, languages=%v: %s", languages, plan)
	}
}
