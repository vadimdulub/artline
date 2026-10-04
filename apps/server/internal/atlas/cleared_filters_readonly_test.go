package atlas

import (
	"context"
	"encoding/json"
	"net/url"
	"os"
	"slices"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Exercise the real broadening actions that failed in the browser, using an
// enforced read-only snapshot. No fixtures or migrations touch the catalogue.
func TestClearedPresetFiltersReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue DSN required")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	for _, id := range []string{"renaissance", "civil-rights"} {
		t.Run(id, func(t *testing.T) {
			tx, err := db.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback(ctx)
			p, _ := FindPreset(id)
			recorder := &discoveryPlanDB{atlasDB: tx}
			repo := &Repository{db: recorder}
			f := Filter{PresetID: id, Range: p.Context, Preview: true, Limit: 30, Selection: true, Types: []string{"artwork", "book", "event"}, Highlights: p.StartingHighlights, Creators: p.StartingCreators, Countries: p.StartingCountries, CountryScope: "artwork", Entities: map[string]url.Values{"artwork": {"image_only": {"true"}}}}
			narrow, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			if id == "renaissance" {
				f.Countries = nil
			} else {
				f.Creators = nil
			}
			recorder.statements = nil
			broad, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			if broad.Lanes[0].Total <= narrow.Lanes[0].Total {
				t.Fatal("clearing recommendations did not broaden the artwork scope")
			}
			if id == "civil-rights" && broad.Lanes[0].Total > 500 {
				// This production regression spent seconds fetching thousands of
				// wide image/evidence heap rows after clearing the creators. Check
				// the actual plan on the real catalogue, not a tiny seed fixture.
				statement := recorder.statements[0]
				var raw []byte
				if err := tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+statement.query, statement.args...).Scan(&raw); err != nil {
					t.Fatal(err)
				}
				var plans []map[string]any
				if err := json.Unmarshal(raw, &plans); err != nil {
					t.Fatal(err)
				}
				covered := map[string]bool{}
				var visit func(map[string]any)
				visit = func(node map[string]any) {
					if node["Node Type"] == "Index Only Scan" {
						if name, ok := node["Index Name"].(string); ok {
							covered[name] = true
						}
					}
					if children, ok := node["Plans"].([]any); ok {
						for _, child := range children {
							visit(child.(map[string]any))
						}
					}
				}
				visit(plans[0]["Plan"].(map[string]any))
				for _, index := range []string{"media_assets_atlas_deliverable_idx", "artwork_atlas_holding_evidence_idx"} {
					if !covered[index] {
						t.Errorf("broad illustrated filter did not use covering index %s", index)
					}
				}
			}
			for i := 1; i < len(broad.Lanes); i++ {
				if broad.Lanes[i].Total != narrow.Lanes[i].Total {
					t.Fatal("artwork-only clearing changed context lanes")
				}
			}
			first := broad.Lanes[0]
			if first.NextCursor == "" {
				t.Fatal("missing bounded next page")
			}
			f.After = map[string]string{"artwork": first.NextCursor}
			next, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			second := next.Lanes[0]
			if second.Total != first.Total || !slices.Equal(first.Density, second.Density) || len(second.Items) != 30 {
				t.Fatal("page changed broad scope")
			}
			last := first.Items[len(first.Items)-1]
			for _, v := range second.Items {
				if compareGalleryItems(v, last) <= 0 {
					t.Fatal("duplicate or unordered page")
				}
				last = v
			}
		})
	}
	t.Run("large-highlight-geography", func(t *testing.T) {
		p, _ := FindPreset("empire")
		recorder := &discoveryPlanDB{atlasDB: db}
		repo := &Repository{db: recorder}
		f := Filter{PresetID: p.ID, Range: p.Context, Preview: true, Limit: 30,
			Types: []string{"artwork"}, Highlights: p.StartingHighlights,
			Countries: p.StartingCountries, CountryScope: "artwork"}
		data, err := repo.List(ctx, f)
		if err != nil {
			t.Fatal(err)
		}
		if len(data.Lanes) != 1 || len(data.Lanes[0].Items) > 30 {
			t.Fatal("invalid bounded highlight page")
		}
		statement := recorder.statements[0]
		var raw []byte
		if err := db.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+statement.query, statement.args...).Scan(&raw); err != nil {
			t.Fatal(err)
		}
		var plans []map[string]any
		if err := json.Unmarshal(raw, &plans); err != nil {
			t.Fatal(err)
		}
		var visit func(map[string]any)
		visit = func(node map[string]any) {
			// The regression repeatedly sorted/deduplicated thousands of country
			// matches for every highlighted artwork, producing quadratic work.
			if node["Node Type"] == "Unique" || node["Node Type"] == "Sort" {
				if node["Actual Rows"].(float64) > 500 && node["Actual Loops"].(float64) > 1 {
					t.Error("large geographic set repeatedly sorted or deduplicated")
				}
			}
			if children, ok := node["Plans"].([]any); ok {
				for _, child := range children {
					visit(child.(map[string]any))
				}
			}
		}
		visit(plans[0]["Plan"].(map[string]any))
	})
	// Repeated calls also exercise PostgreSQL's prepared/generic-plan path for
	// the small explicit cover selection, rather than just a first custom plan.
	repo := NewRepository(db)
	var previous int
	for i := 0; i < 8; i++ {
		presets, err := repo.IllustratedPresets(ctx, true)
		if err != nil {
			t.Fatal(err)
		}
		count := 0
		for _, p := range presets {
			if p.Cover != nil {
				count++
			}
		}
		if i > 0 && count != previous {
			t.Fatal("cover set changed")
		}
		previous = count
	}
	if previous == 0 {
		t.Fatal("no illustrated preset covers")
	}
}
