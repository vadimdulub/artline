package catalog

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Exercise the actual imported Cyprus catalogue without fixtures or writes.
func TestMuseumAnonymousReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
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
	var total, anonymous, published int
	err = tx.QueryRow(ctx, `SELECT count(*),
 count(*) FILTER(WHERE a.unlinked_creator_label IS NULL AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id)),
 count(*) FILTER(WHERE a.status='published')
 FROM artworks a JOIN institutions i ON i.id=a.current_institution_id
 WHERE i.slug='cyprus-museum-nicosia' AND a.status<>'archived'`).Scan(&total, &anonymous, &published)
	if err != nil {
		t.Fatal(err)
	}
	if total == 0 || anonymous == 0 {
		t.Skip("imported Cyprus Museum anonymous collection required")
	}
	repo := &Repository{db: tx}
	museum, err := repo.Museum(ctx, "cyprus-museum-nicosia")
	if err != nil || museum.WorkCount != total {
		t.Fatalf("anonymous holdings missing: expected %d, got %d, error %v", total, museum.WorkCount, err)
	}
	page, err := repo.MuseumWorks(ctx, "cyprus-museum-nicosia", MuseumFilter{Limit: 7})
	if err != nil || page.Total != total || len(page.Items) != 7 || page.NextCursor == "" {
		t.Fatalf("anonymous collection pagination failed: total %d, items %d, error %v", page.Total, len(page.Items), err)
	}
	directory, err := repo.Museums(ctx, MuseumFilter{Countries: []string{"CY"}, Limit: 60})
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, item := range directory.Items {
		found = found || item.Slug == "cyprus-museum-nicosia"
	}
	if !found {
		t.Fatal("Cyprus country filter still hides the anonymous collection")
	}
	t.Logf("%d active holdings, including %d without creator labels and %d with historical published status, are browsable; Cyprus filter returns %d collections", total, anonymous, published, directory.Total)
}
