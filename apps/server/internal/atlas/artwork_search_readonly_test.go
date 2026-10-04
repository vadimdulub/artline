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

// Retain the previous correlated predicate as a semantic comparison against
// real records, including aliases, title matches and unpublished creators.
type legacyArtworkSearchDB struct{ atlasDB }

func legacyArtworkSearch(query string) string {
	legacy := strings.ReplaceAll(`(strpos(lower(a.title),lower($query))>0 OR strpos(lower(coalesce(a.unlinked_creator_label,'')),lower($query))>0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id AND ar.status<>'archived' AND ($3 OR ar.status='published') AND (strpos(lower(ar.display_name),lower($query))>0 OR strpos(lower(ar.sort_name),lower($query))>0 OR EXISTS(SELECT 1 FROM artist_aliases x WHERE x.artist_id=ar.id AND strpos(lower(x.alias),lower($query))>0) OR EXISTS(SELECT 1 FROM artist_movements x JOIN movements m ON m.id=x.movement_id WHERE x.artist_id=ar.id AND m.status<>'archived' AND ($3 OR m.status='published') AND strpos(lower(m.name),lower($query))>0) OR EXISTS(SELECT 1 FROM artist_countries x JOIN countries c ON c.code=x.country_code WHERE x.artist_id=ar.id AND strpos(lower(c.name),lower($query))>0) OR EXISTS(SELECT 1 FROM artist_places x JOIN places pl ON pl.id=x.place_id WHERE x.artist_id=ar.id AND strpos(lower(pl.name),lower($query))>0))))`, "$query", "$8")
	query = strings.ReplaceAll(query, artworkSearchPredicate("$8"), legacy)
	return strings.ReplaceAll(query, "NULL::text AS title,NULL::text AS unlinked_creator_label", "a.title,a.unlinked_creator_label")
}

func (db legacyArtworkSearchDB) QueryRow(ctx context.Context, query string, args ...any) pgx.Row {
	return db.atlasDB.QueryRow(ctx, legacyArtworkSearch(query), args...)
}

func TestArtworkSearchReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "20000"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	for _, preview := range []bool{true, false} {
		for _, term := range []string{"Rossetti", "Monet", "impressionism", "France", "Paris", "Madonna", "no-such-artwork-query"} {
			t.Run(term+map[bool]string{true: "-review", false: "-public"}[preview], func(t *testing.T) {
				tx, err := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
				if err != nil {
					t.Fatal(err)
				}
				defer tx.Rollback(ctx)
				recorder := &discoveryPlanDB{atlasDB: tx}
				f := Filter{Range: Range{1100, 2000}, Limit: 30, Preview: preview, Selection: true, Types: []string{"artwork"}, Entities: map[string]url.Values{"artwork": {"q": {term}, "popular": {"false"}, "women": {"false"}, "image_only": {"true"}}}}
				started := time.Now()
				actual, err := (&Repository{db: recorder}).List(ctx, f)
				if err != nil {
					t.Fatal(err)
				}
				elapsed := time.Since(started)
				expected, err := (&Repository{db: legacyArtworkSearchDB{tx}}).List(ctx, f)
				if err != nil {
					t.Fatal(err)
				}
				a, _ := json.Marshal(actual)
				e, _ := json.Marshal(expected)
				if string(a) != string(e) {
					t.Fatal("search changed counts, dates, ordering, visibility, or cursor")
				}
				t.Logf("matches=%d new=%s legacy=%s", actual.Total, elapsed, time.Since(started)-elapsed)
				if term == "Rossetti" && preview && os.Getenv("ARTLINE_ATLAS_AUDIT_DIR") != "" {
					statement := recorder.statements[0]
					dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR")
					if err := os.MkdirAll(dir, 0700); err != nil {
						t.Fatal(err)
					}
					for name, query := range map[string]string{"new": statement.query, "legacy": legacyArtworkSearch(statement.query)} {
						var plan []byte
						if err := tx.QueryRow(ctx, "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) "+query, statement.args...).Scan(&plan); err != nil {
							t.Fatal(err)
						}
						if err := os.WriteFile(filepath.Join(dir, "artwork-search-"+name+"-plan.json"), plan, 0600); err != nil {
							t.Fatal(err)
						}
					}
				}
			})
		}
	}
}
