package books

import (
	"context"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Explicit opt-in. Every connection is forced read-only; no fixtures,
// migrations, test databases or writes are used against the real catalogue.
func TestReadOnlyBookCatalogue(t *testing.T) {
	dsn := os.Getenv("ARTLINE_BOOKS_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue audit not requested")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	repo := NewRepository(db)
	var expectedTotal, expectedWomen int
	if err = db.QueryRow(ctx, `SELECT count(*),count(*) FILTER(WHERE cardinality(d.woman_author_ids)>0) FROM book_records b LEFT JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum WHERE b.status<>'archived' AND (b.end_year<=2000 OR b.start_year IS NULL)`).Scan(&expectedTotal, &expectedWomen); err != nil {
		t.Fatal(err)
	}
	var laterBook string
	if err = db.QueryRow(ctx, `SELECT id FROM book_records WHERE status<>'archived' AND end_year>2000 ORDER BY id LIMIT 1`).Scan(&laterBook); err != nil {
		t.Fatal(err)
	}
	if _, err = repo.ByID(ctx, laterBook, true); err != ErrNotFound {
		t.Fatalf("post-cutoff detail exposed: %s %v", laterBook, err)
	}
	f := Filter{Range: Bounds, Limit: 100, Preview: true}
	first, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	if first.Total != expectedTotal || first.SelectionTotal != expectedTotal || len(first.Items) != 100 || !first.HasMore || first.Mode != "density" {
		t.Fatalf("unexpected catalogue totals: total=%d selected=%d page=%d mode=%s", first.Total, first.SelectionTotal, len(first.Items), first.Mode)
	}
	seen := map[string]bool{}
	previous := cursor{Year: -5001}
	pages := 0
	for {
		page, err := repo.List(ctx, f)
		if err != nil {
			t.Fatal(err)
		}
		pages++
		for _, b := range page.Items {
			c, err := decodeCursor(encodeCursor(b))
			if err != nil {
				t.Fatal(err)
			}
			if seen[b.ID] || c.Year < previous.Year || (c.Year == previous.Year && c.ID <= previous.ID) {
				t.Fatalf("duplicate or unordered keyset record %s", b.ID)
			}
			if b.EndYear != nil && *b.EndYear > 2000 {
				t.Fatalf("post-cutoff book exposed: %s", b.ID)
			}
			if b.Status != "review" || b.SourceURL == "" {
				t.Fatalf("lost review/source state: %s", b.ID)
			}
			seen[b.ID] = true
			previous = c
		}
		if !page.HasMore {
			break
		}
		f.After = page.NextCursor
	}
	if len(seen) != expectedTotal || pages != (expectedTotal+99)/100 {
		t.Fatalf("incomplete pages: %d records across %d pages", len(seen), pages)
	}
	for _, period := range first.Density {
		if period.Count == 0 {
			continue
		}
		page, err := repo.List(ctx, Filter{Range: Range{period.Start, period.End}, Limit: 1, Preview: true})
		if err != nil {
			t.Fatal(err)
		}
		if page.Total != period.Count {
			t.Fatalf("period count differs from drilled view: %+v => %d", period, page.Total)
		}
	}
	public, err := repo.List(ctx, Filter{Range: Bounds, Limit: 100})
	if err != nil {
		t.Fatal(err)
	}
	if public.Total != 0 {
		t.Fatal("research books were published")
	}
	ancient, err := repo.List(ctx, Filter{Range: Range{Bounds.Start, -1}, Limit: 100, Preview: true})
	if err != nil {
		t.Fatal(err)
	}
	for _, period := range ancient.Density {
		if period.Count == 0 {
			t.Fatal("empty BCE periods obscure the mobile overview")
		}
	}
	if _, err := repo.ByID(ctx, "odyssey", false); err != ErrNotFound {
		t.Fatal("unpublished detail exposed")
	}
	b, err := repo.ByID(ctx, "being-nothingness", true)
	if err != nil {
		t.Fatal(err)
	}
	if len(b.Creators) != 1 || b.Creators[0].Birth == nil || b.Creators[0].Death == nil || !strings.Contains(*b.Creators[0].Birth, "1905") || !strings.Contains(*b.Creators[0].Death, "1980") {
		t.Fatalf("Sartre creator dates missing: %+v", b.Creators)
	}
	options, err := repo.Authors(ctx, "", true, false, false)
	if err != nil {
		t.Fatal(err)
	}
	if len(options.Items) > 30 || !options.HasMore {
		t.Fatal("unbounded author choices")
	}
	options, err = repo.Authors(ctx, "Sartre", true, false, false)
	if err != nil || len(options.Items) == 0 {
		t.Fatalf("author search: %+v, %v", options, err)
	}
	t.Run("discovery intersections and scoped choices", func(t *testing.T) {
		for _, tc := range []struct {
			name   string
			filter Filter
			total  int
		}{
			{"women", Filter{Women: true}, expectedWomen},
			{"top100", Filter{Top100: true}, 100},
			{"women in top100", Filter{Women: true, Top100: true}, 19},
			{"multiple languages are alternatives", Filter{Women: true, Top100: true, Languages: []string{"Q1860", "Q150"}}, 10},
			{"different facets intersect", Filter{Women: true, Top100: true, Languages: []string{"Q150"}, Countries: []string{"Q142"}, Regions: []string{"western-europe"}}, 1},
			{"incompatible region within Top 100", Filter{Top100: true, Countries: []string{"Q142"}, Regions: []string{"eastern-asia"}}, 0},
			{"unknown choice", Filter{Languages: []string{"missing-language"}}, 0},
		} {
			t.Run(tc.name, func(t *testing.T) {
				filter := tc.filter
				filter.Range = Bounds
				filter.Limit = 100
				filter.Preview = true
				page, err := repo.List(ctx, filter)
				if err != nil {
					t.Fatal(err)
				}
				if page.Total != tc.total || page.SelectionTotal != expectedTotal {
					t.Fatalf("got %d/%d, want %d/%d", page.Total, page.SelectionTotal, tc.total, expectedTotal)
				}
				if tc.total == 1 && page.Items[0].Title != "The Second Sex" {
					t.Fatalf("unexpected intersection: %+v", page.Items)
				}
				for _, period := range page.Density {
					filter.Range = Range{period.Start, period.End}
					filter.Limit = 1
					drilled, err := repo.List(ctx, filter)
					if err != nil || drilled.Total != period.Count {
						t.Fatalf("filtered density count mismatch: %+v => %d, %v", period, drilled.Total, err)
					}
				}
			})
		}
		facets, err := repo.Facets(ctx, false, false, false)
		if err != nil || len(facets.Languages)+len(facets.Countries)+len(facets.Regions) != 0 {
			t.Fatalf("unpublished facets exposed: %+v, %v", facets, err)
		}
		facets, err = repo.Facets(ctx, true, true, true)
		if err != nil || len(facets.Languages) == 0 || len(facets.Countries) == 0 || len(facets.Regions) == 0 {
			t.Fatalf("missing scoped facets: %+v, %v", facets, err)
		}
		for _, tc := range []struct {
			query string
			count int
		}{{"Sartre", 0}, {"Jane Austen", 1}} {
			options, err := repo.Authors(ctx, tc.query, true, true, true)
			if err != nil || len(options.Items) != tc.count {
				t.Fatalf("scoped author %s: %+v, %v", tc.query, options, err)
			}
		}
		// Every page in a filtered collection retains membership and keyset order.
		filter := Filter{Range: Bounds, Women: true, Limit: 100, Preview: true}
		seen := map[string]bool{}
		for {
			page, err := repo.List(ctx, filter)
			if err != nil {
				t.Fatal(err)
			}
			for _, b := range page.Items {
				if seen[b.ID] {
					t.Fatalf("duplicate filtered book %s", b.ID)
				}
				seen[b.ID] = true
			}
			if !page.HasMore {
				break
			}
			filter.After = page.NextCursor
		}
		if len(seen) != expectedWomen {
			t.Fatalf("filtered pagination lost books: %d", len(seen))
		}
	})
	t.Logf("Verified %d distinct review books, %d pages, %d periods, %d undated books, creator dates and publication gating", len(seen), pages, len(first.Density), first.UndatedTotal)
}
