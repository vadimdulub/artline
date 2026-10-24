package catalog

import (
	"fmt"
	"strings"
)

// Each ordered branch stops at limit+1 before the merge. In particular, an
// image-first page must not sort or hydrate all 400,000 collection objects.
func museumGalleryPage(sort, where, sortNumber string, unsupportedMedia, imageOnly bool) string {
	if sort != "highlights" && sort != "images" {
		return `, page AS MATERIALIZED (
 SELECT w.id,` + sortNumber + ` AS sort_number,w.normalized_title` + where + `
 AND ($18 OR (` + sortNumber + `,w.normalized_title,w.id::text)>($15,$16,$17))
 ORDER BY 2,w.normalized_title,w.id LIMIT $19)`
	}
	priority := `w.id IN(SELECT id FROM gallery_priority)`
	branches := []string{}
	add := func(rank int, source, condition string) {
		branches = append(branches, fmt.Sprintf(`(SELECT w.id,%d AS sort_number,w.normalized_title%s
 AND $14::text IS NOT NULL AND (%s) AND ($18 OR (%d,w.normalized_title,w.id::text)>($15,$16,$17))
 ORDER BY w.normalized_title,w.id LIMIT $19)`, rank, source, condition, rank))
	}
	prefix := ""
	imageRank, missingRank := 0, 1
	if sort == "highlights" {
		prefix = `, gallery_priority AS MATERIALIZED (
 SELECT unnest($13::uuid[]) AS id UNION
 SELECT artwork_id FROM selections WHERE institution_id=(SELECT id FROM institutions WHERE slug=$1))`
		bounded := strings.Replace(where,
			` FROM institutions i JOIN works w ON `+museumMembership+` WHERE`,
			` FROM gallery_priority selected CROSS JOIN LATERAL (SELECT * FROM works w WHERE w.id=selected.id OFFSET 0) w CROSS JOIN institutions i WHERE `+museumMembership+` AND`, 1)
		add(0, bounded, "true")
		imageRank, missingRank = 1, 2
	}
	other := "true"
	if sort == "highlights" {
		other = "NOT (" + priority + ")"
	}
	seek := func(rank int) string {
		return fmt.Sprintf(`$14::text IS NOT NULL AND ($18 OR (%d,aw.normalized_title,aw.id)>($15,$16,nullif($17,'')::uuid))`, rank)
	}
	image := `EXISTS(SELECT 1 FROM media_assets image WHERE image.id=w.primary_media_id AND image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$')`
	branches = append(branches, museumOrderedCandidates(where, imageRank, image+" AND "+other, "aw.primary_media_id IS NOT NULL", seek(imageRank), "$19")...)
	// A picture-only page cannot contain either missing-image branch.
	// Avoid scanning those holdings merely to reject every candidate.
	if !imageOnly {
		// Null and unsupported media paths share one position in the public order.
		// Separate local prefixes preserve exact ordering without scanning all nulls.
		branches = append(branches, museumOrderedCandidates(where, missingRank, other, "aw.primary_media_id IS NULL", seek(missingRank), "$19")...)
		if unsupportedMedia {
			native := `aw.primary_media_id IN(SELECT image.id FROM media_assets image WHERE image.storage_path IS NULL OR image.storage_path !~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$')`
			branches = append(branches, museumOrderedCandidates(where, missingRank, other, native, seek(missingRank), "$19")...)
		}
	}
	return prefix + `, gallery_page_candidates AS MATERIALIZED (` + strings.Join(branches, " UNION ALL ") + `), page AS MATERIALIZED (
 SELECT * FROM gallery_page_candidates ORDER BY sort_number,normalized_title,id LIMIT $19)`
}

// Keep the ordered artwork scan outside the evidence/card lookup. OFFSET 0
// prevents a hash join over the full collection from discarding index order.
// Holdings and incoming loans get independent bounded prefixes before merging.
func museumOrderedCandidates(where string, rank int, condition, nativeCondition, seek, limit string) []string {
	predicates := strings.TrimPrefix(where, ` FROM institutions i JOIN works w ON `+museumMembership+` WHERE`)
	membership := []string{
		`aw.current_institution_id=i.id`,
		`aw.current_institution_id IS DISTINCT FROM i.id AND aw.id IN(SELECT la.artwork_id FROM artwork_location_assertions la WHERE la.institution_id=i.id AND la.claim_type='display' AND la.review_state='accepted' AND la.superseded_by IS NULL)`,
	}
	branches := make([]string, 0, len(membership))
	for _, member := range membership {
		branches = append(branches, fmt.Sprintf(`(SELECT candidate.* FROM institutions i CROSS JOIN LATERAL (
 SELECT aw.id,%d AS sort_number,aw.normalized_title FROM artworks aw
 CROSS JOIN LATERAL (SELECT * FROM works w WHERE w.id=aw.id OFFSET 0) w
 WHERE aw.status<>'archived' AND (%s) AND (%s) AND (%s) AND (%s) AND (%s) AND `+museumMembership+`
 ORDER BY aw.normalized_title,aw.id LIMIT %s) candidate WHERE i.slug=$1)`, rank, member, nativeCondition, predicates, condition, seek, limit))
	}
	return branches
}
