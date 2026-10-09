package books

import (
	"context"
	"encoding/json"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"reflect"
	"testing"
	"time"
)

// Opt-in production audit. Pool sessions are forced read-only; no fixtures.
func TestSummaryReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("opt-in catalogue audit")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	repo := NewRepository(pool)
	for _, limit := range []int{3, 500} {
		filter := Filter{Range: Bounds, Top100: true, Limit: limit}
		full, err := repo.List(ctx, filter)
		if err != nil {
			t.Fatal(err)
		}
		filter.Summary = true
		summary, err := repo.List(ctx, filter)
		if err != nil {
			t.Fatal(err)
		}
		fullBytes, _ := json.Marshal(full)
		summaryBytes, _ := json.Marshal(summary)
		if len(full.Items) != len(summary.Items) {
			t.Fatal("summary changed page length")
		}
		for i, book := range full.Items {
			book.Summary = true
			expected, _ := json.Marshal(book)
			got, _ := json.Marshal(summary.Items[i])
			if string(expected) != string(got) {
				t.Fatalf("book %s summary differs from complete record", book.ID)
			}
		}
		full.Items = nil
		summary.Items = nil
		if !reflect.DeepEqual(full, summary) {
			t.Fatal("summary changed counts, dates, pagination or metadata")
		}
		t.Logf("%d book page: %d -> %d bytes; identical timeline fields, covers and metadata", limit, len(fullBytes), len(summaryBytes))
	}
}
