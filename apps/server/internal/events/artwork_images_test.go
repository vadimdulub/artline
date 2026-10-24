package events

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func TestArtworkSelectionsRequireReviewedEventIdentity(t *testing.T) {
	for _, row := range []artworkSelection{
		{EventID: "missing", SourceID: "Q1", ArtworkSlug: "artwork"},
		{EventID: "event-q689128", SourceID: "Q1", ArtworkSlug: "artwork"},
		{EventID: "event-q689128", SourceID: "Q689128", ArtworkSlug: "../artwork"},
	} {
		t.Run(row.EventID+row.ArtworkSlug, func(t *testing.T) {
			defer func() {
				if recover() == nil {
					t.Fatal("unreviewed selection accepted")
				}
			}()
			raw, _ := json.Marshal([]artworkSelection{row})
			readArtworkSelection(raw)
		})
	}
}

func TestArtworkImagesNeverUseMismatchedEventSource(t *testing.T) {
	items := []Event{{ID: "event-q689128", SourceID: "Q1", Image: &Image{ImageURL: "unreviewed"}}}
	if err := ResolveImages(context.Background(), nil, items); err != nil || items[0].Image != nil {
		t.Fatal(items, err)
	}
}

func TestNewEventArtworkRequiresContextWithoutLegacyIllustration(t *testing.T) {
	row := artworkSelection{
		EventID: "event-q999999999", SourceID: "Q999999999", ArtworkSlug: "city-view",
		Label:    "Geographical context: Delft · artwork dated c. 1660–1661",
		Relation: "place", EvidenceURL: "https://example.org/collection/city-view",
	}
	if _, exists := selectedImages[row.EventID]; exists {
		t.Fatal("test requires an event without a legacy illustration")
	}
	raw, _ := json.Marshal([]artworkSelection{row})
	if got := readArtworkSelection(raw)[row.EventID]; got != row {
		t.Fatalf("explicit artwork context lost: %#v", got)
	}
	for name, change := range map[string]func(*artworkSelection){
		"missing caption":      func(r *artworkSelection) { r.Label = "" },
		"missing relationship": func(r *artworkSelection) { r.Relation = "" },
		"unknown relationship": func(r *artworkSelection) { r.Relation = "same-name" },
		"missing evidence":     func(r *artworkSelection) { r.EvidenceURL = "" },
		"unsafe evidence":      func(r *artworkSelection) { r.EvidenceURL = "javascript:alert(1)" },
		"different event":      func(r *artworkSelection) { r.SourceID = "Q1" },
	} {
		t.Run(name, func(t *testing.T) {
			invalid := row
			change(&invalid)
			defer func() {
				if recover() == nil {
					t.Fatal("incomplete contextual selection accepted")
				}
			}()
			raw, _ := json.Marshal([]artworkSelection{invalid})
			readArtworkSelection(raw)
		})
	}
}

// VALUES shadow real tables inside a read-only transaction. No database or
// stored fixtures are created; the SQL exercises withdrawal, scope and links.
func TestArtworkImagesReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_EVENTS_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("read-only catalogue not requested")
	}
	ctx := context.Background()
	db, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	tx, err := db.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	fixture := `WITH artworks(id,slug,title,primary_media_id,status,creation_year_start,creation_year_end,date_precision,work_type) AS (
 VALUES ('00000000-0000-4000-8000-000000000001'::uuid,'visible','Painting',1,'review',1845,1845,'exact','painting'),
 ('00000000-0000-4000-8000-000000000002'::uuid,'archived','Withdrawn',1,'archived',1845,1845,'exact','painting'),
 ('00000000-0000-4000-8000-000000000003'::uuid,'missing-media','No image',NULL,'review',1845,1845,'exact','painting'),
 ('00000000-0000-4000-8000-000000000004'::uuid,'post-scope','Later',1,'review',1980,1980,'exact','painting'),
 ('00000000-0000-4000-8000-000000000005'::uuid,'unsafe-media','Remote',2,'review',1845,1845,'exact','painting'),
 ('00000000-0000-4000-8000-000000000006'::uuid,'photo','Photograph',1,'review',1940,1940,'exact','photograph'),
 ('00000000-0000-4000-8000-000000000007'::uuid,'drawing','Drawing',1,'review',1940,1940,'exact','drawing')),
 media_assets(id,storage_path,source_page_url,creator_credit,attribution_text,license_label,rights_status,license_url,verified_at) AS (
 VALUES (1,'/assets/current.jpg','https://example.org/source','Current credit','Attribution','Current licence','restricted','https://example.org/license',now()),
 (2,'https://unreviewed.invalid/image.jpg','https://example.org/source','','','','unknown','',now())),
 artwork_artists(artwork_id,artist_id,attribution_role) AS (VALUES ('00000000-0000-4000-8000-000000000001'::uuid,1,'primary')),
 artists(id,slug,status) AS (VALUES (1,'reviewed-artist','review')) `
	rows, err := tx.Query(ctx, fixture+artworkImagesSQL, []string{"visible", "archived", "missing-media", "post-scope", "unsafe-media", "photo", "drawing"})
	if err != nil {
		t.Fatal(err)
	}
	defer rows.Close()
	values, err := pgx.CollectRows(rows, pgx.RowToMap)
	if err != nil || len(values) != 1 {
		t.Fatalf("eligible images: %v %v", values, err)
	}
	if values[0]["storage_path"] != "/assets/current.jpg" || values[0]["title"] != "Painting" {
		t.Fatal(values)
	}
	// Every production selection resolves via indexed slugs, before media and
	// creator enrichment. A local catalogue may lack production-only works.
	slugs := []string{}
	for _, selection := range selectedArtworks {
		slugs = append(slugs, selection.ArtworkSlug)
	}
	var plan []byte
	if err := tx.QueryRow(ctx, "EXPLAIN (FORMAT JSON) "+artworkImagesSQL, slugs).Scan(&plan); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(plan), "artworks_slug_key") {
		t.Fatalf("slug index missing: %s", plan)
	}
	items := []Event{}
	for _, selection := range selectedArtworks {
		items = append(items, Event{ID: selection.EventID, SourceID: selection.SourceID})
	}
	if err := ResolveImages(ctx, tx, items); err != nil {
		t.Fatal(err)
	}
	count := 0
	for _, event := range items {
		if event.Image == nil {
			continue
		}
		count++
		if event.Image.Artwork == nil || !strings.HasPrefix(event.Image.ImageURL, "/assets/") || !strings.HasPrefix(event.Image.Artwork.Href, "/") {
			t.Fatal(event)
		}
		if label := selectedArtworks[event.ID].Label; label != "" && !strings.HasSuffix(event.Image.Label, label) {
			t.Fatalf("explicit relationship caption replaced by legacy text: %s", event.ID)
		}
	}
	if count == 0 {
		t.Fatal("no catalogue artwork resolved")
	}
	t.Logf("%d/%d selections available in this catalogue", count, len(items))
}
