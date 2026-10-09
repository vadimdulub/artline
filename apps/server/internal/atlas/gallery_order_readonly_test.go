package atlas

import (
	"context"
	"encoding/json"
	"net/url"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Audit real catalogue entries in a stable read-only snapshot. The small picked
// view spans every available medium, so pagination must cross priority groups
// even when graphic works have earlier dates than the preceding paintings.
func TestGalleryOrderReadOnly(t *testing.T) {
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
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	tx, err := db.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	rows, err := tx.Query(ctx, `WITH candidates AS (
 SELECT a.id::text,coalesce(a.creation_year_start,a.creation_year_end) AS start_year,a.work_type,coalesce(a.object_form,'') AS object_form,
 row_number() OVER(PARTITION BY a.work_type,a.object_form ORDER BY a.creation_year_start DESC,a.id) AS ordinal`+artScope+`
 AND EXISTS(SELECT 1 FROM media_assets image WHERE image.id=a.primary_media_id AND image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$'))
 SELECT id,start_year,work_type,object_form FROM candidates WHERE ordinal<=2`, Bounds.Start, Bounds.End, "", false, "")
	if err != nil {
		t.Fatal(err)
	}
	var expected []Item
	ids, media := []string{}, map[string]bool{}
	icon := false
	for rows.Next() {
		var item Item
		var workType, form string
		if err := rows.Scan(&item.ID, &item.StartYear, &workType, &form); err != nil {
			t.Fatal(err)
		}
		switch workType {
		case "painting", "fresco", "watercolor", "manuscript_illumination":
			item.galleryPriority = 0
		case "drawing", "print", "calligraphy":
			item.galleryPriority = 2
		default:
			item.galleryPriority = 1
		}
		media[workType] = true
		icon = icon || form == "icon"
		expected = append(expected, item)
		ids = append(ids, item.ID)
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		t.Fatal(err)
	}
	for _, medium := range []string{"painting", "fresco", "drawing", "print"} {
		if !media[medium] {
			t.Fatalf("real sample lacks %s", medium)
		}
	}
	if !icon || len(ids) > 60 {
		t.Fatal("sample must include an icon and fit the bounded picks limit")
	}
	slices.SortFunc(expected, compareGalleryItems)
	recorder := &discoveryPlanDB{atlasDB: tx}
	repo := &Repository{db: recorder}
	f := Filter{Range: Bounds, Limit: 3, Selection: true, Picks: map[string][]string{"artwork": ids}}
	var got []Item
	for page := 0; page <= len(ids)/f.Limit; page++ {
		out, err := repo.List(ctx, f)
		if err != nil {
			t.Fatal(err)
		}
		lane := out.Lanes[0]
		if lane.Total != len(ids) || len(lane.Items) > f.Limit {
			t.Fatalf("sort changed membership or page bound: %+v", lane)
		}
		got = append(got, lane.Items...)
		if lane.NextCursor == "" {
			break
		}
		f.After = map[string]string{"artwork": lane.NextCursor}
	}
	if !slices.EqualFunc(got, expected, func(a, b Item) bool { return a.ID == b.ID && a.galleryPriority == b.galleryPriority }) {
		t.Fatal("gallery pages skipped, repeated, or reordered selected works")
	}
	for index, item := range got {
		if index == 0 || item.galleryPriority == got[index-1].galleryPriority {
			continue
		}
		nav := f
		nav.After, nav.Types, nav.Limit = nil, []string{"artwork"}, 1
		// Keep this a picked-only lane, including for the neighbour lookup.
		nav.Entities = map[string]url.Values{"artwork": {"painter": {"no-matching-painter"}}}
		for _, direction := range []string{"next", "previous"} {
			nav.Direction, nav.NeighborOf = direction, got[index-1].ID
			want := item.ID
			if direction == "previous" {
				nav.NeighborOf, want = item.ID, got[index-1].ID
			}
			out, err := repo.List(ctx, nav)
			if err != nil || len(out.Lanes) != 1 || len(out.Lanes[0].Items) != 1 || out.Lanes[0].Items[0].ID != want {
				t.Fatalf("%s failed across a medium group: %+v %v", direction, out, err)
			}
		}
	}
	t.Logf("all %d works across %d media retained through group/page boundaries", len(got), len(media))

	// The real filters used by All and Painters must select the preferred works
	// before the page limit, and an explicit Print filter must still show prints.
	for _, tc := range []struct {
		name   string
		filter Filter
	}{
		{"all", Filter{Range: Bounds, Types: []string{"artwork"}, Limit: 30}},
		{"all-highlights", Filter{Range: Bounds, Types: []string{"artwork"}, Limit: 30, Highlights: true}},
		{"painter", Filter{Range: Bounds, Types: []string{"artwork"}, Limit: 60, Entities: map[string]url.Values{"artwork": {"painter": {"rembrandt"}}}}},
		{"prints", Filter{Range: Bounds, Types: []string{"artwork"}, Limit: 30, Entities: map[string]url.Values{"artwork": {"painter": {"rembrandt"}, "work_type": {"print"}}}}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			recorder.statements = nil
			started := time.Now()
			out, err := repo.List(ctx, tc.filter)
			if err != nil || len(out.Lanes) != 1 || len(out.Lanes[0].Items) != tc.filter.Limit {
				t.Fatalf("missing real gallery sample: %+v %v", out, err)
			}
			want := 0
			if tc.name == "prints" {
				want = 2
			}
			for _, item := range out.Lanes[0].Items {
				if item.galleryPriority != want || item.MediaURL == "" {
					t.Fatalf("unexpected first-page medium or missing image: %+v", item)
				}
			}
			t.Logf("%d matching artworks; first page in %s", out.Total, time.Since(started))
			if tc.name != "all" && tc.name != "painter" {
				return
			}
			statement := recorder.statements[0]
			var plan []byte
			if err := tx.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+statement.query, statement.args...).Scan(&plan); err != nil {
				t.Fatal(err)
			}
			if tc.name == "painter" && (!strings.Contains(string(plan), "artwork_artists_artist_work_idx") || !strings.Contains(string(plan), "artworks_pkey")) {
				t.Fatal("painter gallery lost indexed creator/artwork lookups")
			}
			var decoded []struct {
				ExecutionTime float64 `json:"Execution Time"`
			}
			if err := json.Unmarshal(plan, &decoded); err != nil {
				t.Fatal(err)
			}
			t.Logf("query plan: %.2fms", decoded[0].ExecutionTime)
			if dir := os.Getenv("ARTLINE_ATLAS_AUDIT_DIR"); dir != "" {
				if err := os.MkdirAll(dir, 0700); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(filepath.Join(dir, "gallery-order-"+tc.name+"-plan.json"), plan, 0600); err != nil {
					t.Fatal(err)
				}
			}
		})
	}
}
