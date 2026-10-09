package atlas

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/books"
	"github.com/vadimdulub/artline/apps/server/internal/timeline"
)

func TestBookGalleryCoversReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue audit not requested")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	repo := NewRepository(db)
	f := Filter{Range: Bounds, Limit: timeline.IndividualLimit, Types: []string{"book"}, Selection: true}
	seen, covers := map[string]bool{}, 0
	for page := 0; page < 2; page++ {
		out, err := repo.List(ctx, f)
		if err != nil {
			t.Fatal(err)
		}
		lane := out.Lanes[0]
		if lane.Mode != "density" || len(lane.Items) != f.Limit || lane.NextCursor == "" {
			t.Fatalf("expected a bounded crowded book page: mode=%s items=%d", lane.Mode, len(lane.Items))
		}
		ids := make([]string, len(lane.Items))
		for i, item := range lane.Items {
			if seen[item.ID] {
				t.Fatal("duplicate book across cursor pages")
			}
			ids[i], seen[item.ID] = item.ID, true
		}
		rows, err := db.Query(ctx, `SELECT id,source_id FROM book_records WHERE id=ANY($1::text[])`, ids)
		if err != nil {
			t.Fatal(err)
		}
		sources := map[string]string{}
		for rows.Next() {
			var id, source string
			if err := rows.Scan(&id, &source); err != nil {
				t.Fatal(err)
			}
			sources[id] = source
		}
		rows.Close()
		if err := rows.Err(); err != nil {
			t.Fatal(err)
		}
		for _, item := range lane.Items {
			want := books.SelectedCover(item.ID, sources[item.ID])
			if want == nil {
				if item.Cover != nil {
					t.Fatalf("unselected cover exposed for %s", item.ID)
				}
			} else if item.Cover == nil || *item.Cover != *want {
				t.Fatalf("cover identity or provenance mismatch for %s", item.ID)
			} else {
				covers++
			}
		}
		var plan []byte
		if err := db.QueryRow(ctx, `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT id,source_id FROM book_records WHERE id=ANY($1::text[])`, ids).Scan(&plan); err != nil {
			t.Fatal(err)
		}
		var report []map[string]any
		if err := json.Unmarshal(plan, &report); err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(string(plan), "Index") {
			t.Fatal("bounded cover identity lookup did not use an index")
		}
		t.Logf("page %d: %d IDs; indexed cover identity lookup %.3f ms", page+1, len(ids), report[0]["Execution Time"])
		f.After = map[string]string{"book": lane.NextCursor}
	}
	if covers == 0 || covers == len(seen) {
		t.Fatal("expected both reviewed covers and missing-cover cases in the real sample")
	}
	t.Logf("verified %d books across two pages, %d reviewed covers", len(seen), covers)
}
