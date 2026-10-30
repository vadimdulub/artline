package catalog

import (
	"context"
	"encoding/json"
	"os"
	"sort"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Opt-in regression audit against the catalogue; no fixtures or writes.
func TestMuseumSearchWordsReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("ARTLINE_READONLY_DATABASE_URL is not set")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
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
	for _, query := range []string{"Armenia national gallery", "national gallery Armenia", "  Armenia   national  gallery  "} {
		page, err := repo.Museums(ctx, MuseumFilter{Query: query, Limit: 24})
		if err != nil {
			t.Fatal(err)
		}
		found := false
		for _, museum := range page.Items {
			found = found || museum.Slug == "national-gallery-armenia"
		}
		if !found {
			t.Fatalf("%q did not find Armenia's national gallery", query)
		}
		if !sort.SliceIsSorted(page.Facets.Countries, func(i, j int) bool { return page.Facets.Countries[i].Name < page.Facets.Countries[j].Name }) {
			t.Fatal("country choices are not alphabetical")
		}
	}
	page, err := repo.Museums(ctx, MuseumFilter{Query: "Armenia national gallery", Countries: []string{"FR"}, Limit: 24})
	if err != nil {
		t.Fatal(err)
	}
	if page.Total != 0 || len(page.Items) != 0 {
		t.Fatal("search bypassed the country filter")
	}
}

func TestReviewedMuseumProfilesReadOnly(t *testing.T) {
	dsn, inventory := os.Getenv("ARTLINE_READONLY_DATABASE_URL"), os.Getenv("ARTLINE_MUSEUM_PROFILES_INVENTORY")
	if dsn == "" || inventory == "" {
		t.Skip("Read-only database and reviewed museum inventory are required")
	}
	data, err := os.ReadFile(inventory)
	if err != nil {
		t.Fatal(err)
	}
	var profiles []struct{ Slug, City, Country, Description string }
	if err := json.Unmarshal(data, &profiles); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 6*time.Minute)
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
	for _, profile := range profiles {
		museum, err := repo.Museum(ctx, profile.Slug)
		if err != nil {
			t.Fatalf("%s: %v", profile.Slug, err)
		}
		if museum.Description != profile.Description || museum.Country == nil || *museum.Country != profile.Country || museum.City == nil || *museum.City != profile.City {
			t.Fatalf("%s: reviewed copy or location did not reach the museum response", profile.Slug)
		}
	}
	page, err := repo.Museums(ctx, MuseumFilter{Countries: []string{"AM"}, Limit: 24})
	if err != nil {
		t.Fatal(err)
	}
	found, country := false, false
	for _, museum := range page.Items {
		found = found || museum.Slug == "national-gallery-armenia"
	}
	for _, option := range page.Facets.Countries {
		country = country || option.Slug == "AM"
	}
	if !found || !country {
		t.Fatal("Armenia is missing from the directory or country choices")
	}
	t.Logf("%d reviewed museum profiles and Armenia's country filter passed", len(profiles))
}
