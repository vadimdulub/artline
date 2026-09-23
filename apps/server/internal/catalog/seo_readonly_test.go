package catalog

import (
	"context"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"strings"
	"testing"
)

func TestSEOPublishedDiscoveryReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("ARTLINE_READONLY_DATABASE_URL not set")
	}
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	tx, err := pool.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly, IsoLevel: pgx.RepeatableRead})
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback(ctx)
	repo := &Repository{db: tx}
	shards, err := repo.SitemapShards(ctx)
	if err != nil {
		t.Fatal(err)
	}
	for _, shard := range shards {
		kind, prefix, _ := strings.Cut(shard, "-")
		if !ValidSitemapShard(kind, prefix) {
			t.Fatalf("bad shard %s", shard)
		}
	}
	page, err := repo.PublishedArtistDirectory(ctx, "")
	if err != nil {
		t.Fatal(err)
	}
	if len(page.Items) > 60 {
		t.Fatal("unbounded directory")
	}
	for _, entry := range page.Items {
		var status string
		if err := tx.QueryRow(ctx, `SELECT status FROM artists WHERE slug=$1`, strings.TrimPrefix(entry.Path, "/artists/")).Scan(&status); err != nil {
			t.Fatal(err)
		}
		if status != "published" {
			t.Fatal("unpublished artist exposed")
		}
	}
	// Inline SQL VALUES exercise mixed publication states without inserting any
	// records, creating tables or altering the real catalogue.
	fixture := `WITH artworks(id,title,status) AS (VALUES
 ('00000000-0000-0000-0000-000000000001'::uuid,'Published work','published'),
 ('00000000-0000-0000-0000-000000000002'::uuid,'Review work','review'),
 ('00000000-0000-0000-0000-000000000003'::uuid,'Private creator','published')),
 artists(id,slug,status) AS (VALUES (1,'a-published','published'),(2,'b-review','review'),(3,'c-published','published')),
 artwork_artists(artwork_id,artist_id,attribution_role) AS (VALUES
 ('00000000-0000-0000-0000-000000000001'::uuid,1,'primary'),
 ('00000000-0000-0000-0000-000000000001'::uuid,3,'attributed_to'),
 ('00000000-0000-0000-0000-000000000002'::uuid,1,'primary'),
 ('00000000-0000-0000-0000-000000000003'::uuid,2,'primary')), selected`
	query := strings.Replace(sitemapArtworkSQL, "WITH selected", fixture, 1)
	rows, err := tx.Query(ctx, query, strings.Repeat("0", 32), strings.Repeat("f", 32), SitemapLimit)
	if err != nil {
		t.Fatal(err)
	}
	defer rows.Close()
	var entries []SEOEntry
	for rows.Next() {
		var e SEOEntry
		if err := rows.Scan(&e.Path, &e.Name); err != nil {
			t.Fatal(err)
		}
		entries = append(entries, e)
	}
	if err := rows.Err(); err != nil {
		t.Fatal(err)
	}
	if len(entries) != 1 || entries[0].Path != "/artists/a-published/works/00000000-0000-0000-0000-000000000001" {
		t.Fatalf("publication/attribution filtering failed: %+v", entries)
	}
}
