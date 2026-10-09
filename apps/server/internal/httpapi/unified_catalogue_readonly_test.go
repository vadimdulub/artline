package httpapi

import (
	"context"
	"encoding/json"
	"net/http/httptest"
	"net/url"
	"os"
	"strings"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

// This audit performs SELECTs only. PostgreSQL enforces read-only transactions
// on every connection; no fixture schema, migration or catalogue write is used.
func TestUnifiedCatalogueReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("ARTLINE_READONLY_DATABASE_URL not set")
	}
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "25000"
	db, err := pgxpool.NewWithConfig(context.Background(), cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	ctx := context.Background()
	var artist, artistPrefix, work, museum, museumPrefix, book, event string
	lookups := []struct {
		query string
		dest  *string
	}{
		{`SELECT a.slug FROM artists a WHERE a.status<>'archived' AND EXISTS(SELECT 1 FROM artwork_artists aa JOIN artworks aw ON aw.id=aa.artwork_id WHERE aa.artist_id=a.id AND aw.status='review') ORDER BY (a.status='published') DESC,a.slug LIMIT 1`, &artist},
		{`SELECT i.slug FROM institutions i WHERE i.status<>'archived' AND i.canonical_institution_id IS NULL AND EXISTS(SELECT 1 FROM artworks aw WHERE aw.current_institution_id=i.id AND aw.status='review') ORDER BY i.slug LIMIT 1`, &museum},
		{`SELECT id FROM book_records WHERE status<>'archived' AND end_year<=2000 ORDER BY id LIMIT 1`, &book},
		{`SELECT id FROM event_records WHERE status<>'archived' ORDER BY id LIMIT 1`, &event},
	}
	for _, lookup := range lookups {
		if err := db.QueryRow(ctx, lookup.query).Scan(lookup.dest); err != nil {
			t.Fatal(err)
		}
	}
	if err := db.QueryRow(ctx, `SELECT aw.id::text FROM artists a JOIN artwork_artists aa ON aa.artist_id=a.id JOIN artworks aw ON aw.id=aa.artwork_id WHERE a.slug=$1 AND aw.status='review' ORDER BY aw.id LIMIT 1`, artist).Scan(&work); err != nil {
		t.Fatal(err)
	}
	if err := db.QueryRow(ctx, `SELECT left(id::text,3) FROM institutions WHERE slug=$1`, museum).Scan(&museumPrefix); err != nil {
		t.Fatal(err)
	}
	if err := db.QueryRow(ctx, `SELECT left(id::text,3) FROM artists WHERE slug=$1`, artist).Scan(&artistPrefix); err != nil {
		t.Fatal(err)
	}
	handler := New(config.Config{}, db)
	read := func(t *testing.T, path string) map[string]any {
		t.Helper()
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, httptest.NewRequest("GET", "/api/v1/"+path, nil))
		if w.Code != 200 {
			t.Fatalf("%s: %d %s", path, w.Code, w.Body.String())
		}
		var out map[string]any
		if err := json.Unmarshal(w.Body.Bytes(), &out); err != nil {
			t.Fatal(err)
		}
		return out
	}
	for _, path := range []string{
		"artists?limit=2", "artworks?limit=2", "artworks?q=Madonna&limit=2", "artists?q=Monet&limit=2", "artworks?undated=true&limit=2",
		"timeline?painter=" + artist, "timeline/facets", "painters/options?q=" + artist,
		"artists/" + artist, "artists/" + artist + "/identity", "artists/" + artist + "/works?limit=2", "artists/" + artist + "/works/" + work,
		"museums?limit=2", "museums/" + museum, "museums/" + museum + "/works?limit=2",
		"books?limit=2", "books?view=authors&limit=2", "books/authors?q=Homer", "books/facets", "books/" + book,
		"events?limit=2", "events/facets", "events/" + event,
		"atlas?type=artwork&creator=painter:" + artist + "&highlights=false&limit=2",
		"atlas?type=artwork&artwork_movement=impressionism&artwork_popular=false&limit=2",
		"atlas?type=artwork&country=france&continent=europe&highlights=false&limit=2",
		"atlas?selection=true&pick_artwork=" + work + "&limit=2",
		"atlas?type=book&book_language=Q7737&book_top100=false&limit=2", "atlas?type=event&event_q=war&event_top100=false&limit=2",
		"atlas?type=book&limit=2", "atlas?type=event&limit=2", "atlas/creators?q=monet", "atlas/geography", "atlas/presets",
		"catalogue/artists?limit=2", "seo/artists", "seo/sitemaps",
		"seo/sitemaps/artworks/" + strings.Split(work, "-")[0][:3], "seo/sitemaps/museums/" + museumPrefix, "seo/sitemaps/artists/" + artistPrefix,
	} {
		t.Run(path, func(t *testing.T) { read(t, path) })
	}
	t.Run("sitemaps include active review records", func(t *testing.T) {
		for _, entry := range []struct{ endpoint, suffix string }{
			{"seo/sitemaps/artists/" + artistPrefix, "/artists/" + artist},
			{"seo/sitemaps/artworks/" + strings.Split(work, "-")[0][:3], "/works/" + work},
			{"seo/sitemaps/museums/" + museumPrefix, "/museums/" + museum},
		} {
			result := read(t, entry.endpoint)
			found := false
			for _, raw := range result["items"].([]any) {
				if strings.HasSuffix(raw.(map[string]any)["path"].(string), entry.suffix) {
					found = true
					break
				}
			}
			if !found {
				t.Fatalf("active record missing from sitemap: %s", entry.suffix)
			}
		}
	})
	t.Run("legacy flags do not hide active works", func(t *testing.T) {
		path := "artists/" + artist + "/works?limit=2"
		baseline := read(t, path)
		for _, suffix := range []string{"&preview=0", "&preview=1", "&status=published", "&status=review"} {
			got := read(t, path+suffix)
			if got["total"] != baseline["total"] {
				t.Fatalf("%s changed total", suffix)
			}
		}
		got := read(t, "artists/"+artist+"/works/"+work+"?preview=0")
		if got["status"] != "review" {
			t.Fatal("review work should be visible without changing its historical status")
		}
	})
	t.Run("all active artwork counts and keyset pages", func(t *testing.T) {
		var total int
		if err := db.QueryRow(ctx, `SELECT count(*) FROM artworks WHERE status<>'archived'`).Scan(&total); err != nil {
			t.Fatal(err)
		}
		first := read(t, "artworks?limit=2&preview=0&status=published")
		if first["total"] != float64(total) {
			t.Fatalf("got %v active works, want %d", first["total"], total)
		}
		cursor, _ := first["next_cursor"].(string)
		if cursor == "" {
			t.Fatal("expected another bounded artwork page")
		}
		second := read(t, "artworks?limit=2&cursor="+url.QueryEscape(cursor))
		seen := map[string]bool{}
		for _, page := range []map[string]any{first, second} {
			for _, raw := range page["items"].([]any) {
				item := raw.(map[string]any)
				id := item["id"].(string)
				if seen[id] || item["status"] == "archived" {
					t.Fatal("duplicate or archived work in page")
				}
				seen[id] = true
			}
		}
	})
}
