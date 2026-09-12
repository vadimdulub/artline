package main

import (
	"context"
	"net/url"
	"path/filepath"
	"time"
)

var poldiCommonsFiles = []string{
	"File:Piero della Francesca - Saint Nicholas of Tolentino - Google Art Project.jpg",
	"File:Giovanni Bellini - Imago Pietatis - Google Art Project.jpg",
}

const athensIconCommonsFile = "File:Double-side icon with Crucifixion and Hodegetria (14th century, Byzantine museum)-.jpg"
const athensIconCommonsThumb = "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/70/Double-side_icon_with_Crucifixion_and_Hodegetria_%2814th_century%2C_Byzantine_museum%29-.jpg/960px-Double-side_icon_with_Crucifixion_and_Hodegetria_%2814th_century%2C_Byzantine_museum%29-.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail"

var athensFollowupFiles = []string{
	"File:Icon with the Archangel Michael (14th cent.) at the Byzantine and Christian Museum on 12 April 2019.jpg",
	"File:Icon of Saint Marina (14th -15th cent) at the Byzantine and Christian Museum of Athens on 12 April 2019.jpg",
}

func captureAthensFollowup(ctx context.Context, out string) error {
	for i, name := range athensFollowupFiles {
		if i > 0 { select { case <-ctx.Done(): return ctx.Err(); case <-time.After(3*time.Second): } }
		if err := fetch(ctx,filepath.Join(out,[]string{"michael.json","marina.json"}[i]),poldiCommonsURL(name),2<<20); err != nil { return err }
	}
	return nil
}

func poldiCommonsURL(file string) string {
	return "https://commons.wikimedia.org/w/api.php?" + url.Values{"action": {"query"}, "format": {"json"}, "titles": {file}, "prop": {"imageinfo|revisions"}, "iiprop": {"url|extmetadata|size|sha1"}, "iiurlwidth": {"700"}, "rvprop": {"ids|timestamp|content"}, "rvslots": {"main"}, "maxlag": {"5"}}.Encode()
}
func poldiCommonsAllowed(raw string) bool {
	for _, f := range athensFollowupFiles { if raw==poldiCommonsURL(f) { return true } }
	if raw == athensIconCommonsThumb {
		return true
	}
	if raw == poldiCommonsURL(athensIconCommonsFile) {
		return true
	}
	for _, f := range poldiCommonsFiles {
		if raw == poldiCommonsURL(f) {
			return true
		}
	}
	return false
}
func capturePoldiCommons(ctx context.Context, out string) error {
	for i, f := range poldiCommonsFiles {
		if i > 0 {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(3 * time.Second):
			}
		}
		name := []string{"piero.json", "bellini.json"}[i]
		if err := fetch(ctx, filepath.Join(out, name), poldiCommonsURL(f), 2<<20); err != nil {
			return err
		}
	}
	return save(filepath.Join(out, "scope.json"), map[string]any{"files": poldiCommonsFiles, "scope": "Two exact independently hosted Commons image records, not a museum permission claim. No image binaries or database writes. Do not propagate stale Commons dates/dimensions over current museum facts."})
}
