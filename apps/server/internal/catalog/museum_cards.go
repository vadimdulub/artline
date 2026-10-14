package catalog

import "strings"

// Keep holdings and current loans disjoint. Counts need only indexed IDs;
// highlights start at the museum's selection, and cover lookup stops at the
// first ordered image. Do not group or sort every holding to render one card.
// The shared CTE retains the exact source, conflict and display-expiry policy.
var museumDirectoryCardCTE = museumCTE + `, card_holdings AS NOT MATERIALIZED (
 SELECT aw.id,aw.title,aw.creation_year_start,aw.primary_media_id,aw.current_institution_id
 FROM visible_works aw WHERE aw.current_institution_id=page.id
), card_display AS MATERIALIZED (
 SELECT DISTINCT aw.id,aw.title,aw.creation_year_start,aw.primary_media_id,aw.current_institution_id
 FROM current_display d JOIN visible_works aw ON aw.id=d.artwork_id
 WHERE d.institution_id=page.id AND d.state='on_view'
), card_works AS NOT MATERIALIZED (
 SELECT * FROM card_holdings
 UNION ALL
 SELECT * FROM card_display WHERE current_institution_id IS DISTINCT FROM page.id
), card_counts AS MATERIALIZED (
 SELECT (SELECT count(*) FROM card_holdings) AS holdings,
 (SELECT count(*) FROM card_display) AS on_view,
 (SELECT count(*) FROM card_display WHERE current_institution_id IS DISTINCT FROM page.id) AS incoming
) `

// Metadata and cover enrichment use the same JSON contract as other museum
// reads. Only the count and cover-ID selection strategy changes.
var museumDirectoryCardJSON = strings.Split(museumJSON, "'work_count',")[0] + `
 'work_count',(SELECT holdings+incoming FROM card_counts),
 'holding_count',(SELECT holdings FROM card_counts),
 'on_view_count',(SELECT on_view FROM card_counts),
 'highlight_count',(SELECT count(DISTINCT s.artwork_id) FROM selections s
 WHERE s.institution_id=i.id AND EXISTS(
 SELECT 1 FROM card_works aw WHERE aw.id=s.artwork_id OFFSET 0)),
 'cover',(SELECT ` + workCardJSON + ` FROM works w WHERE w.id=(
 SELECT coalesce(
 (SELECT candidate.id FROM (
 (SELECT aw.id,aw.creation_year_start,aw.title FROM card_holdings aw WHERE aw.primary_media_id IS NOT NULL
 AND EXISTS(SELECT 1 FROM media_assets media WHERE media.id=aw.primary_media_id AND media.storage_path IS NOT NULL)
 ORDER BY aw.creation_year_start NULLS LAST,aw.title,aw.id LIMIT 1)
 UNION ALL
 (SELECT aw.id,aw.creation_year_start,aw.title FROM card_display aw
 WHERE aw.current_institution_id IS DISTINCT FROM page.id AND aw.primary_media_id IS NOT NULL
 AND EXISTS(SELECT 1 FROM media_assets media WHERE media.id=aw.primary_media_id AND media.storage_path IS NOT NULL)
 ORDER BY aw.creation_year_start NULLS LAST,aw.title,aw.id LIMIT 1)
 ) candidate ORDER BY candidate.creation_year_start NULLS LAST,candidate.title,candidate.id LIMIT 1),
 (SELECT candidate.id FROM (
 (SELECT aw.id,aw.creation_year_start,aw.title FROM card_holdings aw
 ORDER BY aw.creation_year_start NULLS LAST,aw.title,aw.id LIMIT 1)
 UNION ALL
 (SELECT aw.id,aw.creation_year_start,aw.title FROM card_display aw
 WHERE aw.current_institution_id IS DISTINCT FROM page.id
 ORDER BY aw.creation_year_start NULLS LAST,aw.title,aw.id LIMIT 1)
 ) candidate ORDER BY candidate.creation_year_start NULLS LAST,candidate.title,candidate.id LIMIT 1)))))`
