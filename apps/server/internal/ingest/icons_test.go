package ingest

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestIconImportWithoutInventedAuthorities(t *testing.T) {
	dir := filepath.Join("../../../..", continuationDirectory("icons-athens"))
	manifest, err := os.ReadFile(filepath.Join(dir, "manifest.json"))
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(filepath.Join(dir, "chunk-001.json"))
	if err != nil {
		t.Fatal(err)
	}
	batch, err := continuationBatch(manifest, "chunk-001.json", data)
	if err != nil {
		t.Fatal(err)
	}
	if !batch.AllowUnlinkedCreators || len(batch.Painters) != 0 {
		t.Fatal("invented painter crosswalk")
	}
	pool := europeanDB(t)
	ctx := context.Background()
	var before int
	if err = pool.QueryRow(ctx, `SELECT count(*) FROM artists`).Scan(&before); err != nil {
		t.Fatal(err)
	}
	report, err := ImportContinuation(ctx, pool, manifest, "chunk-001.json", data, true)
	if err != nil {
		t.Fatal(err)
	}
	var after, linked, valid int
	if err = pool.QueryRow(ctx, `SELECT count(*) FROM artists`).Scan(&after); err != nil {
		t.Fatal(err)
	}
	if before != after || report.CreatedWorks != 15 {
		t.Fatalf("counts: before%d after%d %+v", before, after, report)
	}
	if err = pool.QueryRow(ctx, `SELECT count(*) FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE a.object_form='icon'`).Scan(&linked); err != nil || linked != 0 {
		t.Fatal("invented links", linked, err)
	}
	if err = pool.QueryRow(ctx, `SELECT count(*) FROM artworks WHERE object_form='icon' AND unlinked_creator_label IS NOT NULL AND cultural_context IS NOT NULL AND status='review' AND primary_media_id IS NULL`).Scan(&valid); err != nil || valid != 15 {
		t.Fatal("invalid icon state", valid, err)
	}
	// Even a differently pinned evidence wave must refuse a conflicting creator,
	// not silently repurpose an exact source identity that an editor has linked.
	var parsed europeanManifest
	json.Unmarshal(data, &parsed)
	var work europeanWork
	json.Unmarshal(parsed.Works[0], &work)
	id := report.Works[0].ID
	if _, err = pool.Exec(ctx, `INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role) SELECT $1,id,'primary' FROM artists LIMIT 1`, id); err != nil {
		t.Fatal(err)
	}
	batch.Version += "-conflict-fixture"
	if _, err = importEuropeanBatch(ctx, pool, data, false, batch); err == nil {
		t.Fatal("linked/unlinked identity conflict accepted")
	}
}
