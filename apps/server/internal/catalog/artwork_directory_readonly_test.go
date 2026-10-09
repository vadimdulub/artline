package catalog

import (
	"context"
	"errors"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"testing"
	"time"
)

func TestArtworkDirectoryReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
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
	repo := &Repository{db: tx}
	{
		var count int
		err = tx.QueryRow(ctx, "SELECT count(*) FROM artworks WHERE status<>'archived'").Scan(&count)
		if err != nil {
			t.Fatal(err)
		}
		page, e := repo.BrowseArtworks(ctx, ArtworkDirectoryFilter{Limit: 7})
		if e != nil || page.Total != count {
			t.Fatalf("total %d expected %d: %v", page.Total, count, e)
		}
		if len(page.Items) > 7 {
			t.Fatal("unbounded page")
		}
		if page.NextCursor != "" {
			next, e := repo.BrowseArtworks(ctx, ArtworkDirectoryFilter{Limit: 7, Cursor: page.NextCursor})
			if e != nil {
				t.Fatal(e)
			}
			seen := map[string]bool{}
			for _, x := range page.Items {
				seen[x.ID] = true
			}
			for _, x := range next.Items {
				if seen[x.ID] {
					t.Fatal("repeated page")
				}
			}
			_, e = repo.BrowseArtworks(ctx, ArtworkDirectoryFilter{Limit: 7, Cursor: page.NextCursor, Undated: true})
			if !errors.Is(e, ErrChronologyFilter) {
				t.Fatal("cursor scope not enforced", e)
			}
		}
		t.Logf("%d active records", count)
	}
	var title, id string
	err = tx.QueryRow(ctx, `SELECT title,id FROM artworks aw WHERE status='review' AND length(title)<180 AND primary_media_id IS NULL AND current_institution_id IS NULL AND creation_year_start IS NULL AND creation_year_end IS NULL AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=aw.id) ORDER BY length(title) DESC LIMIT 1`).Scan(&title, &id)
	if err != nil {
		t.Fatal(err)
	}
	page, err := repo.BrowseArtworks(ctx, ArtworkDirectoryFilter{Query: title, Undated: true, Limit: 60})
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, x := range page.Items {
		found = found || x.ID == id
	}
	if !found {
		t.Fatal("unassigned undated image-free record missing", title)
	}
	_, err = repo.BrowseArtworks(ctx, ArtworkDirectoryFilter{Limit: 7, Cursor: "invalid"})
	if !errors.Is(err, ErrChronologyFilter) {
		t.Fatal("invalid cursor accepted")
	}
}
func TestEmptyMuseumHiddenReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	var slug, name, country string
	err = tx.QueryRow(ctx, `SELECT i.slug,i.name,trim(p.country_code) FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.status='review' AND i.canonical_institution_id IS NULL AND NOT EXISTS(SELECT 1 FROM artworks aw WHERE aw.current_institution_id=i.id) AND NOT EXISTS(SELECT 1 FROM artwork_location_assertions a WHERE a.institution_id=i.id) AND NOT EXISTS(SELECT 1 FROM curated_collections c WHERE c.institution_id=i.id) AND NOT EXISTS(SELECT 1 FROM institution_venues v WHERE v.institution_id=i.id) ORDER BY length(i.name) DESC LIMIT 1`).Scan(&slug, &name, &country)
	if err != nil {
		t.Fatal(err)
	}
	repo := &Repository{db: tx}
	{
		_, err = repo.Museum(ctx, slug)
		if !errors.Is(err, ErrNotFound) {
			t.Fatal("empty museum overview remains visible", slug, err)
		}
		_, err = repo.MuseumWorks(ctx, slug, MuseumFilter{Limit: 7})
		if !errors.Is(err, ErrNotFound) {
			t.Fatal("empty museum works remain visible", slug, err)
		}
	}
	page, err := repo.Museums(ctx, MuseumFilter{Query: name, Countries: []string{country}, Limit: 60})
	if err != nil {
		t.Fatal(err)
	}
	for _, i := range page.Items {
		if i.Slug == slug || i.WorkCount == 0 {
			t.Fatal("empty museum remains in directory", i.Slug)
		}
	}
	if page.Total != 0 || len(page.Items) != 0 || page.NextCursor != "" {
		t.Fatal("empty museum counted or paginated", page.Total)
	}
	t.Log("empty review museum excluded:", slug, country)

	// A collection with review works and institution geography stays visible
	// even without a separate visitor venue. Missing venue data is not emptiness.
	err = tx.QueryRow(ctx, `SELECT i.slug,i.name,trim(p.country_code) FROM institutions i
 JOIN places p ON p.id=i.place_id WHERE i.status='review' AND i.canonical_institution_id IS NULL
 AND EXISTS(SELECT 1 FROM artworks aw WHERE aw.current_institution_id=i.id AND aw.status='review')
 AND NOT EXISTS(SELECT 1 FROM institution_venues v WHERE v.institution_id=i.id)
 ORDER BY i.id LIMIT 1`).Scan(&slug, &name, &country)
	if err != nil {
		t.Fatal(err)
	}
	page, err = repo.Museums(ctx, MuseumFilter{Query: name, Countries: []string{country}, Limit: 60})
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, i := range page.Items {
		found = found || i.Slug == slug && i.WorkCount > 0
	}
	if !found {
		t.Fatal("nonempty museum with institution geography hidden", slug)
	}
	t.Log("nonempty review museum without venue remains visible:", slug, country)
}
