package catalog

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func TestPerformanceFixesReadOnly(t *testing.T) {
	dsn := os.Getenv("ARTLINE_READONLY_DATABASE_URL")
	if dsn == "" {
		t.Skip("opt-in read-only catalogue comparison")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		t.Fatal(err)
	}
	cfg.MaxConns = 1
	cfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	cfg.ConnConfig.RuntimeParams["statement_timeout"] = "15000"
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
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
	readPage := func(sql string, args ...any) []string {
		rows, err := tx.Query(ctx, sql, museumQueryArgs(args...)...)
		if err != nil {
			t.Fatal(err)
		}
		defer rows.Close()
		out := []string{}
		for rows.Next() {
			var title string
			var body []byte
			if err = rows.Scan(&title, &body); err != nil {
				t.Fatal(err)
			}
			out = append(out, title+string(body))
		}
		if rows.Err() != nil {
			t.Fatal(rows.Err())
		}
		return out
	}
	var projection *string
	if err = tx.QueryRow(ctx, "SELECT to_regclass('artwork_search_documents')::text").Scan(&projection); err != nil {
		t.Fatal(err)
	}
	projected := func(sql string) string {
		if projection != nil {
			return sql
		}
		return strings.Replace(sql, "WITH ", `WITH artwork_search_documents AS NOT MATERIALIZED (
      SELECT aw.id,aw.title,aw.normalized_title,aw.status,
      aw.creation_year_start IS NULL AND aw.creation_year_end IS NULL AS undated,
      aw.primary_media_id
      FROM artworks aw), `, 1)
	}
	queries := []string{"Madonna", "portrait", "a", "%", "no-such-title-perf-audit"}
	if os.Getenv("ARTLINE_PERFORMANCE_QUICK") == "1" {
		queries = []string{"Madonna"}
	}
	for _, query := range queries {
		for _, flags := range [][2]bool{{false, false}, {true, false}, {false, true}} {
			args := []any{query, flags[0], flags[1], false, "", "00000000-0000-0000-0000-000000000000", 25}
			after := readPage(projected(artworkDocumentSearchPageSQL), args...)
			if os.Getenv("ARTLINE_PERFORMANCE_QUICK") != "1" {
				before := readPage(artworkDirectoryPageSQL, args...)
				if !reflect.DeepEqual(readPage(projected(artworkDocumentPageSQL), args...), after) {
					t.Fatal("ordered projection page changed")
				}
				if !reflect.DeepEqual(before, after) {
					t.Fatalf("search order/data changed: %q %+v", query, flags)
				}
			} else {
				t.Logf("candidate search %q %+v: %d bounded rows (legacy comparison is local-only)", query, flags, len(after))
			}
		}
	}
	page, err := repo.BrowseArtworks(ctx, ArtworkDirectoryFilter{Query: "Madonna", Limit: 7})
	if err != nil {
		t.Fatal(err)
	}
	if page.NextCursor != "" {
		next, err := repo.BrowseArtworks(ctx, ArtworkDirectoryFilter{Query: "Madonna", Limit: 7, Cursor: page.NextCursor})
		if err != nil {
			t.Fatal(err)
		}
		if next.Total != page.Total {
			t.Fatal("cursor changed count")
		}
		seen := map[string]bool{}
		for _, w := range page.Items {
			seen[w.ID] = true
		}
		for _, w := range next.Items {
			if seen[w.ID] {
				t.Fatal("cursor repeated work")
			}
		}
	}
	// Public citation projection leaves every other field and claim unchanged.
	raw, err := repo.ArtistBySlug(ctx, "rembrandt")
	if err != nil {
		t.Fatal(err)
	}
	public, err := repo.ArtistBySlug(WithPublicRead(ctx), "rembrandt")
	if err != nil {
		t.Fatal(err)
	}
	before, _ := json.Marshal(raw)
	after, _ := json.Marshal(public)
	strip := func(cs []Citation) {
		for i := range cs {
			cs[i].EvidenceNote = ""
		}
	}
	strip(raw.Citations)
	for i := range raw.Artworks {
		strip(raw.Artworks[i].Citations)
	}
	if raw.KeyArtwork != nil {
		strip(raw.KeyArtwork.Citations)
	}
	for i := range raw.Influences {
		strip(raw.Influences[i].Citations)
	}
	if !reflect.DeepEqual(raw, public) {
		t.Fatal("public projection changed source links, attribution, dates, claims or other fields")
	}
	t.Logf("public painter JSON: %d -> %d bytes", len(before), len(after))
	var influenceArtist string
	err = tx.QueryRow(ctx, `SELECT target_artist_id::text FROM influence_claims WHERE status<>'archived' GROUP BY target_artist_id ORDER BY count(*) DESC LIMIT 1`).Scan(&influenceArtist)
	if err == nil {
		claims, err := repo.artistInfluences(ctx, influenceArtist)
		if err != nil {
			t.Fatal(err)
		}
		for _, claim := range claims {
			legacy, err := repo.entityCitations(ctx, "influence", claim.ID)
			if err != nil {
				t.Fatal(err)
			}
			if !reflect.DeepEqual(legacy, claim.Citations) {
				t.Fatal("batched influence citations changed", claim.ID)
			}
		}
		t.Logf("compared %d batched influence citation sets", len(claims))
	} else if err != pgx.ErrNoRows {
		t.Fatal(err)
	}
	const legacyChoices = `(SELECT DISTINCT 'artist',a.slug,a.display_name FROM institutions i JOIN museum_memberships member ON member.institution_id=i.id
 JOIN artwork_artists aa ON aa.artwork_id=member.artwork_id JOIN artists a ON a.id=aa.artist_id
 WHERE i.slug=$1 AND ` + museumVisible + ` AND a.status<>'archived' ORDER BY 3 LIMIT 30)
 UNION (SELECT DISTINCT 'movement',m.slug,m.name FROM institutions i JOIN museum_memberships member ON member.institution_id=i.id
 JOIN artwork_artists aa ON aa.artwork_id=member.artwork_id JOIN artists a ON a.id=aa.artist_id JOIN artist_movements am ON am.artist_id=a.id JOIN movements m ON m.id=am.movement_id
 WHERE ($1='' OR i.slug=$1) AND ` + museumVisible + ` AND a.status<>'archived' AND m.status<>'archived' ORDER BY 3 LIMIT 500) ORDER BY 1,3`
	choices := func(sql, slug string) [][3]string {
		rows, err := tx.Query(ctx, museumScopedFacetCTE+sql, museumQueryArgs(slug)...)
		if err != nil {
			t.Fatal(err)
		}
		defer rows.Close()
		out := [][3]string{}
		for rows.Next() {
			var row [3]string
			if err = rows.Scan(&row[0], &row[1], &row[2]); err != nil {
				t.Fatal(err)
			}
			out = append(out, row)
		}
		if rows.Err() != nil {
			t.Fatal(rows.Err())
		}
		return out
	}
	for _, slug := range []string{"the-met", "national-gallery-of-art", "musee-du-louvre", "no-such-museum"} {
		if !reflect.DeepEqual(choices(legacyChoices, slug), choices(museumScopedFacetChoicesSQL, slug)) {
			t.Fatal("museum facets changed", slug)
		}
	}
	if dir := os.Getenv("ARTLINE_PERFORMANCE_DIR"); dir != "" {
		if err = os.MkdirAll(dir, 0700); err != nil {
			t.Fatal(err)
		}
		for name, sql := range map[string]string{"search-before": artworkDirectoryPageSQL, "search-after": projected(artworkDocumentSearchPageSQL)} {
			if name == "search-before" && os.Getenv("ARTLINE_PERFORMANCE_QUICK") == "1" {
				continue
			}
			var plan []byte
			if err = tx.QueryRow(ctx, "EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON) "+sql, museumQueryArgs("Madonna", false, false, false, "", "00000000-0000-0000-0000-000000000000", 25)...).Scan(&plan); err != nil {
				t.Fatal(err)
			}
			if err = os.WriteFile(filepath.Join(dir, name+".json"), plan, 0600); err != nil {
				t.Fatal(err)
			}
			var summary []map[string]any
			_ = json.Unmarshal(plan, &summary)
			t.Logf("%s: %v ms", name, summary[0]["Execution Time"])
		}
		for name, sql := range map[string]string{"museum-before": museumScopedFacetCTE + legacyChoices, "museum-after": museumScopedFacetCTE + museumScopedFacetChoicesSQL} {
			var plan []byte
			if err = tx.QueryRow(ctx, "EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON) "+sql, museumQueryArgs("the-met")...).Scan(&plan); err != nil {
				t.Fatal(err)
			}
			if err = os.WriteFile(filepath.Join(dir, name+".json"), plan, 0600); err != nil {
				t.Fatal(err)
			}
			var summary []map[string]any
			_ = json.Unmarshal(plan, &summary)
			t.Logf("%s: %v ms", name, summary[0]["Execution Time"])
		}
	}
}
