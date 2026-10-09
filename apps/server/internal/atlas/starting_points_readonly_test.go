package atlas

import (
	"context"
	"encoding/json"
	"net/url"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func TestStartingPointConfiguration(t *testing.T) {
	for _, p := range Presets() {
		t.Run(p.ID, func(t *testing.T) {
			if strings.TrimSpace(p.StartingScope) == "" {
				t.Fatal("missing visible scope")
			}
			if p.CoverArtworkID == "" || p.Focus.ArtworkIdentities[p.CoverArtworkID] == "" {
				t.Fatal("every starting point needs a cover and its portable artwork identity")
			}
			f := Filter{PresetID: p.ID, Range: p.Context, Limit: 150, Countries: p.StartingCountries, Creators: p.StartingCreators}
			if err := f.Validate(); err != nil {
				t.Fatal(err)
			}
			seen := map[string]bool{}
			for _, country := range p.StartingCountries {
				if country != strings.ToLower(strings.TrimSpace(country)) || seen[country] {
					t.Fatal("noncanonical or duplicate country")
				}
				seen[country] = true
			}
			if len(p.Focus.ArtworkTraditions) > 0 && len(p.StartingCountries) > 0 {
				t.Fatal("hard country defaults exclude unlinked object traditions")
			}
			if !p.Focus.SelectedBooks || !p.Focus.SelectedEvents {
				t.Fatal("themed books and events need an explicit reviewed selection")
			}
		})
	}
}

// All queries use existing records under a database-enforced read-only snapshot.
func TestStartingPointsReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only DSN required")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Minute)
	defer cancel()
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	covers, err := (&Repository{db: db}).IllustratedPresets(ctx)
	if err != nil {
		t.Fatal(err)
	}
	for _, p := range covers {
		if p.Cover == nil || p.Cover.MediaURL == "" || p.Cover.EndYear > 1970 {
			t.Fatalf("%s: missing or ineligible starting-point cover", p.ID)
		}
	}
	summaries := []map[string]any{}
	for _, p := range Presets() {
		t.Run(p.ID, func(t *testing.T) {
			tx, err := db.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback(ctx)
			recorder := &discoveryPlanDB{atlasDB: tx}
			repo := &Repository{db: recorder}
			f := Filter{PresetID: p.ID, Range: p.Context, Limit: 150, Highlights: p.StartingHighlights, Creators: p.StartingCreators, Selection: true, Types: []string{"artwork", "book", "event"}, Entities: map[string]url.Values{"artwork": {"image_only": {"true"}}}}
			broad, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			f.Countries = p.StartingCountries
			f.CountryScope = "artwork"
			focused := broad
			if len(f.Countries) > 0 {
				recorder.statements = nil
				focused, err = repo.List(ctx, f)
				if err != nil {
					t.Fatal(err)
				}
			}
			if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" && slices.Contains([]string{"civil-rights", "french-revolution", "science", "renaissance", "silk-roads", "islamic-learning", "byzantium"}, p.ID) {
				if err := os.MkdirAll(dir, 0700); err != nil {
					t.Fatal(err)
				}
				for i, statement := range slices.Clone(recorder.statements) {
					var plan []byte
					if err := tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+statement.query, statement.args...).Scan(&plan); err != nil {
						t.Fatal(err)
					}
					if err := os.WriteFile(filepath.Join(dir, p.ID+"-"+Definitions[i].Key+"-plan.json"), plan, 0600); err != nil {
						t.Fatal(err)
					}
				}
			}
			for _, creator := range p.StartingCreators {
				role, key, _ := strings.Cut(creator, ":")
				var exists bool
				query := `SELECT EXISTS(SELECT 1 FROM artists WHERE slug=$1 AND status<>'archived')`
				if role == "author" {
					query = `SELECT EXISTS(SELECT 1 FROM book_creators WHERE id=$1)`
				}
				if err := tx.QueryRow(ctx, query, key).Scan(&exists); err != nil || !exists {
					t.Fatalf("missing reviewed creator %s: %v", creator, err)
				}
			}
			before, after := []int{}, []int{}
			lost := map[string][]string{}
			for i, lane := range focused.Lanes {
				if lane.Key == "artwork" && lane.Total < 100 {
					t.Errorf("every starting category needs at least 100 relevant illustrated artworks; got %d", lane.Total)
				}
				before = append(before, broad.Lanes[i].Total)
				after = append(after, lane.Total)
				if lane.Key != "artwork" && lane.Total != broad.Lanes[i].Total {
					t.Fatal("country starting focus removed book/event context")
				}
				if lane.Total > broad.Lanes[i].Total || len(lane.Items) > 150 {
					t.Fatal("scope grew or page unbounded")
				}
				if broad.Lanes[i].Total > 0 && lane.Total == 0 {
					t.Errorf("%s default lost entire layer", lane.Key)
				}
				for _, item := range lane.Items {
					if item.StartYear > f.End || item.EndYear < f.Start {
						t.Fatal("out of range")
					}
					if p.ID == "civil-rights" && strings.Contains(item.Context, "Thomas Weeks Barrett") {
						t.Fatal("unrelated contemporary returned")
					}
					if lane.Key == "book" && p.Focus.SelectedBooks && !slices.Contains(p.Focus.Related["book"], item.ID) && !slices.Contains(p.Focus.Context["book"], item.ID) {
						t.Fatal("book outside reviewed selection")
					}
					if lane.Key == "event" && !slices.Contains(p.Focus.Related["event"], item.ID) && !slices.Contains(p.Focus.Context["event"], item.ID) {
						t.Fatal("event outside reviewed sequence")
					}
					if lane.Key == "artwork" && item.EndYear > 1970 {
						t.Fatal("artwork cutoff bypassed")
					}
					if lane.Key == "artwork" && item.MediaURL == "" {
						t.Fatal("image missing")
					}
				}
				if lane.Key != "artwork" && broad.Lanes[i].Total <= 150 {
					for _, item := range broad.Lanes[i].Items {
						if slices.Contains(p.Focus.Related[lane.Key], item.ID) && !slices.ContainsFunc(lane.Items, func(other Item) bool { return other.ID == item.ID }) {
							lost[lane.Key] = append(lost[lane.Key], item.ID)
						}
					}
				}
			}
			if len(lost) > 0 {
				t.Errorf("country defaults lost reviewed core records: %v", lost)
			}
			summaries = append(summaries, map[string]any{"id": p.ID, "scope": p.StartingScope, "countries": p.StartingCountries, "creators": p.StartingCreators, "highlights": p.StartingHighlights, "full": before, "starting": after, "missing_core": lost})
			t.Logf("full=%v starting=%v missing-core=%v", before, after, lost)
		})
	}
	if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" {
		if err := os.MkdirAll(dir, 0700); err != nil {
			t.Fatal(err)
		}
		raw, _ := json.MarshalIndent(summaries, "", "  ")
		if err := os.WriteFile(filepath.Join(dir, "starting-points.json"), raw, 0600); err != nil {
			t.Fatal(err)
		}
	}
}

func TestCountryScopeValidationAndCursor(t *testing.T) {
	f := Filter{Range: Bounds, Limit: 60, Countries: []string{"france"}, CountryScope: "artwork"}
	if err := f.Validate(); err != nil {
		t.Fatal(err)
	}
	token := encodeCursor(Item{ID: "book-one", StartYear: 1900}, f, "book")
	f.CountryScope = "all"
	if _, err := decodeCursor(token, f, "book"); err == nil {
		t.Fatal("country scope crossed cursor")
	}
	f.CountryScope = "invalid"
	if f.Validate() == nil {
		t.Fatal("invalid country scope accepted")
	}
}

func TestPainterPaintingsReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only DSN required")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	recorder := &discoveryPlanDB{atlasDB: db}
	repo := &Repository{db: recorder}
	f := Filter{Range: Range{1800, 1950}, Types: []string{"artwork"}, Selection: true, Limit: 60, Highlights: false, Entities: map[string]url.Values{"artwork": {"painter": {"claude-monet"}, "popular": {"false"}, "women": {"false"}, "image_only": {"true"}}}}
	data, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	if len(data.Lanes) != 1 || len(data.Lanes[0].Items) != 60 || data.Lanes[0].NextCursor == "" {
		t.Fatal("missing bounded painter works")
	}
	for _, item := range data.Lanes[0].Items {
		if !strings.Contains(item.Context, "Monet") || item.MediaURL == "" || item.EndYear > 1970 {
			t.Fatal("wrong scope or image")
		}
	}
	f.After = map[string]string{"artwork": data.Lanes[0].NextCursor}
	next, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	if len(next.Lanes[0].Items) == 0 || len(next.Lanes[0].Items) > 60 || next.Total != data.Total {
		t.Fatal("invalid second page")
	}
	for _, item := range next.Lanes[0].Items {
		if slices.ContainsFunc(data.Lanes[0].Items, func(first Item) bool { return first.ID == item.ID }) {
			t.Fatal("overlapping artwork pages")
		}
	}
	statement := recorder.statements[0]
	var plan []byte
	if err := db.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+statement.query, statement.args...).Scan(&plan); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(plan), "artwork_artists_artist_work_idx") || !strings.Contains(string(plan), "artworks_pkey") {
		t.Fatal("selected painter needs indexed artwork lookups")
	}
	if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" {
		if err := os.MkdirAll(dir, 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(dir, "painter-paintings-plan.json"), plan, 0600); err != nil {
			t.Fatal(err)
		}
	}
}
