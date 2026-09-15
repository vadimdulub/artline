package catalog

import (
	"context"
	"errors"
	"os"
	"testing"

	"github.com/vadimdulub/artline/apps/server/internal/testdb"
)

func TestMultipleDiscoveryFilters(t *testing.T) {
	dsn := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if dsn == "" {
		t.Skip("test database not configured")
	}
	pool, err := testdb.Open(t, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	ctx := context.Background()
	repo := NewRepository(pool)
	f := TimelineFilter{StartYear: 1100, EndYear: 2000, Painters: []string{"claude-monet", "rembrandt"}}
	p, err := repo.Timeline(ctx, f)
	if err != nil || p.Total != 2 {
		t.Fatalf("OR painters: %+v %v", p, err)
	}
	f.Movements = []string{"impressionism"}
	p, err = repo.Timeline(ctx, f)
	if err != nil || p.Total != 1 || p.Items[0].Slug != "claude-monet" {
		t.Fatalf("AND movements: %+v %v", p, err)
	}
	f.Movements = []string{"impressionism", "baroque"}
	f.Countries = []string{"FR", "NL"}
	p, err = repo.Timeline(ctx, f)
	if err != nil || p.Total != 2 {
		t.Fatalf("OR movement/country sets: %+v %v", p, err)
	}
	f.Countries = []string{"FR"}
	p, err = repo.Timeline(ctx, f)
	if err != nil || p.Total != 1 {
		t.Fatalf("AND country: %+v %v", p, err)
	}
	f.WorkTypes = []string{"painting", "fresco"}
	p, err = repo.Timeline(ctx, f)
	if err != nil || p.Total != 1 {
		t.Fatalf("work types: %+v %v", p, err)
	}
	f.Status = "published"
	p, err = repo.Timeline(ctx, f)
	if err != nil || p.Total != 0 {
		t.Fatalf("visibility: %+v %v", p, err)
	}
	mf := MuseumFilter{Limit: 1, Artists: []string{"rembrandt", "claude-monet"}, WorkTypes: []string{"painting", "fresco"}}
	first, err := repo.MuseumWorks(ctx, "the-met", mf, true)
	if err != nil || first.Total != 2 || first.NextCursor == "" {
		t.Fatalf("museum OR: %+v %v", first, err)
	}
	mf.Cursor = first.NextCursor
	mf.Artists = []string{"claude-monet", "rembrandt", "rembrandt"}
	second, err := repo.MuseumWorks(ctx, "the-met", mf, true)
	if err != nil || len(second.Items) != 1 || second.Items[0].ID == first.Items[0].ID {
		t.Fatalf("canonical cursor: %+v %v", second, err)
	}
	mf.Artists = []string{"claude-monet"}
	if _, err = repo.MuseumWorks(ctx, "the-met", mf, true); !errors.Is(err, ErrMuseumFilter) {
		t.Fatalf("changed cursor accepted: %v", err)
	}
	mf.Cursor = ""
	mf.Movements = []string{"impressionism"}
	mf.Limit = 24
	museums, err := repo.Museums(ctx, mf, true)
	if err != nil || museums.Total < 1 {
		t.Fatalf("museum painter discovery: %+v %v", museums, err)
	}
	options, err := repo.PainterOptions(ctx, "Monet", "the-met", []string{"rembrandt"}, true, false, false)
	if err != nil || len(options.Items) != 1 || options.Items[0].Slug != "claude-monet" || len(options.Selected) != 1 || options.Selected[0].Slug != "rembrandt" {
		t.Fatalf("bounded search/resolution: %+v %v", options, err)
	}
	options, err = repo.PainterOptions(ctx, "", "", []string{"rembrandt"}, false, false, false)
	if err != nil || len(options.Items) != 0 || len(options.Selected) != 0 {
		t.Fatalf("options visibility: %+v %v", options, err)
	}
	options, err = repo.PainterOptions(ctx, "", "", nil, true, false, false)
	if err != nil || len(options.Items) > 30 {
		t.Fatalf("bounded results: %+v %v", options, err)
	}
	if _, err = pool.Exec(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status)
 SELECT 'option-fixture-'||n,'Option fixture '||n,'Option fixture '||n,'option fixture '||n,1800,1900,'1800-1900','life','review' FROM generate_series(1,60) n`); err != nil {
		t.Fatal(err)
	}
	options, err = repo.PainterOptions(ctx, "Option fixture", "", []string{"claude-monet"}, true, false, false)
	if err != nil || len(options.Items) != 30 || !options.HasMore || len(options.Selected) != 1 {
		t.Fatalf("search cap: %+v %v", options, err)
	}
	if _, err = pool.Exec(ctx, `UPDATE artists SET status='published' WHERE slug='claude-monet'; UPDATE movements SET status='review' WHERE slug='impressionism'`); err != nil {
		t.Fatal(err)
	}
	f = TimelineFilter{StartYear: 1100, EndYear: 2000, Status: "published", Painters: []string{"claude-monet"}}
	p, err = repo.Timeline(ctx, f)
	if err != nil || p.Total != 1 || p.Items[0].Movement.Slug != "unclassified" {
		t.Fatalf("private movement leaked: %+v %v", p, err)
	}
	f.Movements = []string{"impressionism"}
	p, err = repo.Timeline(ctx, f)
	if err != nil || p.Total != 0 {
		t.Fatalf("private movement filter leak: %+v %v", p, err)
	}
	facets, err := repo.DiscoveryFacets(ctx, false, false, false)
	if err != nil || len(facets.Movements) != 0 {
		t.Fatalf("private movement facet leak: %+v %v", facets, err)
	}
}
