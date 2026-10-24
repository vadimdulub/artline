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
// picked view spans multiple media. Only paintings remain eligible, including
// when an older link explicitly supplies non-painting artwork IDs or filters.
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
	rows, err := tx.Query(ctx, `WITH sampled AS MATERIALIZED (
 SELECT sample.id FROM unnest(ARRAY['painting','fresco','drawing','print','photograph']) medium
 CROSS JOIN LATERAL (SELECT id FROM artworks WHERE work_type=medium AND status<>'archived'
 AND primary_media_id IS NOT NULL AND creation_year_end<=1970 LIMIT 24) sample
 UNION SELECT id FROM artworks WHERE object_form='icon' AND primary_media_id IS NOT NULL AND status<>'archived' LIMIT 144
 ), candidates AS (
 SELECT a.id::text,coalesce(a.creation_year_start,a.creation_year_end) AS start_year,a.work_type,coalesce(a.object_form,'') AS object_form,
	row_number() OVER(PARTITION BY a.work_type,a.object_form ORDER BY a.creation_year_start DESC,a.id) AS ordinal`+strings.Replace(artScope, "AND a.work_type='painting'", "", 1)+`
	 AND a.id IN(SELECT id FROM sampled)
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
		ids = append(ids, item.ID)
		if workType == "painting" {
			expected = append(expected, item)
		}
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
		if lane.Total != len(expected) || len(lane.Items) > f.Limit {
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
		if index == 0 {
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
				t.Fatalf("%s failed between chronological neighbours: %+v %v", direction, out, err)
			}
		}
	}
	t.Logf("%d paintings retained chronologically; picks from %d media checked", len(got), len(media))

	// All and its painter filter preserve chronology. A legacy Print filter
	// cannot override the catalogue's paintings-only browsing policy.
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
			if tc.name == "prints" {
				if err != nil || len(out.Lanes) != 1 || out.Lanes[0].Total != 0 || len(out.Lanes[0].Items) != 0 {
					t.Fatalf("non-paintings escaped catalogue filter: %+v %v", out, err)
				}
				return
			}
			if err != nil || len(out.Lanes) != 1 || len(out.Lanes[0].Items) != tc.filter.Limit {
				t.Fatalf("missing real gallery sample: %+v %v", out, err)
			}
			if !slices.IsSortedFunc(out.Lanes[0].Items, compareGalleryItems) {
				t.Fatal("gallery is not ordered by creation year")
			}
			for _, item := range out.Lanes[0].Items {
				var workType string
				if err := tx.QueryRow(ctx, "SELECT work_type FROM artworks WHERE id=$1::uuid", item.ID).Scan(&workType); err != nil {
					t.Fatal(err)
				}
				if item.MediaURL == "" || workType != "painting" {
					t.Fatalf("missing image or non-painting in gallery: %+v", item)
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
			if tc.name == "painter" && (!strings.Contains(string(plan), "artwork_artists_artist_work_idx") || !strings.Contains(string(plan), "artwork_atlas_projection_pkey")) {
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
	t.Run("wwii-paintings", func(t *testing.T) {
		out, err := repo.List(ctx, Filter{Range: Range{Start: 1933, End: 1955}, Types: []string{"artwork"}, PresetID: "second-world-war", Limit: 60})
		if err != nil || len(out.Lanes) != 1 || out.Lanes[0].NextCursor != "" {
			t.Fatalf("WWII selection unavailable or unexpectedly unbounded: %+v %v", out, err)
		}
		for _, id := range []string{"ce63eadb-ac6e-465a-a677-36ea881ed79c", "492d8809-9bf3-501b-aebf-61cf4ddfb6a7", "561236b7-9f3a-576c-a23a-4de005dd494f"} {
			if !slices.ContainsFunc(out.Lanes[0].Items, func(item Item) bool { return item.ID == id && item.MediaURL != "" }) {
				t.Fatalf("verified WWII painting missing: %s", id)
			}
		}
		t.Logf("%d illustrated paintings in the WWII context selection, including all three additions", out.Lanes[0].Total)
	})
}
