package atlas

import (
	"context"
	"errors"
	"net/url"
	"slices"
	"strings"
	"testing"

	"github.com/jackc/pgx/v5"
)

// The broad path must not displace the measured, fast creator/preset plans.
func TestBroadGeographyQueryRouting(t *testing.T) {
	for _, tc := range []struct {
		name   string
		change func(*Filter)
		broad  bool
	}{
		{"country", func(f *Filter) {}, true},
		{"continent", func(f *Filter) { f.Countries = nil; f.Continents = []string{"asia"} }, true},
		{"intersection", func(f *Filter) { f.Continents = []string{"asia"} }, true},
		{"browser", func(f *Filter) {
			f.Selection = true
			f.Entities = map[string]url.Values{"artwork": {"popular": {"false"}, "women": {"false"}, "image_only": {"true"}}}
		}, true},
		{"legacy-image-option", func(f *Filter) { f.Entities = map[string]url.Values{"artwork": {"image_only": {"false"}}} }, true},
		{"other-lane-filter", func(f *Filter) { f.Entities = map[string]url.Values{"book": {"author": {"Example"}}} }, true},
		{"cursor", func(f *Filter) {
			f.After = map[string]string{"artwork": encodeCursor(Item{ID: "00000000-0000-0000-0000-000000000001", StartYear: 1800}, *f, "artwork")}
		}, true},
		{"narrow-dates", func(f *Filter) { f.Range = Range{1750, 1870} }, false},
		{"highlights", func(f *Filter) { f.Highlights = true }, false},
		{"preset", func(f *Filter) { f.PresetID = "romanticism" }, false},
		{"shared-creator", func(f *Filter) { f.Creators = []string{"painter:claude-monet"} }, false},
		{"shared-search", func(f *Filter) { f.Query = "Monet" }, false},
		{"legacy-region", func(f *Filter) { f.Region = "western-europe" }, false},
		{"picked-artwork", func(f *Filter) {
			f.Selection = true
			f.Picks = map[string][]string{"artwork": {"00000000-0000-0000-0000-000000000001"}}
		}, false},
		{"neighbor", func(f *Filter) {
			f.Limit = 1
			f.NeighborOf, f.Direction = "00000000-0000-0000-0000-000000000001", "next"
		}, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			f := Filter{Range: Bounds, Limit: 150, Types: []string{"artwork"}, Countries: []string{"japan"}}
			tc.change(&f)
			if broadArtworkGeography(f) != tc.broad {
				t.Fatal("wrong geography strategy")
			}
			if f.PresetID != "" {
				// Presets resolve object identities before building the scope;
				// their complete queries are covered by the read-only A/B audit.
				return
			}
			db := &performanceCaptureDB{}
			_, err := (&Repository{db: db}).List(context.Background(), f)
			if !errors.Is(err, errPerformanceCapture) {
				t.Fatal(err)
			}
			if strings.Contains(db.query, "artwork_geography AS MATERIALIZED") == tc.broad {
				t.Fatalf("wrong geographic query path for %s", tc.name)
			}
			if !strings.Contains(db.query, "artwork_places") || strings.Contains(db.query, "'japan'") {
				t.Fatal("lost production geography or interpolated a filter value")
			}
		})
	}
	for _, key := range []string{"q", "id", "painter", "movement", "country", "region", "work_type", "women", "popular", "future_filter"} {
		f := Filter{Range: Bounds, Countries: []string{"japan"}, Entities: map[string]url.Values{"artwork": {key: {"true"}}}}
		if broadArtworkGeography(f) {
			t.Errorf("native filter %s bypassed scoped geography", key)
		}
	}
}

// Exercise eligibility, independent geographic memberships and pagination with
// both clean projection rows and pending live rows. The fixture helper refuses
// every database except the dedicated disposable PostgreSQL cluster under /tmp.
func TestBroadGeographyPendingAndProductionPlaces(t *testing.T) {
	db, ctx := browseFixturePool(t)
	tx, err := db.Begin(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	exec := func(q string, args ...any) {
		t.Helper()
		if _, err := tx.Exec(ctx, q, args...); err != nil {
			t.Fatal(err)
		}
	}
	id := func(q string, args ...any) string {
		t.Helper()
		var v string
		if err := tx.QueryRow(ctx, q, args...).Scan(&v); err != nil {
			t.Fatal(err)
		}
		return v
	}
	exec(`INSERT INTO countries(code,name,region_code) VALUES
 ('XJ','Fixture Japan','eastern-asia'),('XF','Fixture France','western-europe')`)
	place := id(`INSERT INTO places(name,normalized_name,country_code) VALUES('Fixture origin','fixture origin','XJ') RETURNING id::text`)
	source := id(`INSERT INTO sources(slug,name,source_type) VALUES(gen_random_uuid()::text,'Geography fixture','manual') RETURNING id::text`)
	institution := id(`INSERT INTO institutions(slug,name,normalized_name,status,place_id)
 VALUES(gen_random_uuid()::text,'Geography fixture','geography fixture','review',$1) RETURNING id::text`, place)
	media := id(`INSERT INTO media_assets(storage_kind,storage_path,rights_status)
 VALUES('local','/assets/fixture-'||gen_random_uuid()::text||'.jpg','unknown') RETURNING id::text`)
	artist := func(name, status, country string) string {
		a := id(`INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status)
 VALUES(gen_random_uuid()::text,$1,$1,lower($1),1700,1800,'1700–1800','life',$2) RETURNING id::text`, name, status)
		exec(`INSERT INTO artist_countries(artist_id,country_code,relationship_type) VALUES($1,$2,'active')`, a, country)
		return a
	}
	japanese := artist("Fixture Japanese", "review", "XJ")
	french := artist("Fixture French", "review", "XF")
	archived := artist("Fixture Archived", "archived", "XJ")
	work := func(name, creator string, production bool) string {
		a := id(`INSERT INTO artworks(slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,primary_media_id,status)
 VALUES(gen_random_uuid()::text,$1,lower($1),'1750',1750,1750,'exact','painting',$2,'review') RETURNING id::text`, name, media)
		exec(`INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,source_id,source_url,evidence_note,checked_at,review_state)
 VALUES($1,'holding',$2,$3,'https://example.test/object','Fixture only',now(),'accepted')`, a, institution, source)
		if creator != "" {
			exec(`INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role) VALUES($1,$2,'primary')`, a, creator)
		}
		if production {
			exec(`INSERT INTO artwork_places(artwork_id,place_id,relationship_type) VALUES($1,$2,'created')`, a, place)
		}
		return a
	}
	anonymous := work("Anonymous production", "", true)
	dual := work("French creator, Japanese production", french, true)
	creatorOnly := work("Japanese creator", japanese, false)
	work("Holding only, not production", french, false)
	work("Archived creator only", archived, true)
	mixed := work("Mixed creator statuses", french, false)
	exec(`INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role) VALUES($1,$2,'attributed_to')`, mixed, archived)
	tooLate := work("Outside creation scope", japanese, false)
	exec(`UPDATE artworks SET creation_year_end=1971 WHERE id=$1`, tooLate)
	unillustrated := work("No image", japanese, false)
	exec(`UPDATE artworks SET primary_media_id=NULL WHERE id=$1`, unillustrated)
	duplicate := work("Duplicate geographic evidence", japanese, true)
	exec(`INSERT INTO artist_countries(artist_id,country_code,relationship_type) VALUES($1,'XJ','birth')`, japanese)
	repo := &Repository{db: tx}
	check := func(countries, continents []string, expected []string) {
		t.Helper()
		f := Filter{Range: Bounds, Limit: 2, Types: []string{"artwork"}, Countries: countries, Continents: continents}
		seen := []string{}
		for page := 0; ; page++ {
			if page > len(expected) {
				t.Fatal("pagination did not terminate")
			}
			out, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			if out.Total != len(expected) || len(out.Lanes) != 1 {
				t.Fatalf("got total=%d, want %d", out.Total, len(expected))
			}
			lane := out.Lanes[0]
			for _, item := range lane.Items {
				if slices.Contains(seen, item.ID) {
					t.Fatal("duplicate geographic match or repeated page ID")
				}
				seen = append(seen, item.ID)
			}
			if lane.NextCursor == "" {
				break
			}
			f.After = map[string]string{"artwork": lane.NextCursor}
		}
		slices.Sort(seen)
		want := slices.Clone(expected)
		slices.Sort(want)
		if !slices.Equal(seen, want) {
			t.Fatalf("got IDs %v, want %v", seen, want)
		}
		// The period-page path must preserve the same evidence for pending and
		// clean records, including independent country/continent matches.
		args := []any{pgx.QueryExecModeCacheDescribe}
		predicate := geographyPredicateWithArtwork("artwork", f, &args, pageArtworkGeographyMatch)
		rows, err := tx.Query(ctx, "SELECT a.id::text FROM artwork_atlas_browse a WHERE ("+predicate+") ORDER BY a.id", args...)
		if err != nil {
			t.Fatal(err)
		}
		pageIDs := []string{}
		for rows.Next() {
			var id string
			if err := rows.Scan(&id); err != nil {
				t.Fatal(err)
			}
			pageIDs = append(pageIDs, id)
		}
		rows.Close()
		if rows.Err() != nil || !slices.Equal(pageIDs, want) {
			t.Fatalf("page geography got %v, want %v: %v", pageIDs, want, rows.Err())
		}
	}
	checkAll := func() {
		check([]string{"fixture japan"}, nil, []string{anonymous, dual, creatorOnly, duplicate})
		// Each geographic predicate can match a different recorded origin.
		check([]string{"fixture france"}, []string{"asia"}, []string{dual})
		check([]string{"fixture japan"}, []string{"europe"}, []string{dual})
		check([]string{"missing country"}, nil, nil)
	}
	checkAll() // All new works are pending and evaluated live.
	var pending []string
	rows, err := tx.Query(ctx, `SELECT artwork_id::text FROM artwork_atlas_dirty ORDER BY artwork_id`)
	if err != nil {
		t.Fatal(err)
	}
	for rows.Next() {
		var v string
		if err := rows.Scan(&v); err != nil {
			t.Fatal(err)
		}
		pending = append(pending, v)
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		t.Fatal(err)
	}
	if err := refreshClaimedBrowse(ctx, tx, pending); err != nil {
		t.Fatal(err)
	}
	checkAll() // The same results must survive projection refresh.
	exec(`UPDATE artworks SET status='archived' WHERE id=$1`, creatorOnly)
	check([]string{"fixture japan"}, nil, []string{anonymous, dual, duplicate})
	// Geography stays live even when an unchanged artwork has a clean projection.
	exec(`DELETE FROM artwork_places WHERE artwork_id=$1`, dual)
	check([]string{"fixture japan"}, nil, []string{anonymous, duplicate})
	check([]string{"fixture france"}, []string{"asia"}, nil)
}
