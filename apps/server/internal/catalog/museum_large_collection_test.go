package catalog

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type museumPageTrace struct {
	query string
	args  []any
}

func (trace *museumPageTrace) TraceQueryStart(ctx context.Context, _ *pgx.Conn, data pgx.TraceQueryStartData) context.Context {
	if trace.query == "" && strings.Contains(data.SQL, "gallery_page_candidates") {
		trace.query, trace.args = data.SQL, append([]any{}, data.Args...)
	}
	return ctx
}

func (*museumPageTrace) TraceQueryEnd(context.Context, *pgx.Conn, pgx.TraceQueryEndData) {}

const previousAvailableImage = `EXISTS(SELECT 1 FROM media_assets image WHERE image.id=w.primary_media_id AND image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$')`

// Frozen pre-change page query for a reproducible comparison on an isolated
// 400,000-work collection. It never writes to a catalogue.
func (r *Repository) previousMuseumWorks(ctx context.Context, slug string, f MuseumFilter) (MuseumWorksPage, error) {
	out := MuseumWorksPage{Items: []MuseumWork{}, Facets: emptyMuseumFacets()}
	resolved, err := r.canonicalMuseumSlug(ctx, slug)
	if err != nil {
		return out, err
	}
	slug = resolved
	// Normalize before binding the cursor: an old chronological cursor must not
	// silently become a cursor into the image-first order.
	if f.Sort == "" {
		f.Sort = "images"
	}
	c, err := decodeMuseumCursor(f, slug)
	if err != nil {
		return out, err
	}
	// Preserve the exact visibility/membership policy without rebuilding the
	// museum's cover and six aggregate counts just to check its existence.
	var exists bool
	err = r.db.QueryRow(ctx, museumScopedCTE+`SELECT EXISTS(SELECT 1 FROM institutions i WHERE i.slug=$1 AND `+museumVisible+` AND EXISTS(SELECT 1 FROM works w WHERE `+museumMembership+`))`, museumQueryArgs(slug)...).Scan(&exists)
	if err != nil {
		return out, err
	}
	if !exists {
		return out, ErrNotFound
	}
	args := []any{slug, f.Query, f.Selection, f.Display, filterChoices(f.Artists, f.Artist), filterChoices(f.Movements, f.Movement), filterChoices(f.Venues, f.Venue), filterChoices(f.WorkTypes, f.WorkType), f.Start, f.End, f.UnknownDate, f.ImageOnly}
	where := ` FROM institutions i JOIN works w ON ` + museumMembership + ` WHERE i.slug=$1 AND ` + museumVisible + `
 AND ($2='' OR w.title ILIKE '%'||$2||'%' OR w.alternate_title ILIKE '%'||$2||'%' OR w.unlinked_creator_label ILIKE '%'||$2||'%'
 OR w.cultural_context ILIKE '%'||$2||'%' OR w.object_form ILIKE '%'||$2||'%'
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(w.artists) a WHERE a->>'name' ILIKE '%'||$2||'%'))
 AND ($3='' OR EXISTS(SELECT 1 FROM selections s WHERE s.institution_id=i.id AND s.artwork_id=w.id AND s.curator_kind=$3))
 AND ($4='' OR (w.display_institution_id=i.id AND w.display_state='on_view'))
 AND (cardinality($5::text[])=0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=w.id AND a.slug=ANY($5) AND a.status<>'archived' ))
 AND (cardinality($6::text[])=0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id JOIN artist_movements am ON am.artist_id=a.id JOIN movements m ON m.id=am.movement_id
 WHERE aa.artwork_id=w.id AND m.slug=ANY($6) AND a.status<>'archived' AND m.status<>'archived' ))
 AND (cardinality($7::text[])=0 OR (w.display_venue_id::text=ANY($7) AND w.display_institution_id=i.id AND w.display_state='on_view'))
 AND (cardinality($8::text[])=0 OR w.work_type=ANY($8))
 AND ($9::int IS NULL OR w.creation_year_end>=$9) AND ($10::int IS NULL OR w.creation_year_start<=$10)
 AND (NOT $11 OR w.creation_year_start IS NULL OR w.creation_year_end IS NULL) AND (NOT $12 OR ` + previousAvailableImage + `)`
	if err = r.db.QueryRow(ctx, museumScopedCTE+`SELECT count(*),count(*) FILTER (WHERE `+previousAvailableImage+`)`+where, museumQueryArgs(args...)...).Scan(&out.Total, &out.ImageCount); err != nil {
		return out, err
	}
	args = append(args, f.Sort, c.Number, c.Name, c.ID, f.Cursor == "", f.Limit+1)
	sortNumber := `CASE WHEN $13='images' THEN CASE WHEN ` + previousAvailableImage + ` THEN 0 ELSE 1 END WHEN $13='title' THEN 0 WHEN $13='curated' AND $3<>'' THEN coalesce((SELECT min(position) FROM selections s WHERE s.institution_id=i.id AND s.artwork_id=w.id AND s.curator_kind=$3),2147483647) ELSE coalesce(w.creation_year_start,2147483647) END`
	// Choose the bounded page before enriching cards. Otherwise PostgreSQL can
	// read every museum image row before sorting, even for a 24-work response.
	rows, err := r.db.Query(ctx, museumScopedCTE+`, page AS MATERIALIZED (
 SELECT w.id,`+sortNumber+` AS sort_number,w.normalized_title`+where+`
 AND ($17 OR (`+sortNumber+`,w.normalized_title,w.id::text)>($14,$15,$16))
 ORDER BY 2,w.normalized_title,w.id LIMIT $18)
 SELECT (SELECT `+workCardJSON+` FROM works w CROSS JOIN institutions i WHERE w.id=page.id AND i.slug=$1 OFFSET 0),page.sort_number,page.normalized_title
 FROM page ORDER BY page.sort_number,page.normalized_title,page.id`, museumQueryArgs(args...)...)
	if err != nil {
		return out, err
	}
	for rows.Next() {
		var item MuseumWork
		var data []byte
		if err = rows.Scan(&data, &item.SortNumber, &item.SortName); err != nil {
			break
		}
		if err = json.Unmarshal(data, &item); err != nil {
			break
		}
		out.Items = append(out.Items, item)
	}
	rows.Close()
	if err != nil {
		return out, err
	}
	if err = rows.Err(); err != nil {
		return out, err
	}
	if len(out.Items) > f.Limit {
		out.Items = out.Items[:f.Limit]
		last := out.Items[f.Limit-1]
		out.NextCursor = encodeMuseumCursor(f, slug, last.SortNumber, last.SortName, last.ID)
	}
	out.Facets, err = r.museumFacets(ctx, slug)
	return out, err
}

func TestMuseum400KCollection(t *testing.T) {
	dsn := os.Getenv("ARTLINE_MUSEUM_PERFORMANCE_DATABASE_URL")
	if dsn == "" {
		t.Skip("requires the separate 400,000-work fixture cluster")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()
	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	trace := &museumPageTrace{}
	config.ConnConfig.Tracer = trace
	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	var database string
	var port, n int
	if err = pool.QueryRow(ctx, `SELECT current_database(),inet_server_port(),(SELECT count(*) FROM artworks WHERE current_institution_id=md5('qa-large')::uuid)`).Scan(&database, &port, &n); err != nil {
		t.Fatal(err)
	}
	if database != "postgres" || port != 55442 || n != 400000 {
		t.Fatal("not the isolated large museum fixture")
	}
	repo := NewRepository(pool)
	ctx = WithCatalogueRevision(ctx, "fixture-400k-v1")
	started := time.Now()
	old, err := repo.previousMuseumWorks(ctx, "qa-large", MuseumFilter{Limit: 24})
	beforeTime := time.Since(started)
	if err != nil {
		t.Fatal("baseline", err)
	}
	// Compare empty application caches on both implementations. PostgreSQL's
	// buffer cache is warm; this is not a cold-disk or production load test.
	repo = NewRepository(pool)
	started = time.Now()
	first, err := repo.MuseumWorks(ctx, "qa-large", MuseumFilter{Limit: 24})
	coldTime := time.Since(started)
	if err != nil {
		t.Fatal("first page", err)
	}
	if first.Total != 400000 || first.ImageCount != 40000 || len(first.Items) != 24 || first.NextCursor == "" {
		t.Fatalf("invalid first page: total=%d images=%d returned=%d cursor=%q", first.Total, first.ImageCount, len(first.Items), first.NextCursor)
	}
	if old.Total != first.Total || old.ImageCount != first.ImageCount {
		t.Fatal("count policy changed")
	}
	seen := map[string]bool{}
	for _, w := range first.Items {
		seen[w.ID] = true
		if w.MediaURL == nil {
			t.Fatal("first highlighted page lacks image")
		}
		found := false
		for _, s := range w.Selections {
			found = found || s.Kind == "artlines"
		}
		if !found {
			t.Fatal("fallback selection missing")
		}
	}
	started = time.Now()
	second, err := repo.MuseumWorks(ctx, "qa-large", MuseumFilter{Limit: 24, Cursor: first.NextCursor})
	warmTime := time.Since(started)
	if err != nil {
		t.Fatal("second page", err)
	}
	if len(second.Items) != 24 {
		t.Fatal("page bound lost")
	}
	for _, w := range second.Items {
		if seen[w.ID] {
			t.Fatal("duplicate cursor item")
		}
	}
	highlights, err := repo.MuseumWorks(ctx, "qa-large", MuseumFilter{Limit: 24, Selection: "artlines", Sort: "curated"})
	if err != nil || highlights.Total != 24 || len(highlights.Items) != 24 || highlights.NextCursor != "" {
		t.Fatalf("fallback highlights: %+v %v", highlights, err)
	}
	if len(highlights.Facets.Artists) > museumEditorialHighlightLimit {
		t.Fatal("highlight facets scanned the full collection instead of the selected works")
	}
	official, err := repo.MuseumWorks(ctx, "qa-official", MuseumFilter{Limit: 24, Selection: "museum", Sort: "curated"})
	if err != nil || official.Total != 3 || len(official.Items) != 3 || official.Items[0].Slug != "qa-official-work-100" {
		t.Fatalf("official highlights: %+v %v", official, err)
	}
	summary, err := repo.Museum(ctx, "qa-large")
	if err != nil || summary.HighlightCount != 24 || summary.HighlightSource != "artlines" {
		t.Fatalf("fallback metadata: %+v %v", summary, err)
	}
	summary, err = repo.Museum(ctx, "qa-official")
	if err != nil || summary.HighlightCount != 3 || summary.HighlightSource != "museum" || summary.Cover == nil || summary.Cover.Slug != "qa-official-work-100" {
		t.Fatalf("official metadata: %+v %v", summary, err)
	}
	t.Logf("400,000 museum works plus 200,000 unrelated: previous page=%s; cold highlights page=%s; next page=%s; bounded 24 cards", beforeTime, coldTime, warmTime)
	if coldTime > 8*time.Second || warmTime > 8*time.Second {
		t.Fatal("gallery exceeds the eight-second API deadline")
	}
	var plan []byte
	if err := pool.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+trace.query, trace.args...).Scan(&plan); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(plan), "artworks_museum_image_title_seek_idx") {
		t.Fatal("large gallery lost its illustrated prefix index")
	}
	var decoded []map[string]any
	if err := json.Unmarshal(plan, &decoded); err != nil {
		t.Fatal(err)
	}
	var checkPrefix func(any)
	checkPrefix = func(value any) {
		switch node := value.(type) {
		case map[string]any:
			if index, ok := node["Index Name"].(string); ok && strings.HasPrefix(index, "artworks_museum_") {
				if rows, ok := node["Actual Rows"].(float64); ok && rows > 500 {
					t.Fatalf("page scanned the collection before LIMIT: %s read %.0f rows", index, rows)
				}
			}
			for _, child := range node {
				checkPrefix(child)
			}
		case []any:
			for _, child := range node {
				checkPrefix(child)
			}
		}
	}
	checkPrefix(decoded[0]["Plan"])
	if dir := os.Getenv("ARTLINE_MUSEUM_AUDIT_DIR"); dir != "" {
		if err := os.MkdirAll(dir, 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(dir, "museum-400k-page-plan.json"), plan, 0600); err != nil {
			t.Fatal(err)
		}
	}
	t.Run("low-query-memory", func(t *testing.T) {
		tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly})
		if err != nil {
			t.Fatal(err)
		}
		defer tx.Rollback(ctx)
		if _, err := tx.Exec(ctx, "SET LOCAL work_mem='64kB'"); err != nil {
			t.Fatal(err)
		}
		low := NewRepository(pool)
		low.db = tx
		// Isolate the uncached count query from already verified facet aggregation.
		low.facets.put(facetCacheKey(ctx, "museum:qa-large"), first.Facets)
		bounded, cancel := context.WithTimeout(ctx, 8*time.Second)
		defer cancel()
		page, err := low.MuseumWorks(bounded, "qa-large", MuseumFilter{Limit: 24})
		if err != nil || page.Total != 400000 || page.ImageCount != 40000 || len(page.Items) != 24 {
			t.Fatalf("large image count must spill safely under constrained memory: %+v %v", page, err)
		}
	})
	t.Run("deep-cursor", func(t *testing.T) {
		var name, id string
		if err := pool.QueryRow(ctx, "SELECT normalized_title,id::text FROM artworks WHERE slug='qa-work-390000'").Scan(&name, &id); err != nil {
			t.Fatal(err)
		}
		filter := MuseumFilter{Limit: 24, Sort: "images"}
		filter.Cursor = encodeMuseumCursor(filter, "qa-large", 0, name, id)
		trace.query, trace.args = "", nil
		page, err := repo.MuseumWorks(ctx, "qa-large", filter)
		if err != nil || len(page.Items) != 24 || page.Items[0].SortName <= name {
			t.Fatalf("deep page did not seek past the cursor: %+v %v", page, err)
		}
		var deepPlan []byte
		if err := pool.QueryRow(ctx, "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) "+trace.query, trace.args...).Scan(&deepPlan); err != nil {
			t.Fatal(err)
		}
		if err := json.Unmarshal(deepPlan, &decoded); err != nil {
			t.Fatal(err)
		}
		checkPrefix(decoded[0]["Plan"])
		if dir := os.Getenv("ARTLINE_MUSEUM_AUDIT_DIR"); dir != "" {
			if err := os.WriteFile(filepath.Join(dir, "museum-400k-deep-page-plan.json"), deepPlan, 0600); err != nil {
				t.Fatal(err)
			}
		}
	})
	t.Run("missing-and-unsupported-media", func(t *testing.T) {
		// This transaction runs only after the isolated cluster guard above.
		// Exercise the less common media branch without altering the base fixture.
		tx, err := pool.Begin(ctx)
		if err != nil {
			t.Fatal(err)
		}
		defer tx.Rollback(ctx)
		_, err = tx.Exec(ctx, `INSERT INTO media_assets
 SELECT (jsonb_populate_record(NULL::media_assets,to_jsonb(m)||jsonb_build_object(
 'id',md5('qa-unsupported-media')::uuid,'storage_path','https://example.invalid/qa.jpg'))).* FROM media_assets m LIMIT 1;
 UPDATE artworks SET primary_media_id=md5('qa-unsupported-media')::uuid WHERE slug='qa-official-work-97';
 UPDATE artworks SET primary_media_id=NULL WHERE slug='qa-official-work-96'`)
		if err != nil {
			t.Fatal(err)
		}
		edge := NewRepository(pool)
		edge.db = tx
		first, err := edge.MuseumWorks(ctx, "qa-official", MuseumFilter{Limit: 60, Sort: "images"})
		if err != nil || first.Total != 100 || first.ImageCount != 98 || len(first.Items) != 60 {
			t.Fatalf("mixed media first page: %+v %v", first, err)
		}
		last, err := edge.MuseumWorks(ctx, "qa-official", MuseumFilter{Limit: 60, Sort: "images", Cursor: first.NextCursor})
		if err != nil || len(last.Items) != 40 || last.NextCursor != "" || last.Items[38].Slug != "qa-official-work-96" || last.Items[39].Slug != "qa-official-work-97" {
			t.Fatalf("mixed media page boundary/order: %+v %v", last, err)
		}
	})
}
