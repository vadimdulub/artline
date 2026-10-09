package atlas

import (
	"net/url"
	"strings"
)

// False checkbox defaults do not narrow a broad illustrated view.
func onlyIllustratedDefaults(values url.Values) bool {
	for key, items := range values {
		if key == "image_only" {
			continue
		}
		if (key == "popular" || key == "women") && len(items) == 1 && items[0] == "false" {
			continue
		}
		return false
	}
	return true
}

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
func nativeArtworkScope(f Filter, selection, creators string) string {
	// Entity text searches resolve IDs first; only the shared All search
	// still needs titles here. Keep the native scan on its covering index.
	titles := "NULL::text AS title,NULL::text AS unlinked_creator_label"
	if strings.TrimSpace(f.Query) != "" {
		titles = "a.title,a.unlinked_creator_label"
	}
	return `artwork_native_scope AS MATERIALIZED (
 SELECT a.id,a.status,a.date_precision,a.creation_year_start,a.creation_year_end,
 a.primary_media_id,a.work_type,a.cultural_context,` + titles + `
 FROM artworks a WHERE ` + illustratedNativeEligibility + `

 AND coalesce(a.creation_year_start,a.creation_year_end)<=$2
 AND coalesce(a.creation_year_end,a.creation_year_start)>=$1
 AND (` + selection + `) AND (` + creators + `)),`
}

// Geography needs only the already scoped IDs. In particular, a short date
// window must not rebuild country sets for the entire catalogue. These exact
// fragments belong to artworkGeographyMatch; the native seed itself does not
// use this rewrite, so it never depends on its own CTE.
func boundedArtworkGeography(query string) string {
	query = strings.ReplaceAll(query, "FROM artwork_artists aa\n JOIN artists ar", "FROM artwork_native_scope bounded JOIN artwork_artists aa ON aa.artwork_id=bounded.id\n JOIN artists ar")
	return strings.ReplaceAll(query, "UNION SELECT ap.artwork_id FROM artwork_places ap JOIN places pl", "UNION SELECT ap.artwork_id FROM artwork_native_scope bounded JOIN artwork_places ap ON ap.artwork_id=bounded.id JOIN places pl")
}
