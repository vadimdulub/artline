package catalog

import (
	"context"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"reflect"
	"strings"
	"testing"
	"time"
)

// Retain the old UUID-materializing query for exact response comparisons.
var previousMuseumScopedCTE = `WITH museum_candidates AS MATERIALIZED (
 SELECT aw.id FROM artworks aw WHERE aw.current_institution_id=(SELECT id FROM institutions WHERE slug=$2)
 UNION SELECT la.artwork_id FROM artwork_location_assertions la
 WHERE la.institution_id=(SELECT id FROM institutions WHERE slug=$2)
 AND la.claim_type='display' AND la.review_state='accepted' AND la.superseded_by IS NULL
), ` + strings.Replace(strings.TrimPrefix(museumCTE, "WITH "), "SELECT aw.* FROM artworks aw WHERE", "SELECT aw.* FROM museum_candidates scope JOIN artworks aw ON aw.id=scope.id WHERE", 1)

type museumScopePreviousDB struct{ pgx.Tx }

func (d *museumScopePreviousDB) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	return d.Tx.Query(ctx, strings.NewReplacer(museumScopedFacetCTE, previousMuseumScopedCTE, museumScopedCTE, previousMuseumScopedCTE).Replace(sql), args...)
}
func (d *museumScopePreviousDB) QueryRow(ctx context.Context, sql string, args ...any) pgx.Row {
	return d.Tx.QueryRow(ctx, strings.NewReplacer(museumScopedFacetCTE, previousMuseumScopedCTE, museumScopedCTE, previousMuseumScopedCTE).Replace(sql), args...)
}

func TestMuseumScopeReadOnlyEquivalent(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only real-catalogue DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly, IsoLevel: pgx.RepeatableRead})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	old := &Repository{db: &museumScopePreviousDB{Tx: tx}}
	current := &Repository{db: tx}
	start, end := 1800, 1900
	cases := []struct {
		name   string
		filter MuseumFilter
	}{
		{"images", MuseumFilter{Limit: 24}}, {"year", MuseumFilter{Limit: 24, Sort: "year"}}, {"title", MuseumFilter{Limit: 24, Sort: "title"}},
		{"image-only", MuseumFilter{Limit: 7, ImageOnly: true}}, {"painting", MuseumFilter{Limit: 24, WorkType: "painting"}},
		{"date", MuseumFilter{Limit: 24, Start: &start, End: &end}}, {"unknown-date", MuseumFilter{Limit: 24, UnknownDate: true}},
		{"search", MuseumFilter{Limit: 24, Query: "portrait"}}, {"artist", MuseumFilter{Limit: 24, Artist: "rembrandt"}},
		{"on-view", MuseumFilter{Limit: 24, Display: "on_view"}}, {"museum-highlights", MuseumFilter{Limit: 24, Selection: "museum", Sort: "curated"}},
		{"museum", MuseumFilter{Limit: 24, Selection: "museum", Sort: "curated"}},
	}
	for _, slug := range []string{"musee-du-louvre", "musee-orsay", "the-met", "national-gallery-of-art"} {
		for _, tc := range cases {
			t.Run(slug+"/"+tc.name, func(t *testing.T) {
				before, e := old.MuseumWorks(ctx, slug, tc.filter)
				if e != nil {
					t.Fatal(e)
				}
				after, e := current.MuseumWorks(ctx, slug, tc.filter)
				if e != nil {
					t.Fatal(e)
				}
				if !reflect.DeepEqual(before, after) {
					t.Fatal("items, counts, facets, image coverage or cursor changed")
				}
				if after.NextCursor != "" {
					f := tc.filter
					f.Cursor = after.NextCursor
					a, e := old.MuseumWorks(ctx, slug, f)
					if e != nil {
						t.Fatal(e)
					}
					b, e := current.MuseumWorks(ctx, slug, f)
					if e != nil || !reflect.DeepEqual(a, b) {
						t.Fatalf("next page changed: %v", e)
					}
				}
			})
		}
	}
}
