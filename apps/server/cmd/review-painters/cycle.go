package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

const cycleVersion = "popular-research-cycle-v1"

type cycleArtist struct {
	ID, Name, Slug string
	Names          []string
}
type cycleManifest struct {
	Version, Fingerprint, InventorySHA string
	Created                            time.Time
	Artists                            []cycleArtist
}
type cycleWork struct {
	popularWork
	ReviewState, ImageState, NextAction string
}
type cycleCandidate struct {
	ID, Title, URL, Accession, Date, Artist, ImageURL, Rights, State, ExistingID string
	First, Last                                                                  *int
	Raw                                                                          map[string]any
}
type cycleDiscovery struct {
	URL, State, Error, Capture, SHA string
	At                              time.Time
	Total                           int
	Truncated                       bool
	Candidates                      []cycleCandidate
}
type cycleReport struct {
	Version, ArtistID, Artist, Slug, Fingerprint string
	At                                           time.Time
	AutomatedPassDone, ResearchComplete          bool
	Works                                        []cycleWork
	Museums                                      map[string][]string
	Discovery                                    cycleDiscovery
	Counts                                       map[string]int
}

// One bounded offline cohort fingerprint. No public request executes this query.
// It includes metadata, associations, source identities and media changes so a
// resume cannot silently carry completion across changed records/popularity.
const cycleFingerprintSQL = `WITH cohort AS MATERIALIZED (
 SELECT a.id FROM artists a JOIN artist_discovery_selection d ON d.artist_id=a.id WHERE d.is_popular
), work_ids AS MATERIALIZED (
 SELECT DISTINCT aa.artwork_id id FROM artwork_artists aa JOIN cohort c ON c.id=aa.artist_id
), parts AS (
 SELECT 'a' kind,a.id::text id,to_jsonb(a)::text body FROM artists a JOIN cohort c ON c.id=a.id
 UNION ALL SELECT 'w',a.id::text,to_jsonb(a)::text FROM artworks a JOIN work_ids w ON w.id=a.id
 UNION ALL SELECT 'c',aa.artwork_id::text||aa.artist_id::text,to_jsonb(aa)::text FROM artwork_artists aa JOIN work_ids w ON w.id=aa.artwork_id
 UNION ALL SELECT 'e',e.id::text,to_jsonb(e)::text FROM external_identifiers e JOIN work_ids w ON w.id=e.entity_id WHERE e.entity_type='artwork'
 UNION ALL SELECT 'm',m.id::text,to_jsonb(m)::text FROM media_assets m JOIN artworks a ON a.primary_media_id=m.id JOIN work_ids w ON w.id=a.id
 UNION ALL SELECT 'l',l.id::text,to_jsonb(l)::text FROM artwork_location_assertions l JOIN work_ids w ON w.id=l.artwork_id
 UNION ALL SELECT 'r',r.media_id::text,to_jsonb(r)::text FROM media_rights_evidence r JOIN artworks a ON a.primary_media_id=r.media_id JOIN work_ids w ON w.id=a.id
 UNION ALL SELECT 't',t.id::text,to_jsonb(t)::text FROM citations t JOIN work_ids w ON w.id=t.entity_id WHERE t.entity_type='artwork'
) SELECT md5(string_agg(kind||id||md5(body),'' ORDER BY kind,id)) FROM parts`

func cycleCohort(ctx context.Context, p *pgxpool.Pool) ([]cycleArtist, string, error) {
	var count int
	if err := p.QueryRow(ctx, `SELECT count(*) FROM artwork_artists aa JOIN artist_discovery_selection d ON d.artist_id=aa.artist_id WHERE d.is_popular`).Scan(&count); err != nil {
		return nil, "", err
	}
	if count > 50000 {
		return nil, "", fmt.Errorf("cycle exceeds 50k-link offline budget")
	}
	rows, err := p.Query(ctx, `SELECT a.id::text,a.display_name,a.slug,ARRAY[a.display_name,a.sort_name]||ARRAY(SELECT alias FROM artist_aliases x WHERE x.artist_id=a.id ORDER BY alias) FROM artists a JOIN artist_discovery_selection d ON d.artist_id=a.id WHERE d.is_popular ORDER BY a.display_name,a.id`)
	if err != nil {
		return nil, "", err
	}
	defer rows.Close()
	artists := []cycleArtist{}
	for rows.Next() {
		var a cycleArtist
		if err = rows.Scan(&a.ID, &a.Name, &a.Slug, &a.Names); err != nil {
			return nil, "", err
		}
		artists = append(artists, a)
	}
	if err = rows.Err(); err != nil {
		return nil, "", err
	}
	rows.Close()
	if len(artists) < 1 || len(artists) > 200 {
		return nil, "", fmt.Errorf("invalid popular cohort size")
	}
	var fp string
	err = p.QueryRow(ctx, cycleFingerprintSQL).Scan(&fp)
	return artists, fp, err
}

func classifyCycleWork(w popularWork, leads map[string]imageLead) cycleWork {
	x := cycleWork{popularWork: w, ReviewState: "source_review_pending", ImageState: w.ImageCheck, NextAction: "Check exact museum notice, creator, creation date and per-file permission."}
	if w.Scope != "eligible" {
		x.ReviewState = "date_review_required"
		x.NextAction = "Resolve creation dating before import/image selection; never infer from artist lifespan."
	}
	if !w.HoldingEvidence {
		x.ReviewState = "holding_review_required"
	}
	if w.NGAObject != "" && w.Image == "" {
		l := leads[w.NGAObject]
		switch {
		case l.Count != 1:
			x.ImageState = "cached_NGA_primary_image_missing_or_ambiguous"
		case !l.Open:
			x.ImageState = "cached_NGA_image_not_open"
		default:
			x.ImageState = "cached_NGA_open_image_lead_requires_fresh_check"
		}
	}
	for _, s := range w.Sources {
		u, err := url.Parse(s)
		if err != nil {
			continue
		}
		switch u.Hostname() {
		case "www.musee-orsay.fr":
			x.NextAction = "Museum access paused after HTTP 403; no alternate-host retries."
		case "www.artic.edu":
			if w.Image == "" {
				x.ImageState = "Chicago_image_access_paused_HTTP403"
			}
		case "collection.nationalmuseum.se":
			if w.Image == "" {
				x.ImageState = "Nationalmuseum_image_access_paused_HTTP403"
			}
		case "www.marmottan.fr":
			if w.Image == "" {
				x.ImageState = "Marmottan_image_permission_unresolved"
			}
		}
	}
	return x
}

func cycleName(s string) string {
	return strings.ToLower(strings.Join(strings.Fields(strings.NewReplacer(",", " ", "-", " ", "’", "'", ".", " ").Replace(s)), " "))
}
func cycleCreatorMatches(a cycleArtist, w ingest.Work) bool {
	if w.ArtistName == "" {
		return false
	}
	for _, n := range a.Names {
		if cycleName(n) == cycleName(w.ArtistName) {
			return true
		}
	}
	return false
}

func cycleCandidateFrom(a cycleArtist, raw map[string]any, known map[string]popularWork) cycleCandidate {
	w := ingest.NormalizeCleveland(raw)
	c := cycleCandidate{ID: w.ID, Title: w.Title, URL: w.URL, Accession: w.Accession, Artist: w.ArtistName, Date: w.Date, First: w.First, Last: w.Last, ImageURL: w.ImageURL, Rights: w.Rights, Raw: raw, State: "creator_review_required"}
	if !cycleCreatorMatches(a, w) {
		return c
	}
	if w.Type != "painting" {
		c.State = "object_type_review_required"
		return c
	}
	u, e := url.Parse(w.URL)
	if e != nil || u.Scheme != "https" || (u.Hostname() != "clevelandart.org" && u.Hostname() != "www.clevelandart.org") || u.Path != "/art/"+w.Accession || u.RawQuery != "" || u.User != nil || u.Port() != "" || w.ID == "" || w.Accession == "" || w.Title == "" {
		c.State = "identity_review_required"
		return c
	}
	if catalog.CreationScope(w.First, w.Last, w.Precision) != "eligible" {
		c.State = "date_review_required"
		return c
	}
	c.State = "new_candidate_requires_review"
	for _, k := range known {
		match := false
		for _, s := range k.Sources {
			if s == w.URL {
				match = true
			}
		}
		if !match {
			continue
		}
		if c.ExistingID != "" && c.ExistingID != k.ID {
			c.State = "ambiguous_local_identity"
			return c
		}
		c.ExistingID = k.ID
		if k.Title != w.Title || k.Accession != w.Accession || k.Scope != "eligible" {
			c.State = "existing_metadata_conflict"
			continue
		}
		c.State = "existing_metadata_matched_image_review_pending"
		if k.Image != "" {
			c.State = "existing_image_preserved"
		} else if w.Rights == "cc0" && w.ImageURL != "" && w.Copyright == "" {
			c.State = "existing_CC0_image_candidate"
		}
	}
	return c
}

type cycleClient struct {
	client   *http.Client
	last     time.Time
	paused   string
	failures int
}

func newCycleClient() *cycleClient {
	return &cycleClient{client: &http.Client{Timeout: 25 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return fmt.Errorf("redirect requires review") }}}
}
func (c *cycleClient) discover(ctx context.Context, a cycleArtist, out string, known map[string]popularWork) (cycleDiscovery, error) {
	q := url.Values{"artists": {a.Name}, "type": {"Painting"}, "limit": {"20"}, "skip": {"0"}}
	d := cycleDiscovery{URL: "https://openaccess-api.clevelandart.org/api/artworks/?" + q.Encode(), At: time.Now().UTC(), Candidates: []cycleCandidate{}, State: "not_requested"}
	if c.paused != "" {
		d.State = "source_paused"
		d.Error = c.paused
		return d, nil
	}
	file := filepath.Join(out, "captures", a.ID+".json")
	var b []byte
	if cached, err := os.ReadFile(file); err == nil {
		var meta cycleDiscovery
		mb, e := os.ReadFile(file + ".snapshot.json")
		if e != nil {
			return d, e
		}
		if e = json.Unmarshal(mb, &meta); e != nil {
			return d, e
		}
		if meta.SHA != digest(cached) || meta.URL != d.URL {
			return d, fmt.Errorf("capture identity/hash mismatch")
		}
		d.At = meta.At
		b = cached
	} else if !os.IsNotExist(err) {
		return d, err
	} else {
		if wait := 1500*time.Millisecond - time.Since(c.last); wait > 0 {
			select {
			case <-ctx.Done():
				return d, ctx.Err()
			case <-time.After(wait):
			}
		}
		req, e := http.NewRequestWithContext(ctx, http.MethodGet, d.URL, nil)
		if e != nil {
			return d, e
		}
		req.Header.Set("User-Agent", "ArtlineResearch/1.0 (bounded museum catalogue study)")
		res, e := c.client.Do(req)
		c.last = time.Now()
		if e != nil {
			d.State = "request_failed"
			d.Error = e.Error()
			c.failures++
			if c.failures >= 3 {
				c.paused = "three consecutive metadata failures"
			}
			return d, nil
		}
		defer res.Body.Close()
		if res.StatusCode != 200 {
			d.State = "request_failed"
			d.Error = fmt.Sprintf("HTTP %d", res.StatusCode)
			c.failures++
			if res.StatusCode == 403 || res.StatusCode == 429 || res.StatusCode == 401 || c.failures >= 3 {
				c.paused = d.Error
			}
			return d, nil
		}
		b, e = io.ReadAll(io.LimitReader(res.Body, (4<<20)+1))
		if e != nil {
			return d, e
		}
		if len(b) > 4<<20 {
			return d, fmt.Errorf("metadata response exceeds 4MB budget")
		}
		d.SHA = digest(b)
		d.Capture = filepath.Join("captures", a.ID+".json")
		if e = save(file, b); e != nil {
			return d, e
		}
		if e = save(file+".snapshot.json", encode(d)); e != nil {
			return d, e
		}
	}
	var doc struct {
		Info struct {
			Total int `json:"total"`
		}
		Data []map[string]any
	}
	if err := json.Unmarshal(b, &doc); err != nil {
		d.State = "invalid_response"
		d.Error = err.Error()
		c.failures++
		if c.failures >= 3 {
			c.paused = "three consecutive invalid metadata responses"
		}
		return d, nil
	}
	if doc.Data == nil {
		d.State = "invalid_response"
		d.Error = "missing data array"
		c.failures++
		if c.failures >= 3 {
			c.paused = d.Error
		}
		return d, nil
	}
	if len(doc.Data) > 20 {
		return d, fmt.Errorf("source ignored result limit")
	}
	c.failures = 0
	d.State = "bounded_catalogue_search_checked"
	d.SHA = digest(b)
	d.Capture = filepath.Join("captures", a.ID+".json")
	d.Total = doc.Info.Total
	d.Truncated = doc.Info.Total > len(doc.Data)
	for _, raw := range doc.Data {
		d.Candidates = append(d.Candidates, cycleCandidateFrom(a, raw, known))
	}
	return d, nil
}

func runPopularCycle(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	artists, fp, err := cycleCohort(ctx, p)
	if err != nil {
		return err
	}
	manifestPath := filepath.Join(out, "manifest.json")
	var manifest cycleManifest
	if b, e := os.ReadFile(manifestPath); e == nil {
		if err = json.Unmarshal(b, &manifest); err != nil {
			return err
		}
		if manifest.Version != cycleVersion || manifest.Fingerprint != fp || digest(encode(manifest.Artists)) != digest(encode(artists)) {
			return fmt.Errorf("cohort changed: start a new cycle directory; previous work preserved")
		}
	} else if !os.IsNotExist(e) {
		return e
	} else {
		if err = newSnapshot(out); err != nil {
			return err
		}
		if err = exportPopular(ctx, p, root, filepath.Join(out, "inventory")); err != nil {
			return err
		}
		_, after, e := cycleCohort(ctx, p)
		if e != nil {
			return e
		}
		if fp != after {
			return fmt.Errorf("catalogue changed during initialization; start a new directory")
		}
		b, e := os.ReadFile(filepath.Join(out, "inventory/artworks.jsonl"))
		if e != nil {
			return e
		}
		manifest = cycleManifest{cycleVersion, fp, digest(b), time.Now().UTC(), artists}
		if err = save(manifestPath, encode(manifest)); err != nil {
			return err
		}
	}
	lock, err := os.OpenFile(filepath.Join(out, "run.lock"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return fmt.Errorf("cycle already running or stale lock needs inspection: %w", err)
	}
	lock.Close()
	defer os.Remove(filepath.Join(out, "run.lock"))
	for _, dir := range []string{"captures", "painters"} {
		if err = os.MkdirAll(filepath.Join(out, dir), 0755); err != nil {
			return err
		}
	}
	data, err := os.ReadFile(filepath.Join(out, "inventory/artworks.jsonl"))
	if err != nil {
		return err
	}
	if len(data) > 128<<20 || digest(data) != manifest.InventorySHA {
		return fmt.Errorf("inventory changed or oversized")
	}
	works := map[string]popularWork{}
	groups := map[string][]popularWork{}
	scanner := bufio.NewScanner(strings.NewReader(string(data)))
	scanner.Buffer(make([]byte, 4096), 1<<20)
	for scanner.Scan() {
		var w popularWork
		if err = json.Unmarshal(scanner.Bytes(), &w); err != nil {
			return err
		}
		if _, ok := works[w.ID]; ok {
			return fmt.Errorf("duplicate work in inventory")
		}
		works[w.ID] = w
		for _, c := range w.Credits {
			groups[c.ID] = append(groups[c.ID], w)
		}
	}
	if err = scanner.Err(); err != nil {
		return err
	}
	leads, err := popularNGALeads(root)
	if err != nil {
		return err
	}
	client := newCycleClient()
	reports := []cycleReport{}
	for i, a := range artists {
		file := filepath.Join(out, "painters", a.ID+".json")
		if b, e := os.ReadFile(file); e == nil {
			var r cycleReport
			if err = json.Unmarshal(b, &r); err != nil {
				return err
			}
			if err = validateCycleCheckpoint(out, a, fp, groups[a.ID], r); err != nil {
				return err
			}
			if r.Discovery.State == "request_failed" || r.Discovery.State == "invalid_response" {
				client.failures++
				if client.failures >= 3 {
					client.paused = "three consecutive metadata failures"
				}
			} else if r.Discovery.State == "bounded_catalogue_search_checked" {
				client.failures = 0
			}
			if r.Discovery.State == "source_paused" || r.Discovery.Error == "HTTP 403" || r.Discovery.Error == "HTTP 429" || r.Discovery.Error == "HTTP 401" {
				client.paused = r.Discovery.Error
			}
			reports = append(reports, r)
			continue
		} else if !os.IsNotExist(e) {
			return e
		}
		r := cycleReport{Version: cycleVersion, ArtistID: a.ID, Artist: a.Name, Slug: a.Slug, Fingerprint: fp, At: time.Now().UTC(), Works: []cycleWork{}, Museums: map[string][]string{}, Counts: map[string]int{}}
		local := map[string]popularWork{}
		for _, w := range groups[a.ID] {
			x := classifyCycleWork(w, leads)
			r.Works = append(r.Works, x)
			local[w.ID] = w
			r.Counts["works"]++
			r.Counts[x.ReviewState]++
			r.Counts[x.ImageState]++
			r.Museums[w.Institution] = append(r.Museums[w.Institution], w.Sources...)
		}
		r.Discovery, err = client.discover(ctx, a, out, local)
		if err != nil {
			return err
		}
		for _, c := range r.Discovery.Candidates {
			r.Counts[c.State]++
		}
		r.AutomatedPassDone = true
		if err = save(file, encode(r)); err != nil {
			return err
		}
		reports = append(reports, r)
		fmt.Printf("Cycle %d/%d: %s — %d works checked, %d discovery candidates; %s\n", i+1, len(artists), a.Name, len(r.Works), len(r.Discovery.Candidates), r.Discovery.State)
	}
	return renderCycle(out, manifest, reports)
}

// A checkpoint may only reuse the exact frozen inventory and captured source
// facts; derived decisions are regenerated separately on replay.
func validateCycleCheckpoint(out string, a cycleArtist, fp string, works []popularWork, r cycleReport) error {
	if r.Version != cycleVersion || r.ArtistID != a.ID || r.Artist != a.Name || r.Slug != a.Slug || r.Fingerprint != fp || !r.AutomatedPassDone || r.ResearchComplete || len(r.Works) != len(works) {
		return fmt.Errorf("invalid checkpoint for %s", a.Name)
	}
	for i, w := range works {
		if !reflect.DeepEqual(w, r.Works[i].popularWork) {
			return fmt.Errorf("checkpoint artwork changed for %s", a.Name)
		}
	}
	q := url.Values{"artists": {a.Name}, "type": {"Painting"}, "limit": {"20"}, "skip": {"0"}}
	if r.Discovery.URL != "https://openaccess-api.clevelandart.org/api/artworks/?"+q.Encode() {
		return fmt.Errorf("checkpoint query changed")
	}
	if r.Discovery.State == "bounded_catalogue_search_checked" {
		name := filepath.Join("captures", a.ID+".json")
		if r.Discovery.Capture != name {
			return fmt.Errorf("checkpoint capture path changed")
		}
		b, err := os.ReadFile(filepath.Join(out, name))
		if err != nil {
			return err
		}
		if len(b) > 4<<20 || digest(b) != r.Discovery.SHA {
			return fmt.Errorf("checkpoint source hash changed")
		}
		var doc struct{ Data []map[string]any }
		if err = json.Unmarshal(b, &doc); err != nil {
			return err
		}
		if doc.Data == nil || len(doc.Data) != len(r.Discovery.Candidates) {
			return fmt.Errorf("checkpoint candidates changed")
		}
		for i, raw := range doc.Data {
			if !reflect.DeepEqual(raw, r.Discovery.Candidates[i].Raw) {
				return fmt.Errorf("checkpoint source facts changed")
			}
		}
	} else if len(r.Discovery.Candidates) != 0 {
		return fmt.Errorf("candidates without successful source capture")
	}
	return nil
}

func renderCycle(out string, m cycleManifest, reports []cycleReport) error {
	// Reports are disposable projections of immutable checkpoints. Atomic replace
	// avoids presenting a half-written progress page after interruption.
	write := func(file string, b []byte) error {
		tmp := file + ".next"
		if err := os.WriteFile(tmp, b, 0600); err != nil {
			return err
		}
		return os.Rename(tmp, file)
	}
	var index strings.Builder
	fmt.Fprintf(&index, "# Popular-painter research cycle\n\n%d/%d painters have completed this automated pass. **No painter's worldwide research is marked complete.** Each artwork was inventoried and checked for local image, date, holding and source gaps. Discovery is bounded to the first 20 paintings returned per artist by Cleveland's official catalogue; cached NGA image leads cover additional existing works. European museum gaps remain explicit in each painter's source list. No images are downloaded or records imported by this runner.\n\n[Method and continuation](../../POPULAR_RESEARCH_CYCLE.md) · [Frozen catalogue inventory](inventory/PAINTERS.md)\n\n| Painter | Existing works | Discovery results | Next decisions |\n|---|---:|---:|---|\n", len(reports), len(m.Artists))
	totals := map[string]int{"painters_processed": len(reports), "painters_research_complete": 0}
	for _, r := range reports {
		// Reassess saved source facts with the current classifier without repeating
		// requests or overwriting the original execution checkpoint.
		var artist cycleArtist
		for _, a := range m.Artists {
			if a.ID == r.ArtistID {
				artist = a
			}
		}
		known := map[string]popularWork{}
		r.Counts = map[string]int{}
		for _, w := range r.Works {
			known[w.ID] = w.popularWork
			r.Counts["works"]++
			r.Counts[w.ReviewState]++
			r.Counts[w.ImageState]++
		}
		for j, c := range r.Discovery.Candidates {
			r.Discovery.Candidates[j] = cycleCandidateFrom(artist, c.Raw, known)
			r.Counts[r.Discovery.Candidates[j].State]++
		}
		if err := write(filepath.Join(out, "painters", r.ArtistID+".assessment.json"), encode(r)); err != nil {
			return err
		}
		for k, v := range r.Counts {
			totals[k] += v
		}
		var page strings.Builder
		fmt.Fprintf(&page, "# %s\n\n- [x] All %d snapshot-linked artworks inventoried and automated checks recorded.\n- [x] Bounded discovery attempted or source pause recorded.\n- [ ] Full museum/oeuvre discovery complete.\n- [ ] Every artwork independently reviewed.\n- [ ] All permitted selected images acquired.\n\n[Full artwork inventory](../inventory/painters/%s.md) · [Machine-readable per-artwork assessment](%s.assessment.json)\n\n## Catalogue discovery\n\n%s. %d results returned; source total %d; more results pending: %t. %s\n\n%s\n\n| Work | Date | Museum accession | Decision |\n|---|---|---|---|\n", md(r.Artist), len(r.Works), r.Slug, r.ArtistID, md(r.Discovery.State), len(r.Discovery.Candidates), r.Discovery.Total, r.Discovery.Truncated, md(r.Discovery.Error), link("Exact museum query", r.Discovery.URL))
		for _, c := range r.Discovery.Candidates {
			fmt.Fprintf(&page, "| %s | %s | %s | %s |\n", link(c.Title, c.URL), md(c.Date), md(c.Accession), md(c.State))
		}
		page.WriteString("\n## Museum research queue\n\nThese links are existing source evidence, not fresh confirmations or current-display promises. Revisit European institutions and unresolved dates first.\n\n")
		museums := []string{}
		for museum := range r.Museums {
			museums = append(museums, museum)
		}
		sort.Strings(museums)
		for _, museum := range museums {
			urls := map[string]bool{}
			for _, u := range r.Museums[museum] {
				urls[u] = true
			}
			list := []string{}
			for u := range urls {
				list = append(list, u)
			}
			sort.Strings(list)
			fmt.Fprintf(&page, "### %s\n\n%d recorded object-source links.\n\n", md(museum), len(list))
			for j, u := range list {
				if j == 5 {
					fmt.Fprintln(&page, "Further object links are preserved in the complete artwork inventory.")
					break
				}
				fmt.Fprintf(&page, "- %s\n", link("Museum record", u))
			}
		}
		if err := write(filepath.Join(out, "painters", r.ArtistID+".md"), []byte(page.String())); err != nil {
			return err
		}
		fmt.Fprintf(&index, "| [%s](painters/%s.md) | %d | %d | %d potential additions; %d CC0 image candidates; research pending |\n", md(r.Artist), r.ArtistID, len(r.Works), len(r.Discovery.Candidates), r.Counts["new_candidate_requires_review"], r.Counts["existing_CC0_image_candidate"])
	}
	if err := write(filepath.Join(out, "PAINTERS.md"), []byte(index.String())); err != nil {
		return err
	}
	return write(filepath.Join(out, "summary.json"), encode(totals))
}
