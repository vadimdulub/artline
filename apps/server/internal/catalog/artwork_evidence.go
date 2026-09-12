package catalog

import (
	"context"
	"encoding/json"
)

// Constant query count: location and citations are batched for the selected page.
func (r *Repository) enrichArtworks(ctx context.Context, works []Artwork, preview bool) error {
	if len(works) == 0 {
		return nil
	}
	ids := make([]string, len(works))
	byID := map[string]int{}
	for i := range works {
		ids[i] = works[i].ID
		byID[ids[i]] = i
		works[i].Citations = []Citation{}
	}
	// Restrict by returned UUIDs before joining evidence. A shared global works
	// CTE can materialize millions of rows just to enrich one 24-work page.
	rows, err := r.db.Query(ctx, artworkEvidenceQuery, preview, ids)
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
	rows, err = r.db.Query(ctx, `SELECT entity_id::text,field_name,name,source_url,evidence_note FROM (
 SELECT c.entity_id,c.field_name,s.name,c.source_url,coalesce(c.evidence_note,'') AS evidence_note,
 row_number() OVER(PARTITION BY c.entity_id ORDER BY c.field_name,s.priority,c.id) AS n
 FROM citations c JOIN sources s ON s.id=c.source_id AND s.is_active
 WHERE c.entity_type='artwork' AND c.entity_id=ANY($1::uuid[])) evidence WHERE n<=100 ORDER BY entity_id,n`, ids)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var id string
		var c Citation
		if err = rows.Scan(&id, &c.FieldName, &c.SourceName, &c.SourceURL, &c.EvidenceNote); err != nil {
			return err
		}
		idx := byID[id]
		works[idx].Citations = append(works[idx].Citations, c)
	}
	return rows.Err()
}

const artworkEvidenceQuery = `SELECT aw.id::text,jsonb_build_object(
 'holding',CASE WHEN i.id IS NOT NULL THEN jsonb_build_object('id',i.id,'slug',i.slug,'name',i.name) END,
 'display',d.evidence)
 FROM artworks aw
 LEFT JOIN institutions i ON i.id=aw.current_institution_id AND i.status<>'archived' AND ($1 OR i.status='published')
 LEFT JOIN LATERAL (
 SELECT jsonb_build_object('id',di.id,'slug',di.slug,'name',di.name,'venue_id',v.id,'venue_name',coalesce(v.name,di.name),
 'state',CASE WHEN la.checked_at<now()-interval '30 days' OR la.effective_to<now() THEN 'stale' ELSE la.display_state END,
 'context',la.context,'gallery',la.gallery,'checked_at',la.checked_at,'source_url',la.source_url) AS evidence
 FROM artwork_location_assertions la JOIN institutions di ON di.id=la.institution_id
 LEFT JOIN institution_venues v ON v.id=la.venue_id JOIN sources s ON s.id=la.source_id AND s.is_active
 WHERE la.artwork_id=aw.id AND la.claim_type='display' AND la.review_state='accepted' AND la.superseded_by IS NULL
 AND la.checked_at<=now() AND (la.effective_from IS NULL OR la.effective_from<=now())
 AND di.status<>'archived' AND ($1 OR di.status='published')
 AND (v.id IS NULL OR (v.status<>'archived' AND ($1 OR v.status='published')))
 AND NOT EXISTS(SELECT 1 FROM artwork_location_assertions conflict WHERE conflict.artwork_id=aw.id
 AND conflict.claim_type='display' AND conflict.review_state='conflict' AND conflict.superseded_by IS NULL)
 ) d ON true
 WHERE aw.id=ANY($2::uuid[]) AND aw.status<>'archived' AND ($1 OR aw.status='published')`
