package ingest

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestContinuationPinsAndRollbackReplay(t *testing.T) {
	for source := range continuationPins {
		t.Run(source, func(t *testing.T) {
			dir := filepath.Join("../../../..", continuationDirectory(source))
			manifest, e := os.ReadFile(filepath.Join(dir, "manifest.json"))
			if e != nil {
				t.Fatal(e)
			}
			var m continuationManifest
			if e = json.Unmarshal(manifest, &m); e != nil {
				t.Fatal(e)
			}
			for _, c := range m.Chunks {
				data, e := os.ReadFile(filepath.Join(dir, c.File))
				if e != nil {
					t.Fatal(e)
				}
				if _, e = continuationBatch(manifest, c.File, data); e != nil {
					t.Fatal(c.File, e)
				}
			}
			file := m.Chunks[len(m.Chunks)-1].File
			data, e := os.ReadFile(filepath.Join(dir, file))
			if e != nil {
				t.Fatal(e)
			}
			batch, e := continuationBatch(manifest, file, data)
			if e != nil {
				t.Fatal(e)
			}
			if _, e = continuationBatch(append(manifest, ' '), file, data); e == nil {
				t.Fatal("changed manifest accepted")
			}
			if _, e = continuationBatch(manifest, file, append(data, ' ')); e == nil {
				t.Fatal("changed chunk accepted")
			}
			pool := europeanDB(t)
			ctx := context.Background()
			for _, q := range batch.Painters {
				var exists bool
				if e = pool.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM external_identifiers WHERE scheme='wikidata' AND external_id=$1)`, q).Scan(&exists); e != nil {
					t.Fatal(e)
				}
				if exists {
					continue
				}
				var id string
				if e = pool.QueryRow(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status) VALUES($1,$1,$1,$1,1100,1970,'Isolated test fixture','estimated','review') RETURNING id::text`, "continuation-test-"+q).Scan(&id); e != nil {
					t.Fatal(e)
				}
				if _, e = pool.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id) VALUES('artist',$1,'wikidata',$2)`, id, q); e != nil {
					t.Fatal(e)
				}
			}
			before := europeanCounts(t, pool)
			preview, e := ImportContinuation(ctx, pool, manifest, file, data, false)
			if e != nil || preview.Applied || europeanCounts(t, pool) != before {
				t.Fatal("rollback", e)
			}
			applied, e := ImportContinuation(ctx, pool, manifest, file, data, true)
			if e != nil || applied.CreatedWorks != batch.Works {
				t.Fatal("apply", applied.CreatedWorks, e)
			}
			// Owner-authored edits and intentional clears must survive replay.
			id := applied.Works[0].ID
			if _, e = pool.Exec(ctx, `UPDATE artworks SET title='Owner title',description_md=NULL,medium_text=NULL WHERE id=$1`, id); e != nil {
				t.Fatal(e)
			}
			after := europeanCounts(t, pool)
			replay, e := ImportContinuation(ctx, pool, manifest, file, data, true)
			if e != nil || replay.CreatedWorks != 0 || replay.AddedCitations != 0 || europeanCounts(t, pool) != after {
				t.Fatal("replay", e)
			}
			var clean bool
			if e = pool.QueryRow(ctx, `SELECT title='Owner title' AND description_md IS NULL AND medium_text IS NULL FROM artworks WHERE id=$1`, id).Scan(&clean); e != nil || !clean {
				t.Fatal("editor preservation", e)
			}
		})
	}
}
