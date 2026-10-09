package catalog

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// An artist's own teachers/influences must survive a large outgoing fan-out.
// Uses the real catalogue in an enforced read-only transaction, without fixtures.
func TestArtistInfluencesIncomingPriorityReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("set ARTLINE_READONLY_DATABASE_URL")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
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
	for _, slug := range []string{"rembrandt", "pablo-picasso-q5593", "henri-matisse-q5589"} {
		var id string
		if err := tx.QueryRow(ctx, `SELECT id::text FROM artists WHERE slug=$1`, slug).Scan(&id); err != nil {
			t.Fatal(slug, err)
		}
		rows, err := tx.Query(ctx, `SELECT i.id::text FROM influence_claims i
 JOIN artists t ON t.id=i.target_artist_id LEFT JOIN artists s ON s.id=i.source_artist_id
 WHERE i.target_artist_id=$1 AND i.status='published' AND t.status='published'
 AND (s.id IS NULL OR s.status='published')
 AND EXISTS(SELECT 1 FROM citations c JOIN sources src ON src.id=c.source_id
 WHERE c.entity_type='influence' AND c.entity_id=i.id AND src.is_active)`, id)
		if err != nil {
			t.Fatal(err)
		}
		incoming := map[string]bool{}
		for rows.Next() {
			var claimID string
			if err := rows.Scan(&claimID); err != nil {
				t.Fatal(err)
			}
			incoming[claimID] = true
		}
		if err := rows.Err(); err != nil {
			t.Fatal(err)
		}
		rows.Close()
		if len(incoming) == 0 || len(incoming) > 40 {
			t.Fatalf("%s: audit requires 1–40 incoming claims, found %d", slug, len(incoming))
		}
		claims, err := repo.artistInfluences(ctx, id)
		if err != nil {
			t.Fatal(err)
		}
		if len(claims) > 40 {
			t.Fatal("unbounded influence response")
		}
		outgoingSeen := false
		for _, claim := range claims {
			if claim.Direction == "outgoing" {
				outgoingSeen = true
			} else {
				if outgoingSeen {
					t.Fatal("incoming relationship follows outgoing fan-out", slug)
				}
				delete(incoming, claim.ID)
			}
			if len(claim.Citations) == 0 {
				t.Fatal("relationship lost its citations", claim.ID)
			}
		}
		if len(incoming) != 0 {
			t.Fatalf("%s: %d incoming relationships omitted", slug, len(incoming))
		}
	}
}
