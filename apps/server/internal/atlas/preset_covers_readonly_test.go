package atlas

import (
	"context"
	"os"
	"reflect"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func TestPictorialPresetCoversReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	config.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	db, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	rows, err := db.Query(ctx, `WITH a(work_type) AS (VALUES ('painting'),('print'),('unknown'),('photograph'),('sculpture'),('poster')) SELECT work_type FROM a WHERE `+presetCoverMedium+` ORDER BY work_type`)
	if err != nil {
		t.Fatal(err)
	}
	var eligible []string
	for rows.Next() {
		var medium string
		if err := rows.Scan(&medium); err != nil {
			t.Fatal(err)
		}
		eligible = append(eligible, medium)
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(eligible, []string{"painting", "print", "unknown"}) {
		t.Fatal(eligible)
	}
	covers, err := (&Repository{db: db}).IllustratedPresets(ctx)
	if err != nil {
		t.Fatal(err)
	}
	for _, id := range []string{"edo", "romanticism"} {
		found := false
		for _, p := range covers {
			if p.ID == id {
				found = p.Cover != nil && p.Cover.MediaURL != ""
			}
		}
		if !found {
			t.Fatalf("selected pictorial cover missing: %s", id)
		}
	}
}
