package catalog

import (
	"context"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"testing"
)

// Existing catalogue reads only: no migrations, database creation or fixtures.
func TestWomenReadOnlyScopedDiscovery(t *testing.T) {
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
	repo := &Repository{db: tx}
	for _, popular := range []bool{false, true} {
		for _, preview := range []bool{false, true} {
			facets, err := repo.DiscoveryFacets(ctx, preview, popular, true)
			if err != nil {
				t.Fatal(err)
			}
			var expected int
			err = tx.QueryRow(ctx, `SELECT count(DISTINCT ac.country_code) FROM artist_countries ac
 JOIN artists a ON a.id=ac.artist_id JOIN artist_gender_evidence g ON g.artist_id=a.id AND g.is_woman
 WHERE a.status<>'archived' AND ($1 OR a.status='published')
 AND (NOT $2 OR EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=a.id AND d.is_popular))`, preview, popular).Scan(&expected)
			if err != nil {
				t.Fatal(err)
			}
			if len(facets.Countries) != expected {
				t.Fatalf("countries=%d expected=%d", len(facets.Countries), expected)
			}
			options, err := repo.PainterOptions(ctx, "", "", nil, preview, popular, true)
			if err != nil {
				t.Fatal(err)
			}
			if len(options.Items) > 30 {
				t.Fatal("unbounded painter options")
			}
			for _, item := range options.Items {
				var valid bool
				err = tx.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artists a JOIN artist_gender_evidence g ON g.artist_id=a.id AND g.is_woman WHERE a.slug=$1 AND ($2 OR a.status='published') AND (NOT $3 OR EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=a.id AND d.is_popular)))`, item.Slug, preview, popular).Scan(&valid)
				if err != nil || !valid {
					t.Fatalf("unscoped option %s: %v", item.Slug, err)
				}
			}
		}
	}
}
