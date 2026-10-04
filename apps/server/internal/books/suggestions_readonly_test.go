package books

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Audit the real collection in enforced read-only sessions, with no fixtures.
func TestReadOnlyTimelinePages(t *testing.T) {
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
		if view.Mode != "individual" || len(view.Density) != 0 || len(view.SuggestedFilters) != 0 || len(view.Items) > filter.Limit {
			t.Fatal("Books must return a bounded page of marks without an aggregate chart")
		}
		if view.Total > filter.Limit && (!view.HasMore || view.NextCursor == "") {
			t.Fatal("crowded timeline is missing its next page")
		}
		if view.HasMore {
			filter.After = view.NextCursor
			next, err := repo.List(ctx, filter)
			if err != nil {
				t.Fatal(err)
			}
			ids := map[string]bool{}
			for _, b := range view.Items {
				ids[b.ID] = true
			}
			for _, b := range next.Items {
				if ids[b.ID] {
					t.Fatal("overlapping pages")
				}
			}
			if next.Mode != "individual" || len(next.Items) > filter.Limit || next.Total != view.Total {
				t.Fatal("next page changed scope")
			}
		}
		t.Logf("range=%+v languages=%v countries=%v: %d books, %d on page", filter.Range, filter.Languages, filter.Countries, view.Total, len(view.Items))
	}

	public, err := repo.List(ctx, Filter{Range: Bounds, Limit: 100})
	if err != nil || len(public.SuggestedFilters) > 0 {
		t.Fatalf("unpublished suggestions exposed: %v", err)
	}
}
