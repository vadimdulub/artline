package atlas

import (
	_ "embed"
	"encoding/json"
)

type Source struct {
	Name string `json:"name"`
	URL  string `json:"url"`
}
type Preset struct {
	StartingScope     string       `json:"startingScope"`
	StartingCountries []string     `json:"startingCountries,omitempty"`
	CoverArtworkID    string       `json:"coverArtworkID,omitempty"`
	Cover             *Item        `json:"cover,omitempty"`
	ID                string       `json:"id"`
	Name              string       `json:"name"`
	Group             string       `json:"group"`
	Description       string       `json:"description"`
	Period            Range        `json:"period"`
	Context           Range        `json:"context"`
	Sources           []Source     `json:"sources"`
	Focus             *PresetFocus `json:"focus,omitempty"`
}

// Explicit subject/context links supplement recorded origin. They do not
// change creation dates, geographic provenance, publication or image rules.
type PresetFocus struct {
	Label             string              `json:"label"`
	Countries         []string            `json:"countries"`
	Regions           []string            `json:"regions,omitempty"`
	Global            bool                `json:"global,omitempty"`
	ArtworkTraditions []string            `json:"artworkTraditions,omitempty"`
	SelectedEvents    bool                `json:"selectedEvents,omitempty"`
	Related           map[string][]string `json:"related,omitempty"`
	Context           map[string][]string `json:"context,omitempty"`
}

//go:embed presets.json
var presetsJSON []byte

func Presets() []Preset {
	var out []Preset
	if err := json.Unmarshal(presetsJSON, &out); err != nil {
		panic(err)
	}
	return out
}
func FindPreset(id string) (Preset, bool) {
	for _, p := range Presets() {
		if p.ID == id {
			return p, true
		}
	}
	return Preset{}, false
}
