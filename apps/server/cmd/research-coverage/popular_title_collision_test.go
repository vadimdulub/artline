package main

import (
	"context"
	"os"
	"testing"

	"github.com/jackc/pgx/v5"
)

// Optional real-PostgreSQL regression, entirely read-only CTE fixtures.
func TestAthensEmptyTranslationSQL(t *testing.T) {
	dsn := os.Getenv("ARTLINE_TEST_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only PostgreSQL test DSN not set")
	}
	ctx := context.Background()
	db, err := pgx.Connect(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close(ctx)
	const fixture = `WITH artworks(id,title,alternate_title) AS (VALUES
 ('icon','Богоматерь',NULL::text),('other-icon','Знамение',NULL::text),
 ('english','The Entombment of Christ',NULL::text),('alias','Entombment','The Burial'),
 ('greek','Εικόνα',NULL::text)),
 artwork_artists(artwork_id,artist_id) AS (SELECT ''::text,''::text WHERE false) `
	for _, tc := range []struct {
		title, translation string
		want               int
	}{
		{"Unrecorded painting", "", 0}, {"The Entombment of Christ", "", 1},
		{"Богоматерь", "", 1}, {"Εικόνα", "", 1}, {"The Burial", "", 1},
		{"Unrecorded painting", "The Burial", 1},
	} {
		var n int
		if err = db.QueryRow(ctx, fixture+athensTitleCollisionSQL, tc.title, tc.translation, "artist").Scan(&n); err != nil {
			t.Fatal(err)
		}
		if n != tc.want {
			t.Fatalf("%q/%q got %d want %d", tc.title, tc.translation, n, tc.want)
		}
	}
}
