// research-ng collects a bounded factual metadata snapshot, never images or DB rows.
// It uses the National Gallery's documented public API (structured data: CC0).
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

type obj = map[string]any

func object(v any) obj   { m, _ := v.(map[string]any); return m }
func array(v any) []any  { a, _ := v.([]any); return a }
func str(v any) string   { s, _ := v.(string); return s }
func title(v any) string { return str(object(object(v)["summary"])["title"]) }
func value(a any, kind string) string {
	for _, v := range array(a) {
		m := object(v)
		if str(m["type"]) == kind {
			return str(m["value"])
		}
	}
	return ""
}
func digest(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func save(path string, b []byte) error {
	if old, e := os.ReadFile(path); e == nil {
		if digest(old) == digest(b) {
			return nil
		}
		return fmt.Errorf("refusing changed snapshot %s", path)
	}
	if e := os.MkdirAll(filepath.Dir(path), 0755); e != nil {
		return e
	}
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	defer f.Close()
	_, e = f.Write(b)
	return e
}
func main() {
	dir := flag.String("out", "../../docs/research/european-deep-expansion/ng", "New metadata snapshot directory")
	louvre := flag.Bool("louvre", false, "Collect the separately reviewed 11 Louvre object records instead")
	catalogue := flag.Bool("catalogue-v3", false, "Next bounded catalogue supplement: reuse v2 responses, exclude prior accessions, at most 16 new paintings per artist")
	flag.Parse()
	if *catalogue && (*louvre || *dir == "../../docs/research/european-deep-expansion/ng") {
		log.Fatal("catalogue-v3 requires its own -out directory and cannot be combined with -louvre")
	}
	if *louvre {
		collectLouvre(*dir)
		return
	}
	// Fixed reviewed cohort, <=100 metadata candidates and <=4 selected records
	// per artist. No pagination, concurrent crawling, retries or downloads.
	painters := [][2]string{{"Claude Monet", "Q296"}, {"Camille Pissarro", "Q134741"}, {"Titian", "Q47551"}, {"Raphael", "Q5597"}, {"Caravaggio", "Q42207"}, {"Diego Velázquez", "Q297"}, {"Francisco de Goya", "Q5432"}, {"Johannes Vermeer", "Q41264"}, {"Rembrandt", "Q5598"}, {"Peter Paul Rubens", "Q5599"}, {"Vincent van Gogh", "Q5582"}, {"Paul Cézanne", "Q35548"}, {"Edgar Degas", "Q46373"}, {"Pierre-Auguste Renoir", "Q39931"}, {"Sandro Botticelli", "Q5669"}, {"Jan van Eyck", "Q102272"}, {"Nicolas Poussin", "Q41554"}, {"J.M.W. Turner", "Q159758"}}
	limit := 4
	prior := map[string]bool{}
	if *catalogue {
		limit = 16
		for i := range painters {
			switch painters[i][1] {
			case "Q35548":
				painters[i][0] = "Paul Cezanne"
			case "Q159758":
				painters[i][0] = "Joseph Mallord William Turner"
			}
		}
		for _, path := range []string{"../../docs/research/european-paintings/inventory.json", "../../docs/research/european-deep-expansion/inventory.json"} {
			data, err := os.ReadFile(path)
			if err != nil {
				log.Fatal(err)
			}
			var manifest struct{ Works []obj }
			if err = json.Unmarshal(data, &manifest); err != nil {
				log.Fatal(err)
			}
			for _, w := range manifest.Works {
				if str(w["institution"]) == "ng" && str(w["accession"]) != "" {
					prior[str(w["accession"])] = true
				}
			}
		}
	}
	client := http.Client{Timeout: 25 * time.Second, CheckRedirect: func(r *http.Request, via []*http.Request) error { return fmt.Errorf("unexpected API redirect") }}
	works := []obj{}
	decisions := []obj{}
	used := map[string]bool{}
	for _, p := range painters {
		makerName := p[0]
		if *catalogue {
			makerName = catalogueMaker(p[1], p[0])
		}
		query := url.Values{"q": {`creation.maker.summary.title:"` + p[0] + `" AND @datatype.base:object`}, "size": {"100"}, "_source": {"summary,identifier,creation,material,measurements,classification,category,legal,@admin"}}
		u := "https://data.ng.ac.uk/es/public/_search?" + query.Encode()
		cache := filepath.Join(*dir, "responses", p[1]+".json")
		b, e := os.ReadFile(cache)
		if *catalogue && os.IsNotExist(e) && p[1] != "Q35548" && p[1] != "Q159758" {
			// Same queries and access date: preserve/reuse evidence rather than recrawl.
			b, e = os.ReadFile(filepath.Join("../../docs/research/european-deep-expansion/ng/responses", p[1]+".json"))
			if e == nil {
				e = save(cache, b)
			}
		}
		if os.IsNotExist(e) {
			time.Sleep(500 * time.Millisecond)
			req, _ := http.NewRequest("GET", u, nil)
			req.Header.Set("User-Agent", "ArtlineMuseumResearch/1.0 (bounded metadata-only personal catalogue)")
			res, err := client.Do(req)
			if err != nil {
				decisions = append(decisions, obj{"painter": p[1], "error": err.Error()})
				continue
			}
			b, e = io.ReadAll(io.LimitReader(res.Body, 5*1024*1024+1))
			res.Body.Close()
			if e != nil || res.StatusCode != 200 || len(b) > 5*1024*1024 {
				decisions = append(decisions, obj{"painter": p[1], "error": fmt.Sprint("HTTP ", res.StatusCode, " or invalid response")})
				continue
			}
			if !json.Valid(b) {
				log.Fatal("Non-JSON API response")
			}
			if e = save(cache, b); e != nil {
				log.Fatal(e)
			}
		} else if e != nil {
			log.Fatal(e)
		}
		var payload obj
		if e = json.Unmarshal(b, &payload); e != nil {
			log.Fatal(e)
		}
		hits := array(object(payload["hits"])["hits"])
		sort.Slice(hits, func(i, j int) bool { return str(object(hits[i])["_id"]) < str(object(hits[j])["_id"]) })
		selected := 0
		for _, hit := range hits {
			s := object(object(hit)["_source"])
			pid := str(object(hit)["_id"])
			reject := func(reason string) {
				decisions = append(decisions, obj{"painter": p[1], "pid": pid, "title": title(s), "reason": reason})
			}
			if prior[value(s["identifier"], "object number")] {
				reject("already in an approved earlier inventory")
				continue
			}
			if used[pid] {
				reject("duplicate search hit")
				continue
			}
			if value(s["category"], "department") != "Main Collection" || value(s["classification"], "classification") != "Picture" || str(object(s["legal"])["status"]) != "Accessioned object" {
				reject("not an accessioned main-collection picture")
				continue
			}
			credit := str(object(s["legal"])["credit"])
			if strings.Contains(strings.ToLower(credit), "hugh lane") || strings.Contains(strings.ToLower(credit), "joint") {
				reject("joint custody requires separate review")
				continue
			}
			creation := array(s["creation"])
			if len(creation) != 1 {
				reject("multiple/missing creation events")
				continue
			}
			c := object(creation[0])
			makers := array(c["maker"])
			if len(makers) != 1 || title(makers[0]) != makerName || value(c["attribution"], "attribution") != makerName {
				reject("qualified or non-exact maker attribution")
				continue
			}
			link := object(object(makers[0])["@link"])
			if link["historical"] != false || str(object(link["role"])["value"]) != "Artist" {
				reject("not a current direct artist role")
				continue
			}
			dates := array(c["date"])
			if len(dates) != 1 {
				reject("multiple/missing dates")
				continue
			}
			d := object(dates[0])
			a, ae := strconv.Atoi(str(d["from"]))
			z, ze := strconv.Atoi(str(d["to"]))
			display := str(d["value"])
			if ae != nil || ze != nil || a < 1100 || z < a || z > 1970 || display == "" {
				reject("unknown, unsupported or out-of-scope date")
				continue
			}
			lower := strings.ToLower(display)
			uncertain := false
			for _, word := range []string{"before", "after", "possibly", "probably", "?", " or ", "century"} {
				if strings.Contains(lower, word) {
					uncertain = true
				}
			}
			if uncertain {
				reject("date wording needs manual review")
				continue
			}
			precision := "exact"
			if a != z {
				precision = "range"
			}
			if strings.Contains(lower, "about") || strings.Contains(lower, "circa") {
				if a != z {
					precision = "circa_range"
				} else {
					precision = "circa"
				}
			}
			medium := value(s["material"], "")
			if medium == "" {
				medium = value(s["material"], "detailed")
			}
			ml := strings.ToLower(medium)
			if !(strings.Contains(ml, "oil") || strings.Contains(ml, "tempera") || strings.Contains(ml, "fresco")) || strings.Contains(ml, "print") {
				reject("medium requires manual painting review")
				continue
			}
			if selected >= limit {
				reject("bounded selection cap, eligible but deferred")
				continue
			}
			dimensions := overallDimensions(s["measurements"])
			places := []string{}
			for _, v := range array(c["place"]) {
				m := object(v)
				for _, r := range array(object(m["@link"])["role"]) {
					if str(object(r)["value"]) == "place of production" {
						places = append(places, title(m))
					}
				}
			}
			acc := value(s["identifier"], "object number")
			if acc == "" {
				reject("missing accession")
				continue
			}
			works = append(works, obj{"painter": p[1], "artist_name": p[0], "title": title(s), "institution": "ng", "accession": acc, "source_pid": pid, "url": "https://www.nationalgallery.org.uk/data/" + pid, "api_url": u, "date_display": display, "creation_date": obj{"first": a, "last": z, "precision": precision}, "medium": medium, "dimensions": dimensions, "creation_place_text": strings.Join(places, "; "), "collection": credit, "source_publisher": "National Gallery, London", "source_updated_on": "", "access": "Documented official JSON API; source response retained by artist QID and SHA-256.", "evidence_sha256": digest(b), "notes": "API limits: selected accessioned main-collection paintings with a single current direct artist attribution. Source processed timestamp is not treated as a curatorial update. No display assertion or image imported."})
			used[pid] = true
			selected++
		}
		fmt.Fprintf(os.Stderr, "%s: %d selected from %d bounded candidates\n", p[0], selected, len(hits))
	}
	for name, data := range map[string]any{"works.json": works, "decisions.json": decisions} {
		b, e := json.MarshalIndent(data, "", "  ")
		if e != nil {
			log.Fatal(e)
		}
		b = append(b, '\n')
		if e = save(filepath.Join(*dir, name), b); e != nil {
			log.Fatal(e)
		}
	}
	fmt.Printf("%d selected paintings; %d recorded deferrals/exclusions. No database or image writes.\n", len(works), len(decisions))
}

// Exact source-authority aliases, not fuzzy matching: the broader search phrase
// for Caravaggio also returns the unrelated Polidoro da Caravaggio.
func catalogueMaker(qid, original string) string {
	switch qid {
	case "Q42207":
		return "Michelangelo Merisi da Caravaggio"
	case "Q46373":
		return "Hilaire-Germain-Edgar Degas"
	default:
		return original
	}
}

func overallDimensions(measurements any) string {
	for _, v := range array(measurements) {
		m := object(v)
		if str(m["type"]) == "Overall" && strings.TrimSpace(str(m["display"])) != "" {
			return str(m["display"])
		}
	}
	return ""
}
