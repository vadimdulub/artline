package ingest

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

func TestRussiaItalyEvidenceRollbackReplay(t *testing.T) {
	for _, tc := range []struct {
		name, path, sha   string
		works, highlights int
		importer          func(context.Context, *pgxpool.Pool, []byte, bool) (EuropeanImportReport, error)
	}{
		{"pushkin", PushkinCataloguePath, PushkinCatalogueSHA, 49, 49, ImportPushkinCatalogue},
		{"brera", BreraCataloguePath, BreraCatalogueSHA, 9, 0, ImportBreraCatalogue},
	} {
		t.Run(tc.name, func(t *testing.T) {
			data, err := os.ReadFile("../../../../" + tc.path)
			if err != nil || checksum(data) != tc.sha {
				t.Fatal("snapshot", err)
			}
			var m struct {
				Painters    map[string]string
				Works       []europeanWork
				Definitions map[string]europeanDefinition
			}
			if err = json.Unmarshal(data, &m); err != nil {
				t.Fatal(err)
			}
			seen := map[string]bool{}
			for _, w := range m.Works {
				d, err := europeanWorkDate(w)
				if err != nil || catalog.CreationScope(d.First, d.Last, d.Precision) != "eligible" || seen[w.ObjectID] || w.ObjectID == "" || w.Accession == "" || w.Description == "" || w.WorkType != "painting" || m.Painters[w.Painter] == "" || !europeanAllowedURL(m.Definitions, w.Institution, w.URL) {
					t.Fatal("invalid evidence", w.Title, err)
				}
				seen[w.ObjectID] = true
			}
			if len(seen) != tc.works {
				t.Fatal("count", len(seen))
			}
			ctx := context.Background()
			if _, err = tc.importer(ctx, nil, append(data, ' '), false); err == nil {
				t.Fatal("changed snapshot accepted")
			}
			pool := europeanDB(t)
			for _, q := range m.Painters {
				var exists bool
				if err = pool.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM external_identifiers WHERE scheme='wikidata' AND external_id=$1 AND entity_type='artist')`, q).Scan(&exists); err != nil {
					t.Fatal(err)
				}
				if exists {
					continue
				}
				var id string
				if err = pool.QueryRow(ctx, `INSERT INTO artists(slug,display_name,sort_name,normalized_name,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status) VALUES($1,$2,$2,$2,1100,1970,'Isolated test fixture','estimated','review') RETURNING id::text`, tc.name+"-test-"+strings.ToLower(q), q).Scan(&id); err != nil {
					t.Fatal(err)
				}
				if _, err = pool.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id) VALUES('artist',$1,'wikidata',$2)`, id, q); err != nil {
					t.Fatal(err)
				}
			}
			before := europeanCounts(t, pool)
			preview, err := tc.importer(ctx, pool, data, false)
			if err != nil || preview.Applied || europeanCounts(t, pool) != before {
				t.Fatal("rollback", err)
			}
			applied, err := tc.importer(ctx, pool, data, true)
			if err != nil || applied.CreatedWorks != tc.works || applied.AddedHighlights != tc.highlights {
				t.Fatal("apply", applied.CreatedWorks, err)
			}
			after := europeanCounts(t, pool)
			replay, err := tc.importer(ctx, pool, data, true)
			if err != nil || replay.CreatedWorks != 0 || replay.AddedCitations != 0 || replay.AddedHighlights != 0 || europeanCounts(t, pool) != after {
				t.Fatal("replay", err)
			}
		})
	}
}
