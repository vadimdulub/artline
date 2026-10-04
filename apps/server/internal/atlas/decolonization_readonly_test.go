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

// Source-backed real records only, under a database-enforced read-only snapshot.
// This guards thematic scope, review visibility and bounded pagination together.
func TestDecolonizationReadOnly(t *testing.T) {
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
	tx, err := db.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	p, ok := FindPreset("decolonization")
	if !ok || p.Focus.Global || len(p.StartingCountries)+len(p.StartingCreators) > 0 {
		t.Fatal("decolonization must use an explicit editorial selection, without broad country or creator fallthrough")
	}
	recorder := &discoveryPlanDB{atlasDB: tx}
	repo := &Repository{db: recorder}
	f := Filter{PresetID: p.ID, Range: p.Context, Limit: 150, Preview: true, Selection: true, Types: []string{"artwork", "book", "event"}}
	all, err := repo.List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	statements := slices.Clone(recorder.statements)
	if len(all.Lanes) != 3 || len(statements) != 3 {
		t.Fatalf("expected three populated lanes and three captured lane queries; got %d lanes, %d queries", len(all.Lanes), len(statements))
	}
	want := map[string]int{"artwork": 104, "book": 9, "event": 9}
	for _, lane := range all.Lanes {
		if lane.Total != want[lane.Key] || len(lane.Items) != lane.Total {
			t.Fatalf("%s: total=%d items=%d, want %d", lane.Key, lane.Total, len(lane.Items), want[lane.Key])
		}
		seen := map[string]bool{}
		for _, item := range lane.Items {
			if !slices.Contains(p.Focus.Related[lane.Key], item.ID) && !slices.Contains(p.Focus.Context[lane.Key], item.ID) {
				t.Fatalf("unselected %s", item.ID)
			}
			if lane.Key == "artwork" && (item.MediaURL == "" || item.EndYear > 1970) {
				t.Fatal("artwork image/date rule bypassed")
			}
			if (item.Relation == "context") != slices.Contains(p.Focus.Context[lane.Key], item.ID) {
				t.Fatal("context relationship lost")
			}
		}
		page := f
		page.Types = []string{lane.Key}
		page.Limit = 7
		page.After = map[string]string{}
		for n := 0; n < 20; n++ {
			out, err := repo.List(ctx, page)
			if err != nil {
				t.Fatal(err)
			}
			if len(out.Lanes) != 1 || len(out.Lanes[0].Items) > 7 {
				t.Fatal("unbounded page")
			}
			l := out.Lanes[0]
			for _, item := range l.Items {
				if seen[item.ID] {
					t.Fatal("duplicate across keyset pages")
				}
				seen[item.ID] = true
			}
			if l.NextCursor == "" {
				break
			}
			page.After[lane.Key] = l.NextCursor
		}
		if len(seen) != lane.Total {
			t.Fatalf("%s pagination lost records: %d/%d", lane.Key, len(seen), lane.Total)
		}
	}
	for _, id := range []string{"e3ecdb87-4455-5cfb-994c-d7c21ac74bbe", "2abc5de1-0f89-5472-9d1e-edf86a49e48c", "06d5f22a-89b7-5d72-81ff-3a100edbc562"} {
		if !slices.Contains(p.Focus.Context["artwork"], id) {
			t.Fatal("earlier Bengal School context lost")
		}
	}
	if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" {
		if err := os.MkdirAll(dir, 0700); err != nil {
			t.Fatal(err)
		}
		for i, s := range statements {
			var plan json.RawMessage
			if err := tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+s.query, s.args...).Scan(&plan); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(dir, "decolonization-"+Definitions[i].Key+"-plan.json"), plan, 0600); err != nil {
				t.Fatal(err)
			}
		}
	}
}
