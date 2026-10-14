package atlas

import "strings"

// The database view combines clean projection rows with live pending IDs. Keep
// this CTE inline so broad cursor pages can seek into the ordered browse index.
func browseArtworkScope(selection, creators string) string {
	return `artwork_native_scope AS NOT MATERIALIZED (
 SELECT a.* FROM artwork_atlas_browse a
 WHERE a.start_year<=$2 AND a.end_year>=$1 AND $3::text IS NOT NULL
 AND (` + selection + `) AND (` + creators + `)),`
}

// Keep the clean and pending branches separate until after their local filters
// and page limits. PostgreSQL cannot always push a join or ordered LIMIT through
// a UNION containing a set-returning function, even when pending IDs are empty.
func browseBranches(prefix string) (string, string) {
	clean := strings.Replace(prefix, "artwork_atlas_browse a", `(SELECT p.* FROM artwork_atlas_projection p
 WHERE NOT EXISTS(SELECT 1 FROM artwork_atlas_dirty)
 OR NOT EXISTS(SELECT 1 FROM artwork_atlas_dirty d WHERE d.artwork_id=p.id)) a`, 1)
	pending := strings.Replace(prefix, "artwork_atlas_browse a", `artline_atlas_browse_rows(ARRAY(SELECT artwork_id FROM artwork_atlas_dirty)) a`, 1)
	return clean, pending
}

const localArtworkImage = `image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$'`
const artworkImageScope = ` AND EXISTS(SELECT 1 FROM media_assets image WHERE image.id=a.primary_media_id AND ` + localArtworkImage + `)`

// The accepted current holding index is unique on artwork_id. Active source
// and institution joins cannot multiply a work; ownership is not on-view status.
const broadArtworkHoldingsJoin = ` LEFT JOIN (artwork_location_assertions h JOIN sources s ON s.id=h.source_id AND s.is_active
 JOIN institutions i ON i.id=h.institution_id AND i.status<>'archived')
 ON h.artwork_id=a.id AND h.claim_type='holding' AND h.review_state='accepted' AND h.superseded_by IS NULL`

const artworkCreatorVisibility = `(NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id) OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id AND ar.status<>'archived' ))`

// The FK and non-null artist status guarantee that every link is either active
// or archived. Only artworks with an archived link need the second lookup; an
// unlinked work remains eligible, as does a mixed active/archived attribution.
const artworkActiveCreatorVisibility = `(a.id NOT IN (SELECT aa.artwork_id FROM artists ar JOIN artwork_artists aa ON aa.artist_id=ar.id WHERE ar.status='archived') OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id AND ar.status<>'archived'))`

const boundedSelectedArt = `SELECT ci.artwork_id FROM artwork_native_scope bounded JOIN curated_collection_items ci ON ci.artwork_id=bounded.id JOIN curated_collections cc ON cc.id=ci.collection_id
 WHERE cc.status<>'archived'
 AND (cc.curator_kind='owner' OR (ci.source_url IS NOT NULL AND EXISTS(SELECT 1 FROM sources s WHERE s.id=ci.source_id AND s.is_active)))`

// This predicate also defines the partial covering index. Keep it independent
// of publication, collection membership and museum evidence: those remain live
// query-time decisions, and an image path still needs separate validation.
const illustratedNativeEligibility = `a.status<>'archived' AND a.primary_media_id IS NOT NULL
 AND a.date_precision IN ('exact','circa','range','circa_range','decade','century')
 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
 AND coalesce(a.creation_year_start,a.creation_year_end)<>0
 AND coalesce(a.creation_year_end,a.creation_year_start)<>0`

// Bound dates and explicit creator/ID/facet choices before broad geographic
// membership and holding checks. Without a text search, titles are fetched only
// for the returned page, allowing this relation to use the small covering index
// instead of reading every artwork's much larger catalogue row.
func nativeArtworkScope(selection, creators string) string {
	return `artwork_native_scope AS MATERIALIZED (
 SELECT a.id,a.creation_year_start,a.creation_year_end,
 a.primary_media_id,a.work_type,a.cultural_context,NULL::text AS title,NULL::text AS unlinked_creator_label
 FROM artworks a WHERE ` + illustratedNativeEligibility + `

 AND coalesce(a.creation_year_start,a.creation_year_end)<=$2
 AND coalesce(a.creation_year_end,a.creation_year_start)>=$1
 AND (` + selection + `) AND (` + creators + `)),`
}

// Shared and preset geography reuse one candidate relation. Resolve each
// distinct artist's countries once, even when thousands of works share them.
const artworkGeographyScope = `artwork_scoped_artists AS MATERIALIZED (
 SELECT aa.artwork_id,aa.artist_id FROM artwork_native_scope bounded JOIN artwork_artists aa ON aa.artwork_id=bounded.id
), artwork_artist_geography AS MATERIALIZED (
 SELECT ac.artist_id,c.code,c.name,c.region_code FROM (SELECT DISTINCT artist_id FROM artwork_scoped_artists) chosen
 JOIN artists ar ON ar.id=chosen.artist_id AND ar.status<>'archived'
 JOIN artist_countries ac ON ac.artist_id=ar.id JOIN countries c ON c.code=ac.country_code
), artwork_geography AS MATERIALIZED (
 SELECT aa.artwork_id,g.code,g.name,g.region_code FROM artwork_scoped_artists aa JOIN artwork_artist_geography g ON g.artist_id=aa.artist_id
 UNION ALL SELECT ap.artwork_id,c.code,c.name,c.region_code FROM artwork_native_scope bounded
 JOIN artwork_places ap ON ap.artwork_id=bounded.id JOIN places pl ON pl.id=ap.place_id JOIN countries c ON c.code=pl.country_code
),`

func scopedArtworkGeographyMatch(condition string) string {
	return `(a.id IN (SELECT c.artwork_id FROM artwork_geography c WHERE (` + condition + `))) IS TRUE`
}
