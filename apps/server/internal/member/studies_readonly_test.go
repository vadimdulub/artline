package member

import (
	"context"
	"os"
	"sync/atomic"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type studyQueryCounter struct{ n atomic.Int32 }

func (c *studyQueryCounter) TraceQueryStart(ctx context.Context, _ *pgx.Conn, _ pgx.TraceQueryStartData) context.Context {
	c.n.Add(1)
	return ctx
}
func (c *studyQueryCounter) TraceQueryEnd(context.Context, *pgx.Conn, pgx.TraceQueryEndData) {}

// Opt-in proof against existing records. No account, session, catalogue, or
// test-database writes; PostgreSQL enforces read-only at connection startup.
func TestStudyCatalogueReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "8000"
	counter := &studyQueryCounter{}
	cfg.ConnConfig.Tracer = counter
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	catalogue := PostgresStudyCatalogue{DB: pool}
	for _, f := range []StudySearch{{Kind: "artwork"}, {Kind: "artwork", Query: "Paris"}, {Kind: "artwork", Creator: "Monet", ImageOnly: true}, {Kind: "artwork", Dates: "undated"}, {Kind: "book"}, {Kind: "event"}} {
		t.Run(f.Kind+"-"+f.Query+f.Creator+f.Dates, func(t *testing.T) {
			counter.n.Store(0)
			started := time.Now()
			page, err := catalogue.Search(ctx, "local-debug", f)
			if err != nil {
				t.Fatal(err)
			}
			if len(page.Items) > 24 {
				t.Fatal("unbounded result")
			}
			queries := counter.n.Load()
			if queries > 5 {
				t.Fatalf("per-record enrichment: %d queries", queries)
			}
			t.Logf("%d records in %s; %d queries", len(page.Items), time.Since(started), queries)
			if page.NextCursor != "" {
				f.Cursor = page.NextCursor
				next, err := catalogue.Search(ctx, "local-debug", f)
				if err != nil {
					t.Fatal(err)
				}
				seen := map[string]bool{}
				for _, r := range page.Items {
					seen[studyKey(r)] = true
				}
				for _, r := range next.Items {
					if seen[studyKey(r)] {
						t.Fatal("duplicate keyset record")
					}
				}
				f.Query = "changed"
				if _, err := catalogue.Search(ctx, "local-debug", f); err == nil {
					t.Fatal("cursor accepted across filters")
				}
			}
		})
	}
	refs := []BookmarkRef{{"artwork", "95e6574a-8509-4c70-ad3b-d22ed2cc1e83"}, {"artwork", "cb33c32e-16ea-4d3e-9da0-287f5686585b"}}
	items, err := catalogue.Lookup(ctx, refs)
	if err != nil {
		t.Fatal(err)
	}
	if len(items) != 2 {
		t.Fatal("expected two existing source-backed records")
	}
	for i, item := range items {
		if item.BookmarkRef != refs[i] || item.Date != "1877" || item.Image == nil || len(item.Sources) == 0 {
			t.Fatalf("source/identity/date lost: %+v", item)
		}
	}
	page, err := catalogue.Search(ctx, "local-debug", StudySearch{Kind: "artwork", Bookmarked: true, LocalSaved: []string{refs[0].ID}})
	if err != nil || len(page.Items) != 1 || page.Items[0].ID != refs[0].ID {
		t.Fatal("local bookmark scope", page, err)
	}
}
