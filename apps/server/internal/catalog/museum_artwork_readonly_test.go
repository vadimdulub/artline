package catalog

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Opt-in, real-catalogue read-only comparison. Never creates tables or fixtures,
// never uses ARTLINE_TEST_DATABASE_URL, and never changes catalogue rows.
func TestMuseumArtworkReadOnlyScopedPlan(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("ARTLINE_READONLY_DATABASE_URL is not set")
	}
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly, IsoLevel: pgx.RepeatableRead})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	for _, slug := range []string{"the-met", "national-gallery-of-art", "smithsonian-american-art-museum"} {
		var id string
		err := tx.QueryRow(ctx, `SELECT aw.id::text FROM artworks aw
 WHERE aw.current_institution_id=(SELECT id FROM institutions WHERE slug=$1)
 AND aw.primary_media_id IS NOT NULL AND aw.status='review' LIMIT 1`, slug).Scan(&id)
		if errors.Is(err, pgx.ErrNoRows) {
			t.Logf("no current image-bearing review example for %s", slug)
			continue
		}
		if err != nil {
			t.Fatal(err)
		}
		oldQuery := strings.Replace(museumArtworkSQL(museumScopedCTE), "w.id=$3::uuid", "w.id::text=$3", 1)
		var previous, current []byte
		if err := tx.QueryRow(ctx, oldQuery, true, slug, id).Scan(&previous); err != nil {
			t.Fatal(err)
		}
		if err := tx.QueryRow(ctx, museumArtworkSQL(museumArtworkScopedCTE), museumQueryArgs(true, slug, id)...).Scan(&current); err != nil {
			t.Fatal(err)
		}
		var before, after any
		if json.Unmarshal(previous, &before) != nil || json.Unmarshal(current, &after) != nil || !reflect.DeepEqual(before, after) {
			t.Fatalf("detail metadata or visibility differs for %s", slug)
		}
		var rawPlan []byte
		if err := tx.QueryRow(ctx, `EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON) `+museumArtworkSQL(museumArtworkScopedCTE), museumQueryArgs(true, slug, id)...).Scan(&rawPlan); err != nil {
			t.Fatal(err)
		}
		var plan []map[string]any
		if err := json.Unmarshal(rawPlan, &plan); err != nil {
			t.Fatal(err)
		}
		var inspect func(map[string]any)
		artworkIndex := false
		inspect = func(node map[string]any) {
			if node["Relation Name"] == "artworks" {
				if node["Node Type"] == "Seq Scan" || node["Actual Rows"].(float64) > 1 {
					t.Error("detail query read more than the requested artwork")
				}
				if node["Index Name"] == "artworks_pkey" {
					artworkIndex = true
				}
			}
			if children, ok := node["Plans"].([]any); ok {
				for _, child := range children {
					inspect(child.(map[string]any))
				}
			}
		}
		inspect(plan[0]["Plan"].(map[string]any))
		if !artworkIndex {
			t.Error("detail query did not use artwork UUID index")
		}
		repo := &Repository{db: tx}
		for n := 0; n < 8; n++ {
			requestCtx, cancel := context.WithTimeout(ctx, 8*time.Second)
			work, err := repo.MuseumArtwork(requestCtx, slug, id, true)
			cancel()
			if err != nil || work.ID != id {
				t.Fatalf("repeated detail request %d failed: %v", n, err)
			}
		}
		if _, err := repo.MuseumArtwork(ctx, "not-a-holding-museum", id, true); !errors.Is(err, ErrNotFound) {
			t.Error("an unrelated museum exposed the artwork")
		}
		t.Logf("%s: equivalent detail JSON, single-artwork index plan %.3fms, eight repeated requests passed; not a 10-million-row benchmark", slug, plan[0]["Execution Time"])
	}
}
