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
	"github.com/jackc/pgx/v5/pgtype"
)

var ErrMuseumFilter = errors.New("invalid museum filter or cursor")

// Match ArtworkImage's supported delivery paths. A non-null remote URL or an
// unsupported file is not an image the gallery can actually render.
const museumAvailableImage = `EXISTS(SELECT 1 FROM media_assets image WHERE image.id=w.primary_media_id
 AND image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$')`

// Old source-specific museum URLs continue to address the reviewed canonical
// identity. Each caller still applies its normal publication/access policy.
func (r *Repository) canonicalMuseumSlug(ctx context.Context, slug string) (string, error) {
	var resolved string
	err := r.db.QueryRow(ctx, `SELECT coalesce(c.slug,i.slug) FROM institutions i
 LEFT JOIN institutions c ON c.id=i.canonical_institution_id
 WHERE i.slug=$1 AND i.status<>'archived' AND (c.id IS NULL OR c.status<>'archived')`, slug).Scan(&resolved)
	if errors.Is(err, pgx.ErrNoRows) {
		return "", ErrNotFound
	}
	return resolved, err
}

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
	City           *string       `json:"city"`
	Country        *string       `json:"country"`
	Venues         []MuseumVenue `json:"venues"`
	WorkCount      int           `json:"work_count"`
	HoldingCount   int           `json:"holding_count"`
	OnViewCount    int           `json:"on_view_count"`
	HighlightCount int           `json:"highlight_count"`
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
	ImageCount int          `json:"image_count"`
	NextCursor string       `json:"next_cursor"`
	Facets     MuseumFacets `json:"facets"`
}
type museumCursor struct {
	Number int    `json:"n"`
	Name   string `json:"s"`
	ID     string `json:"i"`
	Scope  string `json:"f"`
}

func cursorScope(f MuseumFilter, slug string) string {
	f.Cursor = ""
	f.Artists, f.Movements = filterChoices(f.Artists, f.Artist), filterChoices(f.Movements, f.Movement)
	f.Venues, f.WorkTypes = filterChoices(f.Venues, f.Venue), filterChoices(f.WorkTypes, f.WorkType)
	f.Regions, f.Countries = filterChoices(f.Regions, ""), filterChoices(f.Countries, "")
	f.Artist, f.Movement, f.Venue, f.WorkType = "", "", "", ""
	data, _ := json.Marshal(struct {
		Filter MuseumFilter
		Slug   string
	}{f, slug})
	return fmt.Sprintf("%x", sha256.Sum256(data))
}
func decodeMuseumCursor(f MuseumFilter, slug string) (museumCursor, error) {
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
	if err != nil || json.Unmarshal(data, &c) != nil || c.Scope != cursorScope(f, slug) || len(c.ID) != 36 {
		return c, ErrMuseumFilter
	}
	// ID is used as a text comparison, not interpolated SQL or a UUID cast.
	return c, nil
}
func encodeMuseumCursor(f MuseumFilter, slug string, number int, name, id string) string {
	data, _ := json.Marshal(museumCursor{number, name, id, cursorScope(f, slug)})
	return base64.RawURLEncoding.EncodeToString(data)
}

// These CTEs form one visibility/evidence policy for list counts, cards and details.
// A room number alone is not evidence of display; old or conflicting assertions
// never pass the on_view predicate. An incoming loan does not change holdings.
// Keep works inline: aggregate/facet consumers must not materialize artist JSON
// and full descriptions for every object in a large museum. Card/detail columns
// are projected only where consumed, with the existing membership policy intact.
const museumCTE = `WITH visible_works AS NOT MATERIALIZED (
 SELECT aw.* FROM artworks aw WHERE aw.status<>'archived'

), current_display AS (
 SELECT la.*,i.slug AS institution_slug,i.name AS institution_name,coalesce(v.name,i.name) AS venue_name,
 CASE WHEN la.checked_at<now()-interval '30 days'
   OR la.effective_to<now() THEN 'stale' ELSE la.display_state END AS state
 FROM artwork_location_assertions la JOIN institutions i ON i.id=la.institution_id
 LEFT JOIN institution_venues v ON v.id=la.venue_id JOIN sources s ON s.id=la.source_id AND s.is_active
 WHERE la.claim_type='display' AND la.review_state='accepted' AND la.superseded_by IS NULL
 AND la.checked_at<=now() AND (la.effective_from IS NULL OR la.effective_from<=now())
 AND i.status<>'archived'
 AND (v.id IS NULL OR (v.status<>'archived' ))
 AND NOT EXISTS(SELECT 1 FROM artwork_location_assertions conflict WHERE conflict.artwork_id=la.artwork_id
   AND conflict.claim_type='display' AND conflict.review_state='conflict' AND conflict.superseded_by IS NULL)
), museum_memberships AS MATERIALIZED (
 ` +
	museumMembershipAggregate + `
), works AS NOT MATERIALIZED (
 SELECT aw.*,i.id AS holding_id,i.slug AS holding_slug,i.name AS holding_name,
 d.institution_id AS display_institution_id,d.venue_id AS display_venue_id,d.state AS display_state,
 CASE WHEN d.id IS NOT NULL THEN jsonb_build_object('id',d.institution_id,'slug',d.institution_slug,'name',d.institution_name,
 'venue_id',d.venue_id,'venue_name',d.venue_name,'state',d.state,'context',d.context,'gallery',d.gallery,
 'checked_at',d.checked_at,'source_url',d.source_url) END AS display,
 ma.storage_path AS media_url,
 ma.alt_text,ma.rights_status,ma.attribution_text,ma.source_page_url,ma.license_label,ma.license_url,
 (SELECT coalesce(jsonb_agg(jsonb_build_object('id',a.id,'slug',a.slug,'name',a.display_name,'role',aa.attribution_role)
 ORDER BY a.sort_name,aa.attribution_role),'[]'::jsonb) FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id
 WHERE aa.artwork_id=aw.id AND a.status<>'archived' ) AS artists
 FROM visible_works aw LEFT JOIN institutions i ON i.id=aw.current_institution_id AND i.status<>'archived'
 LEFT JOIN current_display d ON d.artwork_id=aw.id LEFT JOIN media_assets ma ON ma.id=aw.primary_media_id
), selections AS NOT MATERIALIZED (
 SELECT ci.*,cc.institution_id,cc.curator_kind FROM curated_collection_items ci
 JOIN curated_collections cc ON cc.id=ci.collection_id
 WHERE cc.status<>'archived'
 AND cc.curator_kind='museum' AND EXISTS(SELECT 1 FROM sources s WHERE s.id=ci.source_id AND s.is_active)
) `

const museumMembershipCandidates = `SELECT aw.id AS artwork_id,aw.current_institution_id AS institution_id,true AS holding,false AS on_view
 FROM visible_works aw WHERE aw.current_institution_id IS NOT NULL
 UNION ALL
 SELECT aw.id,d.institution_id,false,true FROM current_display d JOIN visible_works aw ON aw.id=d.artwork_id
 WHERE d.state='on_view'`

const museumMembershipAggregate = `SELECT artwork_id,institution_id,bool_or(holding) AS holding,bool_or(on_view) AS on_view FROM (
 ` + museumMembershipCandidates + `
 ) membership GROUP BY artwork_id,institution_id`

// Directory filters and facets only test membership existence (or DISTINCT
// options). They do not need one aggregated row per artwork/institution. Keep
// the same holding/display evidence branches inline so an institution predicate
// reaches the indexed candidates instead of materializing the entire catalogue.
// Museum cards still use the aggregated, institution-scoped CTE for exact counts.
var museumDirectoryCTE = strings.Replace(strings.Replace(museumCTE,
	"museum_memberships AS MATERIALIZED (", "museum_memberships AS NOT MATERIALIZED (", 1),
	museumMembershipAggregate, museumMembershipCandidates, 1)

const museumMembership = `(w.holding_id=i.id OR (w.display_institution_id=i.id AND w.display_state='on_view'))`

// Read scoped rows directly through the institution index. Materializing every
// UUID first prevents existence checks from stopping early and then forces a
// second random heap lookup for each work. The disjoint incoming-loan branch
// preserves membership without a global artwork scan or duplicate cards.
var museumScopedCTE = `WITH museum_candidates AS NOT MATERIALIZED (
 SELECT aw.* FROM artworks aw WHERE aw.current_institution_id=(SELECT id FROM institutions WHERE slug=$1)
 UNION ALL
 SELECT aw.* FROM artworks aw WHERE aw.current_institution_id IS DISTINCT FROM (SELECT id FROM institutions WHERE slug=$1)
 AND aw.id IN(SELECT la.artwork_id FROM artwork_location_assertions la
 WHERE la.institution_id=(SELECT id FROM institutions WHERE slug=$1)
 AND la.claim_type='display' AND la.review_state='accepted' AND la.superseded_by IS NULL)
), ` + strings.Replace(strings.TrimPrefix(museumCTE, "WITH "),
	"SELECT aw.* FROM artworks aw WHERE", "SELECT aw.* FROM museum_candidates aw WHERE", 1)

// Facets reuse the same visible IDs across holding, display, artist and movement
// branches. Materialize only these two small columns, once per museum; otherwise
// incoming display rows can repeatedly rescan every holding and creator.
var museumScopedFacetCTE = strings.NewReplacer(
	"visible_works AS NOT MATERIALIZED (", "visible_works AS MATERIALIZED (",
	"SELECT aw.* FROM museum_candidates aw WHERE", "SELECT aw.id,aw.current_institution_id FROM museum_candidates aw WHERE",
	"FROM visible_works aw LEFT JOIN institutions", "FROM visible_works visible JOIN artworks aw ON aw.id=visible.id LEFT JOIN institutions",
).Replace(museumScopedCTE)

// Directory cards already have a bounded institution page. Read each holding
// through its institution index directly, avoiding a second artwork UUID lookup
// for every row. Incoming loans remain a separate indexed branch; exclude the
// holding branch's IDs so a work in both branches is counted only once.
var museumDirectoryCardCTE = `WITH card_candidates AS NOT MATERIALIZED (
 SELECT aw.* FROM artworks aw WHERE aw.current_institution_id=page.id
 UNION ALL
 SELECT aw.* FROM artworks aw WHERE aw.current_institution_id IS DISTINCT FROM page.id
 AND aw.id IN(SELECT la.artwork_id FROM artwork_location_assertions la
 WHERE la.institution_id=page.id AND la.claim_type='display' AND la.review_state='accepted' AND la.superseded_by IS NULL)
), ` + strings.NewReplacer(
	"visible_works AS NOT MATERIALIZED (", "visible_works AS MATERIALIZED (",
	"SELECT aw.* FROM artworks aw WHERE", "SELECT aw.id,aw.current_institution_id,aw.primary_media_id,aw.title,aw.creation_year_start FROM card_candidates aw WHERE",
	"FROM visible_works aw LEFT JOIN institutions", "FROM visible_works visible JOIN artworks aw ON aw.id=visible.id LEFT JOIN institutions",
).Replace(strings.TrimPrefix(museumCTE, "WITH "))

// Selective filters start from indexed artwork IDs, not from every museum's
// holdings. Remaining predicates below still apply independently to each work,
// including museum-specific selections and different creators on joint works.
func museumDirectoryFilterCTE(f MuseumFilter) (string, string) {
	candidates := ""
	switch {
	case f.Selection != "":
		candidates = `SELECT DISTINCT artwork_id FROM selections WHERE curator_kind=$4`
	case len(filterChoices(f.Artists, f.Artist)) > 0:
		candidates = `SELECT DISTINCT aa.artwork_id FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id
 WHERE a.slug=ANY($6::text[]) AND a.status<>'archived' `
	case len(filterChoices(f.Movements, f.Movement)) > 0:
		candidates = `SELECT DISTINCT aa.artwork_id FROM movements m JOIN artist_movements am ON am.movement_id=m.id
 JOIN artists a ON a.id=am.artist_id JOIN artwork_artists aa ON aa.artist_id=a.id
 WHERE m.slug=ANY($7::text[]) AND m.status<>'archived' AND a.status<>'archived' `
	default:
		return museumDirectoryCTE, "museum_memberships"
	}
	return museumDirectoryCTE + `, directory_filter_candidates AS MATERIALIZED (` + candidates + `),
 directory_filtered_memberships AS MATERIALIZED (
 SELECT member.* FROM directory_filter_candidates candidate CROSS JOIN LATERAL (
 SELECT * FROM museum_memberships WHERE artwork_id=candidate.artwork_id OFFSET 0) member
 ) /* directory filter end */ `, "directory_filtered_memberships"
}

// A detail request identifies one artwork. Resolve that UUID before applying
// the shared artist, holding, incoming-loan, display and media visibility policy.
// Building every candidate in a large museum first can exceed the HTTP deadline.
var museumArtworkScopedCTE = strings.Replace(museumCTE,
	"SELECT aw.* FROM artworks aw WHERE", "SELECT aw.* FROM artworks aw WHERE aw.id=$2::uuid AND", 1)

const museumVisible = `i.status<>'archived' `
const venueJSON = `(SELECT coalesce(jsonb_agg(jsonb_build_object('id',v.id,'slug',v.slug,'name',v.name,
 'city',p.name,'country',trim(p.country_code),'region',c.region_code,'visit_url',v.visit_url) ORDER BY v.name),'[]'::jsonb)
 FROM institution_venues v JOIN places p ON p.id=v.place_id JOIN countries c ON c.code=p.country_code
 WHERE v.institution_id=i.id AND v.status<>'archived' )`
const selectionJSON = `(SELECT coalesce(jsonb_agg(jsonb_build_object('kind',s.curator_kind,'position',s.position,
 'reason',s.reason,'source_url',s.source_url,'checked_at',s.checked_at) ORDER BY s.curator_kind),'[]'::jsonb)
 FROM selections s WHERE s.institution_id=i.id AND s.artwork_id=w.id)`
const workCardJSON = `jsonb_build_object('id',w.id,'slug',w.slug,'title',w.title,'date_display',w.date_display,
 'unlinked_creator_label',w.unlinked_creator_label,'cultural_context',w.cultural_context,'object_form',w.object_form,
 'media_url',w.media_url,'alt_text',w.alt_text,'rights_status',w.rights_status,'artists',w.artists,'display',w.display,'selections',` + selectionJSON + `)`
const museumJSON = `jsonb_build_object('id',i.id,'slug',i.slug,'name',i.name,'kind',i.kind,'status',i.status,
 'description',i.description,'website_url',i.website_url,'venues',` + venueJSON + `,
 'city',(SELECT name FROM places WHERE id=i.place_id),'country',(SELECT trim(country_code) FROM places WHERE id=i.place_id),
 'work_count',(SELECT count(*) FROM museum_memberships m WHERE m.institution_id=i.id),
 'holding_count',(SELECT count(*) FROM museum_memberships m WHERE m.institution_id=i.id AND m.holding),
 'on_view_count',(SELECT count(*) FROM museum_memberships m WHERE m.institution_id=i.id AND m.on_view),
 'highlight_count',(SELECT count(DISTINCT m.artwork_id) FROM museum_memberships m JOIN selections s ON s.institution_id=m.institution_id AND s.artwork_id=m.artwork_id WHERE m.institution_id=i.id AND s.curator_kind='museum'),
 'cover',(SELECT ` + workCardJSON + ` FROM works w WHERE w.id=(
 SELECT coalesce(
 (SELECT candidate.id FROM (
 SELECT aw.id,aw.primary_media_id,aw.creation_year_start,aw.title FROM museum_memberships member JOIN artworks aw ON aw.id=member.artwork_id
 WHERE member.institution_id=i.id ORDER BY aw.creation_year_start NULLS LAST,aw.title,aw.id OFFSET 0
 ) candidate WHERE candidate.primary_media_id IS NOT NULL AND EXISTS(SELECT 1 FROM media_assets media WHERE media.id=candidate.primary_media_id AND media.storage_path IS NOT NULL)
 ORDER BY candidate.creation_year_start NULLS LAST,candidate.title,candidate.id LIMIT 1),
 (SELECT aw.id FROM museum_memberships member JOIN artworks aw ON aw.id=member.artwork_id
 WHERE member.institution_id=i.id ORDER BY aw.creation_year_start NULLS LAST,aw.title,aw.id LIMIT 1)))))`

// The bounded card CTE retains only the columns needed by counts and cover
// selection. Reuse that narrow relation, then enrich just the chosen cover UUID.
var museumDirectoryCardJSON = strings.ReplaceAll(museumJSON,
	"museum_memberships member JOIN artworks aw", "museum_memberships member JOIN visible_works aw")

// An overview needs the same counts and cover as a directory card. Reuse its
// narrow, materialized visibility set so each count does not revisit full
// artwork rows and cover selection enriches only the chosen artwork.
const museumOverviewPage = `WITH museum_page AS MATERIALIZED (
 SELECT id FROM institutions WHERE slug=$1)
 SELECT detail.data FROM museum_page page CROSS JOIN LATERAL (`

var museumOverviewSQL = museumOverviewPage + museumDirectoryCardCTE + ` SELECT ` + museumDirectoryCardJSON + ` AS data
 FROM institutions i WHERE i.id=page.id AND ` + museumVisible + `
 AND EXISTS(SELECT 1 FROM museum_memberships member WHERE member.institution_id=i.id)) detail`

func (r *Repository) Museums(ctx context.Context, f MuseumFilter) (MuseumPage, error) {
	out := MuseumPage{Items: []Museum{}, Facets: emptyMuseumFacets()}
	c, err := decodeMuseumCursor(f, "")
	if err != nil {
		return out, err
	}
	args := []any{f.Query, f.Regions, f.Countries, f.Selection, f.Display, filterChoices(f.Artists, f.Artist), filterChoices(f.Movements, f.Movement), filterChoices(f.WorkTypes, f.WorkType)}
	cte, memberships := museumDirectoryFilterCTE(f)
	membershipOffset := " OFFSET 0"
	if memberships == "directory_filtered_memberships" {
		// This relation is already bounded by the selected artwork IDs. Let the
		// planner hash it once instead of rescanning it for each institution.
		membershipOffset = ""
	}
	// A museum becomes browsable when it has a visible catalogue work, including
	// anonymous or incomplete review records. Keep this in SQL so totals,
	// keyset pages and filters all exclude empty collections consistently.
	where := ` FROM institutions i WHERE ` + museumVisible + `
 AND i.canonical_institution_id IS NULL
 AND ($1='' OR i.name ILIKE '%'||$1||'%' OR EXISTS(SELECT 1 FROM places p JOIN countries co ON co.code=p.country_code WHERE p.id=i.place_id AND (p.name ILIKE '%'||$1||'%' OR co.name ILIKE '%'||$1||'%')) OR EXISTS(SELECT 1 FROM institution_venues v JOIN places p ON p.id=v.place_id JOIN countries co ON co.code=p.country_code
 WHERE v.institution_id=i.id AND v.status<>'archived'  AND (p.name ILIKE '%'||$1||'%' OR co.name ILIKE '%'||$1||'%')))
 AND ((coalesce(cardinality($2::text[]),0)=0 AND coalesce(cardinality($3::text[]),0)=0) OR EXISTS(SELECT 1 FROM places p JOIN countries co ON co.code=p.country_code WHERE p.id=i.place_id
 AND (coalesce(cardinality($2::text[]),0)=0 OR co.region_code=ANY($2)) AND (coalesce(cardinality($3::text[]),0)=0 OR p.country_code::text=ANY($3))) OR EXISTS(
 SELECT 1 FROM institution_venues v JOIN places p ON p.id=v.place_id JOIN countries co ON co.code=p.country_code
 WHERE v.institution_id=i.id AND v.status<>'archived'
 AND (coalesce(cardinality($2::text[]),0)=0 OR co.region_code=ANY($2)) AND (coalesce(cardinality($3::text[]),0)=0 OR p.country_code::text=ANY($3))))
 AND EXISTS(SELECT 1 FROM ` + memberships + ` member WHERE member.institution_id=i.id
 AND ($4='' OR EXISTS(SELECT 1 FROM selections s WHERE s.institution_id=i.id AND s.artwork_id=member.artwork_id AND s.curator_kind=$4))
 AND ($5='' OR member.on_view)
 AND (cardinality($6::text[])=0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=member.artwork_id AND a.slug=ANY($6) AND a.status<>'archived' ))
 AND (cardinality($7::text[])=0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id JOIN artist_movements am ON am.artist_id=a.id JOIN movements m ON m.id=am.movement_id WHERE aa.artwork_id=member.artwork_id AND m.slug=ANY($7) AND a.status<>'archived' AND m.status<>'archived' ))
 AND (cardinality($8::text[])=0 OR EXISTS(SELECT 1 FROM artworks aw WHERE aw.id=member.artwork_id AND aw.work_type=ANY($8)))` + membershipOffset + `)`
	if err = r.db.QueryRow(ctx, cte+`SELECT count(*)`+where, museumQueryArgs(args...)...).Scan(&out.Total); err != nil {
		return out, err
	}
	args = append(args, c.Name, c.ID, f.Limit+1)
	// Resolve a bounded institution page first. Its cards use institution-scoped
	// candidates inside one SQL request; never scan the whole artwork table for
	// each returned museum's counts and cover. The nested CTE retains exactly the
	// same active-record, incoming-loan, rights and display-evidence policy as details.
	rows, err := r.db.Query(ctx, cte+`, museum_page AS MATERIALIZED (
 SELECT i.id,i.slug,i.normalized_name`+where+`
 AND ($9='' OR (i.normalized_name,i.id::text)>($9,$10)) ORDER BY i.normalized_name,i.id LIMIT $11)
 SELECT detail.data,page.normalized_name FROM museum_page page CROSS JOIN LATERAL (
 `+museumDirectoryCardCTE+` SELECT `+museumDirectoryCardJSON+` AS data FROM institutions i WHERE i.id=page.id
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
		out.NextCursor = encodeMuseumCursor(f, "", 0, names[f.Limit-1], last.ID)
	}
	out.Facets, err = r.museumFacets(ctx, "")
	return out, err
}
func (r *Repository) Museum(ctx context.Context, slug string) (Museum, error) {
	resolved, err := r.canonicalMuseumSlug(ctx, slug)
	if err != nil {
		return Museum{}, err
	}
	slug = resolved
	var out Museum
	var data []byte
	err = r.db.QueryRow(ctx, museumOverviewSQL, museumQueryArgs(slug)...).Scan(&data)
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
func (r *Repository) museumFacets(ctx context.Context, slug string) (MuseumFacets, error) {
	out := emptyMuseumFacets()
	cte := museumDirectoryCTE
	if slug != "" {
		cte = museumScopedCTE
	}
	membership := `EXISTS(SELECT 1 FROM museum_memberships member WHERE member.institution_id=i.id OFFSET 0)`
	if slug != "" {
		membership = `EXISTS(SELECT 1 FROM works w WHERE ` + museumMembership + `)`
	}
	query := cte + `SELECT DISTINCT c.region_code,initcap(replace(c.region_code,'-',' ')),trim(c.code),c.name
 FROM institutions i JOIN LATERAL (SELECT i.place_id AS place_id UNION SELECT v.place_id FROM institution_venues v
 WHERE v.institution_id=i.id AND v.status<>'archived' ) location ON true
 JOIN places p ON p.id=location.place_id JOIN countries c ON c.code=p.country_code
 WHERE ` + museumVisible + ` AND i.canonical_institution_id IS NULL AND ($1='' OR i.slug=$1)
 AND ` + membership + ` ORDER BY c.region_code,c.name`
	rows, err := r.db.Query(ctx, query, museumQueryArgs(slug)...)
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
	// compatibility facet on a single museum. The directory has no artist facet.
	choices := museumDirectoryFacetChoicesSQL
	if slug != "" {
		cte = museumScopedFacetCTE
		choices = museumScopedFacetChoicesSQL
	}
	rows, err = r.db.Query(ctx, cte+choices, museumQueryArgs(slug)...)
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

const museumScopedFacetChoicesSQL = `(SELECT DISTINCT 'artist',a.slug,a.display_name FROM institutions i JOIN museum_memberships member ON member.institution_id=i.id
 JOIN artwork_artists aa ON aa.artwork_id=member.artwork_id JOIN artists a ON a.id=aa.artist_id
 WHERE i.slug=$1 AND ` + museumVisible + ` AND a.status<>'archived'  ORDER BY 3 LIMIT 30)
 UNION (SELECT DISTINCT 'movement',m.slug,m.name FROM institutions i JOIN museum_memberships member ON member.institution_id=i.id
 JOIN artwork_artists aa ON aa.artwork_id=member.artwork_id JOIN artists a ON a.id=aa.artist_id JOIN artist_movements am ON am.artist_id=a.id JOIN movements m ON m.id=am.movement_id
 WHERE ($1='' OR i.slug=$1) AND ` + museumVisible + ` AND a.status<>'archived' AND m.status<>'archived'  ORDER BY 3 LIMIT 500) ORDER BY 1,3`

// OFFSET 0 keeps the directory EXISTS predicates correlated: PostgreSQL must
// look for the first indexed match for an institution/movement, not turn the
// existence check into a hash semi-join over all artworks. No rows are skipped.
const museumDirectoryFacetChoicesSQL = `SELECT 'movement',m.slug,m.name FROM movements m
 WHERE m.status<>'archived'  AND EXISTS(
 SELECT 1 FROM artist_movements am JOIN artists a ON a.id=am.artist_id
 JOIN artwork_artists aa ON aa.artist_id=a.id
 WHERE am.movement_id=m.id AND a.status<>'archived'
 AND EXISTS(SELECT 1 FROM museum_memberships member JOIN institutions i ON i.id=member.institution_id
 WHERE member.artwork_id=aa.artwork_id AND ($1='' OR i.slug=$1) AND ` + museumVisible + `
 OFFSET 0) OFFSET 0) ORDER BY 3 LIMIT 500`

func (r *Repository) MuseumWorks(ctx context.Context, slug string, f MuseumFilter) (MuseumWorksPage, error) {
	out := MuseumWorksPage{Items: []MuseumWork{}, Facets: emptyMuseumFacets()}
	resolved, err := r.canonicalMuseumSlug(ctx, slug)
	if err != nil {
		return out, err
	}
	slug = resolved
	// Normalize before binding the cursor: an old chronological cursor must not
	// silently become a cursor into the image-first order.
	if f.Sort == "" {
		f.Sort = "images"
	}
	c, err := decodeMuseumCursor(f, slug)
	if err != nil {
		return out, err
	}
	// Preserve the exact visibility/membership policy without rebuilding the
	// museum's cover and six aggregate counts just to check its existence.
	var exists bool
	err = r.db.QueryRow(ctx, museumScopedCTE+`SELECT EXISTS(SELECT 1 FROM institutions i WHERE i.slug=$1 AND `+museumVisible+` AND EXISTS(SELECT 1 FROM works w WHERE `+museumMembership+`))`, museumQueryArgs(slug)...).Scan(&exists)
	if err != nil {
		return out, err
	}
	if !exists {
		return out, ErrNotFound
	}
	args := []any{slug, f.Query, f.Selection, f.Display, filterChoices(f.Artists, f.Artist), filterChoices(f.Movements, f.Movement), filterChoices(f.Venues, f.Venue), filterChoices(f.WorkTypes, f.WorkType), f.Start, f.End, f.UnknownDate, f.ImageOnly}
	where := ` FROM institutions i JOIN works w ON ` + museumMembership + ` WHERE i.slug=$1 AND ` + museumVisible + `
 AND ($2='' OR w.title ILIKE '%'||$2||'%' OR w.alternate_title ILIKE '%'||$2||'%' OR w.unlinked_creator_label ILIKE '%'||$2||'%'
 OR w.cultural_context ILIKE '%'||$2||'%' OR w.object_form ILIKE '%'||$2||'%'
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(w.artists) a WHERE a->>'name' ILIKE '%'||$2||'%'))
 AND ($3='' OR EXISTS(SELECT 1 FROM selections s WHERE s.institution_id=i.id AND s.artwork_id=w.id AND s.curator_kind=$3))
 AND ($4='' OR (w.display_institution_id=i.id AND w.display_state='on_view'))
 AND (cardinality($5::text[])=0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=w.id AND a.slug=ANY($5) AND a.status<>'archived' ))
 AND (cardinality($6::text[])=0 OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id JOIN artist_movements am ON am.artist_id=a.id JOIN movements m ON m.id=am.movement_id
 WHERE aa.artwork_id=w.id AND m.slug=ANY($6) AND a.status<>'archived' AND m.status<>'archived' ))
 AND (cardinality($7::text[])=0 OR (w.display_venue_id::text=ANY($7) AND w.display_institution_id=i.id AND w.display_state='on_view'))
 AND (cardinality($8::text[])=0 OR w.work_type=ANY($8))
 AND ($9::int IS NULL OR w.creation_year_end>=$9) AND ($10::int IS NULL OR w.creation_year_start<=$10)
 AND (NOT $11 OR w.creation_year_start IS NULL OR w.creation_year_end IS NULL) AND (NOT $12 OR ` + museumAvailableImage + `)`
	if err = r.db.QueryRow(ctx, museumScopedCTE+`SELECT count(*),count(*) FILTER (WHERE `+museumAvailableImage+`)`+where, museumQueryArgs(args...)...).Scan(&out.Total, &out.ImageCount); err != nil {
		return out, err
	}
	args = append(args, f.Sort, c.Number, c.Name, c.ID, f.Cursor == "", f.Limit+1)
	sortNumber := `CASE WHEN $13='images' THEN CASE WHEN ` + museumAvailableImage + ` THEN 0 ELSE 1 END WHEN $13='title' THEN 0 WHEN $13='curated' AND $3<>'' THEN coalesce((SELECT min(position) FROM selections s WHERE s.institution_id=i.id AND s.artwork_id=w.id AND s.curator_kind=$3),2147483647) ELSE coalesce(w.creation_year_start,2147483647) END`
	// Choose the bounded page before enriching cards. Otherwise PostgreSQL can
	// read every museum image row before sorting, even for a 24-work response.
	rows, err := r.db.Query(ctx, museumScopedCTE+`, page AS MATERIALIZED (
 SELECT w.id,`+sortNumber+` AS sort_number,w.normalized_title`+where+`
 AND ($17 OR (`+sortNumber+`,w.normalized_title,w.id::text)>($14,$15,$16))
 ORDER BY 2,w.normalized_title,w.id LIMIT $18)
 SELECT (SELECT `+workCardJSON+` FROM works w CROSS JOIN institutions i WHERE w.id=page.id AND i.slug=$1 OFFSET 0),page.sort_number,page.normalized_title
 FROM page ORDER BY page.sort_number,page.normalized_title,page.id`, museumQueryArgs(args...)...)
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
		out.NextCursor = encodeMuseumCursor(f, slug, last.SortNumber, last.SortName, last.ID)
	}
	out.Facets, err = r.museumFacets(ctx, slug)
	return out, err
}

func (r *Repository) MuseumArtwork(ctx context.Context, slug, id string) (MuseumArtwork, error) {
	var out MuseumArtwork
	resolved, err := r.canonicalMuseumSlug(ctx, slug)
	if err != nil {
		return out, err
	}
	slug = resolved
	var parsedID pgtype.UUID
	if err := parsedID.Scan(id); err != nil || !parsedID.Valid {
		return out, ErrNotFound
	}
	var data []byte
	query := museumArtworkSQL(museumArtworkScopedCTE)
	err = r.db.QueryRow(ctx, query, museumQueryArgs(slug, id)...).Scan(&data)
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

func museumArtworkSQL(cte string) string {
	return cte + `SELECT to_jsonb(w)||jsonb_build_object('selections',` + selectionJSON + `,
 'attribution_role',coalesce(w.artists->0->>'role','unlinked'),'holding',CASE WHEN w.holding_id IS NOT NULL THEN
 jsonb_build_object('id',w.holding_id,'slug',w.holding_slug,'name',w.holding_name) END)
 FROM institutions i JOIN works w ON ` + museumMembership + ` WHERE i.slug=$1 AND w.id=$2::uuid AND ` + museumVisible
}
