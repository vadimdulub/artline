package books

import (
	"context"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func TestReadOnlyAuthorTimeline(t *testing.T) {
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
	for _, filter := range []Filter{
		{Range: Bounds, Top100: true}, {Range: Bounds},
		{Range: Bounds, Languages: []string{"Q7737"}},
		{Range: Range{1900, 1909}, Languages: []string{"Q7737"}},
		{Range: Bounds, Women: true},
		{Range: Bounds, Women: true, Top100: true},
		{Range: Range{1900, 1910}, Authors: []string{"Jean-Paul Sartre"}},
	} {
		filter.View, filter.Limit, filter.Preview = "authors", 100, true
		view, err := repo.List(ctx, filter)
		if err != nil {
			t.Fatal(err)
		}
		if view.View != "authors" || len(view.Authors) > 100 || len(view.Items) != 0 || view.Total == 0 {
			t.Fatalf("invalid author view: total=%d authors=%d items=%d", view.Total, len(view.Authors), len(view.Items))
		}
		seen := map[string]bool{}
		for _, a := range view.Authors {
			if seen[a.ID] || a.BookCount < 1 {
				t.Fatal("duplicated author or no books")
			}
			seen[a.ID] = true
			if a.StartYear != nil && (*a.StartYear > filter.End || *a.EndYear < filter.Start) {
				t.Fatalf("lifespan outside range: %+v", a)
			}
			if a.Death == nil && a.StartYear != nil && *a.EndYear == Bounds.End {
				t.Fatal("invented present-day lifespan")
			}
			if filter.Women {
				var known bool
				if err := db.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM book_discovery d JOIN book_creator_links l ON l.book_id=d.book_id JOIN book_records b ON b.id=d.book_id AND b.source_checksum=d.book_checksum WHERE l.creator_id=$1 AND $1=ANY(d.woman_author_ids))`, a.ID).Scan(&known); err != nil || !known {
					t.Fatalf("male/unknown coauthor included in women selection: %s, %v", a.ID, err)
				}
			}
		}
		if len(filter.Authors) > 0 {
			if view.Total != 1 || view.Authors[0].Name != "Jean-Paul Sartre" || *view.Authors[0].StartYear != 1905 || *view.Authors[0].EndYear != 1980 {
				t.Fatal("year range used book dates instead of life dates")
			}
		}
		for _, period := range view.Density {
			child := filter
			child.Range = Range{period.Start, period.End}
			child.Limit = 1
			opened, err := repo.List(ctx, child)
			if err != nil || opened.Total != period.Count {
				t.Fatalf("author period count mismatch: %+v -> %d, %v", period, opened.Total, err)
			}
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
				t.Fatal("invalid suggestion")
			}
			if len(*choices) > 0 {
				t.Fatal("suggestion replaces an existing selection")
			}
			*choices = []string{suggestion.Value}
			opened, err := repo.List(ctx, child)
			if err != nil || opened.Total != suggestion.Count || opened.Total >= view.Total {
				t.Fatalf("author suggestion mismatch: %+v -> %d, %v", suggestion, opened.Total, err)
			}
		}
		if view.HasMore {
			child := filter
			child.After = view.NextCursor
			next, err := repo.List(ctx, child)
			if err != nil {
				t.Fatal(err)
			}
			for _, a := range next.Authors {
				if seen[a.ID] {
					t.Fatal("duplicate keyset author")
				}
			}
			if next.Total != view.Total {
				t.Fatal("pagination changed the total")
			}
		}
		t.Logf("%+v languages=%v women=%v top100=%v: %d authors, %d unplaced, %d periods", filter.Range, filter.Languages, filter.Women, filter.Top100, view.Total, view.UndatedTotal, len(view.Density))
	}
	for _, name := range []string{"Homer", "Margaret Atwood"} {
		view, err := repo.List(ctx, Filter{Range: Bounds, View: "authors", Authors: []string{name}, Limit: 100, Preview: true})
		if err != nil || len(view.Authors) != 1 {
			t.Fatalf("%s: %v", name, err)
		}
		a := view.Authors[0]
		if a.StartYear == nil || a.EndYear == nil {
			t.Fatalf("source lifespan not plotted for %s: %+v", name, a)
		}
		if name == "Homer" && (*a.StartYear != -900 || *a.EndYear != -701 || !a.Approximate || !strings.Contains(a.Lifespan, "BCE")) {
			t.Fatalf("lost approximate BCE lifespan: %+v", a)
		}
		if name == "Margaret Atwood" && (*a.StartYear != 1939 || *a.EndYear != 1939 || a.Death != nil || !strings.Contains(a.Lifespan, "death not recorded")) {
			t.Fatalf("invented death: %+v", a)
		}
	}
	public, err := repo.List(ctx, Filter{Range: Bounds, View: "authors", Limit: 100})
	if err != nil {
		t.Fatal(err)
	}
	// The real catalogue may now contain published books. Audit each returned
	// creator against published links instead of assuming an empty public set.
	var eligiblePublished int
	if err = db.QueryRow(ctx, `SELECT count(DISTINCT l.creator_id) FROM book_creator_links l JOIN book_records b ON b.id=l.book_id WHERE b.status='published' AND (b.end_year<=2000 OR b.start_year IS NULL)`).Scan(&eligiblePublished); err != nil {
		t.Fatal(err)
	}
	if public.Total > eligiblePublished {
		t.Fatal("author total exceeds published creator identities")
	}
	for _, author := range public.Authors {
		var publishedBooks int
		if err = db.QueryRow(ctx, `SELECT count(DISTINCT b.id) FROM book_creator_links l JOIN book_records b ON b.id=l.book_id WHERE l.creator_id=$1 AND b.status='published' AND (b.end_year<=2000 OR b.start_year IS NULL)`, author.ID).Scan(&publishedBooks); err != nil {
			t.Fatal(err)
		}
		if publishedBooks == 0 || author.BookCount != publishedBooks {
			t.Fatalf("unpublished creator/book link exposed: %s", author.ID)
		}
	}
	t.Logf("verified %d visible authors against %d published creator identities", public.Total, eligiblePublished)
	for _, languages := range [][]string{nil, {"Q7737"}} {
		args := []any{Bounds.Start, Bounds.End, true, "", []string{}, false, false, languages, []string{}, []string{}}
		var plan string
		if err := db.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+authorTimelineScope+"SELECT count(*),min(start_year),max(end_year) FROM matching", args...).Scan(&plan); err != nil {
			t.Fatal(err)
		}
		t.Logf("author timeline plan languages=%v: %s", languages, plan)
	}
}
