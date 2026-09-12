package main

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"net/url"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"time"
)

type popularNGArtist struct {
	ID, QID, Name string
	Names         []string
	Works         int
}
type ngObject = map[string]any

func ngMap(v any) ngObject { m, _ := v.(map[string]any); return m }
func ngArray(v any) []any  { a, _ := v.([]any); return a }
func ngTitle(v any) string { return str(ngMap(ngMap(v)["summary"]), "title") }
func ngValue(v any, kind string) string {
	for _, x := range ngArray(v) {
		m := ngMap(x)
		if str(m, "type") == kind {
			return str(m, "value")
		}
	}
	return ""
}
func popularNGCohort(ctx context.Context) ([]popularNGArtist, error) {
	if _, err := localAuthors(ctx); err != nil {
		return nil, err
	}
	p, err := pgxpool.New(ctx, config.Load().DatabaseURL)
	if err != nil {
		return nil, err
	}
	defer p.Close()
	rows, err := p.Query(ctx, `SELECT a.id::text,e.external_id,a.display_name,
 ARRAY[a.display_name,a.sort_name]||ARRAY(SELECT alias FROM artist_aliases x WHERE x.artist_id=a.id ORDER BY alias),
 (SELECT count(*) FROM artwork_artists aa WHERE aa.artist_id=a.id)
 FROM artists a JOIN artist_discovery_selection d ON d.artist_id=a.id AND d.is_popular
 JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artist' AND e.scheme='wikidata'
 WHERE a.status<>'archived' ORDER BY 5,a.display_name,a.id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []popularNGArtist{}
	for rows.Next() {
		var a popularNGArtist
		if err = rows.Scan(&a.ID, &a.QID, &a.Name, &a.Names, &a.Works); err != nil {
			return nil, err
		}
		out = append(out, a)
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}
	if len(out) < 1 || len(out) > 200 {
		return nil, fmt.Errorf("popular cohort exceeds bounded scope")
	}
	return out, nil
}

// Exact source spellings established by the earlier National Gallery review.
var popularNGNames = map[string]string{"Q5598": "Rembrandt", "Q5432": "Francisco de Goya", "Q46373": "Hilaire-Germain-Edgar Degas", "Q159758": "Joseph Mallord William Turner", "Q35548": "Paul Cezanne", "Q42207": "Michelangelo Merisi da Caravaggio"}

func popularNGQuery(a popularNGArtist) string {
	name := a.Name
	if v := popularNGNames[a.QID]; v != "" {
		name = v
	}
	q := url.Values{"q": {`creation.maker.summary.title:"` + strings.ReplaceAll(name, `"`, `\"`) + `" AND @datatype.base:object`}, "size": {"100"}, "_source": {"summary,identifier,creation,material,measurements,classification,category,legal,@admin"}}
	return "https://data.ng.ac.uk/es/public/_search?" + q.Encode()
}
func capturePopularNG(ctx context.Context, out string) error {
	artists, err := popularNGCohort(ctx)
	if err != nil {
		return err
	}
	return captureNGCohort(ctx,out,artists)
}

func captureNGCohort(ctx context.Context,out string,artists []popularNGArtist) error {
	var err error
	cohort := filepath.Join(out, "cohort.json")
	if b, e := os.ReadFile(cohort); e == nil {
		var old []popularNGArtist
		if json.Unmarshal(b, &old) != nil || !reflect.DeepEqual(old, artists) {
			return fmt.Errorf("cohort changed; use new capture directory")
		}
	} else if !os.IsNotExist(e) {
		return e
	} else if err = save(cohort, artists); err != nil {
		return err
	}
	if _, e := os.Stat(filepath.Join(out, "source-paused.json")); e == nil {
		return fmt.Errorf("source pause exists; review it before another capture")
	}
	var totalBytes int64
	for i, a := range artists {
		file := filepath.Join(out, a.QID+".json")
		if _, e := os.Stat(file + ".snapshot.json"); os.IsNotExist(e) {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(1500 * time.Millisecond):
			}
		}
		if err = fetch(ctx, file, popularNGQuery(a), 5<<20); err != nil {
			_ = save(filepath.Join(out, "source-paused.json"), map[string]any{"artist": a, "error": err.Error(), "at": time.Now().UTC(), "next": "Source stopped. Diagnose before fresh requests; no alternate-host retry."})
			return err
		}
		_, n, e := hashFile(file)
		if e != nil {
			return e
		}
		totalBytes += n
		if totalBytes > 100<<20 {
			return fmt.Errorf("capture exceeds 100 MB session budget")
		}
		fmt.Printf("National Gallery %d/%d: %s captured\n", i+1, len(artists), a.Name)
	}
	return save(filepath.Join(out, "capture.json"), map[string]any{"artists": len(artists), "bytes": totalBytes, "scope": "one bounded query per popular painter; at most 100 metadata hits per query; no images; no global-completeness claim"})
}
func popularNGWork(hit ngObject, a popularNGArtist, index map[string][]knownAuthor) (map[string]any, string) {
	s := ngMap(hit["_source"])
	pid := str(hit, "_id")
	if pid == "" || strings.ContainsAny(pid, "/?# ") {
		return nil, "invalid source PID"
	}
	if ngValue(s["category"], "department") != "Main Collection" || ngValue(s["classification"], "classification") != "Picture" || str(ngMap(s["legal"]), "status") != "Accessioned object" {
		return nil, "not accessioned main-collection picture"
	}
	credit := str(ngMap(s["legal"]), "credit")
	if strings.Contains(strings.ToLower(credit), "hugh lane") || strings.Contains(strings.ToLower(credit), "joint") {
		return nil, "shared custody review"
	}
	creation := ngArray(s["creation"])
	if len(creation) != 1 {
		return nil, "multiple or missing creation events"
	}
	c := ngMap(creation[0])
	makers := ngArray(c["maker"])
	if len(makers) != 1 {
		return nil, "multiple or missing creators"
	}
	name := ngTitle(makers[0])
	matched := index[authorityKey(name)]
	sourceName := popularNGNames[a.QID]
	exact := len(matched) == 1 && matched[0].QID == a.QID || sourceName != "" && name == sourceName
	if !exact || ngValue(c["attribution"], "attribution") != name {
		return nil, "qualified or non-exact source creator"
	}
	link := ngMap(ngMap(makers[0])["@link"])
	if link["historical"] != false || str(ngMap(link["role"]), "value") != "Artist" {
		return nil, "not a current direct artist role"
	}
	dates := ngArray(c["date"])
	if len(dates) != 1 {
		return nil, "multiple or missing creation dates"
	}
	d := ngMap(dates[0])
	first, e1 := strconv.Atoi(str(d, "from"))
	last, e2 := strconv.Atoi(str(d, "to"))
	display := str(d, "value")
	if e1 != nil || e2 != nil || display == "" {
		return nil, "missing creation date"
	}
	date, ok := campaignDate(strings.TrimSpace(strings.TrimPrefix(strings.ToLower(display), "completed ")), first, last)
	if !ok {
		return nil, "creation date notation or cutoff review"
	}
	// Preserve the museum's explicit narrower search interval for early/late
	// decades; do not widen early 1480s (1480–1483) to the entire decade.
	if date.Precision == "decade" && (date.First != first || date.Last != last) {
		date = creationDate{First: first, Last: last, Precision: "range"}
	}
	medium := ngValue(s["material"], "")
	if medium == "" {
		medium = ngValue(s["material"], "detailed")
	}
	lower := strings.ToLower(medium)
	if !strings.Contains(lower, "oil") && !strings.Contains(lower, "tempera") && !strings.Contains(lower, "fresco") || strings.Contains(lower, "print") {
		return nil, "medium requires painting review"
	}
	acc := ngValue(s["identifier"], "object number")
	if acc == "" {
		return nil, "missing accession"
	}
	dimensions := ""
	for _, x := range ngArray(s["measurements"]) {
		m := ngMap(x)
		if str(m, "type") == "Overall" {
			dimensions = str(m, "display")
			break
		}
	}
	title := ngTitle(s)
	if title == "" {
		return nil, "missing title"
	}
	for _, word := range []string{"recto", "verso", "reverse of", "fragments", "panels from"} {
		if strings.Contains(strings.ToLower(title), word) {
			return nil, "physical-unit relationship review"
		}
	}
	objectURL := "https://www.nationalgallery.org.uk/data/" + pid
	description := fmt.Sprintf("%s — %s. %s.\n\nMedium: %s. Dimensions: %s.\n\nCollection credit: %s. National Gallery, London; accession %s. Holding connection, not a current-display assertion.\n\nSource: [official structured object record](%s), accessed 11 September 2026. Factual metadata only; image rights are separate.", title, name, display, medium, dimensions, credit, acc, objectURL)
	return map[string]any{"painter": a.QID, "title": title, "institution": "popular-ng", "accession": acc, "url": objectURL, "source_object_id": pid, "source_publisher": "National Gallery, London", "date_display": display, "creation_date": date, "attribution_role": "primary", "work_type": "painting", "medium": medium, "dimensions": dimensions, "description_md": description, "collection": credit, "source_raw": s, "notes": "Source-specific exact creator and accession; museum holding only. No image, masterpiece status or publication."}, "eligible"
}

func popularNGIdentity(ctx context.Context, p *pgxpool.Pool, a popularNGArtist, w map[string]any) (string, error) {
	// Exact identity branches cover the whole catalogue; same-title checks are
	// scoped by artist and only defer possible overlaps, never merge by title.
	var exact int
	err := p.QueryRow(ctx, `SELECT count(*) FROM artworks WHERE id IN (
 SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=$1
 UNION SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=$1
 UNION SELECT a.id FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug='national-gallery-london' AND a.accession_number=$2
 UNION SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND external_id=$3 AND scheme LIKE 'european-%'
 )`, w["url"], w["accession"], w["source_object_id"]).Scan(&exact)
	if err != nil {
		return "", err
	}
	if exact > 1 {
		return "ambiguous existing exact identities; reconciliation required", nil
	}
	if exact == 1 {
		return "existing exact object; preserved, source review retained", nil
	}
	var possible int
	err = p.QueryRow(ctx, `SELECT count(*) FROM artworks art JOIN artwork_artists aa ON aa.artwork_id=art.id
 WHERE aa.artist_id=$1 AND lower(regexp_replace(art.title,'[^[:alnum:]]','','g'))=lower(regexp_replace($2,'[^[:alnum:]]','','g'))`, a.ID, w["title"]).Scan(&possible)
	if err != nil {
		return "", err
	}
	if possible > 0 {
		return "same artist/title elsewhere; exact physical identity review required", nil
	}
	return "new candidate", nil
}

func assemblePopularNG(ctx context.Context, root, out string) error {
	dir := filepath.Join(root, "content/imports/popular-europe-session-20260911/ng")
	return assembleNGCohort(ctx,root,out,dir,"popular-ng",false)
}

func assembleNGCohort(ctx context.Context,root,out,dir,source string,aliases bool) error {
	b, err := os.ReadFile(filepath.Join(dir, "cohort.json"))
	if err != nil {
		return err
	}
	var artists []popularNGArtist
	if err = json.Unmarshal(b, &artists); err != nil {
		return err
	}
	current, err := popularNGCohort(ctx)
	if err != nil {
		return err
	}
	if aliases { current = ngAliasCohort(current) }
	if !reflect.DeepEqual(current, artists) {
		return fmt.Errorf("popular cohort/works changed; review new snapshot")
	}
	index, err := localAuthors(ctx)
	if err != nil {
		return err
	}
	pool, err := pgxpool.New(ctx, config.Load().DatabaseURL)
	if err != nil {
		return err
	}
	defer pool.Close()
	s := newSelection(source)
	s.AccessedOn = "2026-09-11"
	s.Definitions[source] = map[string]string{"Slug": "national-gallery-london", "Source": "national-gallery-london", "Website": "https://www.nationalgallery.org.uk", "Host": "www.nationalgallery.org.uk"}
	s.Museums[source] = map[string]string{"id": source, "name": "National Gallery", "city": "London", "country": "GB", "data_url": "https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api", "data_route": "One bounded current-popular artist query each, at most 100 hits per query; individually selected direct-attribution paintings.", "rights": "Structured metadata CC0. Narrative and images separately licensed; no image permission inferred.", "rights_url": "https://www.nationalgallery.org.uk/documentation/ngacuk/licences"}
	decisions := []map[string]any{}
	seen := map[string]bool{}
	for _, a := range artists {
		file := filepath.Join(dir, a.QID+".json")
		if err = verify(file); err != nil {
			return err
		}
		b, err = os.ReadFile(file)
		if err != nil {
			return err
		}
		var data ngObject
		if err = json.Unmarshal(b, &data); err != nil {
			return err
		}
		hits := ngArray(ngMap(data["hits"])["hits"])
		if hits == nil {
			return fmt.Errorf("missing hits array, not an empty museum result")
		}
		if len(hits) > 100 {
			return fmt.Errorf("source ignored query bound")
		}
		sort.Slice(hits, func(i, j int) bool { return str(ngMap(hits[i]), "_id") < str(ngMap(hits[j]), "_id") })
		selected := 0
		for _, h := range hits {
			hit := ngMap(h)
			w, reason := popularNGWork(hit, a, index)
			s.Decisions["examined"]++
			if reason == "eligible" && seen[w["url"].(string)] {
				reason = "duplicate search result"
			}
			if reason == "eligible" {
				var identity string
				identity, err = popularNGIdentity(ctx, pool, a, w)
				if err != nil {
					return err
				}
				if identity != "new candidate" {
					reason = identity
				}
			}
			if reason == "eligible" && selected >= 20 {
				reason = "20-work painter selection budget; further review pending"
			}
			if reason == "eligible" {
				selected++
				w["institution"] = source
				seen[w["url"].(string)] = true
				s.Works = append(s.Works, w)
			}
			s.Decisions[reason]++
			decisions = append(decisions, map[string]any{"artist": a.Name, "qid": a.QID, "pid": str(hit, "_id"), "title": ngTitle(hit["_source"]), "decision": reason})
		}
		fmt.Printf("%s: %d selected from %d source candidates\n", a.Name, selected, len(hits))
	}
	if err = save(filepath.Join(out, "decisions.json"), decisions); err != nil {
		return err
	}
	return s.write(out)
}
