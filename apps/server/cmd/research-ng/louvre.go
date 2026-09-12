package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Ten individually linked paintings on the official masterpiece album's first
// page, plus Vermeer's separately researched Lacemaker. Not the whole album,
// collection, or all objects with these titles. No images or live display claims.
func collectLouvre(dir string) {
	ids := []string{"cl010062370", "cl010066115", "cl010059199", "cl010064382", "cl010065566", "cl010062292", "cl010065426", "cl010065872", "cl010065609", "cl010066276", "cl010064918"}
	client := http.Client{Timeout: 25 * time.Second, CheckRedirect: func(r *http.Request, via []*http.Request) error { return fmt.Errorf("unexpected API redirect") }}
	works := []obj{}
	decisions := []obj{}
	for _, id := range ids {
		u := "https://collections.louvre.fr/ark:/53355/" + id
		path := filepath.Join(dir, "responses", id+".json")
		b, e := os.ReadFile(path)
		if os.IsNotExist(e) {
			time.Sleep(500 * time.Millisecond)
			res, err := client.Get(u + ".json")
			if err != nil {
				decisions = append(decisions, obj{"id": id, "error": err.Error()})
				continue
			}
			b, e = io.ReadAll(io.LimitReader(res.Body, 2*1024*1024+1))
			res.Body.Close()
			if e != nil || res.StatusCode != 200 || len(b) > 2*1024*1024 {
				decisions = append(decisions, obj{"id": id, "error": fmt.Sprint("HTTP ", res.StatusCode)})
				continue
			}
			if !json.Valid(b) {
				log.Fatal("invalid JSON")
			}
			if e = save(path, b); e != nil {
				log.Fatal(e)
			}
		} else if e != nil {
			log.Fatal(e)
		}
		var s obj
		if e = json.Unmarshal(b, &s); e != nil {
			log.Fatal(e)
		}
		reject := func(reason string) {
			decisions = append(decisions, obj{"id": id, "title": s["title"], "reason": reason})
		}
		if str(s["collection"]) != "Département des Peintures" || str(s["longTermLoanTo"]) != "" || !strings.Contains(str(s["heldBy"]), "Musée du Louvre") || s["isMuseesNationauxRecuperation"] == true {
			reject("department, deposit, holder or restitution needs separate review")
			continue
		}
		qid, name := "", ""
		valid := true
		for _, v := range array(s["creator"]) {
			c := object(v)
			if str(c["attributionLevel"]) != "Attribution actuelle" {
				continue
			}
			if str(c["linkType"]) == "École de" {
				continue
			}
			if qid != "" || str(c["wikidata"]) == "" || str(c["doubt"]) != "" || str(c["authenticationType"]) != "" || str(c["linkType"]) != "" {
				valid = false
			}
			qid = str(c["wikidata"])
			name = str(c["label"])
		}
		if !valid || qid == "" {
			reject("qualified or unresolved current creator")
			continue
		}
		dates := array(s["dateCreated"])
		if len(dates) != 1 {
			reject("multiple or missing dates")
			continue
		}
		d := object(dates[0])
		a, aok := d["startYear"].(float64)
		z, zok := d["endYear"].(float64)
		// The documented single-year form omits endYear (empty string), not an
		// open-ended interval. Qualifiers are checked independently below.
		if aok && d["endYear"] == "" {
			z, zok = a, true
		}
		if !aok || !zok || a < 1100 || z < a || z > 1970 || str(d["doubt"]) != "" {
			reject("unresolved or out-of-scope date")
			continue
		}
		precision := "exact"
		if a != z {
			precision = "range"
		}
		imprecision := str(d["imprecision"])
		if imprecision == "vers" {
			if a != z {
				precision = "circa_range"
			} else {
				precision = "circa"
			}
		} else if imprecision != "" {
			reject("unsupported date qualifier")
			continue
		}
		// The source's century envelope is not silently narrowed from memory.
		if z-a >= 99 {
			precision = "century"
		}
		dimensions := []string{}
		for _, v := range array(s["dimension"]) {
			m := object(v)
			kind := str(m["type"])
			if kind == "Hauteur" || kind == "Largeur" || kind == "Diamètre" {
				dimensions = append(dimensions, kind+": "+str(m["displayDimension"]))
			}
		}
		aliases := []string{}
		for _, v := range array(s["denominationTitle"]) {
			m := object(v)
			if str(m["value"]) != str(s["title"]) {
				aliases = append(aliases, str(m["value"]))
			}
		}
		acc := value(s["objectNumber"], "Numéro principal")
		if acc == "" {
			reject("missing primary accession")
			continue
		}
		w := obj{"painter": qid, "artist_name": name, "title": s["title"], "aliases": aliases, "institution": "louvre", "accession": acc, "source_object_id": id, "url": u, "api_url": u + ".json", "date_display": s["displayDateCreated"], "creation_date": obj{"first": int(a), "last": int(z), "precision": precision}, "medium": s["materialsAndTechniques"], "dimensions": strings.Join(dimensions, "; "), "creation_place_text": s["placeOfCreation"], "owner": s["ownedBy"], "collection": s["heldBy"], "source_publisher": "Musée du Louvre", "source_updated_on": s["modified "], "access": "Direct official JSON object record; full source snapshot retained.", "evidence_sha256": digest(b), "notes": "Source dates retained, including broad catalogue intervals. Dimensions exclude frame/accessory measurements. No live display assertion or image imported."}
		if id != "cl010064918" {
			w["museum_highlight_url"] = "https://collections.louvre.fr/album/2"
		}
		works = append(works, w)
		fmt.Fprintf(os.Stderr, "%s | %s | %s\n", qid, acc, str(s["title"]))
	}
	for name, v := range map[string]any{"works-reviewed.json": works, "decisions-reviewed.json": decisions} {
		b, e := json.MarshalIndent(v, "", "  ")
		if e != nil {
			log.Fatal(e)
		}
		if e = save(filepath.Join(dir, name), append(b, '\n')); e != nil {
			log.Fatal(e)
		}
	}
	fmt.Printf("%d selected Louvre paintings, %d deferred. No images or database writes.\n", len(works), len(decisions))
}
