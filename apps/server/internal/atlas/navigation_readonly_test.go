package atlas

import (
	"context"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"testing"
	"time"
)

func TestNeighborValidation(t *testing.T) {
	base := Filter{Range: Bounds, Limit: 1, Types: []string{"book"}, NeighborOf: "wd-q119224", Direction: "next"}
	if err := base.Validate(); err != nil {
		t.Fatal(err)
	}
	for _, change := range []func(*Filter){
		func(f *Filter) { f.Direction = "sideways" }, func(f *Filter) { f.NeighborOf = "" }, func(f *Filter) { f.Limit = 2 },
		func(f *Filter) { f.Types = []string{"book", "artwork"} }, func(f *Filter) { f.Types = []string{"artwork"} },
		func(f *Filter) { f.After = map[string]string{"book": "cursor"} }, func(f *Filter) { f.PresetID = "invented" },
	} {
		f := base
		change(&f)
		if f.Validate() == nil {
			t.Fatalf("accepted invalid neighbour %+v", f)
		}
	}
}

// Every query uses the real catalogue in read-only mode; no fixtures are inserted.
func TestNavigationReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only audit DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	repo := NewRepository(db)
	for _, kind := range []string{"book", "event", "artwork"} {
		t.Run(kind, func(t *testing.T) {
			f := Filter{Range: Range{1780, 1950}, Limit: 24, Preview: true, Types: []string{kind}, Highlights: true}
			first, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			lane := first.Lanes[0]
			if len(lane.Items) < 2 || lane.NextCursor == "" {
				t.Fatalf("need real multi-page %s sample", kind)
			}
			f.After = map[string]string{kind: lane.NextCursor}
			page, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			if len(page.Lanes[0].Items) == 0 {
				t.Fatal("empty second page")
			}
			previous, next := lane.Items[len(lane.Items)-1], page.Lanes[0].Items[0]
			f.After = nil
			f.Limit = 1
			f.NeighborOf = previous.ID
			f.Direction = "next"
			out, err := repo.List(ctx, f)
			if err != nil || len(out.Lanes) != 1 || len(out.Lanes[0].Items) != 1 {
				t.Fatalf("next: %+v %v", out, err)
			}
			if out.Lanes[0].Items[0].ID != next.ID {
				t.Fatal("next skipped page boundary")
			}
			f.NeighborOf = next.ID
			f.Direction = "previous"
			out, err = repo.List(ctx, f)
			if err != nil || len(out.Lanes[0].Items) != 1 || out.Lanes[0].Items[0].ID != previous.ID {
				t.Fatalf("previous: %+v %v", out, err)
			}
			f.NeighborOf = lane.Items[0].ID
			out, err = repo.List(ctx, f)
			if err != nil || len(out.Lanes[0].Items) != 0 {
				t.Fatalf("first record wrapped: %v", err)
			}
			f.NeighborOf = "missing"
			if kind == "artwork" {
				f.NeighborOf = "00000000-0000-0000-0000-000000000000"
			}
			out, err = repo.List(ctx, f)
			if err != nil || len(out.Lanes[0].Items) != 0 {
				t.Fatalf("missing anchor leaked: %v", err)
			}
			if kind == "artwork" {
				for _, item := range lane.Items {
					var image bool
					err = db.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=$1 AND m.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$')`, item.ID).Scan(&image)
					if err != nil || !image {
						t.Fatalf("unillustrated artwork %s: %v", item.ID, err)
					}
				}
			}
		})
	}
}
