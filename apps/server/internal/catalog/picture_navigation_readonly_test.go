package catalog

import (
	"context"
	"errors"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"testing"
	"time"
)

func TestPictureNavigationReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only audit DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	repo := NewRepository(db)
	all, err := repo.ArtistWorks(ctx, "claude-monet", ArtistWorksFilter{Limit: 24})
	if err != nil {
		t.Fatal(err)
	}
	f := ArtistWorksFilter{Limit: 24, ImageOnly: true}
	first, err := repo.ArtistWorks(ctx, "claude-monet", f)
	if err != nil {
		t.Fatal(err)
	}
	if first.Total >= all.Total || first.Total < 25 {
		t.Fatal("picture filter did not change a representative real catalogue")
	}
	sum := first.UndatedCount
	for _, year := range first.Years {
		sum += year.Count
	}
	if sum != first.Total {
		t.Fatal("filtered year counts disagree")
	}
	for _, item := range first.Items {
		if item.MediaURL == nil || *item.MediaURL == "" {
			t.Fatal("missing filtered picture")
		}
	}
	f.Cursor = first.NextCursor
	second, err := repo.ArtistWorks(ctx, "claude-monet", f)
	if err != nil {
		t.Fatal(err)
	}
	invalid := f
	invalid.ImageOnly = false
	if _, err = repo.ArtistWorks(ctx, "claude-monet", invalid); !errors.Is(err, ErrChronologyFilter) {
		t.Fatal("cursor crossed image scope")
	}
	f.Cursor = ""
	f.Limit = 1
	f.NeighborOf = first.Items[len(first.Items)-1].ID
	f.Direction = "next"
	next, err := repo.ArtistWorks(ctx, "claude-monet", f)
	if err != nil || len(next.Items) != 1 {
		t.Fatalf("next %v", err)
	}
	if next.Items[0].ID != second.Items[0].ID {
		t.Fatal("skipped page boundary")
	}
	f.NeighborOf = next.Items[0].ID
	f.Direction = "previous"
	previous, err := repo.ArtistWorks(ctx, "claude-monet", f)
	if err != nil || len(previous.Items) != 1 || previous.Items[0].ID != first.Items[len(first.Items)-1].ID {
		t.Fatalf("previous %v", err)
	}
	f.NeighborOf = first.Items[0].ID
	previous, err = repo.ArtistWorks(ctx, "claude-monet", f)
	if err != nil || len(previous.Items) != 0 {
		t.Fatal("first item wrapped")
	}
	// Creator, image and year restrictions apply to the anchor as well as its neighbour.
	foreign, err := repo.ArtistWorks(ctx, "giotto", ArtistWorksFilter{Limit: 1})
	if err != nil || len(foreign.Items) == 0 {
		t.Fatal("missing real second artist")
	}
	f.NeighborOf = foreign.Items[0].ID
	f.Direction = "next"
	outside, err := repo.ArtistWorks(ctx, "claude-monet", f)
	if err != nil || len(outside.Items) != 0 {
		t.Fatal("cross-creator anchor leaked")
	}
	year := 1
	f.Year = &year
	f.NeighborOf = first.Items[0].ID
	outside, err = repo.ArtistWorks(ctx, "claude-monet", f)
	if err != nil || len(outside.Items) != 0 {
		t.Fatal("out-of-year anchor leaked")
	}
}
