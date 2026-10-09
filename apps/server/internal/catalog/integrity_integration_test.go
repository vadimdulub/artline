package catalog

import (
	"context"
	"fmt"
	"github.com/vadimdulub/artline/apps/server/internal/testdb"
	"os"
	"testing"
)

func TestTimelineDensityIntegrity(t *testing.T) {
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
	dense, err := repo.Timeline(ctx, TimelineFilter{StartYear: 1890, EndYear: 1900, Query: "Density fixture"})
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
	filtered, err := repo.Timeline(ctx, TimelineFilter{StartYear: 1890, EndYear: 1900, Query: "Density fixture", Regions: []string{"northern-europe", "eastern-asia"}})
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

}
