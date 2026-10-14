package catalog

import (
	"context"
	"os"
	"reflect"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Use a separately initialized, disposable PostgreSQL cluster with the public
// migrations applied. Never point this opt-in test at the real catalogue.
func TestMuseumCardsIsolatedFixture(t *testing.T) {
	dsn := os.Getenv("ARTLINE_MUSEUM_FIXTURE_DATABASE_URL")
	if dsn == "" {
		t.Skip("requires a disposable migrated fixture cluster")
	}
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	var database, address string
	var works int
	if err = pool.QueryRow(ctx, `SELECT current_database(),inet_server_addr()::text,(SELECT count(*) FROM artworks)`).Scan(&database, &address, &works); err != nil {
		t.Fatal(err)
	}
	if database != "postgres" || address != "127.0.0.1/32" && address != "127.0.0.1" || works > 100 {
		t.Fatal("not the isolated small fixture database")
	}
	tx, err := pool.Begin(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	before, after := &Repository{db: oldMuseumCardDB{tx}}, &Repository{db: tx}
	check := func(label string) {
		t.Helper()
		for _, filter := range []MuseumFilter{{Limit: 60}, {Limit: 2}, {Limit: 24, Display: "on_view"}, {Limit: 24, Selection: "museum"}} {
			want, e := before.Museums(ctx, filter)
			if e != nil {
				t.Fatal(label, e)
			}
			got, e := after.Museums(ctx, filter)
			if e != nil {
				t.Fatal(label, e)
			}
			if !reflect.DeepEqual(want, got) {
				t.Fatalf("%s: directory, evidence, cover or counts changed", label)
			}
		}
		for _, slug := range []string{"the-met", "national-gallery-of-art"} {
			want, e := before.Museum(ctx, slug)
			if e != nil {
				t.Fatal(label, e)
			}
			got, e := after.Museum(ctx, slug)
			if e != nil {
				t.Fatal(label, e)
			}
			if !reflect.DeepEqual(want, got) {
				t.Fatalf("%s: %s overview changed", label, slug)
			}
		}
	}
	check("seed")
	var assertion string
	err = tx.QueryRow(ctx, `INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,venue_id,display_state,context,source_id,source_url,evidence_note,checked_at,review_state)
 SELECT aw.id,'display',i.id,v.id,'on_view','loan',s.id,'https://example.org/fixture','Isolated regression fixture',now(),'accepted'
 FROM artworks aw,institutions i,institution_venues v,sources s
 WHERE aw.slug='rembrandt-self-portrait-1660' AND i.slug='national-gallery-of-art' AND v.slug='nga-west-building' AND s.slug='nga-washington' RETURNING id::text`).Scan(&assertion)
	if err != nil {
		t.Fatal(err)
	}
	check("incoming loan")
	got, err := after.Museum(ctx, "national-gallery-of-art")
	if err != nil || got.WorkCount != 3 || got.HoldingCount != 2 || got.OnViewCount != 1 {
		t.Fatalf("loan membership: %+v %v", got, err)
	}
	for _, change := range []struct{ label, sql string }{
		{"stale loan", `UPDATE artwork_location_assertions SET checked_at=now()-interval '31 days' WHERE id=$1`},
		{"conflicting loan", `UPDATE artwork_location_assertions SET checked_at=now(),review_state='conflict' WHERE id=$1`},
		{"holding and display deduplicated", `UPDATE artwork_location_assertions SET review_state='accepted',institution_id=(SELECT id FROM institutions WHERE slug='the-met'),venue_id=(SELECT id FROM institution_venues WHERE institution_id=(SELECT id FROM institutions WHERE slug='the-met') ORDER BY id LIMIT 1) WHERE id=$1`},
	} {
		if _, err = tx.Exec(ctx, change.sql, assertion); err != nil {
			t.Fatal(err)
		}
		check(change.label)
	}
	if _, err = tx.Exec(ctx, `UPDATE artworks SET primary_media_id=NULL WHERE current_institution_id=(SELECT id FROM institutions WHERE slug='the-met')`); err != nil {
		t.Fatal(err)
	}
	check("unillustrated cover fallback")
	if _, err = tx.Exec(ctx, `UPDATE artworks SET status='archived' WHERE slug='rembrandt-self-portrait-1660'`); err != nil {
		t.Fatal(err)
	}
	check("archived artwork excluded")
}
