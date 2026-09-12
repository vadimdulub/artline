package catalog

import (
	"context"
	"os"
	"testing"

	"github.com/vadimdulub/artline/apps/server/internal/testdb"
)

func TestRepositoryReadsSeededCatalogue(t *testing.T) {
	databaseURL := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if databaseURL == "" {
		t.Skip("ARTLINE_TEST_DATABASE_URL is not set")
	}
	pool, err := testdb.Open(t, databaseURL)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	repository := NewRepository(pool)

	for _, slug := range []string{"giotto", "jan-van-eyck", "leonardo-da-vinci", "artemisia-gentileschi", "rembrandt", "katsushika-hokusai", "claude-monet", "p-s-kroyer", "anna-ancher", "hilma-af-klint", "edvard-munch"} {
		record, err := repository.ArtistBySlug(context.Background(), slug, true)
		if err != nil {
			t.Fatalf("%s: %v", slug, err)
		}
		if len(record.Artworks) == 0 {
			t.Fatalf("%s has no illustrated selection", slug)
		}
		for _, work := range record.Artworks {
			if work.MediaURL == nil || work.AltText == nil || len(work.Citations) == 0 || work.Status != "review" {
				t.Fatalf("%s: artwork is missing review image metadata or citations", work.Slug)
			}
		}
		if slug == "katsushika-hokusai" {
			work := record.Artworks[0]
			if work.AccessionNumber == nil || *work.AccessionNumber != "JP1847" || work.CreationPlaceDisplay != nil || work.CreationPlaceUnknownReason == nil {
				t.Fatal("Hokusai must identify the specific Met impression without inventing a creation place")
			}
		}
	}

	timeline, err := repository.Timeline(context.Background(), TimelineFilter{StartYear: 1100, EndYear: 2000, Status: "review"})
	if err != nil {
		t.Fatal(err)
	}
	if timeline.Total == 0 || len(timeline.Items) == 0 {
		t.Fatal("expected a non-empty initial review timeline")
	}

	facets, err := repository.Facets(context.Background(), true)
	if err != nil {
		t.Fatal(err)
	}
	if len(facets.Movements) == 0 || len(facets.Countries) == 0 || len(facets.Regions) == 0 {
		t.Fatal("expected movement, country and region facets")
	}
	for _, tc := range []struct {
		regions []string
		country string
		want    int
	}{
		{[]string{"northern-europe"}, "", 4},
		{[]string{"eastern-asia"}, "", 1},
		{[]string{"northern-europe", "eastern-asia", "northern-europe"}, "", 5},
		{[]string{"northern-europe", "eastern-asia"}, "JP", 1},
		{[]string{"unrepresented-region"}, "", 0},
	} {
		result, err := repository.Timeline(context.Background(), TimelineFilter{StartYear: 1100, EndYear: 2000, Status: "review", Regions: tc.regions, Country: tc.country})
		if err != nil {
			t.Fatal(err)
		}
		if result.Total != tc.want || len(result.Items) != tc.want {
			t.Fatalf("regions=%v country=%s got %d/%d want %d", tc.regions, tc.country, result.Total, len(result.Items), tc.want)
		}
	}
	public, err := repository.Timeline(context.Background(), TimelineFilter{StartYear: 1100, EndYear: 2000, Status: "published", Regions: []string{"northern-europe", "eastern-asia"}})
	if err != nil || public.Total != 0 {
		t.Fatalf("multi-region query exposed review records: %v, %v", public, err)
	}

	validation, err := repository.ValidateArtistForPublication(context.Background(), timeline.Items[0].ID)
	if err != nil {
		t.Fatal(err)
	}
	if validation.Ready || len(validation.Issues) == 0 {
		t.Fatal("expected the starter research record to remain blocked from publication")
	}
}
