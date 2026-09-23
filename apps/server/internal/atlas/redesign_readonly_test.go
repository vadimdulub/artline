package atlas

import (
	"context"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func TestSharedCreatorsValidate(t *testing.T) {
	for _, values := range [][]string{{"painter:claude-monet", "author:Q535"}, {}} {
		if err := validateCreators(values); err != nil {
			t.Fatal(err)
		}
	}
	for _, values := range [][]string{{"author:"}, {"creator:monet"}, {"painter:monet", "painter:monet"}, {"author:Q1 OR true"}} {
		if validateCreators(values) == nil {
			t.Fatalf("accepted %v", values)
		}
	}
	f := Filter{Range: Bounds, Limit: 60, Creators: []string{"painter:monet"}}
	token := encodeCursor(Item{ID: "one", StartYear: 1900}, f, "book")
	f.Creators = []string{"author:Q1"}
	if _, err := decodeCursor(token, f, "book"); err == nil {
		t.Fatal("cursor crossed creators")
	}
}

// Audit existing records in a read-only transaction. Never insert fixtures.
func TestAllRedesignReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only DSN required")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "10000"
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	tx, err := db.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	recorder := &discoveryPlanDB{atlasDB: tx}
	repo := &Repository{db: recorder}
	painters, err := repo.Creators(ctx, "Monet", nil, true)
	if err != nil {
		t.Fatal(err)
	}
	authors, err := repo.Creators(ctx, "Tolstoy", nil, true)
	if err != nil {
		t.Fatal(err)
	}
	if len(painters.Items) == 0 || len(authors.Items) == 0 {
		t.Fatal("existing creators missing")
	}
	selected := []string{painters.Items[0].Key, authors.Items[0].Key}
	labels, err := repo.Creators(ctx, "not-an-existing-creator", selected, true)
	if err != nil || len(labels.Selected) != 2 || len(labels.Items) != 0 {
		t.Fatalf("selected labels: %+v %v", labels, err)
	}
	choices, err := repo.Creators(ctx, "", nil, true)
	if err != nil || len(choices.Items) != 30 || !choices.HasMore {
		t.Fatal("options must be bounded", err)
	}
	f := Filter{Range: Bounds, Preview: true, Limit: 30, Creators: selected}
	data, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	if len(data.Lanes) != 3 || data.Lanes[0].Total == 0 || data.Lanes[1].Total == 0 || data.Lanes[2].Total == 0 {
		t.Fatalf("missing mixed creators or event context: %+v", data)
	}
	for _, item := range data.Lanes[0].Items {
		if item.MediaURL == "" || !strings.Contains(item.Context, "Monet") {
			t.Fatalf("wrong painter/image: %+v", item)
		}
	}
	for _, item := range data.Lanes[1].Items {
		if !strings.Contains(item.Context, "Tolstoy") {
			t.Fatalf("wrong author: %+v", item)
		}
	}
	f.Creators = selected[:1]
	only, err := repo.List(ctx, f)
	if err != nil || only.Lanes[1].Total != 0 || only.Lanes[2].Total != data.Lanes[2].Total {
		t.Fatal("creator roles or context mixed", err)
	}
	statement := recorder.statements[0]
	var plan []byte
	if err := tx.QueryRow(ctx, `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) `+statement.query, statement.args...).Scan(&plan); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(plan), "artwork_artists_artist_work_idx") || !strings.Contains(string(plan), "artworks_pkey") {
		t.Fatal("creator lost indexed artwork lookups")
	}
	if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" {
		if err := os.MkdirAll(dir, 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(dir, "shared-creator-artwork.json"), plan, 0600); err != nil {
			t.Fatal(err)
		}
	}
	preset, _ := FindPreset("renaissance")
	f = Filter{Range: preset.Context, PresetID: preset.ID, Preview: true, Highlights: true, Limit: 60, Selection: true, Types: []string{"artwork", "book", "event"}, Entities: map[string]url.Values{"artwork": {"image_only": {"true"}}}}
	first, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	if len(first.Lanes[0].Items) != 60 || first.Lanes[0].NextCursor == "" {
		t.Fatal("expected bounded dense artwork page")
	}
	seen := map[string]bool{}
	for _, item := range first.Lanes[0].Items {
		if item.MediaURL == "" {
			t.Fatal("image missing")
		}
		seen[item.ID] = true
	}
	f.After = map[string]string{"artwork": first.Lanes[0].NextCursor}
	second, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	for _, item := range second.Lanes[0].Items {
		if seen[item.ID] || item.MediaURL == "" {
			t.Fatal("duplicate or missing image")
		}
	}
	for _, preview := range []bool{true, false} {
		presets, err := repo.IllustratedPresets(ctx, preview)
		if err != nil {
			t.Fatal(err)
		}
		covers := 0
		for _, preset := range presets {
			if preset.Cover != nil {
				covers++
				visible, err := repo.ArtworkVisible(ctx, preset.Cover.ID, preview)
				if err != nil || !visible || preset.Cover.MediaURL == "" || preset.Cover.Type != "artwork" || preset.Cover.StartYear == 0 || preset.Cover.EndYear == 0 {
					t.Fatal("ineligible preset cover", err)
				}
			}
		}
		if preview && covers != 4 {
			t.Fatalf("expected four existing covers; got %d", covers)
		}
	}
	t.Logf("mixed creators: %d artworks, %d books; Renaissance %d artworks, 60 per page", data.Lanes[0].Total, data.Lanes[1].Total, first.Lanes[0].Total)
}
