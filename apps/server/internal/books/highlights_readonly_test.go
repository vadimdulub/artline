package books

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Uses the actual catalogue with writes disabled; no fixtures or schema changes.
func TestReadOnlyHighlightsTimeline(t *testing.T) {
	dsn := os.Getenv("ARTLINE_BOOKS_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue audit not requested")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	repo := NewRepository(db)
	f := Filter{Range: Bounds, Top100: true, Preview: true}
	f.Limit = f.MaxPageSize()
	highlights, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	wantMode := "individual"
	if highlights.Total > HighlightsLimit || (highlights.Total > 0 && highlights.UndatedTotal == highlights.Total) {
		wantMode = "density"
	}
	if highlights.Total <= 100 || len(highlights.Items) != min(highlights.Total, f.Limit) || highlights.Mode != wantMode || highlights.HasMore != (highlights.Total > f.Limit) {
		t.Fatalf("highlights must respect the bounded timeline: total=%d items=%d mode=%s more=%v", highlights.Total, len(highlights.Items), highlights.Mode, highlights.HasMore)
	}
	// The editorial selection can grow. Traverse bounded keyset pages
	// at both supported sizes, verifying complete, identical order and visibility.
	var complete []Book
	for _, limit := range []int{f.MaxPageSize(), 100} {
		f.Limit, f.After = limit, ""
		var pages []Book
		seen := map[string]bool{}
		for {
			page, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			if page.Total != highlights.Total || len(page.Items) > limit || len(page.Items) == 0 {
				t.Fatalf("invalid highlight page: total=%d items=%d", page.Total, len(page.Items))
			}
			for _, book := range page.Items {
				if seen[book.ID] {
					t.Fatalf("duplicate highlighted book: %s", book.ID)
				}
				seen[book.ID] = true
			}
			pages = append(pages, page.Items...)
			if !page.HasMore {
				break
			}
			if page.NextCursor == "" || page.NextCursor == f.After || len(page.Items) != limit {
				t.Fatal("highlight pagination did not advance")
			}
			f.After = page.NextCursor
		}
		if len(pages) != highlights.Total {
			t.Fatal("highlight pagination lost records")
		}
		if complete == nil {
			complete = pages
		} else {
			for i, book := range complete {
				if pages[i].ID != book.ID || pages[i].Status != book.Status {
					t.Fatal("highlight pagination changed order or visibility")
				}
			}
		}
	}
	f.After, f.View, f.Limit = "", "authors", f.MaxPageSize()
	authors, err := repo.List(ctx, f)
	wantMode = "individual"
	if authors.Total > HighlightsLimit || (authors.Total > 0 && authors.UndatedTotal == authors.Total) {
		wantMode = "density"
	}
	if err != nil || authors.Mode != wantMode || len(authors.Authors) != min(authors.Total, f.Limit) || authors.HasMore != (authors.Total > f.Limit) {
		t.Fatalf("highlight author page incomplete: total=%d items=%d err=%v", authors.Total, len(authors.Authors), err)
	}
	f.View, f.Top100, f.Limit = "", false, 100
	catalogue, err := repo.List(ctx, f)
	if err != nil || catalogue.Mode != "density" || len(catalogue.Density) != 0 || len(catalogue.Items) != 100 || !catalogue.HasMore {
		t.Fatalf("full catalogue lost its bounded overview: items=%d mode=%s err=%v", len(catalogue.Items), catalogue.Mode, err)
	}
	t.Logf("Bounded highlights: %d books, %d authors; full catalogue: %d books in pages of 100", highlights.Total, authors.Total, catalogue.Total)
}
