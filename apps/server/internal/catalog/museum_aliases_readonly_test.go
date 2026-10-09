package catalog

import (
	"context"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"reflect"
	"testing"
)

func TestMuseumAliasesReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue required")
	}
	ctx := context.Background()
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
	var alias, canonical string
	err = tx.QueryRow(ctx, `SELECT i.slug,c.slug FROM institutions i JOIN institutions c ON c.id=i.canonical_institution_id WHERE i.slug='joconde-m5060'`).Scan(&alias, &canonical)
	if err == pgx.ErrNoRows {
		t.Skip("reviewed Orsay reconciliation not applied")
	}
	if err != nil {
		t.Fatal(err)
	}
	repo := &Repository{db: tx}
	old, e := repo.Museum(ctx, alias)
	if e != nil {
		t.Fatal(e)
	}
	current, e := repo.Museum(ctx, canonical)
	if e != nil || !reflect.DeepEqual(old, current) {
		t.Fatalf("alias museum differs: %v", e)
	}
	for _, f := range []MuseumFilter{{Limit: 24}, {Limit: 7, ImageOnly: true}, {Limit: 24, Query: "portrait"}, {Limit: 24, Sort: "year"}, {Limit: 24, Selection: "museum", Sort: "curated"}} {
		before, e := repo.MuseumWorks(ctx, alias, f)
		if e != nil {
			t.Fatal(e)
		}
		after, e := repo.MuseumWorks(ctx, canonical, f)
		if e != nil || !reflect.DeepEqual(before, after) {
			t.Fatalf("alias works differ: %v", e)
		}
		if after.NextCursor != "" {
			f.Cursor = after.NextCursor
			a, e := repo.MuseumWorks(ctx, alias, f)
			if e != nil {
				t.Fatal(e)
			}
			b, e := repo.MuseumWorks(ctx, canonical, f)
			if e != nil || !reflect.DeepEqual(a, b) {
				t.Fatal("alias cursor differs")
			}
		}
		if len(after.Items) > 0 {
			a, e := repo.MuseumArtwork(ctx, alias, after.Items[0].ID)
			if e != nil {
				t.Fatal(e)
			}
			b, e := repo.MuseumArtwork(ctx, canonical, after.Items[0].ID)
			if e != nil || !reflect.DeepEqual(a, b) {
				t.Fatal("alias detail differs")
			}
		}
	}
	a, e := repo.PainterOptions(ctx, "", alias, nil, false, false)
	if e != nil {
		t.Fatal(e)
	}
	b, e := repo.PainterOptions(ctx, "", canonical, nil, false, false)
	if e != nil || !reflect.DeepEqual(a, b) {
		t.Fatal("alias painter options differ")
	}
	var stranded, chains int
	if e := tx.QueryRow(ctx, `SELECT count(*) FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.canonical_institution_id IS NOT NULL`).Scan(&stranded); e != nil || stranded != 0 {
		t.Fatalf("works stranded on aliases: %d %v", stranded, e)
	}
	if e := tx.QueryRow(ctx, `SELECT count(*) FROM institutions i JOIN institutions c ON c.id=i.canonical_institution_id WHERE c.canonical_institution_id IS NOT NULL`).Scan(&chains); e != nil || chains != 0 {
		t.Fatal("alias chain or cycle")
	}
	t.Logf("%s → %s: %d works; museum, pages, details, cursors and painter options agree", alias, canonical, current.WorkCount)
}
