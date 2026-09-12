// Assemble the third reviewed European supplement offline, with explicit manual
// decisions. Source files, earlier inventories and response caches are immutable.
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

type object = map[string]any

func str(v any) string { s, _ := v.(string); return s }
func obj(v any) object { m, _ := v.(map[string]any); return m }
func list(v any) []any { a, _ := v.([]any); return a }
func read(path string, dst any) []byte {
	b, e := os.ReadFile(path)
	if e != nil {
		log.Fatal(e)
	}
	if e = json.Unmarshal(b, dst); e != nil {
		log.Fatal(e)
	}
	return b
}
func save(path string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		log.Fatal(e)
	}
	b = append(b, '\n')
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		log.Fatal(e)
	}
	defer f.Close()
	if _, e = f.Write(b); e != nil {
		log.Fatal(e)
	}
	fmt.Printf("%s SHA256 %x\n", path, sha256.Sum256(b))
}

func main() {
	dir := "../../docs/research/european-catalogue-expansion"
	var previous object
	read("../../docs/research/european-deep-expansion/inventory.json", &previous)
	ng := object{}
	for _, raw := range list(previous["institutions"]) {
		i := obj(raw)
		if i["id"] == "ng" {
			ng = i
		}
	}
	if ng["id"] != "ng" {
		log.Fatal("missing NG institution")
	}
	ng["data_route"] = "Documented Elasticsearch API; 18 fixed queries, 251 metadata candidates; 16 same-day caches reused and two corrected-name queries. No pagination or image downloads."
	orsay := object{"id": "orsay", "name": "Musée d’Orsay", "city": "Paris", "country": "FR", "data_route": "Exact official object records, including collection assignment, factual technical fields and selected catalogue references; no public bulk API verified", "rights": "Private local factual research only. Website content and photograph publication have separate authorization conditions; no blanket open-data or image grant inferred.", "rights_url": "https://www.musee-orsay.fr/fr/mentions-legales"}
	definitions := object{"ng": obj(previous["definitions"])["ng"], "orsay": object{"Slug": "musee-orsay", "Source": "musee-orsay", "Website": "https://www.musee-orsay.fr", "Host": "www.musee-orsay.fr"}}
	// Publisher/responsible museum is not necessarily the physical holder.
	grenoble := object{"id": "grenoble", "name": "Musée de Grenoble", "city": "Grenoble", "country": "FR", "data_route": "Orsay exact object 422 names Grenoble as conservation institution and records its 1981 deposit; Grenoble official visitor page confirms institutional geography", "data_url": "https://www.musee-orsay.fr/fr/oeuvres/la-maison-de-la-folie-eragny-422", "rights": orsay["rights"], "rights_url": orsay["rights_url"]}
	definitions["grenoble"] = object{"Slug": "musee-de-grenoble", "Source": "musee-orsay", "Website": "https://www.museedegrenoble.fr", "Host": "www.musee-orsay.fr"}
	var ngWorks, orsayWorks []object
	read(filepath.Join(dir, "ng/works.json"), &ngWorks)
	read(filepath.Join(dir, "orsay.json"), &orsayWorks)
	works := []object{}
	decisions := []object{}
	for _, w := range ngWorks {
		if w["accession"] == "NG224" {
			decisions = append(decisions, object{"accession": "NG224", "url": w["url"], "decision": "deferred", "reason": "Literal date allows possible start in the 1540s outside API bounds 1560-1568. Multi-stage dating requires editorial review."})
			continue
		}
		var response object
		data := read(filepath.Join(dir, "ng/responses", str(w["painter"])+".json"), &response)
		if fmt.Sprintf("%x", sha256.Sum256(data)) != w["evidence_sha256"] {
			log.Fatal("changed NG evidence")
		}
		found := false
		for _, raw := range list(obj(response["hits"])["hits"]) {
			hit := obj(raw)
			if hit["_id"] != w["source_pid"] {
				continue
			}
			found = true
			s := obj(hit["_source"])
			creation := list(s["creation"])
			if len(creation) != 1 {
				log.Fatal("creation shape")
			}
			makers := list(obj(creation[0])["maker"])
			if len(makers) != 1 {
				log.Fatal("maker shape")
			}
			maker := obj(makers[0])
			w["source_creator_name"] = obj(maker["summary"])["title"]
			w["source_creator_pid"] = obj(maker["@admin"])["uid"]
			refs := []string{}
			for _, v := range list(s["identifier"]) {
				m := obj(v)
				if m["type"] == "Catalogue Raisonné Ref" {
					refs = append(refs, str(m["value"]))
				}
			}
			if len(refs) > 0 {
				w["catalogue_references"] = refs
			}
			if w["accession"] == "NG6700" {
				for _, v := range list(s["measurements"]) {
					m := obj(v)
					if m["type"] == "Overall" && str(m["display"]) != "" {
						w["dimensions"] = m["display"]
						break
					}
				}
				w["notes"] = str(w["notes"]) + " Selected displayed Overall measurement 96 x 121.2 cm; earlier nondisplayed components give 95.5 x 121 cm. The 2024 acquisition announcement corroborates the displayed measurement; no blending of alternatives."
			}
			if w["accession"] == "NG190" {
				w["notes"] = str(w["notes"]) + " Source literal says late 1650s; numeric 1655-1659 is the museum API range, not an exact creation date."
			}
		}
		if !found {
			log.Fatal("missing raw NG record")
		}
		works = append(works, w)
	}
	for _, w := range orsayWorks {
		w["source_publisher"] = "Musée d’Orsay"
		switch w["source_object_id"] {
		case "1147", "904", "342":
			w["source_updated_on"] = "2026-09-07"
		}
		if w["source_updated_on"] == nil {
			w["source_updated_on"] = ""
		}
		if w["access"] == nil {
			w["access"] = "Direct official object technical fields and collection/provenance record"
		}
		w["notes"] = str(w["notes"]) + " Local factual review record; source collection assignment is not a current-display assertion. No image or narrative essay copied."
		works = append(works, w)
	}
	painters, seen := map[string]string{}, map[string]bool{}
	ledger := []object{}
	for _, w := range works {
		u := str(w["url"])
		if seen[u] || u == "" {
			log.Fatal("duplicate or missing URL")
		}
		seen[u] = true
		qid := str(w["painter"])
		painters[qid] = qid
		confidence := "high for literal museum metadata, not independent authentication"
		if str(w["confidence"]) != "" {
			confidence = str(w["confidence"])
		}
		ledger = append(ledger, object{"claim": "Object identity, named creator, creation date, material, dimensions and museum collection connection", "source_title": w["title"], "publisher": w["source_publisher"], "updated_on": w["source_updated_on"], "accessed_on": "2026-09-09", "url": u, "api_url": w["api_url"], "access_notes": w["access"], "evidence_refs": w["evidence_refs"], "evidence_sha256": w["evidence_sha256"], "confidence": confidence, "qualifiers": w["notes"]})
	}
	sort.Slice(works, func(i, j int) bool { return str(works[i]["url"]) < str(works[j]["url"]) })
	manifest := object{"schema_version": 2, "accessed_on": "2026-09-09", "scope": "Bounded National Gallery and Orsay catalogue supplement, including one Grenoble deposit; creation cutoff 1970; private local factual research, review only, no images or display assertions", "institutions": []object{ng, orsay, grenoble}, "definitions": definitions, "painters": painters, "works": works}
	save(filepath.Join(dir, "manual-decisions.json"), decisions)
	save(filepath.Join(dir, "source-ledger.json"), ledger)
	save(filepath.Join(dir, "inventory.json"), manifest)
	fmt.Printf("%d works, %d existing painter authorities, 3 institutions\n", len(works), len(painters))
}
