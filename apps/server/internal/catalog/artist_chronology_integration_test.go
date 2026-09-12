package catalog

import (
	"context"
	"errors"
	"os"
	"testing"

	"github.com/vadimdulub/artline/apps/server/internal/testdb"
)

func TestArtistChronology(t *testing.T) {
	url := os.Getenv("ARTLINE_TEST_DATABASE_URL")
	if url == "" {
		t.Skip("no test database")
	}
	ctx := context.Background()
	pool, err := testdb.Open(t, url)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.Begin(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	r := &Repository{db: tx}
	f := ArtistWorksFilter{Limit: 24}
	page, err := r.ArtistWorks(ctx, "giotto", f, true)
	if err != nil || page.Total != 5 || len(page.Years) != 1 || page.Years[0].Year != 1303 || page.Years[0].Count != 5 {
		t.Fatalf("seed: %+v %v", page, err)
	}
	if page.Items[0].DateDisplay == "1303" || len(page.Items[0].Citations) == 0 {
		t.Fatal("range labels or evidence lost")
	}
	// Long catalogue narratives belong to one opened record, not every card.
	if _, err = tx.Exec(ctx, `UPDATE artworks SET description_md='A sourced description for the detail record.' WHERE id=$1`, page.Items[0].ID); err != nil {
		t.Fatal(err)
	}
	descriptionDetail, err := r.ArtistArtwork(ctx, "giotto", page.Items[0].ID, true)
	if err != nil || descriptionDetail.DescriptionMD == nil || *descriptionDetail.DescriptionMD != "A sourced description for the detail record." {
		t.Fatal("missing detail description", err)
	}
	leanPage, err := r.ArtistWorks(ctx, "giotto", f, true)
	if err != nil {
		t.Fatal(err)
	}
	for _, w := range leanPage.Items {
		if w.DescriptionMD != nil {
			t.Fatal("long text leaked into chronology page")
		}
	}
	var seedStart, seedEnd int
	if err = tx.QueryRow(ctx, `SELECT timeline_start_year,timeline_end_year FROM artists WHERE slug='giotto'`).Scan(&seedStart, &seedEnd); err != nil {
		t.Fatal(err)
	}
	if len(page.Groups) != 1 || page.Groups[0].Count != 5 || !page.Groups[0].HasUncertainDates || page.RangeStart != seedStart || page.RangeEnd != seedEnd {
		t.Fatalf("server grouping/extent: %+v %d–%d", page.Groups, page.RangeStart, page.RangeEnd)
	}
	_, err = tx.Exec(ctx, `WITH added AS (
 INSERT INTO artworks(slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,status)
 SELECT 'chronology-fixture-'||n,'Study '||lpad(n::text,2,'0'),'study '||n,
 CASE WHEN n=33 THEN 'Date unknown' WHEN n=32 THEN 'Before 1320' ELSE '1310' END,
 CASE WHEN n>=32 THEN NULL ELSE 1310 END, CASE WHEN n=33 THEN NULL WHEN n=32 THEN 1320 ELSE 1310 END,
 CASE WHEN n=33 THEN 'unknown' WHEN n=32 THEN 'before' ELSE 'exact' END,'painting','review'
 FROM generate_series(1,33) n RETURNING id
 ) INSERT INTO artwork_artists(artist_id,artwork_id,attribution_role)
 SELECT a.id,added.id,'primary' FROM added,artists a WHERE a.slug='giotto';
 INSERT INTO artwork_artists(artist_id,artwork_id,attribution_role)
 SELECT a.id,w.id,'attributed_to' FROM artists a,artworks w WHERE a.slug='giotto' AND w.slug='chronology-fixture-1';`)
	if err != nil {
		t.Fatal(err)
	}
	page, err = r.ArtistWorks(ctx, "giotto", f, true)
	if err != nil || page.Total != 38 || len(page.Items) != 24 || page.UndatedCount != 1 || page.NextCursor == "" {
		t.Fatalf("all works dedup/paging: %+v %v", page, err)
	}
	seen := map[string]bool{}
	for _, w := range page.Items {
		seen[w.ID] = true
	}
	f.Cursor = page.NextCursor
	next, err := r.ArtistWorks(ctx, "giotto", f, true)
	if err != nil || len(next.Items) != 14 || next.NextCursor != "" {
		t.Fatalf("next page %+v %v", next, err)
	}
	for _, w := range next.Items {
		if seen[w.ID] {
			t.Fatal("duplicate page work")
		}
		seen[w.ID] = true
	}
	last := next.Items[len(next.Items)-1]
	if last.DatePrecision != "unknown" || last.CreationYearStart != nil || last.CreationYearEnd != nil {
		t.Fatal("unknown not last or date fabricated")
	}
	if next.Groups[len(next.Groups)-1].Year != nil {
		t.Fatal("undated group not terminal")
	}
	detail, err := r.ArtistArtwork(ctx, "giotto", last.ID, true)
	if err != nil || detail.RepresentativeOrder != nil || detail.ID != last.ID {
		t.Fatalf("nonrepresentative detail %+v %v", detail, err)
	}
	if _, err = r.ArtistArtwork(ctx, "rembrandt", last.ID, true); !errors.Is(err, ErrNotFound) {
		t.Fatal("unrelated painter exposed work")
	}
	year := 1310
	f.Year = &year
	if _, err = r.ArtistWorks(ctx, "giotto", f, true); !errors.Is(err, ErrChronologyFilter) {
		t.Fatalf("cursor scope: %v", err)
	}
	f = ArtistWorksFilter{Limit: 60, Year: &year}
	page, err = r.ArtistWorks(ctx, "giotto", f, true)
	if err != nil || page.MatchingTotal != 31 || len(page.Items) != 31 {
		t.Fatalf("same year: %+v %v", page, err)
	}
	f = ArtistWorksFilter{Limit: 24, Undated: true}
	page, err = r.ArtistWorks(ctx, "giotto", f, true)
	if err != nil || page.MatchingTotal != 1 || len(page.Items) != 1 {
		t.Fatalf("undated: %+v %v", page, err)
	}
	f = ArtistWorksFilter{Limit: 24}
	f.Cursor = "not-a-valid-cursor"
	if _, err = r.ArtistWorks(ctx, "giotto", f, true); !errors.Is(err, ErrChronologyFilter) {
		t.Fatal("invalid cursor accepted")
	}
	f.Cursor = ""
	if _, err = r.ArtistWorks(ctx, "giotto", f, false); !errors.Is(err, ErrNotFound) {
		t.Fatal("review painter leaked")
	}
	_, err = tx.Exec(ctx, `UPDATE artists SET status='published' WHERE slug='giotto'; UPDATE artworks SET status='published' WHERE slug='chronology-fixture-33'`)
	if err != nil {
		t.Fatal(err)
	}
	page, err = r.ArtistWorks(ctx, "giotto", f, false)
	if err != nil || page.Total != 1 || page.UndatedCount != 1 || len(page.Years) != 0 {
		t.Fatalf("nested visibility: %+v %v", page, err)
	}
	_, err = tx.Exec(ctx, `UPDATE artworks SET status='archived' WHERE id IN (SELECT artwork_id FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE a.slug='giotto')`)
	if err != nil {
		t.Fatal(err)
	}
	page, err = r.ArtistWorks(ctx, "giotto", f, true)
	if err != nil || page.Total != 0 || len(page.Items) != 0 || len(page.Years) != 0 {
		t.Fatalf("empty/archived: %+v %v", page, err)
	}
}
