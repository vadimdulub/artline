package catalog

import (
	"context"
	"os"
	"testing"

	"github.com/vadimdulub/artline/apps/server/internal/testdb"
)

func TestPopularDiscoveryIsIndependentOfImagesAndRespectsVisibility(t *testing.T) {
	dsn := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if dsn == "" {
		t.Skip("ARTLINE_TEST_DATABASE_URL is not set")
	}
	pool, err := testdb.Open(t, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	ctx := context.Background()
	repo := NewRepository(pool)
	// Hokusai is a curated seed inclusion even when no Pantheon cohort is imported.
	filter := TimelineFilter{StartYear: 1100, EndYear: 2000, PopularOnly: true}
	result, err := repo.Timeline(ctx, filter)
	if err != nil || result.Total != 1 || result.Items[0].Slug != "katsushika-hokusai" {
		t.Fatalf("popular: %+v, %v", result, err)
	}
	_, err = pool.Exec(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status)
 VALUES('popular-no-images','Popular no images','Popular no images','popular no images',1600,1660,'1600–1660','life','review');
 INSERT INTO artist_discovery_selection(artist_id,is_popular,basis,source_url)
 SELECT id,true,'Test explicit selection','https://example.org/selection' FROM artists WHERE slug='popular-no-images'`)
	if err != nil {
		t.Fatal(err)
	}
	result, err = repo.Timeline(ctx, filter)
	if err != nil || result.Total != 2 {
		t.Fatalf("missing-image painter excluded: %+v %v", result, err)
	}
	filter.Query = "Popular no images"
	result, err = repo.Timeline(ctx, filter)
	if err != nil || result.Total != 1 || result.Items[0].ArtworkCount != 0 {
		t.Fatalf("search: %+v %v", result, err)
	}
	filter.Query = ""
	filter.Regions = []string{"eastern-asia"}
	result, err = repo.Timeline(ctx, filter)
	if err != nil || result.Total != 1 {
		t.Fatalf("region: %+v %v", result, err)
	}
	facets, err := repo.DiscoveryFacets(ctx, true, true, false)
	if err != nil || len(facets.Countries) != 1 || facets.Countries[0].Slug != "JP" {
		t.Fatalf("popular facets: %+v %v", facets, err)
	}
	filter.Status = "published"
	result, err = repo.Timeline(ctx, filter)
	if err != nil || result.Total != 0 {
		t.Fatalf("publication leak: %+v %v", result, err)
	}
}
