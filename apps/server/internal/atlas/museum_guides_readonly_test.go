package atlas

import (
	"context"
	"encoding/json"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Audits existing records only. Never creates a database, fixture or migration.
func TestMuseumGuideSelectionsReadOnly(t *testing.T) {
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
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	files, err := filepath.Glob("../../../web/content/articles/museum-guides/*/en.json")
	if err != nil || len(files) == 0 {
		t.Fatal("guide content missing", err)
	}
	for _, file := range files {
		var guide struct {
			Slug    string
			Context struct{ Start, End int }
			Works   []struct{ ID string }
		}
		raw, err := os.ReadFile(file)
		if err != nil {
			t.Fatal(err)
		}
		if err = json.Unmarshal(raw, &guide); err != nil {
			t.Fatal(err)
		}
		t.Run(guide.Slug, func(t *testing.T) {
			tx, err := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback(ctx)
			ids := []string{}
			wanted := map[string]bool{}
			for _, w := range guide.Works {
				ids = append(ids, w.ID)
				wanted[w.ID] = true
			}
			recorder := &discoveryPlanDB{atlasDB: tx}
			repo := &Repository{db: recorder}
			f := Filter{Range: Bounds, Limit: 30, Selection: true, Types: []string{"artwork", "book", "event"}, Entities: map[string]url.Values{"artwork": {"id": ids, "popular": {"false"}}, "book": {"top100": {"true"}}, "event": {"top100": {"true"}}}}
			f.Start, f.End = guide.Context.Start, guide.Context.End
			data, err := repo.List(ctx, f)
			if err != nil {
				t.Fatal(err)
			}
			if len(data.Lanes) != 3 {
				t.Fatal("missing context lanes")
			}
			for _, item := range data.Lanes[0].Items {
				if !wanted[item.ID] {
					t.Fatalf("unselected artwork leaked: %s", item.ID)
				}
			}
			if data.Lanes[0].Total > len(ids) || data.Lanes[0].Total < len(ids)-3 {
				t.Fatalf("unexpected selected artwork count %d of %d", data.Lanes[0].Total, len(ids))
			}
			if data.Lanes[1].Total == 0 || data.Lanes[2].Total == 0 {
				t.Fatal("guide removed book/event context")
			}
			statement := recorder.statements[0]
			var plan []byte
			if err = tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+statement.query, statement.args...).Scan(&plan); err != nil {
				t.Fatal(err)
			}
			if !strings.Contains(string(plan), "artworks_pkey") {
				t.Fatal("guide lost indexed artwork lookup")
			}
			if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" {
				if err = os.MkdirAll(dir, 0700); err != nil {
					t.Fatal(err)
				}
				if err = os.WriteFile(filepath.Join(dir, "guide-"+guide.Slug+".json"), plan, 0600); err != nil {
					t.Fatal(err)
				}
			}
			t.Logf("selected artworks %d/%d; books %d; events %d", data.Lanes[0].Total, len(ids), data.Lanes[1].Total, data.Lanes[2].Total)
		})
	}
}
