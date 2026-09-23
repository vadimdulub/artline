package atlas

import "context"

// This enrichment only receives an already validated, bounded page of eligible IDs.
func (r *Repository) attachImages(ctx context.Context, items []Item) error {
	if len(items) == 0 {
		return nil
	}
	ids := make([]string, len(items))
	index := map[string]int{}
	for i, item := range items {
		ids[i] = item.ID
		index[item.ID] = i
	}
	rows, err := r.db.Query(ctx, `SELECT a.id::text,m.storage_path,coalesce(m.alt_text,''),m.rights_status
 FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id
 WHERE a.id=ANY($1::uuid[]) AND m.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$'`, ids)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var id, path, alt, rights string
		if err := rows.Scan(&id, &path, &alt, &rights); err != nil {
			return err
		}
		i := index[id]
		items[i].MediaURL = path
		items[i].AltText = alt
		items[i].RightsStatus = rights
	}
	return rows.Err()
}

func (r *Repository) IllustratedPresets(ctx context.Context, preview bool) ([]Preset, error) {
	presets := Presets()
	if r.db == nil {
		return presets, nil
	}
	ids := []string{}
	for _, p := range presets {
		if p.CoverArtworkID != "" {
			ids = append(ids, p.CoverArtworkID)
		}
	}
	// Scope the small explicit ID set before eligibility and creator enrichment.
	rows, err := r.db.Query(ctx, `SELECT a.id::text,a.title,coalesce(a.date_display,''),coalesce(a.creation_year_start,a.creation_year_end),coalesce(a.creation_year_end,a.creation_year_start),a.date_precision<>'exact'`+artScope+` AND a.id=ANY($7::uuid[])`, Bounds.Start, Bounds.End, preview, "", false, "", ids)
	if err != nil {
		return nil, err
	}
	items := []Item{}
	for rows.Next() {
		item := Item{Type: "artwork"}
		if err := rows.Scan(&item.ID, &item.Title, &item.Years, &item.StartYear, &item.EndYear, &item.Approximate); err != nil {
			rows.Close()
			return nil, err
		}
		items = append(items, item)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	if err := r.attachImages(ctx, items); err != nil {
		return nil, err
	}
	for i := range presets {
		for j := range items {
			if presets[i].CoverArtworkID == items[j].ID && items[j].MediaURL != "" {
				presets[i].Cover = &items[j]
			}
		}
	}
	return presets, nil
}
