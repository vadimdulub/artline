package atlas

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Existing research records only. Never inserts fixtures or changes publication.
func TestPresetFocusReadOnly(t *testing.T) {
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
	for _, id := range []string{"russian-revolution", "french-revolution"} {
		t.Run(id, func(t *testing.T) {
			tx, err := db.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback(ctx)
			p, _ := FindPreset(id)
			recorder := &discoveryPlanDB{atlasDB: tx}
			repo := &Repository{db: recorder}
			f := Filter{PresetID: id, Range: p.Context, Highlights: true, Limit: 60}
			data, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			if len(data.Lanes) != 3 {
				t.Fatal("missing focus lanes")
			}
			statements := append([]discoveryStatement(nil), recorder.statements...)
			for _, lane := range data.Lanes {
				if lane.Total == 0 {
					t.Fatalf("empty %s focus", lane.Key)
				}
				if lane.Key == "event" {
					contexts := map[string]bool{}
					for _, item := range lane.Items {
						if item.Relation == "context" {
							contexts[item.ID] = true
						}
					}
					if len(contexts) != len(p.Focus.Context["event"]) {
						t.Fatalf("wrong context events: %v", contexts)
					}
					for _, event := range p.Focus.Context["event"] {
						if !contexts[event] {
							t.Fatalf("missing context %s", event)
						}
					}
				}
				if lane.Key == "artwork" && lane.NextCursor != "" {
					other := f
					other.PresetID = "renaissance"
					other.Types = []string{"artwork"}
					other.After = map[string]string{"artwork": lane.NextCursor}
					if _, err := repo.List(ctx, other); err == nil {
						t.Fatal("cursor crossed preset scope")
					}
				}
			}
			if id == "french-revolution" {
				for _, artwork := range []string{"7c39775d-8d55-5c91-9e1a-15890c791102", "098882cb-b551-5d11-b8b7-dff723541052", "f9207af7-b19f-58cd-b5fe-7140899e4071", "dab844dd-389a-59b6-876b-dd2c9d7db27e", "44ce1484-a49a-48f5-8135-5bb8d309027f", "bd026785-c3e7-5370-a47d-5731a5406a61"} {
					selected := f
					selected.Selection = true
					selected.Picks = map[string][]string{"artwork": {artwork}}
					out, err := repo.List(ctx, selected)
					if err != nil || out.Total != 1 {
						t.Fatalf("selected illustrated work missing: %s, %v", artwork, err)
					}

				}
			}
			for _, change := range []func(*Filter){func(f *Filter) { f.Countries = []string{"not-a-recorded-country"} }, func(f *Filter) { f.Query = "no-such-revolution-record-zzzz" }} {
				empty := f
				change(&empty)
				out, err := repo.List(ctx, empty)
				if err != nil || out.Total != 0 {
					t.Fatalf("focus bypassed user filter: %+v %v", out, err)
				}
			}
			all := f
			all.Highlights = false
			out, err := repo.List(ctx, all)
			if err != nil || out.Total <= data.Total {
				t.Fatalf("highlights cannot be switched off: %v", err)
			}
			t.Logf("highlights=%d all=%d", data.Total, out.Total)
			if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" {
				if err := os.MkdirAll(dir, 0700); err != nil {
					t.Fatal(err)
				}
				for i, s := range statements {
					var plan []byte
					if err := tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+s.query, s.args...).Scan(&plan); err != nil {
						t.Fatal(err)
					}
					if err := os.WriteFile(filepath.Join(dir, id+"-"+Definitions[i].Key+".json"), plan, 0600); err != nil {
						t.Fatal(err)
					}
				}
			}
		})
	}
}
