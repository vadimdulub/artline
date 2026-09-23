package catalog

import (
	"context"
	"os"
	"testing"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Exercise actual attached images without inserting fixtures or changing review
// state. The same media enrichment is used for public and review-visible works.
func TestAttachedMediaVisibilityReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("ARTLINE_READONLY_DATABASE_URL is not set")
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
	rows, err := tx.Query(ctx, `SELECT a.id::text,p.slug,m.storage_path,m.rights_status,m.source_page_url,i.slug
 FROM media_assets m JOIN artworks a ON a.primary_media_id=m.id
 JOIN artwork_artists aa ON aa.artwork_id=a.id JOIN artists p ON p.id=aa.artist_id
 LEFT JOIN institutions i ON i.id=a.current_institution_id
 WHERE a.status<>'archived' AND p.status<>'archived'
 AND m.provider_name='WikiArt' AND m.rights_status='restricted' AND m.verified_at IS NULL
 AND m.storage_path IS NOT NULL ORDER BY a.id LIMIT 12`)
	if err != nil {
		t.Fatal(err)
	}
	type sample struct {
		id, artist, path, rights, source string
		museum                           *string
	}
	var samples []sample
	for rows.Next() {
		var s sample
		if err := rows.Scan(&s.id, &s.artist, &s.path, &s.rights, &s.source, &s.museum); err != nil {
			t.Fatal(err)
		}
		samples = append(samples, s)
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		t.Fatal(err)
	}
	if len(samples) == 0 {
		t.Fatal("no attached WikiArt examples with an unverified restricted label")
	}
	repo := &Repository{db: tx}
	for _, s := range samples {
		t.Run(s.id, func(t *testing.T) {
			check := func(name string, work Artwork, err error) {
				t.Helper()
				if err != nil {
					t.Fatalf("%s: %v", name, err)
				}
				if work.MediaURL == nil || *work.MediaURL != s.path {
					t.Errorf("%s hid the attached image: %v", name, work.MediaURL)
				}
				if work.RightsStatus == nil || *work.RightsStatus != s.rights || work.SourcePageURL == nil || *work.SourcePageURL != s.source {
					t.Errorf("%s changed the rights label or lost the source link", name)
				}
			}
			work, err := repo.ArtistArtwork(ctx, s.artist, s.id, true)
			check("artist detail", work, err)
			atlas, err := repo.AtlasArtwork(ctx, s.id, true)
			check("atlas detail", atlas.Artwork, err)
			if s.museum != nil {
				museum, err := repo.MuseumArtwork(ctx, *s.museum, s.id, true)
				check("museum detail", museum.Artwork, err)
			}
		})
	}
}
