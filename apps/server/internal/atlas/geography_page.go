package atlas

// Ordered pages need geography only for the candidate IDs reached by the browse
// index, not a materialized geographic join for the whole period. OFFSET 0 keeps
// these EXISTS lookups correlated: without that fence PostgreSQL can replace
// them with hashed sets of hundreds of thousands of unrelated artwork IDs before
// returning the first page. The small matching-artist set can still be reused.
// Keep artist associations and recorded production places as independent evidence;
// a museum holding is not geographic origin, and archived creators do not qualify.
func pageArtworkGeographyMatch(condition string) string {
	return `(EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id
 AND aa.artist_id IN (SELECT ac.artist_id FROM artist_countries ac
 JOIN artists ar ON ar.id=ac.artist_id AND ar.status<>'archived'
 JOIN countries c ON c.code=ac.country_code WHERE (` + condition + `)) OFFSET 0)
 OR EXISTS(SELECT 1 FROM artwork_places ap JOIN places pl ON pl.id=ap.place_id
 JOIN countries c ON c.code=pl.country_code WHERE ap.artwork_id=a.id AND (` + condition + `) OFFSET 0))`
}
