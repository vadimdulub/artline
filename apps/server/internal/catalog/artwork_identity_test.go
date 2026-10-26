package catalog

import (
	"context"
	"errors"
	"os"
	"testing"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func TestCanonicalArtworkIDRejectsInvalidID(t *testing.T) {
	// Invalid input must fail before a database call, including SQL-shaped text.
	repo := &Repository{}
	for _, id := range []string{"", "not-a-uuid", "00000000-0000-0000-0000-000000000000' OR true--"} {
		if _, err := repo.CanonicalArtworkID(context.Background(), id); !errors.Is(err, ErrNotFound) {
			t.Fatalf("%q: expected not found, got %v", id, err)
		}
	}
}

// Opt-in owner database verification. All reads share a read-only repeatable
// transaction; no local fixture database, inserted data, or catalogue mutation.
func TestCanonicalArtworkIDReadOnly(t *testing.T) {
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
	rows, err := tx.Query(ctx, `SELECT old.id::text,canonical.id::text
 FROM artworks old JOIN slug_redirects redirect ON redirect.entity_type='artwork' AND redirect.old_slug=old.slug
 JOIN artworks canonical ON canonical.id=redirect.entity_id
 WHERE old.status='archived' AND canonical.status<>'archived' ORDER BY old.id LIMIT 16`)
	if err != nil {
		t.Fatal(err)
	}
	var pairs [][2]string
	for rows.Next() {
		var pair [2]string
		if err := rows.Scan(&pair[0], &pair[1]); err != nil {
			t.Fatal(err)
		}
		pairs = append(pairs, pair)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		t.Fatal(err)
	}
	if len(pairs) == 0 {
		t.Fatal("no existing reviewed artwork redirects to verify")
	}
	for _, pair := range pairs {
		for _, input := range pair {
			resolved, err := repo.CanonicalArtworkID(ctx, input)
			if err != nil || resolved != pair[1] {
				t.Fatalf("resolve %s: got %s, %v; want %s", input, resolved, err, pair[1])
			}
			work, err := repo.AtlasArtwork(ctx, input)
			if err != nil || work.ID != pair[1] {
				t.Fatalf("detail %s: got %s, %v; want %s", input, work.ID, err, pair[1])
			}
		}
	}
	var archived string
	err = tx.QueryRow(ctx, `SELECT id::text FROM artworks a WHERE status='archived'
 AND NOT EXISTS(SELECT 1 FROM slug_redirects s WHERE s.entity_type='artwork' AND s.old_slug=a.slug)
 ORDER BY id LIMIT 1`).Scan(&archived)
	if err != nil && !errors.Is(err, pgx.ErrNoRows) {
		t.Fatal(err)
	}
	if err == nil {
		if _, err := repo.CanonicalArtworkID(ctx, archived); !errors.Is(err, ErrNotFound) {
			t.Fatalf("unmapped archive %s became available: %v", archived, err)
		}
	}
	if _, err := repo.CanonicalArtworkID(ctx, "00000000-0000-0000-0000-000000000000"); !errors.Is(err, ErrNotFound) {
		t.Fatalf("unknown UUID became available: %v", err)
	}
	t.Logf("Verified %d existing redirects, active UUIDs, unmapped archives and unknown UUIDs", len(pairs))
}
