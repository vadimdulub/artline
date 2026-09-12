package catalog

import (
	"context"
	"os"
	"testing"

	"github.com/vadimdulub/artline/apps/server/internal/testdb"
)

func TestPublicationChecksCreationAndSelection(t *testing.T) {
	db := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if db == "" {
		t.Skip("database URL not set")
	}
	pool, err := testdb.Open(t, db)
	if err != nil {
		t.Fatal(err)
	}
	ctx := context.Background()
	repo := NewRepository(pool)
	var artist, work string
	if err = pool.QueryRow(ctx, `SELECT a.id::text,aw.id::text FROM artists a JOIN artwork_artists aa ON aa.artist_id=a.id JOIN artworks aw ON aw.id=aa.artwork_id WHERE a.slug='giotto' ORDER BY aw.id LIMIT 1`).Scan(&artist, &work); err != nil {
		t.Fatal(err)
	}
	check := func(want bool) {
		t.Helper()
		report, err := repo.ValidateArtistForPublication(ctx, artist)
		if err != nil {
			t.Fatal(err)
		}
		got := false
		for _, i := range report.Issues {
			if i.Code == "ARTWORK_CONTENT_SCOPE" {
				got = true
			}
		}
		if got != want {
			t.Fatalf("scope issue=%v want %v: %+v", got, want, report)
		}
	}
	// Non-representative works must not bypass the gate.
	if _, err = pool.Exec(ctx, `UPDATE artwork_artists SET representative_order=NULL WHERE artwork_id=$1`, work); err != nil {
		t.Fatal(err)
	}
	if _, err = pool.Exec(ctx, `UPDATE artworks SET status='published',creation_year_start=1971,creation_year_end=1971,date_precision='exact' WHERE id=$1`, work); err != nil {
		t.Fatal(err)
	}
	check(true)
	if _, err = pool.Exec(ctx, `UPDATE artworks SET creation_year_start=1970,creation_year_end=1970 WHERE id=$1`, work); err != nil {
		t.Fatal(err)
	}
	check(false)
	if _, err = pool.Exec(ctx, `UPDATE artwork_location_assertions SET review_state='rejected' WHERE artwork_id=$1 AND claim_type='holding'`, work); err != nil {
		t.Fatal(err)
	}
	check(true)
}
