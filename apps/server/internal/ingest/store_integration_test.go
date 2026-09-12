package ingest

import (
	"context"
	"fmt"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/db/migrations"
)

func TestStoreIdempotenceAndPreservesEdits(t *testing.T) {
	db := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if db == "" {
		t.Skip("database URL not set")
	}
	ctx := context.Background()
	admin, err := pgxpool.New(ctx, db)
	if err != nil {
		t.Fatal(err)
	}
	defer admin.Close()
	schema := fmt.Sprintf("artline_import_test_%d", time.Now().UnixNano())
	quoted := pgx.Identifier{schema}.Sanitize()
	if _, err = admin.Exec(ctx, "CREATE SCHEMA "+quoted); err != nil {
		t.Fatal(err)
	}
	// Only this uniquely created test schema is removed. Public data is untouched.
	defer func() {
		if _, e := admin.Exec(ctx, "DROP SCHEMA "+quoted+" CASCADE"); e != nil {
			t.Error(e)
		}
	}()
	cfg, err := pgxpool.ParseConfig(db)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["search_path"] = schema + ",public"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	entries, _ := migrations.Files.ReadDir(".")
	for _, e := range entries {
		if !strings.HasSuffix(e.Name(), ".sql") {
			continue
		}
		b, err := migrations.Files.ReadFile(e.Name())
		if err != nil {
			t.Fatal(err)
		}
		if _, err = pool.Exec(ctx, string(b)); err != nil {
			t.Fatalf("%s: %v", e.Name(), err)
		}
	}
	s := Store{pool}
	sid, err := s.Source(ctx, "pantheon")
	if err != nil {
		t.Fatal(err)
	}
	job, err := s.Job(ctx, sid, "fixture-painters", map[string]any{})
	if err != nil {
		t.Fatal(err)
	}
	death := 1880
	p := Painter{Name: "Import Fixture Painter", QID: "Q987654321", Birth: 1800, Death: &death, Rank: 1, Score: 50, Country: "France", SourceSlug: "Import_Fixture_Painter", Raw: map[string]string{"name": "Import Fixture Painter"}}
	if err = s.Painter(ctx, job, sid, &p); err != nil {
		t.Fatal(err)
	}
	original := p.ID
	var popular bool
	if err = pool.QueryRow(ctx, `SELECT is_popular FROM artist_discovery_selection WHERE artist_id=$1`, p.ID).Scan(&popular); err != nil || !popular {
		t.Fatal("fresh import did not seed discovery", err)
	}
	if _, err = pool.Exec(ctx, `UPDATE artist_discovery_selection SET is_popular=false,basis='Owner exclusion' WHERE artist_id=$1`, p.ID); err != nil {
		t.Fatal(err)
	}
	if _, err = pool.Exec(ctx, `UPDATE artists SET biography_md='Owner prose',revision=revision+1 WHERE id=$1`, p.ID); err != nil {
		t.Fatal(err)
	}
	if err = s.Painter(ctx, job, sid, &p); err != nil {
		t.Fatal(err)
	}
	if p.ID != original {
		t.Fatal("duplicate painter created")
	}
	if err = pool.QueryRow(ctx, `SELECT is_popular FROM artist_discovery_selection WHERE artist_id=$1`, p.ID).Scan(&popular); err != nil || popular {
		t.Fatal("import overwrote discovery curation", err)
	}
	var bio string
	if err = pool.QueryRow(ctx, `SELECT biography_md FROM artists WHERE id=$1`, p.ID).Scan(&bio); err != nil || bio != "Owner prose" {
		t.Fatal("owner prose overwritten", err)
	}
	met, err := s.Source(ctx, "met")
	if err != nil {
		t.Fatal(err)
	}
	museum, err := s.Institution(ctx, "met", met)
	if err != nil {
		t.Fatal(err)
	}
	wjob, err := s.Job(ctx, met, "fixture-works", map[string]any{})
	if err != nil {
		t.Fatal(err)
	}
	w := fixture()
	w.ArtistName = p.Name
	created, err := s.Work(ctx, wjob, met, museum, p, w, nil, "")
	if err != nil || !created {
		t.Fatal("first work import", err)
	}
	created, err = s.Work(ctx, wjob, met, museum, p, w, nil, "")
	if err != nil || created {
		t.Fatal("duplicate work import", err)
	}
	var n int
	if err = pool.QueryRow(ctx, `SELECT count(*) FROM external_identifiers WHERE scheme='met-object' AND external_id='123'`).Scan(&n); err != nil || n != 1 {
		t.Fatal("identity not unique", n, err)
	}
	if err = pool.QueryRow(ctx, `SELECT count(*) FROM artwork_location_assertions WHERE claim_type='display'`).Scan(&n); err != nil || n != 0 {
		t.Fatal("invented on-view claim", err)
	}
	w.Highlight = false
	if _, err = s.Work(ctx, wjob, met, museum, p, w, nil, ""); err == nil {
		t.Fatal("ordinary artwork passed import gate")
	}
	w = fixture()
	w.Rights = "restricted"
	if _, err = s.Work(ctx, wjob, met, museum, p, w, &ImageFile{Path: "/assets/not-allowed.jpg"}, ""); err == nil {
		t.Fatal("restricted media passed store gate")
	}
	w = fixture()
	w.Raw["title"] = "Changed source"
	if _, err = s.Work(ctx, wjob, met, museum, p, w, nil, ""); err == nil {
		t.Fatal("changed source silently accepted")
	}
	testReviewedMuseumStore(t, ctx, s, p)
}
