package catalog

import "context"

func (r *Repository) artistInfluences(ctx context.Context, id string) ([]Influence, error) {
	result := []Influence{}
	rows, err := r.db.Query(ctx, `SELECT i.id::text,
 CASE WHEN i.target_artist_id=$1 THEN coalesce(s.display_name,i.source_label) ELSE t.display_name END,
 CASE WHEN i.target_artist_id=$1 THEN s.slug ELSE t.slug END,
 CASE WHEN i.target_artist_id=$1 THEN 'incoming' ELSE 'outgoing' END,
 i.relationship_type,i.evidence_level,i.evidence_note
 FROM influence_claims i LEFT JOIN artists s ON s.id=i.source_artist_id
 JOIN artists t ON t.id=i.target_artist_id
 WHERE (i.source_artist_id=$1 OR i.target_artist_id=$1) AND i.status='published'
 AND t.status='published' AND (s.id IS NULL OR s.status='published')
 AND EXISTS(SELECT 1 FROM citations c JOIN sources src ON src.id=c.source_id WHERE c.entity_type='influence' AND c.entity_id=i.id AND src.is_active)
 ORDER BY i.created_at LIMIT 40`, id)
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		var item Influence
		if err := rows.Scan(&item.ID, &item.Name, &item.Slug, &item.Direction, &item.RelationshipType, &item.EvidenceLevel, &item.EvidenceNote); err != nil {
			rows.Close()
			return nil, err
		}
		result = append(result, item)
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		return nil, err
	}
	for i := range result {
		result[i].Citations, err = r.entityCitations(ctx, "influence", result[i].ID)
		if err != nil {
			return nil, err
		}
	}
	return result, nil
}
