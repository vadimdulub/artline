// Offline, deterministic assembly of independently reviewed source evidence.
// The resulting checksum must be reviewed/pinned before the DB importer accepts it.
package main

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sort"
)

func main() {
	dir := "../../docs/research/european-deep-expansion"
	read := func(name string) []map[string]any {
		b, e := os.ReadFile(filepath.Join(dir, name))
		if e != nil {
			log.Fatal(e)
		}
		var rows []map[string]any
		if e = json.Unmarshal(b, &rows); e != nil {
			log.Fatal(e)
		}
		return rows
	}
	inst := read("institutions.json")
	byID := map[string]map[string]any{}
	defs := map[string]any{}
	for _, i := range inst {
		id := i["id"].(string)
		byID[id] = i
		defs[id] = i["definition"]
		delete(i, "definition")
	}
	works := []map[string]any{}
	painters := map[string]string{}
	seen := map[string]bool{}
	for _, file := range []string{"ng/works.json", "louvre/works-reviewed.json", "iberia-italy.json", "northern.json", "ireland-courtauld.json"} {
		for _, w := range read(file) {
			i := byID[w["institution"].(string)]
			if i == nil {
				log.Fatal("missing institution")
			}
			u := w["url"].(string)
			if seen[u] {
				log.Fatal("duplicate URL ", u)
			}
			seen[u] = true
			if years, ok := w["years"].([]any); ok {
				if len(years) != 3 {
					log.Fatal("date shape")
				}
				w["creation_date"] = map[string]any{"first": years[0], "last": years[1], "precision": years[2]}
				delete(w, "years")
			}
			if w["source_publisher"] == nil {
				w["source_publisher"] = i["name"]
			}
			if w["source_updated_on"] == nil {
				w["source_updated_on"] = ""
			}
			if w["access"] == nil {
				w["access"] = "Official object evidence, accessed 2026-09-09"
				if file == "iberia-italy.json" {
					w["access"] = "Official indexed technical object record; direct access varies by institution"
				}
			}
			if w["institution"] == "vgm" {
				w["owner"] = "Vincent van Gogh Foundation"
				w["custody"] = "Permanent loan to Van Gogh Museum"
				w["collection"] = "Van Gogh Museum, Amsterdam (Vincent van Gogh Foundation)"
				w["access"] = "Direct official HTML technical fields and provenance"
				w["notes"] = fmt.Sprint(w["notes"]) + " Foundation transfer 10 July 1962; permanent museum loan from 2 June 1973, renamed Van Gogh Museum 1994."
			}
			if w["institution"] == "smk" {
				w["api_url"] = "https://api.smk.dk/api/v1/art/?object_number=" + w["accession"].(string) + "&lang=en"
				w["image_rights"] = "public_domain=true in core museum API; no image downloaded"
				w["access"] = "Direct official core JSON API, excluding AI enrichment"
			}
			if w["institution"] == "zurich" {
				w["access"] = "Direct official page-embedded structured metadata; PDF corroboration where accessible"
			}
			if w["institution"] == "ngi" {
				w["museum_highlight_url"] = "https://www.nationalgallery.ie/art-and-artists/highlights-collection"
				w["access"] = "Direct official highlights object technical table"
			}
			// Our year-level 'before' type is exclusive. Before February 1506 may
			// include January 1506, so do not encode it as strictly before 1506.
			if w["date_display"] == "Before February 1506" {
				w["creation_date"] = map[string]any{"first": nil, "last": nil, "precision": "unknown"}
				w["notes"] = fmt.Sprint(w["notes"]) + " Year-level exclusive-before semantics cannot faithfully encode this month bound; creation years left unknown pending editorial review."
			}
			qid := w["painter"].(string)
			painters[qid] = qid
			works = append(works, w)
		}
	}
	sort.Slice(works, func(a, b int) bool { return works[a]["url"].(string) < works[b]["url"].(string) })
	m := map[string]any{"schema_version": 2, "accessed_on": "2026-09-09", "scope": "Selected European museum paintings, creation cutoff 1970; source-backed review catalogue, not exhaustive holdings or current-display census. No image downloads.", "institutions": inst, "definitions": defs, "painters": painters, "works": works}
	b, e := json.MarshalIndent(m, "", "  ")
	if e != nil {
		log.Fatal(e)
	}
	b = append(b, '\n')
	target := filepath.Join(dir, "inventory.json")
	f, e := os.OpenFile(target, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		log.Fatal(e)
	}
	defer f.Close()
	if _, e = f.Write(b); e != nil {
		log.Fatal(e)
	}
	fmt.Printf("%d works, %d museums, %d painters; SHA256 %x\n", len(works), len(inst), len(painters), sha256.Sum256(b))
}
