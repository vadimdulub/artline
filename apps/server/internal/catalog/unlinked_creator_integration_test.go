package catalog

import (
	"context"
	"errors"
	"github.com/vadimdulub/artline/apps/server/internal/testdb"
	"os"
	"testing"
)

func TestUnlinkedCreatorsMuseumVisibility(t *testing.T) {
	url := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if url == "" {
		t.Skip("no test database")
	}
	pool, err := testdb.Open(t, url)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	ctx := context.Background()
	tx, err := pool.Begin(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	r := &Repository{db: tx}
	var id string
	err = tx.QueryRow(ctx, `INSERT INTO artworks(slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,status,current_institution_id,unlinked_creator_label,cultural_context,object_form)
 SELECT 'unlinked-test','Virgin icon','virgin icon','14th century',1301,1400,'century','painting','review',id,'Workshops of Constantinople','Byzantine','icon' FROM institutions WHERE slug='the-met' RETURNING id::text`).Scan(&id)
	if err != nil {
		t.Fatal(err)
	}
	f := MuseumFilter{Limit: 1, Query: "Byzantine"}
	page, err := r.MuseumWorks(ctx, "the-met", f, true)
	if err != nil || page.Total != 1 || len(page.Items) != 1 || len(page.Items[0].Artists) != 0 || page.Items[0].UnlinkedCreatorLabel == nil || page.Items[0].ObjectForm == nil {
		t.Fatalf("unlinked cards: %+v %v", page, err)
	}
	if _, err = tx.Exec(ctx, `UPDATE artworks SET alternate_title='Alternate icon title' WHERE id=$1`, id); err != nil {
		t.Fatal(err)
	}
	aliasQuery := f
	aliasQuery.Query = "Alternate icon title"
	aliasPage, err := r.MuseumWorks(ctx, "the-met", aliasQuery, true)
	if err != nil || aliasPage.Total != 1 {
		t.Fatalf("alternate title not searchable: %+v %v", aliasPage, err)
	}
	museum, err := r.Museum(ctx, "the-met", true)
	if err != nil || museum.WorkCount != 4 {
		t.Fatalf("missing anonymous museum count: %+v %v", museum, err)
	}
	d, err := r.MuseumArtwork(ctx, "the-met", id, true)
	if err != nil || d.CulturalContext == nil || d.CreationYearStart == nil || *d.CreationYearStart != 1301 {
		t.Fatalf("detail: %+v %v", d, err)
	}
	f.Artists = []string{"claude-monet"}
	page, err = r.MuseumWorks(ctx, "the-met", f, true)
	if err != nil || page.Total != 0 {
		t.Fatalf("unlinked became Monet: %+v %v", page, err)
	}
	if _, err = r.MuseumArtwork(ctx, "the-met", id, false); !errors.Is(err, ErrNotFound) {
		t.Fatalf("review leaked: %v", err)
	}
	// Publish only within the disposable fixture transaction, never the owner catalogue.
	if _, err = tx.Exec(ctx, `UPDATE institutions SET status='published' WHERE slug='the-met'; UPDATE artworks SET status='published' WHERE slug='unlinked-test'`); err != nil {
		t.Fatal(err)
	}
	if _, err = r.MuseumArtwork(ctx, "the-met", id, false); err != nil {
		t.Fatal(err)
	}
	// An explicit label must never become a loophole around hidden linked creators.
	if tag, e := tx.Exec(ctx, `INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role) SELECT $1,id,'primary' FROM artists WHERE slug='claude-monet'`, id); e != nil || tag.RowsAffected() != 1 {
		t.Fatal("missing fixture artist", e)
	}
	if _, err = r.MuseumArtwork(ctx, "the-met", id, false); !errors.Is(err, ErrNotFound) {
		t.Fatalf("hidden artist bypass: %v", err)
	}
	if _, err = tx.Exec(ctx, `UPDATE artists SET status='archived' WHERE slug='claude-monet'`); err != nil {
		t.Fatal(err)
	}
	if _, err = r.MuseumArtwork(ctx, "the-met", id, true); !errors.Is(err, ErrNotFound) {
		t.Fatalf("archived artist bypass: %v", err)
	}
	// Plain missing links without a reviewed creator label remain hidden.
	if _, err = tx.Exec(ctx, `DELETE FROM artwork_artists WHERE artwork_id=$1`, id); err != nil {
		t.Fatal(err)
	}
	if _, err = tx.Exec(ctx, `UPDATE artworks SET unlinked_creator_label=NULL WHERE id=$1`, id); err != nil {
		t.Fatal(err)
	}
	if _, err = r.MuseumArtwork(ctx, "the-met", id, true); !errors.Is(err, ErrNotFound) {
		t.Fatalf("unreviewed missing creator visible: %v", err)
	}
}
