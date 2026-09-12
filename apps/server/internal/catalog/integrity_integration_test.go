package catalog

import (
	"context"
	"errors"
	"fmt"
	"github.com/vadimdulub/artline/apps/server/internal/testdb"
	"os"
	"testing"
)

func TestTimelineDensityAndRevisionIntegrity(t *testing.T) {
	url := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if url == "" {
		t.Skip("ARTLINE_TEST_DATABASE_URL is not set")
	}
	ctx := context.Background()
	pool, err := testdb.Open(t, url)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.Begin(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	repo := &Repository{db: tx}
	// All fixture writes roll back. No existing catalogue record is changed.
	for i := 0; i < 305; i++ {
		_, err = tx.Exec(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status)
  VALUES($1,$2,$2,lower($2),1800,1900,'1800–1900','life','draft')`, fmt.Sprintf("artline-test-density-%d", i), fmt.Sprintf("Density fixture %d", i))
		if err != nil {
			t.Fatal(err)
		}
	}
	dense, err := repo.Timeline(ctx, TimelineFilter{StartYear: 1890, EndYear: 1900, Status: "draft", Query: "Density fixture"})
	if err != nil {
		t.Fatal(err)
	}
	if dense.Mode != "density" || len(dense.Items) != 0 || dense.Total != 305 {
		t.Fatalf("unexpected density response: %+v", dense)
	}
	count := 0
	for _, bin := range dense.Bins {
		count += bin.Count
		if bin.StartYear < 1890 || bin.EndYear > 1900 {
			t.Fatalf("offscreen density bin: %+v", bin)
		}
	}
	if count != dense.Total {
		t.Fatalf("bin total %d != count %d", count, dense.Total)
	}
	// Give every fixture associations in both regions and two relationship
	// types. EXISTS must not duplicate either result totals or density bins.
	_, err = tx.Exec(ctx, `INSERT INTO artist_countries(artist_id,country_code,relationship_type)
      SELECT id,country,relationship FROM artists
      CROSS JOIN (VALUES ('DK'),('JP')) AS c(country)
      CROSS JOIN (VALUES ('birth'),('active')) AS r(relationship)
      WHERE slug LIKE 'artline-test-density-%'`)
	if err != nil {
		t.Fatal(err)
	}
	filtered, err := repo.Timeline(ctx, TimelineFilter{StartYear: 1890, EndYear: 1900, Status: "draft", Query: "Density fixture", Regions: []string{"northern-europe", "eastern-asia"}})
	if err != nil {
		t.Fatal(err)
	}
	count = 0
	for _, bin := range filtered.Bins {
		count += bin.Count
	}
	if filtered.Mode != "density" || filtered.Total != 305 || count != 305 {
		t.Fatalf("multi-region density duplicates or loses painters: total=%d bins=%d", filtered.Total, count)
	}

	input := ArtistInput{Slug: "artline-test-revisions", DisplayName: "Revision fixture", SortName: "Fixture", EntityType: "person", TimelineStartYear: 1095, TimelineEndYear: 1120, TimelineDisplay: "1095–1120", TimelineBasis: "life", Status: "draft"}
	created, err := repo.CreateArtist(ctx, input)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := repo.ArtistBySlug(ctx, input.Slug, false); !errors.Is(err, ErrNotFound) {
		t.Fatalf("draft leaked into public read: %v", err)
	}
	input.ExpectedRevision = created.Revision
	input.Slug = "artline-test-revisions-renamed"
	updated, err := repo.UpdateArtist(ctx, created.ID, input)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := repo.UpdateArtist(ctx, created.ID, input); !errors.Is(err, ErrRevisionConflict) {
		t.Fatalf("stale update accepted: %v", err)
	}
	redirected, err := repo.ArtistBySlug(ctx, "artline-test-revisions", true)
	if err != nil || redirected.Slug != input.Slug {
		t.Fatalf("old slug not preserved: %v", err)
	}
	if _, err := repo.SetArchived(ctx, created.ID, true, created.Revision); !errors.Is(err, ErrRevisionConflict) {
		t.Fatalf("stale archive accepted: %v", err)
	}
	archived, err := repo.SetArchived(ctx, created.ID, true, updated.Revision)
	if err != nil {
		t.Fatal(err)
	}
	restored, err := repo.SetArchived(ctx, created.ID, false, archived.Revision)
	if err != nil {
		t.Fatal(err)
	}
	if restored.Status != "draft" {
		t.Fatalf("restored status %s", restored.Status)
	}
	if _, err := repo.SetPublished(ctx, created.ID, restored.Revision, true); err == nil {
		t.Fatal("incomplete artist was published")
	}
	var audits int
	if err := tx.QueryRow(ctx, "SELECT count(*) FROM audit_log WHERE entity_id=$1", created.ID).Scan(&audits); err != nil || audits < 4 {
		t.Fatalf("audit history missing: %d %v", audits, err)
	}
}
