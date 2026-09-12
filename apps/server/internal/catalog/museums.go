package catalog

import (
	"context"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
)

var ErrMuseumFilter = errors.New("invalid museum filter or cursor")

// Museum selectivity varies from a few paintings to tens of thousands. Cache
// parameter descriptions, not named statements that can switch to a generic
// plan after repeated use. Parameters remain bound; no SQL interpolation.
func museumQueryArgs(values ...any) []any {
	return append([]any{pgx.QueryExecModeCacheDescribe}, values...)
}

type MuseumFilter struct {
	Query       string
	Regions     []string
	Countries   []string
	Selection   string
	Display     string
	Artist      string
	Movement    string
	Venue       string
	WorkType    string
	Artists     []string
	Movements   []string
	Venues      []string
	WorkTypes   []string
	Start       *int
	End         *int
	UnknownDate bool
	ImageOnly   bool
	Sort        string
	Limit       int
	Cursor      string
}
type MuseumRef struct {
	ID   string `json:"id"`
	Slug string `json:"slug"`
	Name string `json:"name"`
}
type MuseumVenue struct {
	MuseumRef
	City     string `json:"city"`
	Country  string `json:"country"`
	Region   string `json:"region"`
	VisitURL string `json:"visit_url"`
}
type Museum struct {
	MuseumRef
	Kind           string        `json:"kind"`
	Description    string        `json:"description"`
	WebsiteURL     *string       `json:"website_url"`
	Status         string        `json:"status"`
	Venues         []MuseumVenue `json:"venues"`
	WorkCount      int           `json:"work_count"`
	HoldingCount   int           `json:"holding_count"`
	OnViewCount    int           `json:"on_view_count"`
	HighlightCount int           `json:"highlight_count"`
	MustSeeCount   int           `json:"must_see_count"`
	OwnerRevision  int           `json:"owner_revision"`
	Cover          *MuseumWork   `json:"cover"`
}
type MuseumArtist struct {
	MuseumRef
	Role string `json:"role"`
}
type MuseumSelection struct {
	Kind      string     `json:"kind"`
	Position  int        `json:"position"`
	Reason    string     `json:"reason"`
	SourceURL *string    `json:"source_url"`
	CheckedAt *time.Time `json:"checked_at"`
}
type DisplayEvidence struct {
	MuseumRef
	VenueID   string    `json:"venue_id"`
	VenueName string    `json:"venue_name"`
	State     string    `json:"state"`
	Context   *string   `json:"context"`
	Gallery   *string   `json:"gallery"`
	CheckedAt time.Time `json:"checked_at"`
	SourceURL string    `json:"source_url"`
}
type MuseumWork struct {
	ID                   string            `json:"id"`
	Slug                 string            `json:"slug"`
	Title                string            `json:"title"`
	DateDisplay          string            `json:"date_display"`
	UnlinkedCreatorLabel *string           `json:"unlinked_creator_label"`
	CulturalContext      *string           `json:"cultural_context"`
	ObjectForm           *string           `json:"object_form"`
	MediaURL             *string           `json:"media_url"`
	AltText              *string           `json:"alt_text"`
	RightsStatus         *string           `json:"rights_status"`
	Artists              []MuseumArtist    `json:"artists"`
	Selections           []MuseumSelection `json:"selections"`
	Display              *DisplayEvidence  `json:"display"`
	SortNumber           int               `json:"-"`
	SortName             string            `json:"-"`
}
type MuseumArtwork struct {
	Artwork
	Artists    []MuseumArtist    `json:"artists"`
	Selections []MuseumSelection `json:"selections"`
}
type MuseumFacets struct {
	Regions   []FacetOption `json:"regions"`
	Countries []FacetOption `json:"countries"`
	Artists   []FacetOption `json:"artists"`
	Movements []FacetOption `json:"movements"`
}
type MuseumPage struct {
	Items      []Museum     `json:"items"`
	Total      int          `json:"total"`
	NextCursor string       `json:"next_cursor"`
	Facets     MuseumFacets `json:"facets"`
}
type MuseumWorksPage struct {
	Items      []MuseumWork `json:"items"`
	Total      int          `json:"total"`
	NextCursor string       `json:"next_cursor"`
	Facets     MuseumFacets `json:"facets"`
}
type museumCursor struct {
	Number int    `json:"n"`
	Name   string `json:"s"`
	ID     string `json:"i"`
	Scope  string `json:"f"`
}

func cursorScope(f MuseumFilter, slug string, preview bool) string {
	f.Cursor = ""
	f.Artists, f.Movements = filterChoices(f.Artists, f.Artist), filterChoices(f.Movements, f.Movement)
	f.Venues, f.WorkTypes = filterChoices(f.Venues, f.Venue), filterChoices(f.WorkTypes, f.WorkType)
	f.Regions, f.Countries = filterChoices(f.Regions, ""), filterChoices(f.Countries, "")
	f.Artist, f.Movement, f.Venue, f.WorkType = "", "", "", ""
	data, _ := json.Marshal(struct {
		Filter  MuseumFilter
		Slug    string
		Preview bool
	}{f, slug, preview})
	return fmt.Sprintf("%x", sha256.Sum256(data))
}
func decodeMuseumCursor(f MuseumFilter, slug string, preview bool) (museumCursor, error) {
	var c museumCursor
	if f.Limit < 1 || f.Limit > 60 {
		return c, ErrMuseumFilter
	}
	if f.Cursor == "" {
		return c, nil
	}
	if len(f.Cursor) > 2048 {
		return c, ErrMuseumFilter
	}
	data, err := base64.RawURLEncoding.DecodeString(f.Cursor)
	if err != nil || json.Unmarshal(data, &c) != nil || c.Scope != cursorScope(f, slug, preview) || len(c.ID) != 36 {
		return c, ErrMuseumFilter
	}
	// ID is used as a text comparison, not interpolated SQL or a UUID cast.
	return c, nil
}
func encodeMuseumCursor(f MuseumFilter, slug string, preview bool, number int, name, id string) string {
	data, _ := json.Marshal(museumCursor{number, name, id, cursorScope(f, slug, preview)})
	return base64.RawURLEncoding.EncodeToString(data)
}

// These CTEs form one visibility/evidence policy for list counts, cards and details.
// A room number alone is not evidence of display; old or conflicting assertions
// never pass the on_view predicate. An incoming loan does not change holdings.
// Keep works inline: aggregate/facet consumers must not materialize artist JSON
// and full descriptions for every object in a large museum. Card/detail columns
// are projected only where consumed, with the existing membership policy intact.
const museumCTE = `WITH visible_works AS NOT MATERIALIZED (
 SELECT aw.* FROM artworks aw WHERE aw.status<>'archived' AND ($1 OR aw.status='published')
 AND (EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id
   WHERE aa.artwork_id=aw.id AND a.status<>'archived' AND ($1 OR a.status='published'))
 OR (aw.unlinked_creator_label IS NOT NULL
   AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=aw.id)))
), current_display AS (
 SELECT la.*,i.slug AS institution_slug,i.name AS institution_name,coalesce(v.name,i.name) AS venue_name,
 CASE WHEN la.checked_at<now()-interval '30 days'
   OR la.effective_to<now() THEN 'stale' ELSE la.display_state END AS state
 FROM artwork_location_assertions la JOIN institutions i ON i.id=la.institution_id
 LEFT JOIN institution_venues v ON v.id=la.venue_id JOIN sources s ON s.id=la.source_id AND s.is_active
 WHERE la.claim_type='display' AND la.review_state='accepted' AND la.superseded_by IS NULL
 AND la.checked_at<=now() AND (la.effective_from IS NULL OR la.effective_from<=now())
 AND i.status<>'archived' AND ($1 OR i.status='published')
 AND (v.id IS NULL OR (v.status<>'archived' AND ($1 OR v.status='published')))
 AND NOT EXISTS(SELECT 1 FROM artwork_location_assertions conflict WHERE conflict.artwork_id=la.artwork_id
   AND conflict.claim_type='display' AND conflict.review_state='conflict' AND conflict.superseded_by IS NULL)
), museum_memberships AS MATERIALIZED (
 SELECT artwork_id,institution_id,bool_or(holding) AS holding,bool_or(on_view) AS on_view FROM (
 SELECT aw.id AS artwork_id,aw.current_institution_id AS institution_id,true AS holding,false AS on_view
 FROM visible_works aw WHERE aw.current_institution_id IS NOT NULL
 UNION ALL
 SELECT aw.id,d.institution_id,false,true FROM current_display d JOIN visible_works aw ON aw.id=d.artwork_id
 WHERE d.state='on_view'
 ) membership GROUP BY artwork_id,institution_id
), works AS NOT MATERIALIZED (
 SELECT aw.*,i.id AS holding_id,i.slug AS holding_slug,i.name AS holding_name,
 d.institution_id AS display_institution_id,d.venue_id AS display_venue_id,d.state AS display_state,
 CASE WHEN d.id IS NOT NULL THEN jsonb_build_object('id',d.institution_id,'slug',d.institution_slug,'name',d.institution_name,
 'venue_id',d.venue_id,'venue_name',d.venue_name,'state',d.state,'context',d.context,'gallery',d.gallery,
 'checked_at',d.checked_at,'source_url',d.source_url) END AS display,
 CASE WHEN ma.verified_at IS NOT NULL AND ma.rights_status IN ('public_domain','cc0','cc_by','cc_by_sa','licensed')
 AND nullif(trim(ma.alt_text),'') IS NOT NULL THEN ma.storage_path END AS media_url,
 ma.alt_text,ma.rights_status,ma.attribution_text,ma.source_page_url,ma.license_label,ma.license_url,
 (SELECT coalesce(jsonb_agg(jsonb_build_object('id',a.id,'slug',a.slug,'name',a.display_name,'role',aa.attribution_role)
 ORDER BY a.sort_name,aa.attribution_role),'[]'::jsonb) FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id
 WHERE aa.artwork_id=aw.id AND a.status<>'archived' AND ($1 OR a.status='published')) AS artists
 FROM visible_works aw LEFT JOIN institutions i ON i.id=aw.current_institution_id AND i.status<>'archived' AND ($1 OR i.status='published')
 LEFT JOIN current_display d ON d.artwork_id=aw.id LEFT JOIN media_assets ma ON ma.id=aw.primary_media_id
), selections AS NOT MATERIALIZED (
 SELECT ci.*,cc.institution_id,cc.curator_kind FROM curated_collection_items ci
 JOIN curated_collections cc ON cc.id=ci.collection_id
 WHERE cc.status<>'archived' AND ($1 OR cc.status='published')
 AND (cc.curator_kind='owner' OR EXISTS(SELECT 1 FROM sources s WHERE s.id=ci.source_id AND s.is_active))
) `
const museumMembership = `(w.holding_id=i.id OR (w.display_institution_id=i.id AND w.display_state='on_view'))`

// Scope before any media/display/artist enrichment. UNION preserves incoming loans
// without using an OR across the complete artwork table. Each branch is indexed.
var museumScopedCTE = `WITH museum_candidates AS MATERIALIZED (
 SELECT aw.id FROM artworks aw WHERE aw.current_institution_id=(SELECT id FROM institutions WHERE slug=$2)
 UNION SELECT la.artwork_id FROM artwork_location_assertions la
 WHERE la.institution_id=(SELECT id FROM institutions WHERE slug=$2)
 AND la.claim_type='display' AND la.review_state='accepted' AND la.superseded_by IS NULL
), ` + strings.Replace(strings.TrimPrefix(museumCTE, "WITH "),
	"SELECT aw.* FROM artworks aw WHERE", "SELECT aw.* FROM museum_candidates scope JOIN artworks aw ON aw.id=scope.id WHERE", 1)

const museumVisible = `i.status<>'archived' AND ($1 OR i.status='published')`
const venueJSON = `(SELECT coalesce(jsonb_agg(jsonb_build_object('id',v.id,'slug',v.slug,'name',v.name,
 'city',p.name,'country',trim(p.country_code),'region',c.region_code,'visit_url',v.visit_url) ORDER BY v.name),'[]'::jsonb)
 FROM institution_venues v JOIN places p ON p.id=v.place_id JOIN countries c ON c.code=p.country_code
 WHERE v.institution_id=i.id AND v.status<>'archived' AND ($1 OR v.status='published'))`
const selectionJSON = `(SELECT coalesce(jsonb_agg(jsonb_build_object('kind',s.curator_kind,'position',s.position,
 'reason',s.reason,'source_url',s.source_url,'checked_at',s.checked_at) ORDER BY s.curator_kind),'[]'::jsonb)
 FROM selections s WHERE s.institution_id=i.id AND s.artwork_id=w.id)`
const workCardJSON = `jsonb_build_object('id',w.id,'slug',w.slug,'title',w.title,'date_display',w.date_display,
 'unlinked_creator_label',w.unlinked_creator_label,'cultural_context',w.cultural_context,'object_form',w.object_form,
 'media_url',w.media_url,'alt_text',w.alt_text,'rights_status',w.rights_status,'artists',w.artists,'display',w.display,'selections',` + selectionJSON + `)`
const museumJSON = `jsonb_build_object('id',i.id,'slug',i.slug,'name',i.name,'kind',i.kind,'status',i.status,
 'description',i.description,'website_url',i.website_url,'venues',` + venueJSON + `,
 'work_count',(SELECT count(*) FROM museum_memberships m WHERE m.institution_id=i.id),
 'holding_count',(SELECT count(*) FROM museum_memberships m WHERE m.institution_id=i.id AND m.holding),
 'on_view_count',(SELECT count(*) FROM museum_memberships m WHERE m.institution_id=i.id AND m.on_view),
 'highlight_count',(SELECT count(DISTINCT m.artwork_id) FROM museum_memberships m JOIN selections s ON s.institution_id=m.institution_id AND s.artwork_id=m.artwork_id WHERE m.institution_id=i.id AND s.curator_kind='museum'),
 'must_see_count',(SELECT count(DISTINCT m.artwork_id) FROM museum_memberships m JOIN selections s ON s.institution_id=m.institution_id AND s.artwork_id=m.artwork_id WHERE m.institution_id=i.id AND s.curator_kind='owner'),
 'owner_revision',CASE WHEN $1 THEN (SELECT revision FROM curated_collections WHERE institution_id=i.id AND curator_kind='owner') ELSE 0 END,
 'cover',(SELECT ` + workCardJSON + ` FROM works w WHERE w.id=(
 SELECT aw.id FROM museum_memberships member JOIN artworks aw ON aw.id=member.artwork_id
 LEFT JOIN media_assets media ON media.id=aw.primary_media_id WHERE member.institution_id=i.id
 ORDER BY (CASE WHEN media.verified_at IS NOT NULL AND media.rights_status IN ('public_domain','cc0','cc_by','cc_by_sa','licensed')
 AND nullif(trim(media.alt_text),'') IS NOT NULL THEN media.storage_path END IS NULL),aw.creation_year_start NULLS LAST,aw.title,aw.id LIMIT 1)))`

func (r *Repository) Museums(ctx context.Context, f MuseumFilter, preview bool) (MuseumPage, error) {
	out := MuseumPage{Items: []Museum{}, Facets: emptyMuseumFacets()}
	c, err := decodeMuseumCursor(f, "", preview)
	if err != nil {
		return out, err
	}
	args := []any{preview, f.Query, f.Regions, f.Countries, f.Selection, f.Display, filterChoices(f.Artists, f.Artist), filterChoices(f.Movements, f.Movement), filterChoices(f.WorkTypes, f.WorkType)}
	where := ` FROM institutions i WHERE ` + museumVisible + `
 AND ($2='' OR i.name ILIKE '%'||$2||'%' OR EXISTS(SELECT 1 FROM institution_venues v JOIN places p ON p.id=v.place_id JOIN countries co ON co.code=p.country_code
 WHERE v.institution_id=i.id AND v.status<>'archived' AND ($1 OR v.status='published') AND (p.name ILIKE '%'||$2||'%' OR co.name ILIKE '%'||$2||'%')))
 AND ((coalesce(cardinality($3::text[]),0)=0 AND coalesce(cardinality($4::text[]),0)=0) OR EXISTS(
 SELECT 1 FROM institution_venues v JOIN places p ON p.id=v.place_id JOIN countries co ON co.code=p.country_code
 WHERE v.institution_id=i.id AND v.status<>'archived' AND ($1 OR v.status='published')
 AND (coalesce(cardinality($3::text[]),0)=0 OR co.region_code=ANY($3)) AND (coalesce(cardinality($4::text[]),0)=0 OR p.country_code::text=ANY($4))))
 AND EXISTS(SELECT 1 FROM museum_memberships member WHERE member.institution_id=i.id
 AND ($5='' OR EXISTS(SELECT 1 FROM selections s WHERE s.institution_id=i.id AND s.artwork_id=member.artwork_id AND s.curator_kind=$5))
 AND ($6='' OR member.on_view)
 AND (cardinality($7::text[])=0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=member.artwork_id AND a.slug=ANY($7) AND a.status<>'archived' AND ($1 OR a.status='published')))
 AND (cardinality($8::text[])=0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id JOIN artist_movements am ON am.artist_id=a.id JOIN movements m ON m.id=am.movement_id WHERE aa.artwork_id=member.artwork_id AND m.slug=ANY($8) AND a.status<>'archived' AND m.status<>'archived' AND ($1 OR (a.status='published' AND m.status='published'))))
 AND (cardinality($9::text[])=0 OR EXISTS(SELECT 1 FROM artworks aw WHERE aw.id=member.artwork_id AND aw.work_type=ANY($9))))`
	if err = r.db.QueryRow(ctx, museumCTE+`SELECT count(*)`+where, museumQueryArgs(args...)...).Scan(&out.Total); err != nil {
		return out, err
	}
	args = append(args, c.Name, c.ID, f.Limit+1)
	// Resolve a bounded institution page first. Its cards use institution-scoped
	// candidates inside one SQL request; never scan the whole artwork table for
	// each returned museum's counts and cover. The nested CTE retains exactly the
	// same preview, incoming-loan, rights and display-evidence policy as details.
	rows, err := r.db.Query(ctx, museumCTE+`, museum_page AS MATERIALIZED (
 SELECT i.id,i.slug,i.normalized_name`+where+`
 AND ($10='' OR (i.normalized_name,i.id::text)>($10,$11)) ORDER BY i.normalized_name,i.id LIMIT $12)
 SELECT detail.data,page.normalized_name FROM museum_page page CROSS JOIN LATERAL (
 `+strings.ReplaceAll(museumScopedCTE, "$2", "page.slug")+` SELECT `+museumJSON+` AS data FROM institutions i WHERE i.id=page.id
 ) detail ORDER BY page.normalized_name,page.id`, museumQueryArgs(args...)...)
	if err != nil {
		return out, err
	}
	var names []string
	for rows.Next() {
		var item Museum
		var data []byte
		var name string
		if err = rows.Scan(&data, &name); err != nil {
			break
		}
		if err = json.Unmarshal(data, &item); err != nil {
			break
		}
		out.Items = append(out.Items, item)
		names = append(names, name)
	}
	rows.Close()
	if err != nil {
		return out, err
	}
	if err = rows.Err(); err != nil {
		return out, err
	}
	if len(out.Items) > f.Limit {
		out.Items = out.Items[:f.Limit]
		last := out.Items[f.Limit-1]
		out.NextCursor = encodeMuseumCursor(f, "", preview, 0, names[f.Limit-1], last.ID)
	}
	out.Facets, err = r.museumFacets(ctx, "", preview)
	return out, err
}
func (r *Repository) Museum(ctx context.Context, slug string, preview bool) (Museum, error) {
	var out Museum
	var data []byte
	err := r.db.QueryRow(ctx, museumScopedCTE+`SELECT `+museumJSON+` FROM institutions i WHERE i.slug=$2 AND `+museumVisible+` AND EXISTS(SELECT 1 FROM works w WHERE `+museumMembership+`)`, museumQueryArgs(preview, slug)...).Scan(&data)
	if errors.Is(err, pgx.ErrNoRows) {
		return out, ErrNotFound
	}
	if err != nil {
		return out, err
	}
	err = json.Unmarshal(data, &out)
	return out, err
}
func emptyMuseumFacets() MuseumFacets {
	return MuseumFacets{Regions: []FacetOption{}, Countries: []FacetOption{}, Artists: []FacetOption{}, Movements: []FacetOption{}}
}
func (r *Repository) museumFacets(ctx context.Context, slug string, preview bool) (MuseumFacets, error) {
	out := emptyMuseumFacets()
	cte := museumCTE
	if slug != "" {
		cte = museumScopedCTE
	}
	query := cte + `SELECT DISTINCT c.region_code,initcap(replace(c.region_code,'-',' ')),trim(c.code),c.name
 FROM institutions i JOIN institution_venues v ON v.institution_id=i.id JOIN places p ON p.id=v.place_id JOIN countries c ON c.code=p.country_code
 WHERE ` + museumVisible + ` AND v.status<>'archived' AND ($1 OR v.status='published') AND ($2='' OR i.slug=$2)
 AND EXISTS(SELECT 1 FROM museum_memberships member WHERE member.institution_id=i.id) ORDER BY c.region_code,c.name`
	rows, err := r.db.Query(ctx, query, museumQueryArgs(preview, slug)...)
	if err != nil {
		return out, err
	}
	regions, countries := map[string]bool{}, map[string]bool{}
	for rows.Next() {
		var region, name, country, countryName string
		if err = rows.Scan(&region, &name, &country, &countryName); err != nil {
			break
		}
		if !regions[region] {
			out.Regions = append(out.Regions, FacetOption{Slug: region, Name: name})
			regions[region] = true
		}
		if !countries[country] {
			out.Countries = append(out.Countries, FacetOption{Slug: country, Name: countryName})
			countries[country] = true
		}
	}
	rows.Close()
	if err != nil {
		return out, err
	}
	if err = rows.Err(); err != nil {
		return out, err
	}
	// Artist discovery is paged/searchable through PainterOptions; retain a small
	// compatibility facet instead of shipping every painter in a large collection.
	rows, err = r.db.Query(ctx, cte+`(SELECT DISTINCT 'artist',a.slug,a.display_name FROM institutions i JOIN museum_memberships member ON member.institution_id=i.id
 JOIN artwork_artists aa ON aa.artwork_id=member.artwork_id JOIN artists a ON a.id=aa.artist_id
 WHERE i.slug=$2 AND `+museumVisible+` AND a.status<>'archived' AND ($1 OR a.status='published') ORDER BY 3 LIMIT 30)
 UNION (SELECT DISTINCT 'movement',m.slug,m.name FROM institutions i JOIN museum_memberships member ON member.institution_id=i.id
 JOIN artwork_artists aa ON aa.artwork_id=member.artwork_id JOIN artists a ON a.id=aa.artist_id JOIN artist_movements am ON am.artist_id=a.id JOIN movements m ON m.id=am.movement_id
 WHERE ($2='' OR i.slug=$2) AND `+museumVisible+` AND a.status<>'archived' AND m.status<>'archived' AND ($1 OR (a.status='published' AND m.status='published')) ORDER BY 3 LIMIT 500) ORDER BY 1,3`, museumQueryArgs(preview, slug)...)
	if err != nil {
		return out, err
	}
	defer rows.Close()
	for rows.Next() {
		var kind string
		var option FacetOption
		if err = rows.Scan(&kind, &option.Slug, &option.Name); err != nil {
			return out, err
		}
		if kind == "artist" {
			out.Artists = append(out.Artists, option)
		} else {
			out.Movements = append(out.Movements, option)
		}
	}
	return out, rows.Err()
}

func (r *Repository) MuseumWorks(ctx context.Context, slug string, f MuseumFilter, preview bool) (MuseumWorksPage, error) {
	out := MuseumWorksPage{Items: []MuseumWork{}, Facets: emptyMuseumFacets()}
	c, err := decodeMuseumCursor(f, slug, preview)
	if err != nil {
		return out, err
	}
	// Preserve the exact visibility/membership policy without rebuilding the
	// museum's cover and six aggregate counts just to check its existence.
	var exists bool
	err = r.db.QueryRow(ctx, museumScopedCTE+`SELECT EXISTS(SELECT 1 FROM institutions i WHERE i.slug=$2 AND `+museumVisible+` AND EXISTS(SELECT 1 FROM works w WHERE `+museumMembership+`))`, museumQueryArgs(preview, slug)...).Scan(&exists)
	if err != nil {
		return out, err
	}
	if !exists {
		return out, ErrNotFound
	}
	args := []any{preview, slug, f.Query, f.Selection, f.Display, filterChoices(f.Artists, f.Artist), filterChoices(f.Movements, f.Movement), filterChoices(f.Venues, f.Venue), filterChoices(f.WorkTypes, f.WorkType), f.Start, f.End, f.UnknownDate, f.ImageOnly}
	where := ` FROM institutions i JOIN works w ON ` + museumMembership + ` WHERE i.slug=$2 AND ` + museumVisible + `
 AND ($3='' OR w.title ILIKE '%'||$3||'%' OR w.alternate_title ILIKE '%'||$3||'%' OR w.unlinked_creator_label ILIKE '%'||$3||'%'
 OR w.cultural_context ILIKE '%'||$3||'%' OR w.object_form ILIKE '%'||$3||'%'
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(w.artists) a WHERE a->>'name' ILIKE '%'||$3||'%'))
 AND ($4='' OR EXISTS(SELECT 1 FROM selections s WHERE s.institution_id=i.id AND s.artwork_id=w.id AND s.curator_kind=$4))
 AND ($5='' OR (w.display_institution_id=i.id AND w.display_state='on_view'))
 AND (cardinality($6::text[])=0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=w.id AND a.slug=ANY($6) AND a.status<>'archived' AND ($1 OR a.status='published')))
 AND (cardinality($7::text[])=0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id JOIN artist_movements am ON am.artist_id=a.id JOIN movements m ON m.id=am.movement_id
 WHERE aa.artwork_id=w.id AND m.slug=ANY($7) AND a.status<>'archived' AND m.status<>'archived' AND ($1 OR (a.status='published' AND m.status='published'))))
 AND (cardinality($8::text[])=0 OR (w.display_venue_id::text=ANY($8) AND w.display_institution_id=i.id AND w.display_state='on_view'))
 AND (cardinality($9::text[])=0 OR w.work_type=ANY($9))
 AND ($10::int IS NULL OR w.creation_year_end>=$10) AND ($11::int IS NULL OR w.creation_year_start<=$11)
 AND (NOT $12 OR w.creation_year_start IS NULL OR w.creation_year_end IS NULL) AND (NOT $13 OR w.media_url IS NOT NULL)`
	if err = r.db.QueryRow(ctx, museumScopedCTE+`SELECT count(*)`+where, museumQueryArgs(args...)...).Scan(&out.Total); err != nil {
		return out, err
	}
	args = append(args, f.Sort, c.Number, c.Name, c.ID, f.Cursor == "", f.Limit+1)
	sortNumber := `CASE WHEN $14='title' THEN 0 WHEN $14='curated' AND $4<>'' THEN coalesce((SELECT min(position) FROM selections s WHERE s.institution_id=i.id AND s.artwork_id=w.id AND s.curator_kind=$4),2147483647) ELSE coalesce(w.creation_year_start,2147483647) END`
	rows, err := r.db.Query(ctx, museumScopedCTE+`SELECT `+workCardJSON+`,`+sortNumber+`,w.normalized_title`+where+`
 AND ($18 OR (`+sortNumber+`,w.normalized_title,w.id::text)>($15,$16,$17))
 ORDER BY 2,w.normalized_title,w.id LIMIT $19`, museumQueryArgs(args...)...)
	if err != nil {
		return out, err
	}
	for rows.Next() {
		var item MuseumWork
		var data []byte
		if err = rows.Scan(&data, &item.SortNumber, &item.SortName); err != nil {
			break
		}
		if err = json.Unmarshal(data, &item); err != nil {
			break
		}
		out.Items = append(out.Items, item)
	}
	rows.Close()
	if err != nil {
		return out, err
	}
	if err = rows.Err(); err != nil {
		return out, err
	}
	if len(out.Items) > f.Limit {
		out.Items = out.Items[:f.Limit]
		last := out.Items[f.Limit-1]
		out.NextCursor = encodeMuseumCursor(f, slug, preview, last.SortNumber, last.SortName, last.ID)
	}
	out.Facets, err = r.museumFacets(ctx, slug, preview)
	return out, err
}

func (r *Repository) MuseumArtwork(ctx context.Context, slug, id string, preview bool) (MuseumArtwork, error) {
	var out MuseumArtwork
	var data []byte
	query := museumScopedCTE + `SELECT to_jsonb(w)||jsonb_build_object('selections',` + selectionJSON + `,
 'attribution_role',coalesce(w.artists->0->>'role','unlinked'),'holding',CASE WHEN w.holding_id IS NOT NULL THEN
 jsonb_build_object('id',w.holding_id,'slug',w.holding_slug,'name',w.holding_name) END)
 FROM institutions i JOIN works w ON ` + museumMembership + ` WHERE i.slug=$2 AND w.id::text=$3 AND ` + museumVisible
	err := r.db.QueryRow(ctx, query, preview, slug, id).Scan(&data)
	if errors.Is(err, pgx.ErrNoRows) {
		return out, ErrNotFound
	}
	if err != nil {
		return out, err
	}
	if err = json.Unmarshal(data, &out); err != nil {
		return out, err
	}
	out.Citations, err = r.entityCitations(ctx, "artwork", id)
	return out, err
}

type MustSeeInput struct {
	ArtworkID        string `json:"artwork_id"`
	Selected         bool   `json:"selected"`
	Position         int    `json:"position"`
	Reason           string `json:"reason"`
	ExpectedRevision int    `json:"expected_revision"`
}

func (r *Repository) SaveMustSee(ctx context.Context, slug string, in MustSeeInput) (int, error) {
	tx, err := r.db.Begin(ctx)
	if err != nil {
		return 0, err
	}
	defer tx.Rollback(ctx)
	var id string
	var revision int
	err = tx.QueryRow(ctx, `SELECT cc.id::text,cc.revision FROM curated_collections cc JOIN institutions i ON i.id=cc.institution_id
 WHERE i.slug=$1 AND i.status<>'archived' AND cc.curator_kind='owner' AND cc.status<>'archived' FOR UPDATE OF cc`, slug).Scan(&id, &revision)
	if errors.Is(err, pgx.ErrNoRows) {
		return 0, ErrNotFound
	}
	if err != nil {
		return 0, err
	}
	if in.ExpectedRevision != revision {
		return revision, ErrRevisionConflict
	}
	repo := &Repository{db: tx}
	if _, err = repo.MuseumArtwork(ctx, slug, in.ArtworkID, true); err != nil {
		return 0, err
	}
	if in.Selected {
		_, err = tx.Exec(ctx, `INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason) VALUES($1,$2,$3,$4)
   ON CONFLICT(collection_id,artwork_id) DO UPDATE SET position=EXCLUDED.position,reason=EXCLUDED.reason`, id, in.ArtworkID, in.Position, in.Reason)
	} else {
		_, err = tx.Exec(ctx, `DELETE FROM curated_collection_items WHERE collection_id=$1 AND artwork_id=$2`, id, in.ArtworkID)
	}
	if err != nil {
		return 0, err
	}
	// Editing an already published selection returns it to review; no implicit publication.
	_, err = tx.Exec(ctx, `UPDATE curated_collections SET revision=revision+1,updated_at=now(),status='review' WHERE id=$1`, id)
	if err != nil {
		return 0, err
	}
	if err = tx.Commit(ctx); err != nil {
		return 0, err
	}
	return revision + 1, nil
}
