package catalog

import (
	"context"
	"errors"
	"os"
	"testing"

	"github.com/vadimdulub/artline/apps/server/internal/testdb"
)

func TestMuseumsAndMustSee(t *testing.T) {
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
	repo := &Repository{db: tx}
	// Writes are contained by this outer transaction, including nested savepoints.
	f := MuseumFilter{Limit: 24}
	page, err := repo.Museums(ctx, f, true)
	if err != nil {
		t.Fatal(err)
	}
	if page.Total != 7 || len(page.Items) != 7 {
		t.Fatalf("museum seed: %+v", page)
	}
	public, err := repo.Museums(ctx, f, false)
	if err != nil || public.Total != 0 || len(public.Facets.Countries) != 0 {
		t.Fatalf("public leak: %+v %v", public, err)
	}
	for _, tc := range []struct {
		regions, countries []string
		want               int
	}{
		{[]string{"northern-america"}, nil, 2}, {[]string{"northern-europe"}, nil, 2},
		{[]string{"northern-america", "northern-europe"}, nil, 4},
		{[]string{"northern-america", "northern-europe"}, []string{"DK"}, 1},
	} {
		q := f
		q.Regions = tc.regions
		q.Countries = tc.countries
		p, e := repo.Museums(ctx, q, true)
		if e != nil || p.Total != tc.want {
			t.Fatalf("region/country: %+v %v", p, e)
		}
	}
	q := f
	q.Selection = "museum"
	p, err := repo.Museums(ctx, q, true)
	if err != nil || p.Total != 1 {
		t.Fatalf("highlight filter %+v %v", p, err)
	}
	q.Display = "on_view"
	p, err = repo.Museums(ctx, q, true)
	if err != nil || p.Total != 0 {
		t.Fatalf("holding became display %+v %v", p, err)
	}
	met, err := repo.Museum(ctx, "the-met", true)
	if err != nil {
		t.Fatal(err)
	}
	if met.WorkCount != 3 || met.HighlightCount != 2 || met.OnViewCount != 0 || len(met.Venues) != 2 {
		t.Fatalf("met: %+v", met)
	}
	works, err := repo.MuseumWorks(ctx, "the-met", f, true)
	if err != nil {
		t.Fatal(err)
	}
	if works.Total != 3 || len(works.Items) != 3 {
		t.Fatalf("works: %+v", works)
	}
	q = f
	q.Selection = "museum"
	q.Sort = "curated"
	q.Limit = 1
	first, err := repo.MuseumWorks(ctx, "the-met", q, true)
	if err != nil {
		t.Fatal(err)
	}
	if first.Total != 2 || first.NextCursor == "" || first.Items[0].Slug != "rembrandt-self-portrait-1660" {
		t.Fatalf("first page: %+v", first)
	}
	q.Cursor = first.NextCursor
	second, err := repo.MuseumWorks(ctx, "the-met", q, true)
	if err != nil {
		t.Fatal(err)
	}
	if len(second.Items) != 1 || second.Items[0].Slug != "monet-bridge-over-a-pond-of-water-lilies" || second.NextCursor != "" {
		t.Fatalf("second: %+v", second)
	}
	q.Query = "changed"
	if _, err = repo.MuseumWorks(ctx, "the-met", q, true); !errors.Is(err, ErrMuseumFilter) {
		t.Fatalf("cursor not bound: %v", err)
	}
	detail, err := repo.MuseumArtwork(ctx, "the-met", first.Items[0].ID, true)
	if err != nil {
		t.Fatal(err)
	}
	if detail.Holding == nil || detail.Holding.Slug != "the-met" || detail.Display != nil || len(detail.Citations) == 0 {
		t.Fatalf("detail: %+v", detail)
	}
	input := MustSeeInput{ArtworkID: detail.ID, Selected: true, Position: 1, Reason: "Study the painted light", ExpectedRevision: met.OwnerRevision}
	revision, err := repo.SaveMustSee(ctx, "the-met", input)
	if err != nil {
		t.Fatal(err)
	}
	if revision != met.OwnerRevision+1 {
		t.Fatal("revision not incremented")
	}
	if _, err = repo.SaveMustSee(ctx, "the-met", input); !errors.Is(err, ErrRevisionConflict) {
		t.Fatalf("stale selection accepted: %v", err)
	}
	q = f
	q.Selection = "owner"
	p, err = repo.Museums(ctx, q, true)
	if err != nil || p.Total != 1 {
		t.Fatalf("must-see: %+v %v", p, err)
	}
	detail, err = repo.MuseumArtwork(ctx, "the-met", detail.ID, true)
	if err != nil || len(detail.Selections) != 2 {
		t.Fatalf("selection detail: %+v %v", detail, err)
	}
	input.ExpectedRevision = revision
	input.Selected = false
	if _, err = repo.SaveMustSee(ctx, "the-met", input); err != nil {
		t.Fatal(err)
	}
	// Nested visibility gates: publishing an institution or artwork alone must
	// not expose an unpublished artist, highlight membership or venue.
	if _, err = tx.Exec(ctx, `UPDATE institutions SET status='published' WHERE slug='the-met';
      UPDATE artworks SET status='published' WHERE slug='rembrandt-self-portrait-1660'`); err != nil {
		t.Fatal(err)
	}
	public, err = repo.Museums(ctx, f, false)
	if err != nil || public.Total != 0 {
		t.Fatalf("private painter leaked: %+v %v", public, err)
	}
	if _, err = tx.Exec(ctx, `UPDATE artists SET status='published' WHERE slug='rembrandt'`); err != nil {
		t.Fatal(err)
	}
	public, err = repo.Museums(ctx, f, false)
	if err != nil || public.Total != 1 {
		t.Fatalf("public gating: %+v %v", public, err)
	}
	if public.Items[0].WorkCount != 1 || public.Items[0].HighlightCount != 0 || len(public.Items[0].Venues) != 0 || public.Items[0].OwnerRevision != 0 {
		t.Fatalf("nested private data leaked: %+v", public.Items[0])
	}
	if _, err = tx.Exec(ctx, `UPDATE curated_collections SET status='published' WHERE institution_id=(SELECT id FROM institutions WHERE slug='the-met') AND curator_kind='museum'`); err != nil {
		t.Fatal(err)
	}
	public, err = repo.Museums(ctx, f, false)
	if err != nil || public.Items[0].HighlightCount != 1 {
		t.Fatalf("highlight visibility: %+v %v", public, err)
	}
}

func TestMuseumDisplayAndIndependentWorkSelection(t *testing.T) {
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
	repo := &Repository{db: tx}
	// A reviewed loan at another museum must not change the holding institution.
	var id string
	err = tx.QueryRow(ctx, `INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,venue_id,display_state,context,source_id,source_url,evidence_note,checked_at,review_state)
 SELECT aw.id,'display',i.id,v.id,'on_view','loan',s.id,'https://example.org/test-only','Test fixture, never a real display claim',now(),'accepted'
 FROM artworks aw,institutions i,institution_venues v,sources s
 WHERE aw.slug='rembrandt-self-portrait-1660' AND i.slug='national-gallery-of-art' AND v.slug='nga-west-building' AND s.slug='nga-washington' RETURNING id::text`).Scan(&id)
	if err != nil {
		t.Fatal(err)
	}
	nga, err := repo.Museum(ctx, "national-gallery-of-art", true)
	if err != nil {
		t.Fatal(err)
	}
	if nga.WorkCount != 3 || nga.HoldingCount != 2 || nga.OnViewCount != 1 {
		t.Fatalf("loan totals: %+v", nga)
	}
	met, err := repo.Museum(ctx, "the-met", true)
	if err != nil || met.HoldingCount != 3 || met.OnViewCount != 0 {
		t.Fatalf("loan ownership: %+v %v", met, err)
	}
	f := MuseumFilter{Limit: 24, Display: "on_view"}
	works, err := repo.MuseumWorks(ctx, "national-gallery-of-art", f, true)
	if err != nil || works.Total != 1 {
		t.Fatalf("loan filter: %+v %v", works, err)
	}
	if _, err = tx.Exec(ctx, `UPDATE artwork_location_assertions SET checked_at=now()-interval '31 days' WHERE id=$1`, id); err != nil {
		t.Fatal(err)
	}
	works, err = repo.MuseumWorks(ctx, "national-gallery-of-art", f, true)
	if err != nil || works.Total != 0 {
		t.Fatalf("stale display confirmed %+v %v", works, err)
	}
	if _, err = tx.Exec(ctx, `UPDATE artwork_location_assertions SET checked_at=now(),review_state='conflict' WHERE id=$1`, id); err != nil {
		t.Fatal(err)
	}
	works, err = repo.MuseumWorks(ctx, "national-gallery-of-art", f, true)
	if err != nil || works.Total != 0 {
		t.Fatalf("conflict confirmed %+v %v", works, err)
	}
	// Not-on-view can be known without identifying a physical venue.
	if _, err = tx.Exec(ctx, `UPDATE artwork_location_assertions SET review_state='accepted',display_state='not_on_view',venue_id=NULL WHERE id=$1`, id); err != nil {
		t.Fatal(err)
	}
	var workID string
	if err = tx.QueryRow(ctx, `SELECT id::text FROM artworks WHERE slug='rembrandt-self-portrait-1660'`).Scan(&workID); err != nil {
		t.Fatal(err)
	}
	detail, err := repo.MuseumArtwork(ctx, "the-met", workID, true)
	if err != nil || detail.Display == nil || detail.Display.State != "not_on_view" {
		t.Fatalf("explicit non-display lost: %+v %v", detail, err)
	}
	// The ID-scoped painter enrichment must agree with museum display policy.
	for _, tc := range []struct{ state, review, age, want string }{
		{"not_on_view", "accepted", "0 days", "not_on_view"},
		{"on_view", "accepted", "0 days", "on_view"},
		{"on_view", "accepted", "31 days", "stale"},
		{"on_view", "conflict", "0 days", ""},
	} {
		if _, err = tx.Exec(ctx, `UPDATE artwork_location_assertions SET display_state=$2,review_state=$3,checked_at=now()-$4::interval,
 venue_id=CASE WHEN $2='on_view' THEN (SELECT id FROM institution_venues WHERE slug='nga-west-building') ELSE NULL END WHERE id=$1`, id, tc.state, tc.review, tc.age); err != nil {
			t.Fatal(err)
		}
		work, e := repo.ArtistArtwork(ctx, "rembrandt", workID, true)
		if e != nil {
			t.Fatal(e)
		}
		if (tc.want == "" && work.Display != nil) || (tc.want != "" && (work.Display == nil || work.Display.State != tc.want)) {
			t.Fatalf("painter display policy: want %s, got %+v", tc.want, work.Display)
		}
		if work.Holding == nil || work.Holding.Slug != "the-met" {
			t.Fatal("display enrichment changed holding")
		}
	}
	// Museum browsing must not inherit the representative-only query restriction.
	if _, err = tx.Exec(ctx, `UPDATE artwork_artists SET representative_order=NULL WHERE artwork_id=(SELECT id FROM artworks WHERE slug='rembrandt-self-portrait-1660')`); err != nil {
		t.Fatal(err)
	}
	works, err = repo.MuseumWorks(ctx, "the-met", MuseumFilter{Limit: 24}, true)
	if err != nil || works.Total != 3 {
		t.Fatalf("representative cap: %+v %v", works, err)
	}
}
