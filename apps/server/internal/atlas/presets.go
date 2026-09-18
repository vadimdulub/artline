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
	ID          string   `json:"id"`
	Name        string   `json:"name"`
	Group       string   `json:"group"`
	Description string   `json:"description"`
	Period      Range    `json:"period"`
	Context     Range    `json:"context"`
	Sources     []Source `json:"sources"`
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
