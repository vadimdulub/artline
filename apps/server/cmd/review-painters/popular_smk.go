package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// Timestamped exact-object research, not an assertion that every artwork was reviewed.
func popularSMKResearch(root string) (map[string]string, error) {
	b, err := os.ReadFile(filepath.Join(root, "content/imports/popular-smk-20260911/facts.json"))
	if err != nil {
		return nil, err
	}
	if digest(b) != "f4ddb3996d609276c4fab3754988665baf4d445d34cf7b0a99903670dd0da044" {
		return nil, fmt.Errorf("SMK research capture changed")
	}
	var facts []struct {
		ID       string `json:"external_id"`
		Page     string
		HasImage bool   `json:"has_image"`
		Image    string `json:"image_iiif_id"`
	}
	if err = json.Unmarshal(b, &facts); err != nil {
		return nil, err
	}
	if len(facts) != 41 {
		return nil, fmt.Errorf("incomplete SMK research")
	}
	out := map[string]string{}
	for _, f := range facts {
		if f.Page != "https://open.smk.dk/artwork/image/"+f.ID {
			return nil, fmt.Errorf("SMK object URL mismatch")
		}
		status := "SMK exact-object API checked 2026-09-11: public-domain image candidate; local download status is shown separately."
		if !f.HasImage {
			status = "SMK exact-object API checked 2026-09-11: has_image=false; no photograph supplied by this source."
		} else if f.Image == "" {
			status = "SMK exact-object API checked 2026-09-11: image recorded, but no downloadable IIIF URL supplied; image acquisition deferred."
		}
		if f.ID == "KMSsp198" {
			status = "SMK source date notes partly derive from artist years; dating review required. Image not downloaded."
		}
		out[f.Page] = status
	}
	return out, nil
}
