package events

import (
	"context"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"strings"
	"testing"
	"time"
)

// Opt-in audit of real catalogue rows. No fixtures, database creation or writes.
func TestReadOnlyHistoricalEvents(t *testing.T) {
	dsn := os.Getenv("ARTLINE_EVENTS_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only audit not requested")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	repo := NewRepository(db)
	var count, top, published, badDates int
	err = db.QueryRow(ctx, `SELECT count(*),count(*) FILTER(WHERE top100),count(*) FILTER(WHERE status='published'),count(*) FILTER(WHERE end_year>2000 OR start_year=0 OR end_year=0) FROM event_records`).Scan(&count, &top, &published, &badDates)
	if err != nil || count != 10000 || top != 100 || published != 0 || badDates != 0 {
		t.Fatalf("invalid import: %d events, %d top, %d published, %d invalid dates: %v", count, top, published, badDates, err)
	}
	for _, f := range []Filter{{Range: Bounds, Top100: true}, {Range: Bounds}, {Range: Range{1700, 1800}}, {Range: Range{1939, 1945}}, {Range: Bounds, Topics: []string{"Religion and ideas"}}, {Range: Bounds, Countries: []string{"France"}}, {Range: Bounds, Query: "Byzantine"}, {Range: Range{-12000, -1}}} {
		f.Preview = true
		f.Limit = 100
		view, err := repo.List(ctx, f)
		if err != nil {
			t.Fatal(err)
		}
		if view.Total < 1 || len(view.Items) > 100 {
			t.Fatalf("unexpected selection %+v: %+v", f, view)
		}
		for _, e := range view.Items {
			if e.StartYear != nil && (*e.StartYear > f.End || *e.EndYear < f.Start) {
				t.Fatalf("event outside scope %s", e.ID)
			}
		}
		for _, p := range view.Density {
			child := f
			child.Range = Range{p.Start, p.End}
			child.Limit = 1
			opened, err := repo.List(ctx, child)
			if err != nil || opened.Total != p.Count {
				t.Fatalf("density mismatch %+v: %d %v", p, opened.Total, err)
			}
		}
		for _, s := range view.Suggestions {
			child := f
			switch s.Key {
			case "topic":
				child.Topics = []string{s.Value}
			case "country":
				child.Countries = []string{s.Value}
			case "region":
				child.Regions = []string{s.Value}
			case "kind":
				child.Kinds = []string{s.Value}
			default:
				t.Fatal("unknown suggestion")
			}
			opened, err := repo.List(ctx, child)
			if err != nil || opened.Total != s.Count || opened.Total >= view.Total {
				t.Fatalf("suggestion mismatch %+v: %d %v", s, opened.Total, err)
			}
		}
		t.Logf("filter %+v: %d events, %s, %d periods", f, view.Total, view.Mode, len(view.Density))
	}
	// Walk every bounded keyset page and prove no gaps or duplicates.
	f := Filter{Range: Bounds, Preview: true, Limit: 100}
	seen := map[string]bool{}
	for {
		view, err := repo.List(ctx, f)
		if err != nil {
			t.Fatal(err)
		}
		for _, e := range view.Items {
			if seen[e.ID] {
				t.Fatal("duplicate keyset record")
			}
			seen[e.ID] = true
		}
		if !view.HasMore {
			break
		}
		if view.NextCursor == "" {
			t.Fatal("missing cursor")
		}
		f.After = view.NextCursor
	}
	if len(seen) != 10000 {
		t.Fatalf("keyset walked %d records", len(seen))
	}
	public, err := repo.List(ctx, Filter{Range: Bounds, Limit: 100})
	if err != nil || public.Total != 0 {
		t.Fatal("review records leaked publicly", err)
	}
	if _, err = repo.ByID(ctx, "event-q6534", false); err != ErrNotFound {
		t.Fatal("review detail leaked publicly", err)
	}
	for _, qid := range []string{"event-q6534", "event-q361", "event-q362", "event-q12544", "event-q18578423", "event-q12562"} {
		e, err := repo.ByID(ctx, qid, true)
		if err != nil || !e.Top100 || e.StartYear == nil {
			t.Fatalf("missing required event %s %v", qid, err)
		}
	}
	for _, query := range []string{`EXPLAIN (ANALYZE,BUFFERS) SELECT id FROM event_records WHERE status<>'archived' AND top100 ORDER BY coalesce(start_year,2147483647),id LIMIT 101`, `EXPLAIN (ANALYZE,BUFFERS) SELECT id FROM event_records WHERE status<>'archived' AND countries && ARRAY['France'] AND start_year<=1900 AND end_year>=1700 ORDER BY coalesce(start_year,2147483647),id LIMIT 101`} {
		rows, err := db.Query(ctx, query)
		if err != nil {
			t.Fatal(err)
		}
		plan := []string{}
		for rows.Next() {
			var line string
			if err = rows.Scan(&line); err != nil {
				t.Fatal(err)
			}
			plan = append(plan, line)
		}
		err = rows.Err()
		rows.Close()
		if err != nil {
			t.Fatal(err)
		}
		t.Log(strings.Join(plan, "\n"))
	}
}
