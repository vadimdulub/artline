package catalog

import (
	"context"
	"fmt"
	"regexp"
	"strings"
)

const SitemapLimit = 10000

var sitemapPrefix = regexp.MustCompile(`^[0-9a-f]{3}$`)

type SEOEntry struct {
	Path string `json:"path"`
	Name string `json:"name"`
}

type ArtistDirectory struct {
	Items []SEOEntry `json:"items"`
	Next  string     `json:"next"`
}

func sitemapTable(kind string) string {
	switch kind {
	case "artists":
		return "artists"
	case "artworks":
		return "artworks"
	case "museums":
		return "institutions"
	default:
		return ""
	}
}

func ValidSitemapShard(kind, prefix string) bool {
	return sitemapTable(kind) != "" && sitemapPrefix.MatchString(prefix)
}

// Jump between occupied UUID ranges using the published-ID index, rather than
// counting/sorting every artwork. At most 4096 ranges per entity kind.
func sitemapShardsSQL(table string) string {
	return `WITH RECURSIVE occupied AS (
 (SELECT id FROM ` + table + ` WHERE status='published' ORDER BY id LIMIT 1)
 UNION ALL
 SELECT next.id FROM occupied current CROSS JOIN LATERAL (
   SELECT id FROM ` + table + ` WHERE status='published'
   AND id > rpad(left(replace(current.id::text,'-',''),3),32,'f')::uuid
   ORDER BY id LIMIT 1
 ) next
) SELECT left(id::text,3) FROM occupied`
}

func (r *Repository) SitemapShards(ctx context.Context) ([]string, error) {
	result := []string{}
	for _, kind := range []string{"artists", "artworks", "museums"} {
		rows, err := r.db.Query(ctx, sitemapShardsSQL(sitemapTable(kind)))
		if err != nil {
			return nil, err
		}
		for rows.Next() {
			var prefix string
			if err = rows.Scan(&prefix); err != nil {
				rows.Close()
				return nil, err
			}
			result = append(result, kind+"-"+prefix)
		}
		rows.Close()
		if err = rows.Err(); err != nil {
			return nil, err
		}
	}
	return result, nil
}

const sitemapArtworkSQL = `WITH selected AS MATERIALIZED (
 SELECT id,title FROM artworks
 WHERE status='published' AND id >= $1::uuid AND id <= $2::uuid
 ORDER BY id LIMIT $3
)
SELECT '/artists/'||a.slug||'/works/'||aw.id::text, aw.title
FROM selected aw
JOIN LATERAL (
 SELECT a.slug FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id
 WHERE aa.artwork_id=aw.id AND a.status='published'
 ORDER BY (aa.attribution_role='primary') DESC, a.slug, aa.attribution_role LIMIT 1
) a ON true ORDER BY aw.id`

func (r *Repository) SitemapEntries(ctx context.Context, kind, prefix string) ([]SEOEntry, error) {
	if !ValidSitemapShard(kind, prefix) {
		return nil, fmt.Errorf("invalid sitemap shard")
	}
	lower, upper := prefix+strings.Repeat("0", 29), prefix+strings.Repeat("f", 29)
	query := sitemapArtworkSQL
	switch kind {
	case "artists":
		query = `SELECT '/artists/'||slug,display_name FROM artists WHERE status='published' AND id >= $1::uuid AND id <= $2::uuid ORDER BY id LIMIT $3`
	case "museums":
		query = `SELECT '/museums/'||slug,name FROM institutions WHERE status='published' AND id >= $1::uuid AND id <= $2::uuid ORDER BY id LIMIT $3`
	}
	// Check the raw range before enrichment: an artwork without a public creator
	// must not conceal overflow and silently truncate other URLs in the shard.
	var count int
	if err := r.db.QueryRow(ctx, `SELECT count(*) FROM (SELECT id FROM `+sitemapTable(kind)+` WHERE status='published' AND id >= $1::uuid AND id <= $2::uuid ORDER BY id LIMIT $3) bounded`, lower, upper, SitemapLimit+1).Scan(&count); err != nil {
		return nil, err
	}
	if count > SitemapLimit {
		return nil, fmt.Errorf("sitemap shard %s-%s exceeds %d entries; split ranges before publishing more content", kind, prefix, SitemapLimit)
	}
	rows, err := r.db.Query(ctx, query, lower, upper, SitemapLimit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	result := []SEOEntry{}
	for rows.Next() {
		var entry SEOEntry
		if err := rows.Scan(&entry.Path, &entry.Name); err != nil {
			return nil, err
		}
		result = append(result, entry)
	}
	return result, rows.Err()
}

func (r *Repository) PublishedArtistDirectory(ctx context.Context, after string) (ArtistDirectory, error) {
	result := ArtistDirectory{Items: []SEOEntry{}}
	rows, err := r.db.Query(ctx, `SELECT slug,display_name FROM artists WHERE status='published' AND slug > $1 ORDER BY slug LIMIT 61`, after)
	if err != nil {
		return result, err
	}
	defer rows.Close()
	var last string
	for rows.Next() {
		var slug, name string
		if err := rows.Scan(&slug, &name); err != nil {
			return result, err
		}
		if len(result.Items) == 60 {
			result.Next = last
			break
		}
		result.Items = append(result.Items, SEOEntry{Path: "/artists/" + slug, Name: name})
		last = slug
	}
	return result, rows.Err()
}
