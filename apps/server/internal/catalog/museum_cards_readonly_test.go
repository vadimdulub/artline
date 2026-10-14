package catalog

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type oldMuseumCardDB struct{ pgx.Tx }

// Pinned pre-optimization reference, retained only for read-only equivalence.
var museumLegacyCardCTE = `WITH card_candidates AS NOT MATERIALIZED (
 SELECT aw.* FROM artworks aw WHERE aw.current_institution_id=page.id
 UNION ALL
 SELECT aw.* FROM artworks aw WHERE aw.current_institution_id IS DISTINCT FROM page.id
 AND aw.id IN(SELECT la.artwork_id FROM artwork_location_assertions la
 WHERE la.institution_id=page.id AND la.claim_type='display' AND la.review_state='accepted' AND la.superseded_by IS NULL)
), ` + strings.NewReplacer(
	"visible_works AS NOT MATERIALIZED (", "visible_works AS MATERIALIZED (",
	"SELECT aw.* FROM artworks aw WHERE", "SELECT aw.id,aw.current_institution_id,aw.primary_media_id,aw.title,aw.creation_year_start FROM card_candidates aw WHERE",
	"FROM visible_works aw LEFT JOIN institutions", "FROM visible_works visible JOIN artworks aw ON aw.id=visible.id LEFT JOIN institutions",
).Replace(strings.TrimPrefix(museumCTE, "WITH "))

var museumLegacyCardJSON = strings.ReplaceAll(museumJSON,
	"museum_memberships member JOIN artworks aw", "museum_memberships member JOIN visible_works aw")

func oldMuseumCardSQL(sql string) string {
	sql = strings.ReplaceAll(sql, museumDirectoryCardCTE, museumLegacyCardCTE)
	sql = strings.ReplaceAll(sql, museumDirectoryCardJSON, museumLegacyCardJSON)
	return strings.ReplaceAll(sql, "EXISTS(SELECT 1 FROM card_works)", "EXISTS(SELECT 1 FROM museum_memberships member WHERE member.institution_id=i.id)")
}
func (d oldMuseumCardDB) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	return d.Tx.Query(ctx, oldMuseumCardSQL(sql), args...)
}
func (d oldMuseumCardDB) QueryRow(ctx context.Context, sql string, args ...any) pgx.Row {
	return d.Tx.QueryRow(ctx, oldMuseumCardSQL(sql), args...)
}

// Production-safe opt-in audit: compare every response field and cursor in one
// read-only snapshot. Real catalogue data is never used for fixture tests.
func TestMuseumCardsReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("opt-in read-only museum audit")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 4*time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.MaxConns = 1
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "20000"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly, IsoLevel: pgx.RepeatableRead})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	before, after := &Repository{db: oldMuseumCardDB{tx}}, &Repository{db: tx}
	for _, f := range []MuseumFilter{
		{Limit: 24}, {Limit: 60}, {Limit: 5, Countries: []string{"NL", "DE"}},
		{Limit: 5, Selection: "museum"}, {Limit: 5, Artist: "rembrandt"},
		{Limit: 5, Movement: "impressionism"}, {Limit: 5, Display: "on_view"},
		{Limit: 5, Query: "no-such-museum-audit"},
	} {
		t.Run(cursorScope(f, ""), func(t *testing.T) {
			want, err := before.Museums(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			got, err := after.Museums(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			if !reflect.DeepEqual(want, got) {
				t.Fatalf("museum response changed for %+v", f)
			}
			if got.NextCursor != "" {
				f.Cursor = got.NextCursor
				want, err = before.Museums(ctx, f)
				if err != nil {
					t.Fatal(err)
				}
				got, err = after.Museums(ctx, f)
				if err != nil {
					t.Fatal(err)
				}
				if !reflect.DeepEqual(want, got) {
					t.Fatal("next page changed")
				}
			}
		})
	}
	for _, slug := range []string{"the-met", "rijksmuseum", "national-gallery-of-art", "musee-du-louvre", "ateneum-art-museum"} {
		t.Run(slug, func(t *testing.T) {
			want, err := before.Museum(ctx, slug)
			if err != nil {
				t.Fatal(err)
			}
			got, err := after.Museum(ctx, slug)
			if err != nil {
				t.Fatal(err)
			}
			if !reflect.DeepEqual(want, got) {
				t.Fatal("overview counts, cover or evidence changed")
			}
			if dir := os.Getenv("ARTLINE_CARD_PLAN_DIR"); dir != "" {
				if err := os.MkdirAll(dir, 0700); err != nil {
					t.Fatal(err)
				}
				for _, variant := range []struct{ name, sql string }{{"before", oldMuseumCardSQL(museumOverviewSQL)}, {"after", museumOverviewSQL}} {
					var raw []byte
					if err := tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+variant.sql, museumQueryArgs(slug)...).Scan(&raw); err != nil {
						t.Fatal(err)
					}
					if err := os.WriteFile(filepath.Join(dir, slug+"-"+variant.name+".json"), raw, 0600); err != nil {
						t.Fatal(err)
					}
					var plan []map[string]any
					if err := json.Unmarshal(raw, &plan); err != nil {
						t.Fatal(err)
					}
					t.Logf("%s: %v ms", variant.name, plan[0]["Execution Time"])
				}
			}
		})
	}
}
