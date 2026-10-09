package catalog

import (
	"context"
	"errors"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"reflect"
	"regexp"
	"testing"
	"time"
)

// No fixtures or writes: pin real museum counts and page boundaries while
// independent research may update the catalogue.
func TestMuseumImagesReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("ARTLINE_READONLY_DATABASE_URL is not set")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()
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
	slug := "musee-du-louvre"
	image := regexp.MustCompile(`^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$`)
	available := func(w MuseumWork) bool { return w.MediaURL != nil && image.MatchString(*w.MediaURL) }
	get := func(f MuseumFilter) MuseumWorksPage {
		t.Helper()
		p, e := repo.MuseumWorks(ctx, slug, f)
		if e != nil {
			t.Fatal(e)
		}
		return p
	}
	base := MuseumFilter{Limit: 60}
	first := get(base)
	if first.Total == 0 || first.ImageCount == 0 {
		t.Fatal("audit requires real Louvre works and images")
	}
	t.Logf("Louvre: %d works, %d renderable images", first.Total, first.ImageCount)
	t.Run("default-equivalent-to-images", func(t *testing.T) {
		f := base
		f.Sort = "images"
		if !reflect.DeepEqual(first, get(f)) {
			t.Fatal("default differs")
		}
	})
	t.Run("complete-keyset-and-image-boundary", func(t *testing.T) {
		seen := map[string]bool{}
		images := 0
		withoutImage := false
		p := first
		f := base
		for {
			if p.Total != first.Total || p.ImageCount != first.ImageCount || len(p.Items) > f.Limit {
				t.Fatal("inconsistent bounded counts")
			}
			for _, w := range p.Items {
				if seen[w.ID] {
					t.Fatalf("duplicate %s", w.ID)
				}
				seen[w.ID] = true
				if available(w) {
					images++
					if withoutImage {
						t.Fatal("image after metadata-only work")
					}
				} else {
					withoutImage = true
				}
			}
			if p.NextCursor == "" {
				break
			}
			if len(p.Items) != f.Limit {
				t.Fatal("short intermediate page")
			}
			f.Cursor = p.NextCursor
			p = get(f)
		}
		if len(seen) != first.Total || images != first.ImageCount {
			t.Fatalf("omitted: %d/%d works, %d/%d images", len(seen), first.Total, images, first.ImageCount)
		}
	})
	t.Run("image-only-all-pages", func(t *testing.T) {
		f := MuseumFilter{Limit: 7, ImageOnly: true}
		seen := map[string]bool{}
		for {
			p := get(f)
			if p.Total != first.ImageCount || p.ImageCount != p.Total {
				t.Fatal("count differs")
			}
			for _, w := range p.Items {
				if !available(w) || seen[w.ID] {
					t.Fatal("missing/duplicate image")
				}
				seen[w.ID] = true
			}
			if p.NextCursor == "" {
				break
			}
			f.Cursor = p.NextCursor
		}
		if len(seen) != first.ImageCount {
			t.Fatal("dropped images")
		}
	})
	for _, sort := range []string{"images", "year", "title", "curated"} {
		t.Run("sort-"+sort, func(t *testing.T) {
			f := base
			f.Sort = sort
			p := get(f)
			if p.Total != first.Total || p.ImageCount != first.ImageCount {
				t.Fatal("sort changed coverage")
			}
			for i := 1; i < len(p.Items); i++ {
				a, b := p.Items[i-1], p.Items[i]
				if a.SortNumber > b.SortNumber || (a.SortNumber == b.SortNumber && a.SortName > b.SortName) {
					t.Fatal("invalid order")
				}
			}
		})
	}
	t.Run("cursor-scope", func(t *testing.T) {
		for _, change := range []func(*MuseumFilter){func(f *MuseumFilter) { f.Sort = "year" }, func(f *MuseumFilter) { f.ImageOnly = true }, func(f *MuseumFilter) { f.Query = "Dante" }, func(f *MuseumFilter) { f.Limit = 24 }, func(f *MuseumFilter) { f.Selection = "museum" }, func(f *MuseumFilter) { f.Artist = "rembrandt" }} {
			f := base
			f.Cursor = first.NextCursor
			change(&f)
			if _, e := repo.MuseumWorks(ctx, slug, f); !errors.Is(e, ErrMuseumFilter) {
				t.Fatalf("changed filter accepted cursor: %v", e)
			}
		}
		f := base
		f.Cursor = first.NextCursor
		if _, e := repo.MuseumWorks(ctx, "the-met", f); !errors.Is(e, ErrMuseumFilter) {
			t.Fatal("cross-museum cursor accepted")
		}
		if _, e := repo.MuseumWorks(ctx, slug, f); e != nil {
			t.Fatal("unchanged catalogue cursor rejected", e)
		}
		f.Cursor = encodeMuseumCursor(base, slug, 1827, "a title", first.Items[0].ID)
		if _, e := repo.MuseumWorks(ctx, slug, f); !errors.Is(e, ErrMuseumFilter) {
			t.Fatal("old year cursor reinterpreted as image order")
		}
	})
	t.Run("empty-search", func(t *testing.T) {
		f := base
		f.Query = "no-such-artwork-audit-20261005"
		p := get(f)
		if p.Total != 0 || p.ImageCount != 0 || len(p.Items) != 0 || p.NextCursor != "" {
			t.Fatal("empty filter leaked results")
		}
	})
	t.Run("detail-and-list-agree", func(t *testing.T) {
		for _, w := range first.Items {
			if !available(w) {
				continue
			}
			d, e := repo.MuseumArtwork(ctx, slug, w.ID)
			if e != nil || !reflect.DeepEqual(d.MediaURL, w.MediaURL) || d.Title != w.Title {
				t.Fatalf("detail/list mismatch %s: %v", w.ID, e)
			}
		}
	})
	for _, museum := range []string{"the-met", "national-gallery-of-art", "uffizi"} {
		t.Run("other-"+museum, func(t *testing.T) {
			p, e := repo.MuseumWorks(ctx, museum, base)
			if errors.Is(e, ErrNotFound) {
				t.Skip("not present in catalogue")
			}
			if e != nil {
				t.Fatal(e)
			}
			if p.ImageCount > p.Total {
				t.Fatal("image count exceeds total")
			}
			for i, w := range p.Items {
				if i < p.ImageCount && !available(w) {
					t.Fatal("image omitted from first page")
				}
			}
		})
	}
}
