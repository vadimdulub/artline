package events

import (
	"context"
	"encoding/json"
	"os"
	"reflect"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Opt-in audit of the real enriched records. It never inserts fixtures or
// creates a database. Compare every immutable JSON field to import evidence.
func TestReadOnlyEventDescriptions(t *testing.T) {
	dsn := os.Getenv("ARTLINE_EVENTS_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only audit not requested")
	}
	raw, err := os.ReadFile("../../../../docs/research/historical-events-20260917/events.json")
	if err != nil {
		t.Fatal(err)
	}
	var original []map[string]any
	if err = json.Unmarshal(raw, &original); err != nil {
		t.Fatal(err)
	}
	baseline := map[string]map[string]any{}
	for _, record := range original {
		delete(record, "description")
		baseline[record["id"].(string)] = record
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	rows, err := db.Query(ctx, `SELECT id,record,status FROM event_records ORDER BY id`)
	if err != nil {
		t.Fatal(err)
	}
	counts := map[string]int{}
	seen := 0
	for rows.Next() {
		var id, status string
		var data []byte
		if err = rows.Scan(&id, &data, &status); err != nil {
			t.Fatal(err)
		}
		var event Event
		var fields map[string]any
		if err = json.Unmarshal(data, &event); err != nil {
			t.Fatal(err)
		}
		if event.DescriptionSource == nil || status != "review" {
			t.Fatalf("missing review description source: %s", id)
		}
		update := DescriptionUpdate{ID: id, Description: event.Description, PreviousDescription: event.Description, Source: *event.DescriptionSource}
		if err = ValidateDescriptions([]DescriptionUpdate{update}, 1); err != nil {
			t.Fatal(err)
		}
		if err = json.Unmarshal(data, &fields); err != nil {
			t.Fatal(err)
		}
		delete(fields, "description")
		delete(fields, "descriptionSource")
		if !reflect.DeepEqual(fields, baseline[id]) {
			t.Fatalf("unrelated historical metadata changed: %s", id)
		}
		counts[event.DescriptionSource.Kind]++
		seen++
	}
	if err = rows.Err(); err != nil {
		t.Fatal(err)
	}
	rows.Close()
	if seen != 10000 || counts["wikipedia"] < 9000 {
		t.Fatalf("unexpected coverage %d %+v", seen, counts)
	}
	e, err := NewRepository(db).ByID(ctx, "event-q361", true)
	if err != nil || e.DescriptionSource == nil || e.DescriptionSource.Kind != "wikipedia" {
		t.Fatal("attribution missing from detail projection", err)
	}
	t.Logf("%d attributed descriptions; unchanged historical metadata for all rows; sources=%+v", seen, counts)
}
