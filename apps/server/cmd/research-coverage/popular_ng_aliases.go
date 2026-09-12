package main

import (
	"context"
	"path/filepath"
)

// Official artist pages document these exact catalogue spellings. This is a
// separate two-artist follow-up, never a repeat of the unchanged 99 queries.
func ngAliasCohort(all []popularNGArtist) []popularNGArtist {
	out := []popularNGArtist{}
	for _, a := range all {
		switch a.Name {
		case "Claude Lorrain":
			a.Name = "Claude"
		case "Giotto di Bondone":
			a.Name = "Giotto"
		default:
			continue
		}
		out = append(out, a)
	}
	return out
}
func captureNGAliases(ctx context.Context, out string) error {
	all, err := popularNGCohort(ctx)
	if err != nil {
		return err
	}
	if err = save(filepath.Join(out, "authority-evidence.json"), map[string]any{
		"Claude": map[string]string{"local": "Claude Lorrain", "source": "https://www.nationalgallery.org.uk/artists/claude", "basis": "Official artist biography identifies Claude Gellée, Lorraine-born, 1604/5–1682; exact source display name Claude. Distinct from Claude Monet."},
		"Giotto": map[string]string{"local": "Giotto di Bondone", "source": "https://www.nationalgallery.org.uk/artists/giotto", "basis": "Official painter page; both listed works have qualified credits (and Workshop / Neapolitan follower), which must remain qualified."},
	}); err != nil {
		return err
	}
	return captureNGCohort(ctx, out, ngAliasCohort(all))
}
