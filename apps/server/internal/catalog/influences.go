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
 WHERE (i.source_artist_id=$1 OR i.target_artist_id=$1) AND i.status<>'archived'
 AND t.status<>'archived' AND (s.id IS NULL OR s.status<>'archived')
 AND EXISTS(SELECT 1 FROM citations c JOIN sources src ON src.id=c.source_id WHERE c.entity_type='influence' AND c.entity_id=i.id AND src.is_active)
 ORDER BY CASE WHEN i.target_artist_id=$1 THEN 0 ELSE 1 END, i.created_at, i.id LIMIT 40`, id)
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
	if len(result) == 0 {
		return result, nil
	}
	ids := make([]string, len(result))
	positions := make(map[string]int, len(result))
	for i := range result {
		ids[i] = result[i].ID
		positions[result[i].ID] = i
		result[i].Citations = []Citation{}
	}
	// Scope every citation lookup to the at-most-40 returned claims in one query.
	rows, err = r.db.Query(ctx, `SELECT selected.id::text,e.field_name,e.name,e.source_url,e.evidence_note
 FROM unnest($1::uuid[]) WITH ORDINALITY selected(id,n)
 CROSS JOIN LATERAL (
  SELECT c.field_name,s.name,c.source_url,s.priority,
  CASE WHEN $2 THEN '' ELSE coalesce(c.evidence_note,'') END AS evidence_note
  FROM citations c JOIN sources s ON s.id=c.source_id AND s.is_active
  WHERE c.entity_type='influence' AND c.entity_id=selected.id
  ORDER BY c.field_name,s.priority LIMIT 100
 ) e ORDER BY selected.n,e.field_name,e.priority`, ids, publicRead(ctx))
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	for rows.Next() {
		var id string
		var c Citation
		if err = rows.Scan(&id, &c.FieldName, &c.SourceName, &c.SourceURL, &c.EvidenceNote); err != nil {
			return nil, err
		}
		i := positions[id]
		result[i].Citations = append(result[i].Citations, c)
	}
	return result, rows.Err()
}
