package atlas

import (
	"context"
	"fmt"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Fixtures are allowed ONLY in the isolated disposable cluster under /tmp.
// Neither the real local catalogue nor a remote database can pass this guard.
func browseFixturePool(t *testing.T) (*pgxpool.Pool, context.Context) {
	t.Helper()
	dsn := os.Getenv("ARTLINE_ATLAS_FIXTURE_DATABASE_URL")
	if dsn == "" {
		t.Skip("isolated browse fixture cluster not requested")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(cfg.ConnConfig.Host, "/tmp/artline-atlas-browse-") || cfg.ConnConfig.Port != 55439 || cfg.ConnConfig.User != "artline_browse_fixture" {
		t.Fatal("refusing fixture writes outside isolated cluster")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	t.Cleanup(cancel)
	db, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(db.Close)
	var dir string
	if err = db.QueryRow(ctx, "SHOW data_directory").Scan(&dir); err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(dir, "/tmp/artline-atlas-browse-") && !strings.HasPrefix(dir, "/private/tmp/artline-atlas-browse-") {
		t.Fatal("refusing non-disposable data directory")
	}
	return db, ctx
}

func TestBrowseProjectionChangesAndConcurrentRefresh(t *testing.T) {
	db, ctx := browseFixturePool(t)
	exec := func(q string, args ...any) {
		t.Helper()
		if _, err := db.Exec(ctx, q, args...); err != nil {
			t.Fatal(err)
		}
	}
	id := func(q string, args ...any) string {
		t.Helper()
		var v string
		if err := db.QueryRow(ctx, q, args...).Scan(&v); err != nil {
			t.Fatal(err)
		}
		return v
	}
	source := id(`INSERT INTO sources(slug,name,source_type) VALUES(gen_random_uuid()::text,'Browse fixture','manual') RETURNING id::text`)
	institution := id(`INSERT INTO institutions(slug,name,normalized_name,status) VALUES(gen_random_uuid()::text,'Browse fixture','browse fixture','review') RETURNING id::text`)
	media := id(`INSERT INTO media_assets(storage_kind,storage_path,rights_status) VALUES('local','/assets/fixture-'||gen_random_uuid()::text||'.jpg','unknown') RETURNING id::text`)
	artwork := id(`INSERT INTO artworks(slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,primary_media_id,status)
 VALUES(gen_random_uuid()::text,'Fixture','fixture','1750',1750,1750,'exact','painting',$1,'review') RETURNING id::text`, media)
	holding := id(`INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,source_id,source_url,evidence_note,checked_at,review_state)
 VALUES($1,'holding',$2,$3,'https://example.test/object','Fixture only',now(),'accepted') RETURNING id::text`, artwork, institution, source)
	visible := func(want bool) {
		t.Helper()
		var got bool
		if err := db.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM artwork_atlas_browse WHERE id=$1)", artwork).Scan(&got); err != nil {
			t.Fatal(err)
		}
		if got != want {
			t.Fatalf("visible=%v want=%v", got, want)
		}
	}
	drain := func() {
		t.Helper()
		for i := 0; i < 30; i++ {
			n, err := RefreshBrowseBatch(ctx, db, 500)
			if err != nil {
				t.Fatal(err)
			}
			if n == 0 {
				return
			}
		}
		t.Fatal("fixture queue did not drain")
	}
	visible(true)
	drain()
	visible(true)
	for _, tc := range []struct {
		sql     string
		args    []any
		visible bool
	}{
		{"UPDATE media_assets SET storage_path='/remote/unavailable.jpg' WHERE id=$1", []any{media}, false},
		{"UPDATE media_assets SET storage_path='/assets/restored-'||id::text||'.jpg' WHERE id=$1", []any{media}, true},
		{"UPDATE artworks SET status='archived' WHERE id=$1", []any{artwork}, false},
		{"UPDATE artworks SET status='review' WHERE id=$1", []any{artwork}, true},
		{"UPDATE artworks SET creation_year_end=1971 WHERE id=$1", []any{artwork}, false},
		{"UPDATE artworks SET creation_year_end=1750 WHERE id=$1", []any{artwork}, true},
		{"UPDATE sources SET is_active=false WHERE id=$1", []any{source}, false},
		{"UPDATE sources SET is_active=true WHERE id=$1", []any{source}, true},
		{"UPDATE institutions SET status='archived' WHERE id=$1", []any{institution}, false},
		{"UPDATE institutions SET status='review' WHERE id=$1", []any{institution}, true},
		{"UPDATE artwork_location_assertions SET review_state='review' WHERE id=$1", []any{holding}, false},
		{"UPDATE artwork_location_assertions SET review_state='accepted' WHERE id=$1", []any{holding}, true},
	} {
		exec(tc.sql, tc.args...)
		visible(tc.visible)
		drain()
		visible(tc.visible)
	}
	artist := id(`INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status)
 VALUES(gen_random_uuid()::text,'Fixture','Fixture','fixture',1700,1800,'1700–1800','life','archived') RETURNING id::text`)
	exec("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role) VALUES($1,$2,'primary')", artwork, artist)
	visible(false)
	drain()
	visible(false)
	exec("UPDATE artists SET status='review' WHERE id=$1", artist)
	visible(true)
	drain()
	visible(true)
	exec("UPDATE artists SET status='archived' WHERE id=$1", artist)
	visible(false)
	exec("DELETE FROM artwork_artists WHERE artwork_id=$1", artwork)
	visible(true)
	drain()
	collection := id("INSERT INTO curated_collections(institution_id,curator_kind,title) VALUES($1,'owner','Fixture selection') RETURNING id::text", institution)
	item := id("INSERT INTO curated_collection_items(collection_id,artwork_id,position) VALUES($1,$2,1) RETURNING id::text", collection, artwork)
	exec("UPDATE artwork_location_assertions SET review_state='review' WHERE id=$1", holding)
	visible(true)
	drain()
	exec("UPDATE curated_collections SET status='archived' WHERE id=$1", collection)
	visible(false)
	drain()
	exec("UPDATE curated_collections SET status='review' WHERE id=$1", collection)
	visible(true)
	drain()
	exec("UPDATE curated_collections SET curator_kind='museum' WHERE id=$1", collection)
	visible(false)
	exec("UPDATE curated_collection_items SET source_id=$1,source_url='https://example.test/selection',checked_at=now() WHERE id=$2", source, item)
	visible(true)
	drain()
	exec("UPDATE sources SET is_active=false WHERE id=$1", source)
	visible(false)
	drain()
	exec("UPDATE sources SET is_active=true WHERE id=$1", source)
	visible(true)
	drain()
	exec("DELETE FROM curated_collection_items WHERE id=$1", item)
	visible(false)
	drain()
	exec("UPDATE artwork_location_assertions SET review_state='accepted' WHERE id=$1", holding)
	visible(true)
	drain()

	// A writer changes its source row while blocked on the refresher's marker.
	// The worker must not erase the writer's eventual invalidation.
	exec("UPDATE artworks SET creation_year_start=1749 WHERE id=$1", artwork)
	tx, err := db.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.ReadCommitted})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, "SELECT 1 FROM artwork_atlas_dirty WHERE artwork_id=$1 FOR UPDATE", artwork); err != nil {
		t.Fatal(err)
	}
	writer, err := db.Acquire(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer writer.Release()
	pid := writer.Conn().PgConn().PID()
	done := make(chan error, 1)
	go func() {
		_, e := writer.Exec(ctx, "UPDATE media_assets SET storage_path='/unavailable/concurrent.jpg' WHERE id=$1", media)
		done <- e
	}()
	blocked := false
	for until := time.Now().Add(3 * time.Second); time.Now().Before(until); time.Sleep(5 * time.Millisecond) {
		if err = db.QueryRow(ctx, "SELECT cardinality(pg_blocking_pids($1))>0", pid).Scan(&blocked); err != nil {
			t.Fatal(err)
		}
		if blocked {
			break
		}
	}
	if !blocked {
		t.Fatal("writer did not reach the marker conflict")
	}
	if err = refreshClaimedBrowse(ctx, tx, []string{artwork}); err != nil {
		t.Fatal(err)
	}
	if err = tx.Commit(ctx); err != nil {
		t.Fatal(err)
	}
	if err = <-done; err != nil {
		t.Fatal(err)
	}
	if id("SELECT count(*)::text FROM artwork_atlas_dirty WHERE artwork_id=$1", artwork) != "1" {
		t.Fatal("lost concurrent invalidation")
	}
	visible(false)
	drain()
	visible(false)
	exec("UPDATE media_assets SET storage_path='/assets/final-'||id::text||'.jpg' WHERE id=$1", media)
	visible(true)
	drain()
	// A rolled-back source change must not alter the view or leave dirty work.
	rollback, err := db.Begin(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = rollback.Exec(ctx, "UPDATE artworks SET status='archived' WHERE id=$1", artwork); err != nil {
		t.Fatal(err)
	}
	if err = rollback.Rollback(ctx); err != nil {
		t.Fatal(err)
	}
	visible(true)
	if id("SELECT count(*)::text FROM artwork_atlas_dirty WHERE artwork_id=$1", artwork) != "0" {
		t.Fatal("rolled-back marker survived")
	}
	exec("DELETE FROM artwork_location_assertions WHERE artwork_id=$1", artwork)
	exec("DELETE FROM artworks WHERE id=$1", artwork)
	visible(false)
	drain()
	if id("SELECT count(*)::text FROM artwork_atlas_projection WHERE id=$1", artwork) != "0" {
		t.Fatal("deleted projection survived")
	}
	t.Log("source changes, pending reads, refresh, rollback and concurrent invalidation verified")
}

func TestBrowseSnapshotAndAggregateReuse(t *testing.T) {
	db, ctx := browseFixturePool(t)
	// Existing disposable migration seeds supply a small selection. No source
	// fixtures are needed to prove cache reuse and snapshot consistency here.
	for i := 0; i < 30; i++ {
		n, err := RefreshBrowseBatch(ctx, db, 500)
		if err != nil {
			t.Fatal(err)
		}
		if n == 0 {
			break
		}
	}
	tx, err := db.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	var revision string
	if err = tx.QueryRow(ctx, "SELECT sum(revision)::text FROM catalogue_cache_revisions").Scan(&revision); err != nil {
		t.Fatal(err)
	}
	recorded := &performanceDB{atlasDB: tx}
	repo := &Repository{db: recorded, aggregates: newAggregateCache()}
	f := Filter{Range: Bounds, Types: []string{"artwork"}, Limit: 1}
	first, err := repo.list(ctx, f, revision)
	if err != nil {
		t.Fatal(err)
	}
	if len(first.Lanes) != 1 || first.Total == 0 {
		t.Fatal("expected disposable seed artworks")
	}
	before := len(recorded.statements)
	f.Limit = 2
	second, err := repo.list(ctx, f, revision)
	if err != nil {
		t.Fatal(err)
	}
	if first.Total != second.Total || len(recorded.statements)-before != 2 {
		t.Fatal("page-size change recomputed aggregates; expected page and image queries only")
	}
	emptyFilter := f
	emptyFilter.Query = "browse-fixture-impossible-search-58ea6208"
	before = len(recorded.statements)
	empty, err := repo.list(ctx, emptyFilter, revision)
	if err != nil || empty.Total != 0 || len(empty.Lanes) != 1 || len(empty.Lanes[0].Items) != 0 || len(recorded.statements)-before != 1 {
		t.Fatalf("empty search must issue only an aggregate query: %+v %v", empty, err)
	}
	artwork := first.Lanes[0].Items[0].ID
	if _, err = db.Exec(ctx, "UPDATE artworks SET status='archived' WHERE id=$1", artwork); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		_, _ = db.Exec(context.Background(), "UPDATE artworks SET status='review' WHERE id=$1", artwork)
	})
	old, err := repo.list(ctx, f, revision)
	if err != nil {
		t.Fatal(err)
	}
	if old.Total != first.Total || old.Lanes[0].Items[0].ID != artwork {
		t.Fatal("page escaped its aggregate snapshot")
	}
	latest, err := NewRepository(db).List(ctx, f)
	if err != nil {
		t.Fatal(err)
	}
	if latest.Total != first.Total-1 {
		t.Fatal(fmt.Sprintf("fresh snapshot did not invalidate aggregate: old=%d latest=%d", first.Total, latest.Total))
	}
}
