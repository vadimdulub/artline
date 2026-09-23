package atlas

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Uses imported collection records through read-only connections; no fixtures,
// migrations, publication changes or invented museum associations.
func TestPersonalCollectionReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
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
	rows, err := db.Query(ctx, `SELECT a.id::text,a.creation_year_start,a.creation_year_end,
 a.status,a.research_candidate,a.current_institution_id IS NULL,
 NOT EXISTS(SELECT 1 FROM artwork_location_assertions h WHERE h.artwork_id=a.id)
 FROM curated_collections c JOIN curated_collection_items ci ON ci.collection_id=c.id
 JOIN artworks a ON a.id=ci.artwork_id JOIN sources s ON s.id=ci.source_id
 WHERE c.institution_id IS NULL AND c.curator_kind='owner'
 AND s.slug='wikiart-artist-coverage-20260920' ORDER BY a.id LIMIT 12`)
	if err != nil {
		t.Fatal(err)
	}
	type work struct {
		id                 string
		start, end         int
		status             string
		candidate          bool
		noHolding, noClaim bool
	}
	var works []work
	for rows.Next() {
		var w work
		if err := rows.Scan(&w.id, &w.start, &w.end, &w.status, &w.candidate, &w.noHolding, &w.noClaim); err != nil {
			t.Fatal(err)
		}
		works = append(works, w)
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		t.Fatal(err)
	}
	if len(works) == 0 {
		t.Fatal("no imported personal collection records available")
	}
	repo := NewRepository(db)
	for _, w := range works {
		if w.status != "review" || !w.candidate || !w.noHolding || !w.noClaim || w.end > 1955 {
			t.Fatalf("personal selection changed editorial/holding semantics: %+v", w)
		}
		visible, err := repo.ArtworkVisible(ctx, w.id, true)
		if err != nil || !visible {
			t.Fatalf("personal artwork unavailable in atlas: %s %v %v", w.id, visible, err)
		}
		out, err := repo.List(ctx, Filter{Range: Range{Start: w.start, End: max(w.end, w.start+1)}, Preview: true,
			Highlights: true, Selection: true, Limit: 10, Picks: map[string][]string{"artwork": {w.id}}})
		if err != nil || out.Total != 1 || len(out.Lanes) != 1 || len(out.Lanes[0].Items) != 1 || out.Lanes[0].Items[0].ID != w.id {
			t.Fatalf("personal selection missing from bounded atlas page: %s total=%d err=%v", w.id, out.Total, err)
		}
	}
	t.Logf("Verified %d real personal selections without museum holdings or publication", len(works))
}
