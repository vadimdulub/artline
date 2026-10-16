// Exhibition-preview serves source-backed local research without a database.
// It is deliberately a separate loopback-only command, never a production mode.
package main

import (
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/exhibitions"
)

type record map[string]any
type archive struct {
	records  []record
	byID     map[string]record
	artworks map[string]record
	upstream string
	client   *http.Client
}

func str(r record, k string) string { s, _ := r[k].(string); return s }
func number(r record, k string) int { n, _ := r[k].(float64); return int(n) }
func objects(r record, k string) []record {
	out := []record{}
	for _, v := range array(r, k) {
		if m, ok := v.(map[string]any); ok {
			out = append(out, m)
		}
	}
	return out
}
func array(r record, k string) []any { a, _ := r[k].([]any); return a }
func clone(r record) record {
	out := record{}
	for k, v := range r {
		out[k] = v
	}
	return out
}
func compact(r record) record {
	out := clone(r)
	delete(out, "entries")
	delete(out, "publications")
	delete(out, "sources")
	people := objects(r, "participants")
	if len(people) > 3 {
		people = people[:3]
	}
	out["participants"] = people
	return out
}
func respond(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Robots-Tag", "noindex")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(data)
}
func fail(w http.ResponseWriter, status int) {
	respond(w, status, record{"error": "Invalid exhibition request or unavailable source."})
}

func (a *archive) proxy(w http.ResponseWriter, r *http.Request) {
	req, err := http.NewRequestWithContext(r.Context(), http.MethodGet, a.upstream+r.URL.RequestURI(), nil)
	if err != nil {
		fail(w, 503)
		return
	}
	response, err := a.client.Do(req)
	if err != nil {
		fail(w, 503)
		return
	}
	defer response.Body.Close()
	var payload record
	if err = json.NewDecoder(io.LimitReader(response.Body, 8<<20)).Decode(&payload); err != nil {
		fail(w, 503)
		return
	}
	if response.StatusCode == 200 && r.URL.Path == "/api/v1/exhibitions" {
		items := objects(payload, "items")
		for i, item := range items {
			if local := a.byID[str(item, "id")]; local != nil {
				items[i] = compact(local)
			}
		}
		payload["items"] = items
		payload["localStudyCount"] = len(a.records)
	}
	respond(w, response.StatusCode, payload)
}

func (a *archive) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		fail(w, 405)
		return
	}
	if r.URL.Path == "/healthz" {
		respond(w, 200, record{"localOnly": true, "records": len(a.records), "artworks": len(a.artworks)})
		return
	}
	prefix := "/api/v1/exhibitions"
	if r.URL.Path != prefix && !strings.HasPrefix(r.URL.Path, prefix+"/") {
		fail(w, 404)
		return
	}
	q := r.URL.Query()
	localFilter := q.Get("theme") != "" || q.Get("person") != ""
	limit := 40
	if raw := q.Get("limit"); raw != "" {
		var err error
		limit, err = strconv.Atoi(raw)
		if err != nil || limit < 1 || limit > 100 {
			fail(w, 400)
			return
		}
	}
	if strings.HasPrefix(r.URL.Path, prefix+"/artworks/") {
		parts := strings.Split(strings.TrimPrefix(r.URL.Path, prefix+"/artworks/"), "/")
		if len(parts) > 2 || !exhibitions.ValidID(parts[0]) || (len(parts) == 2 && parts[1] != "exhibitions") {
			fail(w, 404)
			return
		}
		artwork := a.artworks[parts[0]]
		if artwork == nil {
			fail(w, 404)
			return
		}
		if len(parts) == 1 {
			out := clone(artwork)
			delete(out, "appearances")
			respond(w, 200, out)
			return
		}
		after := q.Get("after")
		if after != "" && !exhibitions.ValidID(after) {
			fail(w, 400)
			return
		}
		all := objects(artwork, "appearances")
		items := []record{}
		for _, item := range all {
			if str(item, "id") > after && len(items) <= limit {
				items = append(items, item)
			}
		}
		more, next := len(items) > limit, ""
		if more {
			items = items[:limit]
			next = str(items[len(items)-1], "id")
		}
		respond(w, 200, record{"items": items, "total": len(all), "hasMore": more, "nextCursor": next})
		return
	}
	if r.URL.Path == prefix {
		if !localFilter && (q.Get("collection") == "archive" || (q.Get("source") != "" && q.Get("source") != "artsy") || q.Get("institution") != "" || q.Get("artwork") != "") {
			a.proxy(w, r)
			return
		}
		f := exhibitions.Filter{Query: q.Get("q"), Source: q.Get("source"), Artist: q.Get("artist"), Institution: q.Get("institution"), Artwork: q.Get("artwork"), Format: q.Get("format"), State: q.Get("state"), After: q.Get("after"), Limit: limit}
		for key, ptr := range map[string]**int{"start": &f.Start, "end": &f.End} {
			if q.Get(key) != "" {
				n, err := strconv.Atoi(q.Get(key))
				if err != nil {
					fail(w, 400)
					return
				}
				*ptr = &n
			}
		}
		if f.Validate() != nil || len(q.Get("theme")) > 80 || (q.Get("person") != "" && !exhibitions.ValidID(q.Get("person"))) {
			fail(w, 400)
			return
		}
		cursor, _ := exhibitions.DecodeCursor(f.After)
		items := []record{}
		total := 0
		for _, row := range a.records {
			if f.Institution != "" {
				match := false
				for _, venue := range objects(row, "venues") {
					if str(venue, "institution_id") == f.Institution {
						match = true
					}
				}
				if !match {
					continue
				}
			}
			if f.Artwork != "" {
				match := false
				for _, entry := range objects(row, "entries") {
					if str(entry, "artworkId") == f.Artwork {
						match = true
					}
				}
				if !match {
					continue
				}
			}
			if f.Query != "" && !strings.Contains(strings.ToLower(str(row, "title")), strings.ToLower(strings.TrimSpace(f.Query))) {
				continue
			}
			if f.Format != "" && f.Format != str(row, "format") || f.State != "" && f.State != str(row, "state") {
				continue
			}
			if f.Source != "" {
				match := false
				for _, s := range objects(row, "sources") {
					if str(s, "provider") == f.Source {
						match = true
					}
				}
				if !match {
					continue
				}
			}
			if f.Start != nil && number(row, "endYear") < *f.Start || f.End != nil && number(row, "startYear") > *f.End {
				continue
			}
			if f.Artist != "" || q.Get("person") != "" {
				match := false
				for _, p := range objects(row, "participants") {
					if f.Artist != "" && str(p, "artist_id") == f.Artist || q.Get("person") != "" && str(p, "id") == q.Get("person") {
						match = true
					}
				}
				if !match {
					continue
				}
			}
			if q.Get("theme") != "" {
				match := false
				research, _ := row["research"].(map[string]any)
				for _, tag := range array(research, "concepts") {
					if tag == q.Get("theme") {
						match = true
					}
				}
				if !match {
					continue
				}
			}
			total++
			if f.After != "" && (number(row, "startYear") > cursor.Year || number(row, "startYear") == cursor.Year && str(row, "id") >= cursor.ID) {
				continue
			}
			if len(items) <= limit {
				items = append(items, compact(row))
			}
		}
		more := len(items) > limit
		next := ""
		if more {
			items = items[:limit]
			last := items[len(items)-1]
			b, _ := json.Marshal(exhibitions.Cursor{Year: number(last, "startYear"), ID: str(last, "id")})
			next = base64.RawURLEncoding.EncodeToString(b)
		}
		featured := []record{}
		for _, row := range a.records {
			if row["featured"] == true {
				featured = append(featured, compact(row))
			}
		}
		respond(w, 200, record{"items": items, "total": total, "heldTotal": total, "hasMore": more, "nextCursor": next, "localStudyCount": len(a.records), "featured": featured})
		return
	}
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, prefix+"/"), "/")
	if len(parts) > 2 || !exhibitions.ValidID(parts[0]) {
		fail(w, 404)
		return
	}
	row := a.byID[parts[0]]
	if row == nil {
		a.proxy(w, r)
		return
	}
	if len(parts) == 2 {
		if parts[1] != "entries" {
			fail(w, 404)
			return
		}
		after := q.Get("after")
		if after != "" && !exhibitions.ValidID(after) {
			fail(w, 400)
			return
		}
		all := objects(row, "entries")
		participation := q.Get("participation")
		if participation != "" && participation != "exhibited" {
			fail(w, 400)
			return
		}
		if participation != "" {
			filtered := []record{}
			for _, entry := range all {
				if str(entry, "participation") == participation {
					filtered = append(filtered, entry)
				}
			}
			all = filtered
		}
		sort.Slice(all, func(i, j int) bool { return str(all[i], "id") < str(all[j], "id") })
		items := []record{}
		for _, e := range all {
			if str(e, "id") > after && len(items) <= limit {
				items = append(items, e)
			}
		}
		more := len(items) > limit
		next := ""
		if more {
			items = items[:limit]
			next = str(items[len(items)-1], "id")
		}
		respond(w, 200, record{"items": items, "total": len(all), "hasMore": more, "nextCursor": next})
		return
	}
	out := clone(row)
	delete(out, "entries")
	// Related records use exact source artist identity, not guessed influences.
	people := map[string]bool{}
	for _, p := range objects(row, "participants") {
		people[str(p, "id")] = true
		if str(p, "artist_id") != "" {
			people["artist:"+str(p, "artist_id")] = true
		}
	}
	related := []record{}
	for _, other := range a.records {
		if str(other, "id") == str(row, "id") {
			continue
		}
		match := false
		for _, p := range objects(other, "participants") {
			if people[str(p, "id")] || str(p, "artist_id") != "" && people["artist:"+str(p, "artist_id")] {
				match = true
			}
		}
		if match {
			related = append(related, record{"id": other["id"], "title": other["title"], "startYear": other["startYear"]})
		}
		if len(related) == 6 {
			break
		}
	}
	out["related"] = related
	out["localStudy"] = true
	respond(w, 200, out)
}

func main() {
	file := flag.String("corpus", "", "Source-backed local corpus JSON")
	upstream := flag.String("upstream", "http://127.0.0.1:8097", "Read-only loopback catalogue API")
	listen := flag.String("listen", "127.0.0.1:8098", "Loopback listen address")
	flag.Parse()
	host, _, err := net.SplitHostPort(*listen)
	if err != nil || net.ParseIP(host) == nil || !net.ParseIP(host).IsLoopback() {
		log.Fatal("loopback listen address required")
	}
	u, err := url.Parse(*upstream)
	if err != nil || u.Scheme != "http" || net.ParseIP(u.Hostname()) == nil || !net.ParseIP(u.Hostname()).IsLoopback() || u.User != nil || u.Path != "" || u.RawQuery != "" {
		log.Fatal("loopback upstream required")
	}
	raw, err := os.ReadFile(*file)
	if err != nil {
		log.Fatal(err)
	}
	var corpus struct {
		Version  int      `json:"version"`
		Records  []record `json:"records"`
		Artworks []record `json:"artworks"`
	}
	if err = json.Unmarshal(raw, &corpus); err != nil || corpus.Version != 1 {
		log.Fatal("invalid review corpus")
	}
	a := &archive{records: corpus.Records, byID: map[string]record{}, artworks: map[string]record{}, upstream: *upstream, client: &http.Client{Timeout: 10 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}}
	for _, artwork := range corpus.Artworks {
		id := str(artwork, "id")
		if !exhibitions.ValidID(id) || a.artworks[id] != nil || len(objects(artwork, "appearances")) != number(artwork, "appearanceCount") || len(objects(artwork, "artists")) > 100 {
			log.Fatal("invalid artwork identity, appearance count or artist bound")
		}
		appearances := objects(artwork, "appearances")
		sort.Slice(appearances, func(i, j int) bool { return str(appearances[i], "id") < str(appearances[j], "id") })
		// Keep the JSON-array representation used by objects/array.
		ordered := make([]any, len(appearances))
		for i, appearance := range appearances {
			ordered[i] = map[string]any(appearance)
		}
		artwork["appearances"] = ordered
		a.artworks[id] = artwork
	}
	for _, r := range a.records {
		id := str(r, "id")
		if !exhibitions.ValidID(id) || a.byID[id] != nil || len(objects(r, "entries")) != number(r, "entryCount") {
			log.Fatal("invalid exhibition identity or entry count")
		}
		a.byID[id] = r
		for _, entry := range objects(r, "entries") {
			if artworkID := str(entry, "localArtworkId"); artworkID != "" && a.artworks[artworkID] == nil {
				log.Fatal("exhibition references a missing local artwork")
			}
		}
	}
	for id, artwork := range a.artworks {
		seen := map[string]bool{}
		for _, appearance := range objects(artwork, "appearances") {
			entryID := str(appearance, "id")
			exhibition := a.byID[str(appearance, "exhibitionId")]
			if !exhibitions.ValidID(entryID) || seen[entryID] || exhibition == nil {
				log.Fatal("invalid artwork exhibition reference")
			}
			seen[entryID] = true
			matched := false
			for _, entry := range objects(exhibition, "entries") {
				if str(entry, "id") == entryID && str(entry, "localArtworkId") == id && str(entry, "participation") == str(appearance, "participation") {
					matched = true
				}
			}
			if !matched {
				log.Fatal("artwork and exhibition references disagree")
			}
		}
	}
	sort.Slice(a.records, func(i, j int) bool {
		x, y := a.records[i], a.records[j]
		if number(x, "startYear") == number(y, "startYear") {
			return str(x, "id") > str(y, "id")
		}
		return number(x, "startYear") > number(y, "startYear")
	})
	fmt.Printf("Local exhibition review: %d records at http://%s\n", len(a.records), *listen)
	server := &http.Server{Addr: *listen, Handler: a, ReadHeaderTimeout: 5 * time.Second, WriteTimeout: 15 * time.Second, IdleTimeout: 30 * time.Second}
	log.Fatal(server.ListenAndServe())
}
