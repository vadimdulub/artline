package catalog

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Real catalogue verification uses an explicit read-only transaction. No fixture
// insertion or ARTLINE_TEST_DATABASE_URL is involved.
func TestArtistKeyArtworkReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue DSN required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	r := &Repository{db: tx}
	var id, expected string
	err = tx.QueryRow(ctx, `SELECT k.artist_id::text,k.artwork_id::text FROM artist_key_artworks k
 JOIN artists a ON a.id=k.artist_id WHERE a.slug='leonardo-da-vinci'`).Scan(&id, &expected)
	if err != nil {
		t.Fatal(err)
	}
	work, err := r.artistKeyArtwork(ctx, id)
	if err != nil || work == nil || work.ID != expected {
		t.Fatalf("saved opening work: %v %v", work, err)
	}
	missing, err := r.artistKeyArtwork(ctx, "00000000-0000-0000-0000-000000000000")
	if err != nil || missing != nil {
		t.Fatalf("missing selection: %v %v", missing, err)
	}
	var raw []byte
	if err = tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+artistKeyArtworkQuery, id).Scan(&raw); err != nil {
		t.Fatal(err)
	}
	var plans []map[string]any
	if err = json.Unmarshal(raw, &plans); err != nil {
		t.Fatal(err)
	}

	t.Logf("indexed key-work plan: %s", raw)
	if !strings.Contains(string(raw), "artist_key_artworks_artist_id_key") || !strings.Contains(string(raw), "artworks_pkey") {
		t.Fatal("key lookup lost its indexed artist/artwork access")
	}
}
