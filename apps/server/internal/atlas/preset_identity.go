package atlas

import (
	"context"
	"fmt"
	"maps"
	"slices"
)

// Earlier independent imports assigned different UUIDs to a few of the same
// catalogue objects. Resolve only the explicit, reviewed slug identities for
// this preset, using the artwork slug index before timeline enrichment.
func (r *Repository) resolveArtworkIdentities(ctx context.Context, focus *PresetFocus) (*PresetFocus, error) {
	slugs := make([]string, 0, len(focus.ArtworkIdentities))
	for _, slug := range focus.ArtworkIdentities {
		slugs = append(slugs, slug)
	}
	rows, err := r.db.Query(ctx, `SELECT slug,id::text FROM artworks WHERE slug=ANY($1::text[])`, slugs)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	identities := map[string]string{}
	for rows.Next() {
		var slug, id string
		if err := rows.Scan(&slug, &id); err != nil {
			return nil, err
		}
		identities[slug] = id
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return resolvedArtworkFocus(focus, identities)
}

func resolvedArtworkFocus(focus *PresetFocus, identities map[string]string) (*PresetFocus, error) {
	replacements := map[string]string{}
	for original, slug := range focus.ArtworkIdentities {
		id, ok := identities[slug]
		if !ok {
			return nil, fmt.Errorf("preset artwork identity unavailable: %s", slug)
		}
		replacements[original] = id
	}
	out := *focus
	out.Related, out.Context = maps.Clone(focus.Related), maps.Clone(focus.Context)
	for _, group := range []map[string][]string{out.Related, out.Context} {
		if group == nil {
			continue
		}
		group["artwork"] = slices.Clone(group["artwork"])
		for i, id := range group["artwork"] {
			if replacement, ok := replacements[id]; ok {
				group["artwork"][i] = replacement
			}
		}
	}
	return &out, nil
}
