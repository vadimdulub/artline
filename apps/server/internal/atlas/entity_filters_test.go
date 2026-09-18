package atlas

import (
	"context"
	"encoding/json"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/books"
	"github.com/vadimdulub/artline/apps/server/internal/events"
)

func TestEntityFiltersValidationAndCursor(t *testing.T) {
	for kind, fields := range EntityFields {
		for _, field := range fields {
			value := "choice"
			if field == "women" || field == "popular" || field == "top100" {
				value = "true"
			}
			f := Filter{Range: Bounds, Limit: 30, Entities: map[string]url.Values{kind: {field: {value}}}}
			if err := f.Validate(); err != nil {
				t.Fatalf("%s/%s: %v", kind, field, err)
			}
			raw := encodeCursor(Item{ID: "entry", StartYear: 1900}, f, kind)
			f.Entities = nil
			if _, err := decodeCursor(raw, f, kind); err == nil {
				t.Fatalf("cursor crossed %s/%s", kind, field)
			}
		}
	}
	for _, values := range []url.Values{{"language": {strings.Repeat("x", 251)}}, {"top100": {"yes"}}, {"top100": {"true", "false"}}, {"q": {strings.Repeat("x", 201)}}, {"invented": {"x"}}, {"country": {" "}}, {"region": make([]string, 33)}} {
		if err := (Filter{Range: Bounds, Limit: 30, Entities: map[string]url.Values{"book": values}}).Validate(); err == nil {
			t.Fatalf("accepted invalid filters: %v", values)
		}
	}
}

// Uses real catalogue records with read-only connections; no fixtures or migrations.
func TestEntityFiltersReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only audit DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	repo := NewRepository(db)
	cases := []struct {
		kind   string
		values url.Values
	}{
		{"book", url.Values{"language": {"Q7737"}, "top100": {"false"}}},
		{"book", url.Values{"author": {"Leo Tolstoy"}, "region": {"eastern-europe"}, "top100": {"false"}}},
		{"book", url.Values{"women": {"true"}, "top100": {"true"}}},
		{"book", url.Values{"country": {"Q159"}, "language": {"Q7737"}, "q": {"war"}, "top100": {"false"}}},
		{"event", url.Values{"topic": {"Conflict"}, "region": {"Eastern Europe"}, "top100": {"false"}}},
		{"event", url.Values{"country": {"France"}, "kind": {"Event"}, "top100": {"true"}}},
		{"event", url.Values{"q": {"war"}, "top100": {"false"}}},
		{"artwork", url.Values{"q": {"impressionism"}, "popular": {"true"}}},
		{"artwork", url.Values{"painter": {"claude-monet"}, "popular": {"false"}}},
		{"artwork", url.Values{"movement": {"impressionism"}, "country": {"FR"}, "region": {"western-europe"}, "work_type": {"painting"}, "popular": {"true"}}},
		{"artwork", url.Values{"women": {"true"}, "popular": {"true"}}},
	}
	for _, tc := range cases {
		t.Run(tc.kind+tc.values.Encode(), func(t *testing.T) {
			f := Filter{Range: Bounds, Limit: 30, Preview: true, Highlights: true, Selection: true, Types: []string{tc.kind}, Entities: map[string]url.Values{tc.kind: tc.values}}
			out, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			if len(out.Lanes) != 1 {
				t.Fatalf("wrong lanes %+v", out)
			}
			switch tc.kind {
			case "book":
				v := tc.values
				n, err := books.NewRepository(db).List(ctx, books.Filter{Range: books.Bounds, Limit: 100, Preview: true, Query: v.Get("q"), Authors: v["author"], Languages: v["language"], Countries: v["country"], Regions: v["region"], Women: v.Get("women") == "true", Top100: v.Get("top100") == "true"})
				if err != nil {
					t.Fatal(err)
				}
				if out.Total != n.Total-n.UndatedTotal {
					t.Fatalf("native book count %d, undated %d, atlas %d", n.Total, n.UndatedTotal, out.Total)
				}
			case "event":
				v := tc.values
				n, err := events.NewRepository(db).List(ctx, events.Filter{Range: events.Bounds, Limit: 100, Preview: true, Query: v.Get("q"), Topics: v["topic"], Kinds: v["kind"], Countries: v["country"], Regions: v["region"], Top100: v.Get("top100") == "true"})
				if err != nil {
					t.Fatal(err)
				}
				if out.Total != n.Total-n.UndatedTotal {
					t.Fatalf("native event count %d, undated %d, atlas %d", n.Total, n.UndatedTotal, out.Total)
				}
			case "artwork":
				for _, item := range out.Lanes[0].Items {
					var matches bool
					err = db.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id JOIN artists ar ON ar.id=aa.artist_id
      WHERE a.id=$1::uuid AND ar.status<>'archived'
      AND ($2='' OR ar.slug=$2) AND ($3='' OR a.work_type=$3)
      AND (NOT $4 OR EXISTS(SELECT 1 FROM artist_gender_evidence g WHERE g.artist_id=ar.id AND g.is_woman))
      AND (NOT $5 OR EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=ar.id AND d.is_popular))
      AND ($6='' OR EXISTS(SELECT 1 FROM artist_movements am JOIN movements m ON m.id=am.movement_id WHERE am.artist_id=ar.id AND m.slug=$6))
      AND ($7='' OR EXISTS(SELECT 1 FROM artist_countries ac JOIN countries c ON c.code=ac.country_code WHERE ac.artist_id=ar.id AND ac.country_code::text=$7 AND c.region_code=$8)))`, item.ID, tc.values.Get("painter"), tc.values.Get("work_type"), tc.values.Get("women") == "true", tc.values.Get("popular") == "true", tc.values.Get("movement"), tc.values.Get("country"), tc.values.Get("region")).Scan(&matches)
					if err != nil || !matches {
						t.Fatalf("artwork escaped native facets: %s %v", item.ID, err)
					}
				}
			}
			t.Logf("matching dated entries=%d", out.Total)
			if len(out.Lanes[0].Items) > 30 {
				t.Fatal("unbounded page")
			}
			if raw := out.Lanes[0].NextCursor; raw != "" {
				f.After = map[string]string{tc.kind: raw}
				next, err := repo.List(ctx, f)
				if err != nil {
					t.Fatal(err)
				}
				if next.Total != out.Total {
					t.Fatal("page count changed")
				}
				seen := map[string]bool{}
				for _, i := range out.Lanes[0].Items {
					seen[i.ID] = true
				}
				for _, i := range next.Lanes[0].Items {
					if seen[i.ID] {
						t.Fatal("duplicate page entry")
					}
				}
			}
		})
	}
	// An explicit book outside a filtered layer is still included exactly once.
	var pick string
	if err = db.QueryRow(ctx, `SELECT b.id FROM book_records b JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum WHERE b.start_year IS NOT NULL AND b.end_year<=2000 AND b.status<>'archived' AND NOT ('Q7737'=ANY(d.languages)) ORDER BY b.id LIMIT 1`).Scan(&pick); err != nil {
		t.Fatal(err)
	}
	f := Filter{Range: Bounds, Limit: 30, Preview: true, Selection: true, Types: []string{"book"}, Entities: map[string]url.Values{"book": {"language": {"Q7737"}, "top100": {"false"}}}}
	before, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	f.Picks = map[string][]string{"book": {pick}}
	after, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	if after.Total != before.Total+1 {
		t.Fatal("explicit pick lost outside filtered layer")
	}
	// Keep representative query-plan evidence outside Documents.
	args := []any{pgx.QueryExecModeCacheDescribe, Bounds.Start, Bounds.End, true, "", false, "", []string(nil)}
	clause := entityPredicate("artwork", url.Values{"painter": {"claude-monet"}, "popular": {"false"}}, &args)
	var plan json.RawMessage
	if err = db.QueryRow(ctx, `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT a.id`+artScope+` AND $7::text[] IS NULL AND (`+clause+`)`, args...).Scan(&plan); err != nil {
		t.Fatal(err)
	}
	dir := "/tmp/artline-entity-filter-audit"
	if err = os.MkdirAll(dir, 0755); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(dir, "monet-plan.json"), plan, 0644); err != nil {
		t.Fatal(err)
	}
	geo := geographyPredicate("artwork", Filter{Countries: []string{"france"}, Continents: []string{"europe"}}, &args)
	if err = db.QueryRow(ctx, `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT a.id`+artScope+` AND $7::text[] IS NULL AND (`+clause+`) AND (`+geo+`)`, args...).Scan(&plan); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(plan), "artwork_artists_artist_work_idx") || !strings.Contains(string(plan), "artworks_pkey") {
		t.Fatal("geography lost the scoped painter artwork lookups")
	}
	if err = os.WriteFile(filepath.Join(dir, "monet-geography-plan.json"), plan, 0644); err != nil {
		t.Fatal(err)
	}
}
