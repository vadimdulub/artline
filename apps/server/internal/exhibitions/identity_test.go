package exhibitions

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func TestCanonicalExhibitionInvalidID(t *testing.T) {
	r := &Repository{}
	for _, id := range []string{"", "invalid", "00000000-0000-0000-0000-000000000000' OR true--"} {
		if _, err := r.CanonicalID(context.Background(), id); !errors.Is(err, ErrNotFound) {
			t.Fatalf("invalid ID %q reached the database: %v", id, err)
		}
	}
}

// Reads the owner-authorized production connection only. No local fixtures,
// migrations or test records are created by this test.
func TestCanonicalExhibitionReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_EXHIBITIONS_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("explicit read-only exhibition connection required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	var readonly string
	if err = pool.QueryRow(ctx, "SHOW default_transaction_read_only").Scan(&readonly); err != nil || readonly != "on" {
		t.Fatal("read-only connection required", err)
	}
	r := NewRepository(pool)
	rows, err := pool.Query(ctx, `SELECT id::text,coalesce(canonical_exhibition_id,id)::text FROM exhibitions
 WHERE (status<>'archived' AND canonical_exhibition_id IS NULL) OR canonical_exhibition_id IS NOT NULL
 ORDER BY canonical_exhibition_id NULLS LAST,id LIMIT 16`)
	if err != nil {
		t.Fatal(err)
	}
	var pairs [][2]string
	for rows.Next() {
		var pair [2]string
		if err = rows.Scan(&pair[0], &pair[1]); err != nil {
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
		t.Fatal("no production exhibitions")
	}
	for _, pair := range pairs {
		resolved, err := r.CanonicalID(ctx, pair[0])
		if err != nil || resolved != pair[1] {
			t.Fatalf("%s resolved to %s: %v", pair[0], resolved, err)
		}
		raw, err := r.ByID(ctx, pair[0])
		if err != nil {
			t.Fatal(err)
		}
		var detail struct{ ID string }
		if err = json.Unmarshal(raw, &detail); err != nil || detail.ID != pair[1] {
			t.Fatalf("incorrect canonical detail: %s, %v", detail.ID, err)
		}
		if _, err = r.Entries(ctx, pair[0], "", 2); err != nil {
			t.Fatal(err)
		}
	}
	if _, err = r.CanonicalID(ctx, "00000000-0000-0000-0000-000000000000"); !errors.Is(err, ErrNotFound) {
		t.Fatal("unknown exhibition became visible", err)
	}
	t.Logf("Verified %d production canonical identities, detail and entry routes", len(pairs))
}
