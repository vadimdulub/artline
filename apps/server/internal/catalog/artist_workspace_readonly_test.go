package catalog

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Real-catalogue audits use an enforced read-only transaction. No fixtures,
// migrations, temporary tables or publication changes are made here.
func TestArtistWorkspaceReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("set ARTLINE_READONLY_DATABASE_URL")
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
	directory, err := repo.BrowseArtists(ctx, ArtistDirectoryFilter{Sort: "popular", Limit: 24}, true)
	if err != nil || len(directory.Items) != 24 || directory.Total < 1000 || directory.NextCursor == "" {
		t.Fatalf("directory: %d %d %v", directory.Total, len(directory.Items), err)
	}
	next, err := repo.BrowseArtists(ctx, ArtistDirectoryFilter{Sort: "popular", Limit: 24, Cursor: directory.NextCursor}, true)
	if err != nil {
		t.Fatal(err)
	}
	seen := map[string]bool{}
	for _, item := range append(directory.Items, next.Items...) {
		if seen[item.ID] {
			t.Fatal("duplicate directory page item")
		}
		seen[item.ID] = true
		var count int
		if err := tx.QueryRow(ctx, `SELECT count(DISTINCT aw.id) FROM artwork_artists aa JOIN artworks aw ON aw.id=aa.artwork_id WHERE aa.artist_id=$1 AND aw.status<>'archived'`, item.ID).Scan(&count); err != nil || count != item.ArtworkCount {
			t.Fatal("incorrect scoped artwork count", err, item.Name, count, item.ArtworkCount)
		}
	}
	if _, err = repo.BrowseArtists(ctx, ArtistDirectoryFilter{Sort: "name", Limit: 24, Cursor: directory.NextCursor}, true); !errors.Is(err, ErrChronologyFilter) {
		t.Fatal("directory cursor accepted different sort")
	}
	popular, err := repo.BrowseArtists(ctx, ArtistDirectoryFilter{Sort: "popular", Limit: 24, Popular: true}, true)
	if err != nil || popular.Total != 1000 {
		t.Fatal("ranked cohort", popular.Total, err)
	}
	found, err := repo.BrowseArtists(ctx, ArtistDirectoryFilter{Sort: "name", Limit: 24, Query: "Rembrandt", Country: "NL"}, true)
	if err != nil || found.Total == 0 {
		t.Fatal("name/country", err)
	}
	for _, a := range found.Items {
		if !strings.Contains(strings.Join(a.Countries, ","), "NL") {
			t.Fatal("country filter ignored")
		}
	}
	public, err := repo.BrowseArtists(ctx, ArtistDirectoryFilter{Sort: "name", Limit: 24}, false)
	if err != nil {
		t.Fatal(err)
	}
	for _, a := range public.Items {
		if a.Status != "published" {
			t.Fatal("unpublished artist leaked")
		}
	}
	for _, slug := range []string{"rembrandt", "vincent-van-gogh-q5582"} {
		artist, err := repo.ArtistBySlug(ctx, slug, true)
		if err != nil {
			t.Fatal(err)
		}
		if artist.ArtworkCount <= 24 || artist.CollectionCount == 0 || artist.ReferenceBiography == nil {
			t.Fatal("incomplete artist workspace", slug)
		}
		first, err := repo.ArtistWorks(ctx, slug, ArtistWorksFilter{Limit: 24}, true)
		if err != nil || first.Total != artist.ArtworkCount || len(first.Items) != 24 || first.NextCursor == "" {
			t.Fatal("full catalogue missing", slug, err)
		}
		second, err := repo.ArtistWorks(ctx, slug, ArtistWorksFilter{Limit: 24, Cursor: first.NextCursor}, true)
		if err != nil {
			t.Fatal(err)
		}
		seen := map[string]bool{}
		for _, w := range append(first.Items, second.Items...) {
			if seen[w.ID] {
				t.Fatal("duplicate artwork pages")
			}
			seen[w.ID] = true
		}
		collection := artist.Collections[0]
		scoped, err := repo.ArtistWorks(ctx, slug, ArtistWorksFilter{Limit: 24, Museum: collection.Slug}, true)
		if err != nil || scoped.Total != collection.WorkCount {
			t.Fatal("holding count differs from museum-filtered works", slug, scoped.Total, collection.WorkCount, err)
		}
		for _, w := range scoped.Items {
			if w.Holding == nil || w.Holding.ID != collection.ID {
				t.Fatal("museum filter ignored")
			}
		}
		paintings, err := repo.ArtistWorks(ctx, slug, ArtistWorksFilter{Limit: 24, WorkType: "painting"}, true)
		if err != nil || paintings.Total == 0 {
			t.Fatal(err)
		}
		for _, w := range paintings.Items {
			if w.WorkType != "painting" {
				t.Fatal("work type ignored")
			}
		}
		pictures, err := repo.ArtistWorks(ctx, slug, ArtistWorksFilter{Limit: 24, ImageOnly: true}, true)
		if err != nil {
			t.Fatal(err)
		}
		for _, w := range pictures.Items {
			if w.MediaURL == nil {
				t.Fatal("image filter ignored")
			}
		}
		title := first.Items[0].Title
		searched, err := repo.ArtistWorks(ctx, slug, ArtistWorksFilter{Limit: 24, Query: title}, true)
		if err != nil || searched.Total < 1 {
			t.Fatal("title search", err)
		}
		missing, err := repo.ArtistWorks(ctx, slug, ArtistWorksFilter{Limit: 24, Query: "ArtlineNonexistentCatalogueTitle"}, true)
		if err != nil || missing.Total != 0 {
			t.Fatal("empty search", err)
		}
		if _, err = repo.ArtistWorks(ctx, slug, ArtistWorksFilter{Limit: 24, Cursor: first.NextCursor, Museum: collection.Slug}, true); !errors.Is(err, ErrChronologyFilter) {
			t.Fatal("artwork cursor accepted different museum")
		}
		neighbor, err := repo.ArtistWorks(ctx, slug, ArtistWorksFilter{Limit: 1, Museum: collection.Slug, NeighborOf: scoped.Items[0].ID, Direction: "next"}, true)
		if err != nil || len(neighbor.Items) != 1 || neighbor.Items[0].ID != scoped.Items[1].ID {
			t.Fatal("filtered next navigation", err)
		}
		previous, err := repo.ArtistWorks(ctx, slug, ArtistWorksFilter{Limit: 1, Museum: collection.Slug, NeighborOf: scoped.Items[1].ID, Direction: "previous"}, true)
		if err != nil || len(previous.Items) != 1 || previous.Items[0].ID != scoped.Items[0].ID {
			t.Fatal("filtered previous navigation", err)
		}
		var plan []byte
		if err = tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+artistWorksPageQuery, true, artist.ID, "", "", "", nil, false, "", nil, "", "", 25, 0).Scan(&plan); err != nil {
			t.Fatal(err)
		}
		var reports []map[string]any
		if err = json.Unmarshal(plan, &reports); err != nil {
			t.Fatal(err)
		}
		var walk func(map[string]any)
		painterIndex := false
		walk = func(node map[string]any) {
			if node["Relation Name"] == "artworks" && node["Node Type"] == "Seq Scan" {
				t.Error("full artwork scan")
			}
			if strings.Contains(fmtString(node["Index Name"]), "artwork_artists_artist_work") {
				painterIndex = true
			}
			if children, ok := node["Plans"].([]any); ok {
				for _, child := range children {
					walk(child.(map[string]any))
				}
			}
		}
		walk(reports[0]["Plan"].(map[string]any))
		if !painterIndex {
			t.Error("missing indexed painter scope")
		}
		if dir := os.Getenv("ARTLINE_ARTIST_PLAN_DIR"); dir != "" {
			if err = os.WriteFile(filepath.Join(dir, slug+"-plan.json"), plan, 0600); err != nil {
				t.Fatal(err)
			}
		}
		t.Logf("%s: %d artworks, %d sourced collections, plan %.2fms", slug, artist.ArtworkCount, artist.CollectionCount, reports[0]["Execution Time"])
	}
}
func fmtString(value any) string {
	if text, ok := value.(string); ok {
		return text
	}
	return ""
}
