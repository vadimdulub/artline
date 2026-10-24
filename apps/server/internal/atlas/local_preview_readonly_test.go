package atlas

import (
	"context"
	"encoding/json"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"net/url"
	"os"
	"path/filepath"
	"testing"
	"time"
)

// Uses existing catalogue records only, with database-enforced read-only access.
func TestLocalMapPreviewReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue DSN required")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "10000"
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	normal := NewRepository(pool)
	if normal.localNative {
		t.Fatal("production repository must require projections")
	}
	if err = normal.EnableLocalReadOnlyPreview(ctx); err != nil {
		t.Fatal(err)
	}
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	var readOnly string
	if err = tx.QueryRow(ctx, "SHOW transaction_read_only").Scan(&readOnly); err != nil || readOnly != "on" {
		t.Fatal("read-only transaction required", err)
	}
	recorder := &discoveryPlanDB{atlasDB: tx}
	repo := &Repository{db: recorder, localNative: true}
	filter := Filter{Range: Range{1888, 1890}, Selection: true, Types: []string{"artwork"}, Limit: 5, Entities: map[string]url.Values{"artwork": {"painter": {"vincent-van-gogh-q5582"}, "popular": {"false"}, "image_only": {"true"}}}}
	first, err := repo.List(ctx, filter)
	if err != nil {
		t.Fatal(err)
	}
	if len(first.Lanes) != 1 || len(first.Lanes[0].Items) != 5 || first.Lanes[0].NextCursor == "" {
		t.Fatalf("expected bounded real Van Gogh page: %+v", first)
	}
	filter.After = map[string]string{"artwork": first.Lanes[0].NextCursor}
	second, err := repo.List(ctx, filter)
	if err != nil {
		t.Fatal(err)
	}
	if first.Total != second.Total || first.Lanes[0].Items[0].ID == second.Lanes[0].Items[0].ID {
		t.Fatal("native keyset/count mismatch")
	}
	for i, item := range first.Lanes[0].Items {
		if item.StartYear > 1890 || item.EndYear < 1888 {
			t.Fatal("date scope escaped")
		}
		if item.MediaURL == "" {
			t.Fatalf("unillustrated item %d", i)
		}
	}
	if dir := os.Getenv("ARTLINE_MAP_PROOF_DIR"); dir != "" {
		plans := []json.RawMessage{}
		for _, statement := range recorder.statements[:2] {
			var plan []byte
			if err = tx.QueryRow(ctx, "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) "+statement.query, statement.args...).Scan(&plan); err != nil {
				t.Fatal(err)
			}
			plans = append(plans, plan)
		}
		data, _ := json.MarshalIndent(plans, "", "  ")
		if err = os.WriteFile(filepath.Join(dir, "native-map-preview-plans.json"), data, 0600); err != nil {
			t.Fatal(err)
		}
	}
}
