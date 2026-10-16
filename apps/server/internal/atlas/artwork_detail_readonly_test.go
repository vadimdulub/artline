package atlas

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Exercise real source-backed objects without creating catalogue fixtures.
func TestArtworkDetailDatesReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("requires read-only catalogue connection")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "10000"
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	repo := NewRepository(db)
	for _, predicate := range []string{"a.creation_year_start BETWEEN 1971 AND 1979", "a.date_precision='unknown'"} {
		var id string
		err = db.QueryRow(ctx, `SELECT a.id::text FROM artworks a WHERE a.status<>'archived' AND `+predicate+` AND `+acceptedArtHolding+` AND `+artworkCreatorVisibility+` LIMIT 1`).Scan(&id)
		if err != nil {
			t.Fatal(err)
		}
		visible, err := repo.ArtworkVisible(ctx, id)
		if err != nil || !visible {
			t.Fatalf("detail rejected supported object %s: visible=%v error=%v", id, visible, err)
		}
	}
	visible, err := repo.ArtworkVisible(ctx, "00000000-0000-0000-0000-000000000000")
	if err != nil || visible {
		t.Fatalf("missing object: visible=%v error=%v", visible, err)
	}
}
