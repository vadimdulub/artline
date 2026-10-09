package atlas

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"slices"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Audits existing data only. Database-enforced read-only transactions prohibit
// fixtures, migrations, publication changes and discovery-index writes.
func TestAllPresetReviewsReadOnly(t *testing.T) {
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
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	for _, p := range Presets() {
		t.Run(p.ID, func(t *testing.T) {
			tx, err := db.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback(ctx)
			recorder := &discoveryPlanDB{atlasDB: tx}
			repo := &Repository{db: recorder}
			f := Filter{PresetID: p.ID, Range: p.Context, Highlights: true, Limit: 60}
			data, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			statements := slices.Clone(recorder.statements)
			if len(data.Lanes) != 3 || len(statements) != 3 {
				t.Fatal("expected one bounded query per lane")
			}
			for _, lane := range data.Lanes {
				if len(lane.Items) > 60 || lane.Total < len(lane.Items) {
					t.Fatal("unbounded/inconsistent response")
				}
				for _, item := range lane.Items {
					if item.StartYear > f.End || item.EndYear < f.Start {
						t.Fatalf("outside period: %s", item.ID)
					}
					if (item.Relation == "context") != slices.Contains(p.Focus.Context[lane.Key], item.ID) {
						t.Fatalf("wrong context label: %s", item.ID)
					}
					if lane.Key == "event" && p.Focus.SelectedEvents && !slices.Contains(p.Focus.Related["event"], item.ID) && item.Relation != "context" {
						t.Fatalf("unrelated event: %s", item.ID)
					}
					if lane.Key == "artwork" {
						var valid bool
						if err := tx.QueryRow(ctx, `SELECT a.creation_year_end<=1970 AND m.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$' FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=$1::uuid`, item.ID).Scan(&valid); err != nil || !valid {
							t.Fatalf("art scope/image: %s %v", item.ID, err)
						}
					}
				}
				// All links must point to existing catalogue records. Unknown dates
				// remain absent; eligible core records must survive default highlights.
				if lane.Key != "artwork" {
					table := "book_records"
					if lane.Key == "event" {
						table = "event_records"
					}
					for _, id := range append(slices.Clone(p.Focus.Related[lane.Key]), p.Focus.Context[lane.Key]...) {
						var eligible bool
						if err := tx.QueryRow(ctx, `SELECT coalesce(status<>'archived' AND start_year<=$2 AND end_year>=$1,false) FROM `+table+` WHERE id=$3`, f.Start, f.End, id).Scan(&eligible); err != nil {
							t.Fatalf("missing linked %s %s: %v", lane.Key, id, err)
						}
						if eligible && lane.Total <= 60 && slices.Contains(p.Focus.Related[lane.Key], id) && !slices.ContainsFunc(lane.Items, func(i Item) bool { return i.ID == id }) {
							t.Fatalf("core %s lost to highlights/country metadata: %s", lane.Key, id)
						}
					}
				}
			}
			variants := []struct {
				name   string
				change func(*Filter)
			}{
				{"highlights-off", func(f *Filter) { f.Highlights = false }},
				{"main-period", func(f *Filter) { f.Range = p.Period }},

				{"country-intersection", func(f *Filter) { f.Countries = []string{"not-a-recorded-country"} }},
			}
			for _, v := range variants {
				t.Run(v.name, func(t *testing.T) {
					changed := f
					v.change(&changed)
					out, err := repo.List(ctx, changed)
					if err != nil {
						t.Fatal(err)
					}
					for i, lane := range out.Lanes {
						if v.name == "highlights-off" && lane.Total < data.Lanes[i].Total {
							t.Fatal("switching off highlights removed entries")
						}
						if (v.name == "main-period" || v.name == "public") && lane.Total > data.Lanes[i].Total {
							t.Fatal("narrowed scope grew")
						}
						if v.name == "country-intersection" && lane.Total != 0 {
							t.Fatal("preset bypassed user's country choice")
						}
					}
				})
			}
			t.Logf("art=%d books=%d events=%d", data.Lanes[0].Total, data.Lanes[1].Total, data.Lanes[2].Total)
			if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" {
				if err := os.MkdirAll(dir, 0700); err != nil {
					t.Fatal(err)
				}
				raw, _ := json.MarshalIndent(data, "", "  ")
				if err := os.WriteFile(filepath.Join(dir, p.ID+"-response.json"), raw, 0600); err != nil {
					t.Fatal(err)
				}
				if slices.Contains([]string{"byzantium", "edo", "renaissance", "sahel", "first-world-war", "science", "civil-rights", "digital"}, p.ID) {
					for i, s := range statements {
						var plan []byte
						if err := tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+s.query, s.args...).Scan(&plan); err != nil {
							t.Fatal(err)
						}
						if err := os.WriteFile(filepath.Join(dir, p.ID+"-"+Definitions[i].Key+"-plan.json"), plan, 0600); err != nil {
							t.Fatal(err)
						}
					}
				}
			}
		})
	}
}
