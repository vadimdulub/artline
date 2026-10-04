package catalog

import (
	"context"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
)

// Directory queries touch artists and their metadata first. Artwork counts are
// batched only for the returned page, never for every artist in the catalogue.
type ArtistDirectoryFilter struct {
	Query, Country, Movement, Sort, Cursor string
	Popular, Women                         bool
	Limit                                  int
}
type ArtistBrowsePage struct {
	Items      []TimelineArtist `json:"items"`
	Total      int              `json:"total"`
	NextCursor string           `json:"next_cursor"`
	Facets     TimelineFacets   `json:"facets"`
}
type artistDirectoryCursor struct {
	Rank  int    `json:"r"`
	Name  string `json:"n"`
	ID    string `json:"i"`
	Scope string `json:"s"`
}

const artistDirectoryPredicate = ` FROM artists a
 LEFT JOIN (SELECT artist_id,min(rank) AS rank FROM painter_import_cohort GROUP BY artist_id) popularity ON popularity.artist_id=a.id
 LEFT JOIN artist_movements am ON am.artist_id=a.id AND am.role='primary'
 LEFT JOIN movements m ON m.id=am.movement_id AND m.status<>'archived' AND ($1 OR m.status='published')
 WHERE a.status<>'archived' AND ($1 OR a.status='published')
 AND ($2='' OR a.display_name ILIKE '%'||$2||'%' OR a.sort_name ILIKE '%'||$2||'%'
   OR EXISTS(SELECT 1 FROM artist_aliases x WHERE x.artist_id=a.id AND x.alias ILIKE '%'||$2||'%'))
 AND ($3='' OR EXISTS(SELECT 1 FROM artist_countries x WHERE x.artist_id=a.id AND trim(x.country_code::text)=$3))
 AND ($4='' OR EXISTS(SELECT 1 FROM artist_movements x JOIN movements y ON y.id=x.movement_id WHERE x.artist_id=a.id AND y.slug=$4 AND y.status<>'archived' AND ($1 OR y.status='published')))
 AND (NOT $5 OR popularity.rank<=1000)
 AND (NOT $6 OR EXISTS(SELECT 1 FROM artist_gender_evidence x WHERE x.artist_id=a.id AND x.is_woman))`
const artistDirectoryOrder = `CASE WHEN $7='popular' THEN coalesce(popularity.rank,2147483647) ELSE 0 END`
const artistDirectoryPageQuery = `SELECT a.id::text,a.slug,a.display_name,a.timeline_start_year,a.timeline_end_year,a.timeline_display,a.status,
 coalesce(m.slug,'unclassified'),coalesce(m.name,'Unclassified'),coalesce(m.color_hex,'#717776'),
 ARRAY(SELECT DISTINCT trim(x.country_code::text) FROM artist_countries x WHERE x.artist_id=a.id ORDER BY 1),
 ` + artistDirectoryOrder + `,lower(a.sort_name)` + artistDirectoryPredicate + `
 AND (NOT $11 OR (` + artistDirectoryOrder + `,lower(a.sort_name),a.id::text)>($8,$9,$10))
 ORDER BY ` + artistDirectoryOrder + `,lower(a.sort_name),a.id LIMIT $12`

func (r *Repository) BrowseArtists(ctx context.Context, f ArtistDirectoryFilter, preview bool) (ArtistBrowsePage, error) {
	out := ArtistBrowsePage{Items: []TimelineArtist{}}
	if len(f.Query) > 200 || len(f.Country) > 2 || len(f.Movement) > 100 || f.Limit < 1 || f.Limit > 60 || len(f.Cursor) > 2048 || (f.Sort != "popular" && f.Sort != "name") {
		return out, ErrChronologyFilter
	}
	scopeFilter := f
	scopeFilter.Cursor = ""
	scopeData, _ := json.Marshal([]any{scopeFilter, preview})
	scope := fmt.Sprintf("%x", sha256.Sum256(scopeData))[:24]
	cursor := artistDirectoryCursor{}
	if f.Cursor != "" {
		data, err := base64.RawURLEncoding.DecodeString(f.Cursor)
		if err != nil || json.Unmarshal(data, &cursor) != nil || cursor.Scope != scope || len(cursor.ID) != 36 || len(cursor.Name) > 1000 {
			return out, ErrChronologyFilter
		}
	}
	args := []any{preview, f.Query, f.Country, f.Movement, f.Popular, f.Women}
	if err := r.db.QueryRow(ctx, "SELECT count(*)"+artistDirectoryPredicate, museumQueryArgs(args...)...).Scan(&out.Total); err != nil {
		return out, err
	}
	args = append(args, f.Sort, cursor.Rank, cursor.Name, cursor.ID, f.Cursor != "", f.Limit+1)
	rows, err := r.db.Query(ctx, artistDirectoryPageQuery, museumQueryArgs(args...)...)
	if err != nil {
		return out, err
	}
	last := artistDirectoryCursor{Scope: scope}
	for rows.Next() {
		var item TimelineArtist
		var rank int
		var name string
		if err = rows.Scan(&item.ID, &item.Slug, &item.Name, &item.StartYear, &item.EndYear, &item.DateDisplay, &item.Status, &item.Movement.Slug, &item.Movement.Name, &item.Movement.Color, &item.Countries, &rank, &name); err != nil {
			break
		}
		if len(out.Items) == f.Limit {
			data, _ := json.Marshal(last)
			out.NextCursor = base64.RawURLEncoding.EncodeToString(data)
			break
		}
		out.Items = append(out.Items, item)
		last = artistDirectoryCursor{rank, name, item.ID, scope}
	}
	rows.Close()
	if err != nil {
		return out, err
	}
	if err = rows.Err(); err != nil {
		return out, err
	}
	if len(out.Items) > 0 {
		ids := make([]string, len(out.Items))
		positions := map[string]int{}
		for i, item := range out.Items {
			ids[i] = item.ID
			positions[item.ID] = i
		}
		visibility := "published"
		if preview {
			visibility = ""
		}
		counts, e := r.db.Query(ctx, timelineArtworkCountsQuery, museumQueryArgs(ids, visibility)...)
		if e != nil {
			return out, e
		}
		for counts.Next() {
			var id string
			var count int
			if err = counts.Scan(&id, &count); err != nil {
				break
			}
			out.Items[positions[id]].ArtworkCount = count
		}
		counts.Close()
		if err != nil {
			return out, err
		}
		if err = counts.Err(); err != nil {
			return out, err
		}
	}
	out.Facets, err = r.DiscoveryFacets(ctx, preview, false, false)
	return out, err
}

type ArtistCollection struct {
	MuseumRef
	WorkCount int `json:"work_count"`
}

// Holdings require the existing institution pointer plus accepted, active source
// evidence for that same institution. This never infers current display.
const artistHoldingEvidence = `EXISTS(SELECT 1 FROM artwork_location_assertions la JOIN sources s ON s.id=la.source_id AND s.is_active
 WHERE la.artwork_id=aw.id AND la.institution_id=aw.current_institution_id AND la.claim_type='holding'
 AND la.review_state='accepted' AND la.superseded_by IS NULL
 AND la.checked_at<=now() AND (la.effective_from IS NULL OR la.effective_from<=now())
 AND (la.effective_to IS NULL OR la.effective_to>=now())
 AND NOT EXISTS(SELECT 1 FROM artwork_location_assertions conflict WHERE conflict.artwork_id=aw.id
 AND conflict.claim_type='holding' AND conflict.review_state='conflict' AND conflict.superseded_by IS NULL))`

func (r *Repository) artistCollectionSummary(ctx context.Context, artist *ArtistDetail, preview bool) error {
	const query = `WITH linked AS MATERIALIZED (
 SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=$2
 ), scoped AS MATERIALIZED (
 SELECT aw.id,aw.current_institution_id,aw.work_type FROM linked l JOIN artworks aw ON aw.id=l.artwork_id
 WHERE aw.status<>'archived' AND ($1 OR aw.status='published')
 ), collections AS MATERIALIZED (
 SELECT i.id,i.slug,i.name,count(*) AS work_count FROM scoped aw JOIN institutions i ON i.id=aw.current_institution_id
 WHERE i.status<>'archived' AND ($1 OR i.status='published') AND ` + artistHoldingEvidence + `
 GROUP BY i.id,i.slug,i.name
 ) SELECT (SELECT count(*) FROM scoped),(SELECT count(*) FROM collections),
 coalesce((SELECT jsonb_agg(c ORDER BY c.work_count DESC,c.name,c.id) FROM (SELECT * FROM collections ORDER BY work_count DESC,name,id LIMIT 100)c),'[]'::jsonb), coalesce((SELECT jsonb_agg(t ORDER BY t.name) FROM (SELECT work_type AS slug,initcap(replace(work_type,'_',' ')) AS name,count(*) AS count FROM scoped GROUP BY work_type LIMIT 100)t),'[]'::jsonb)`
	var data, types []byte
	if err := r.db.QueryRow(ctx, query, museumQueryArgs(preview, artist.ID)...).Scan(&artist.ArtworkCount, &artist.CollectionCount, &data, &types); err != nil {
		return err
	}
	if err := json.Unmarshal(types, &artist.WorkTypes); err != nil {
		return err
	}
	return json.Unmarshal(data, &artist.Collections)
}
