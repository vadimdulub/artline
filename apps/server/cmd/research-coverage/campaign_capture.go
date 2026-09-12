package main

import (
	"context"
	"fmt"
	"net/url"
	"path/filepath"
)

// Official, version-pinned metadata exports only. Chicago's server date is
// retained in its snapshot: documentation freshness does not imply fresh data.
const metExport = "https://media.githubusercontent.com/media/metmuseum/openaccess/6fa206f0df6cf349d4fe558028d4c08e95f44eb6/MetObjects.csv"
const clevelandExport = "https://media.githubusercontent.com/media/ClevelandMuseumArt/openaccess/0abfbf9c4217696d3abd600b8623118e6cd5598b/data.json"
const chicagoExport = "https://artic-api-data.s3.amazonaws.com/artic-api-data.tar.bz2"

func campaignURL(u *url.URL) bool {
	if u.Host == "api.smk.dk" && u.Path == "/api/v1/art/" && u.Query().Get("lang") == "en" && len(u.Query()) == 2 {
		for _, id := range append(append([]string{}, smkMatisseObjects...), imageFocusSMKObjects...) {
			if u.Query().Get("object_number") == id {
				return true
			}
		}
	}
	if u.Host == "data.rijksmuseum.nl" {
		if u.Path == "/search/collection" {
			for _, creator := range rijksQueries {
				if u.Query().Get("creator") == creator && u.Query().Get("type") == "painting" && u.Query().Get("imageAvailable") == "true" {
					return true
				}
			}
		}
		return rijksID.MatchString("https://id.rijksmuseum.nl"+u.Path) && u.Query().Get("_profile") == "la-framed"
	}
	if u.Host == "api.smk.dk" && u.Path == "/api/v1/art/search/" {
		return u.Query().Get("filters") == "[object_names:Painting],[public_domain:true]" && u.Query().Get("rows") == "100" && u.Query().Get("lang") == "en"
	}
	if u.String() == metExport || u.String() == clevelandExport || u.String() == chicagoExport {
		return true
	}
	return u.Host == "www.dati.lombardia.it" && (u.Path == "/api/views/ay8b-p38f.json" || u.Path == "/resource/ay8b-p38f.json")
}

func captureCampaign(ctx context.Context, source, out string) error {
	switch source {
	case "met", "cleveland":
		file, raw, expected := "objects.csv", metExport, "de617b9c947458e426111207f81a65bd1379a151c0077d3ce29cfc22fc0b9183"
		if source == "cleveland" {
			file, raw, expected = "objects.json", clevelandExport, "0c15cb6b3b195e69f901af00fbd5205697c4fca50049196d4d232fa8af08fc94"
		}
		path := filepath.Join(out, file)
		if e := fetch(ctx, path, raw, 400<<20); e != nil {
			return e
		}
		sha, _, e := hashFile(path)
		if e != nil || sha != expected {
			return fmt.Errorf("pinned Git LFS object hash mismatch: %v", e)
		}
		return nil
	case "chicago":
		return fetch(ctx, filepath.Join(out, "metadata.tar.bz2"), chicagoExport, 300<<20)
	case "lombardia":
		if e := fetch(ctx, filepath.Join(out, "dataset.json"), "https://www.dati.lombardia.it/api/views/ay8b-p38f.json", 1<<20); e != nil {
			return e
		}
		q := url.Values{"$where": {"ogtd in ('dipinto','disegno','stampa','acquerello')"}, "$order": {"idk"}, "$limit": {"60000"}}
		return fetch(ctx, filepath.Join(out, "objects.json"), "https://www.dati.lombardia.it/resource/ay8b-p38f.json?"+q.Encode(), 150<<20)
	}
	return fmt.Errorf("unknown campaign source")
}
