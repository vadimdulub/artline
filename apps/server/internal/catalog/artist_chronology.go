package catalog

import (
	"context"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
)

var ErrChronologyFilter = errors.New("invalid artwork chronology filter")

type ArtistWorksFilter struct {
	Query, Museum, WorkType string
	Year                    *int
	Undated                 bool
	Limit                   int
	Cursor                  string
	ImageOnly               bool
	NeighborOf, Direction   string
}
type ArtworkYear struct {
	Year  int `json:"year"`
	Count int `json:"count"`
}
type ArtworkYearGroup struct {
	Year              *int `json:"year"`
	StartIndex        int  `json:"start_index"`
	Count             int  `json:"count"`
	HasUncertainDates bool `json:"has_uncertain_dates"`
}
type ArtistWorksPage struct {
	Items         []Artwork          `json:"items"`
	Years         []ArtworkYear      `json:"years"`
	Total         int                `json:"total"`
	UndatedCount  int                `json:"undated_count"`
	MatchingTotal int                `json:"matching_total"`
	NextCursor    string             `json:"next_cursor"`
	Groups        []ArtworkYearGroup `json:"groups"`
	RangeStart    int                `json:"range_start"`
	RangeEnd      int                `json:"range_end"`
}
type artworkCursor struct {
	Year  *int   `json:"y"`
	Order int    `json:"o"`
	Title string `json:"t"`
	ID    string `json:"i"`
	Scope string `json:"s"`
}

// Keep a range/open-ended date's recorded boundary; never substitute a painter's
// lifespan for an unknown work date. Materialize ONLY this painter's attribution
// links first: no museum/global-artworks CTE, media join or JSON in the aggregate.
// Multiple attribution links yield one artwork, not duplicates.
const artistWorksCTE = `WITH artist_links AS MATERIALIZED (
 SELECT DISTINCT ON (artwork_id) artwork_id,attribution_role,representative_order
 FROM artwork_artists WHERE artist_id=$1
 ORDER BY artwork_id,(attribution_role='primary') DESC,representative_order NULLS LAST,attribution_role
), painter_works AS NOT MATERIALIZED (
 SELECT aw.*,aa.attribution_role,aa.representative_order,
 CASE WHEN aw.date_precision='unknown' THEN NULL ELSE coalesce(aw.creation_year_start,aw.creation_year_end) END AS chronology_year
 FROM artist_links aa JOIN artworks aw ON aw.id=aa.artwork_id
 WHERE aw.status<>'archived'
) `

// Search and collection filters are applied inside the already painter-scoped
// set, before summaries, pagination and record navigation.
var artistWorksFilteredCTE = strings.Replace(artistWorksCTE, "WHERE aw.status<>'archived'", `WHERE
 ($2='' OR aw.title ILIKE '%'||$2||'%' OR aw.alternate_title ILIKE '%'||$2||'%' OR aw.accession_number ILIKE '%'||$2||'%')
 AND ($3='' OR EXISTS(SELECT 1 FROM institutions i WHERE i.id=aw.current_institution_id AND i.slug=$3 AND i.status<>'archived'  AND `+artistHoldingEvidence+`))
 AND ($4='' OR aw.work_type=$4)
 AND aw.status<>'archived'`, 1)

// Rank narrow keys first. Full rows/JSON are fetched only after LIMIT, including
// one extra key to detect the next page. No deep OFFSET or full-catalogue sort.
var artistWorksPageQuery = artistWorksFilteredCTE + `, page_keys AS MATERIALIZED (
 SELECT id,chronology_year,lower(title) AS sort_title,coalesce(representative_order,2147483647) AS sort_order,
 attribution_role,representative_order FROM painter_works
 WHERE ($5::int IS NULL OR chronology_year=$5) AND (NOT $6 OR chronology_year IS NULL)
 AND ($7='' OR (chronology_year IS NULL,coalesce(chronology_year,0),coalesce(representative_order,2147483647),lower(title),id::text)>
 ($8::int IS NULL,coalesce($8::int,0),$12,$9,$10))
 ORDER BY chronology_year NULLS LAST,coalesce(representative_order,2147483647),lower(title),id LIMIT $11
 ) SELECT (to_jsonb(aw)-'description_md')||jsonb_build_object('attribution_role',p.attribution_role,'representative_order',p.representative_order),
 p.chronology_year,p.sort_title,p.sort_order FROM page_keys p JOIN artworks aw ON aw.id=p.id
 ORDER BY p.chronology_year NULLS LAST,p.sort_order,p.sort_title,p.id`

func (r *Repository) chronologyArtistID(ctx context.Context, slug string) (string, error) {
	var id string
	err := r.db.QueryRow(ctx, `SELECT id::text FROM artists WHERE
 (slug=$1 OR id=(SELECT entity_id FROM slug_redirects WHERE entity_type='artist' AND old_slug=$1))
 AND status<>'archived' `, slug).Scan(&id)
	if errors.Is(err, pgx.ErrNoRows) {
		return "", ErrNotFound
	}
	return id, err
}

func (r *Repository) ArtistWorks(ctx context.Context, slug string, f ArtistWorksFilter) (ArtistWorksPage, error) {
	out := ArtistWorksPage{Items: []Artwork{}, Years: []ArtworkYear{}, Groups: []ArtworkYearGroup{}}
	if len(f.Query) > 200 || len(f.Museum) > 100 || len(f.WorkType) > 64 || f.Limit < 1 || f.Limit > 60 || len(f.Cursor) > 2048 || (f.Undated && f.Year != nil) || (f.Year != nil && (*f.Year < -10000 || *f.Year > 3000)) {
		return out, ErrChronologyFilter
	}
	if f.NeighborOf != "" || f.Direction != "" {
		var neighborID pgtype.UUID
		if neighborID.Scan(f.NeighborOf) != nil || !neighborID.Valid || f.Cursor != "" || f.Limit != 1 || (f.Direction != "previous" && f.Direction != "next") {
			return out, ErrChronologyFilter
		}
	}
	id, err := r.chronologyArtistID(ctx, slug)
	if err != nil {
		return out, err
	}
	if err = r.db.QueryRow(ctx, `SELECT timeline_start_year,timeline_end_year FROM artists WHERE id=$1`, id).Scan(&out.RangeStart, &out.RangeEnd); err != nil {
		return out, err
	}
	scopeData, _ := json.Marshal([]any{id, f.Year, f.Undated, f.Limit, f.ImageOnly, f.Query, f.Museum, f.WorkType})
	scope := fmt.Sprintf("%x", sha256.Sum256(scopeData))[:24]
	var cursor artworkCursor
	if f.Cursor != "" {
		data, e := base64.RawURLEncoding.DecodeString(f.Cursor)
		if e != nil || json.Unmarshal(data, &cursor) != nil || cursor.Scope != scope || len(cursor.ID) != 36 || len(cursor.Title) > 1000 {
			return out, ErrChronologyFilter
		}
	}
	cte := artistWorksFilteredCTE
	if f.ImageOnly {
		cte = strings.Replace(cte, "AND aw.status<>'archived'", `AND EXISTS(SELECT 1 FROM media_assets image WHERE image.id=aw.primary_media_id AND image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$') AND aw.status<>'archived'`, 1)
	}
	rows, err := r.db.Query(ctx, cte+`SELECT chronology_year,count(*) FROM painter_works GROUP BY chronology_year ORDER BY chronology_year NULLS LAST`, museumQueryArgs(id, f.Query, f.Museum, f.WorkType)...)
	if err != nil {
		return out, err
	}
	for rows.Next() {
		var year *int
		var count int
		if err = rows.Scan(&year, &count); err != nil {
			break
		}
		out.Total += count
		if year == nil {
			out.UndatedCount = count
		} else {
			out.Years = append(out.Years, ArtworkYear{*year, count})
			out.RangeStart = min(out.RangeStart, *year)
			out.RangeEnd = max(out.RangeEnd, *year)
		}
		if (f.Year == nil && !f.Undated) || (f.Undated && year == nil) || (f.Year != nil && year != nil && *f.Year == *year) {
			out.MatchingTotal += count
		}
	}
	rows.Close()
	if err != nil {
		return out, err
	}
	if err = rows.Err(); err != nil {
		return out, err
	}
	pageQuery := strings.Replace(artistWorksPageQuery, artistWorksFilteredCTE, cte, 1)
	pageLimit := f.Limit + 1
	if f.NeighborOf != "" {
		// The anchor must match the active creator, date and image filters.
		anchor, e := r.db.Query(ctx, cte+`SELECT chronology_year,coalesce(representative_order,2147483647),lower(title),id::text FROM painter_works WHERE id=$5 AND ($6::int IS NULL OR chronology_year=$6) AND (NOT $7 OR chronology_year IS NULL)`, museumQueryArgs(id, f.Query, f.Museum, f.WorkType, f.NeighborOf, f.Year, f.Undated)...)
		if e != nil {
			return out, e
		}
		found := anchor.Next()
		if found {
			e = anchor.Scan(&cursor.Year, &cursor.Order, &cursor.Title, &cursor.ID)
		} else {
			e = anchor.Err()
		}
		anchor.Close()
		if e != nil || !found {
			return out, e
		}
		f.Cursor = "neighbor"
		pageLimit = 1
		if f.Direction == "previous" {
			pageQuery = strings.Replace(pageQuery, "id::text)>", "id::text)<", 1)
			pageQuery = strings.Replace(pageQuery, "ORDER BY chronology_year NULLS LAST,coalesce(representative_order,2147483647),lower(title),id LIMIT", "ORDER BY chronology_year DESC NULLS FIRST,coalesce(representative_order,2147483647) DESC,lower(title) DESC,id DESC LIMIT", 1)
		}
	}
	rows, err = r.db.Query(ctx, pageQuery, museumQueryArgs(id, f.Query, f.Museum, f.WorkType, f.Year, f.Undated, f.Cursor, cursor.Year, cursor.Title, cursor.ID, pageLimit, cursor.Order)...)
	if err != nil {
		return out, err
	}
	var last artworkCursor
	for rows.Next() {
		var work Artwork
		var data []byte
		var year *int
		var title string
		var order int
		if err = rows.Scan(&data, &year, &title, &order); err != nil {
			break
		}
		if err = json.Unmarshal(data, &work); err != nil {
			break
		}
		if len(out.Items) == f.Limit {
			encoded, _ := json.Marshal(last)
			out.NextCursor = base64.RawURLEncoding.EncodeToString(encoded)
			break
		}
		out.Items = append(out.Items, work)
		if len(out.Groups) == 0 || !sameYear(out.Groups[len(out.Groups)-1].Year, year) {
			out.Groups = append(out.Groups, ArtworkYearGroup{Year: year, StartIndex: len(out.Items) - 1})
		}
		group := &out.Groups[len(out.Groups)-1]
		group.Count++
		group.HasUncertainDates = group.HasUncertainDates || work.DatePrecision != "exact"
		last = artworkCursor{Year: year, Order: order, Title: title, ID: work.ID, Scope: scope}
	}
	rows.Close()
	if err != nil {
		return out, err
	}
	if err = rows.Err(); err != nil {
		return out, err
	}
	return out, r.enrichChronologyPage(ctx, out.Items)
}

func (r *Repository) ArtistArtwork(ctx context.Context, slug, workID string) (Artwork, error) {
	var work Artwork
	id, err := r.chronologyArtistID(ctx, slug)
	if err != nil {
		return work, err
	}
	var data []byte
	// Resolve a single work by its UUID primary key, not by casting the column.
	err = r.db.QueryRow(ctx, `SELECT to_jsonb(aw)||jsonb_build_object('attribution_role',aa.attribution_role,'representative_order',aa.representative_order)
 FROM artworks aw JOIN LATERAL (SELECT attribution_role,representative_order FROM artwork_artists
 WHERE artwork_id=aw.id AND artist_id=$1 ORDER BY (attribution_role='primary') DESC,representative_order NULLS LAST,attribution_role LIMIT 1) aa ON true
 WHERE aw.id=$2::uuid AND aw.status<>'archived' `, id, workID).Scan(&data)
	if errors.Is(err, pgx.ErrNoRows) {
		return work, ErrNotFound
	}
	if err != nil {
		return work, err
	}
	if err = json.Unmarshal(data, &work); err != nil {
		return work, err
	}
	works := []Artwork{work}
	err = r.enrichChronologyPage(ctx, works)
	return works[0], err
}

func sameYear(a, b *int) bool { return (a == nil && b == nil) || (a != nil && b != nil && *a == *b) }

// Fetch media only after the 24/60-work page has been selected. Full museum
// membership, other artists and curated collection data are irrelevant here.
func (r *Repository) enrichChronologyPage(ctx context.Context, works []Artwork) error {
	if len(works) == 0 {
		return nil
	}
	ids := make([]string, len(works))
	byID := map[string]int{}
	for i, w := range works {
		ids[i] = w.ID
		byID[w.ID] = i
	}
	rows, err := r.db.Query(ctx, `SELECT aw.id::text,jsonb_build_object(
 'media_url',ma.storage_path,
 'alt_text',ma.alt_text,'rights_status',ma.rights_status,'attribution_text',ma.attribution_text,
 'source_page_url',ma.source_page_url,'license_label',ma.license_label,'license_url',ma.license_url)
 FROM artworks aw LEFT JOIN media_assets ma ON ma.id=aw.primary_media_id WHERE aw.id=ANY($1::uuid[])`, ids)
	if err != nil {
		return err
	}
	for rows.Next() {
		var id string
		var data []byte
		if err = rows.Scan(&id, &data); err != nil {
			break
		}
		if err = json.Unmarshal(data, &works[byID[id]]); err != nil {
			break
		}
	}
	rows.Close()
	if err != nil {
		return err
	}
	if err = rows.Err(); err != nil {
		return err
	}
	return r.enrichArtworks(ctx, works)
}
