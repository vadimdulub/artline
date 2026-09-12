// Explicit local-only coverage audit and selected museum-highlight image import.
// No bulk picture crawl, publication, metadata replacement, or inferred highlights.
package main

import (
	"context"
	"crypto/sha256"
	"encoding/csv"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

const actor = "local-european-research"
const version = "museum-masterpieces-100kb-v1"
const metCSVHash = "de617b9c947458e426111207f81a65bd1379a151c0077d3ce29cfc22fc0b9183"

type candidate struct {
	ID, Scheme, Object, Institution, SourceID, Fingerprint string
	Title, Artist                                          string
	HasImage, HasHighlight                                 bool
}
type entry struct {
	Candidate candidate
	Work      ingest.Work
	Retrieved time.Time
}
type selection struct {
	Version  string
	Created  time.Time
	Entries  []entry
	Deferred []string
}

func hash(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func jsonBytes(v any) []byte {
	b, e := json.Marshal(v)
	if e != nil {
		panic(e)
	}
	return b
}
func save(p string, v any) error {
	b, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return e
	}
	return writeNew(p, append(b, '\n'))
}
func writeNew(p string, b []byte) error {
	if e := os.MkdirAll(filepath.Dir(p), 0755); e != nil {
		return e
	}
	f, e := os.OpenFile(p, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return e
	}
	_, e = f.Write(b)
	ce := f.Close()
	if e != nil {
		return e
	}
	return ce
}
func audit(ctx context.Context, p *pgxpool.Pool, out string) error {
	// One offline aggregate, never executed by a public endpoint or per painter.
	rows, e := p.Query(ctx, `WITH h AS (
 SELECT DISTINCT ci.artwork_id FROM curated_collection_items ci JOIN curated_collections c ON c.id=ci.collection_id WHERE c.curator_kind='museum' AND c.status<>'archived'
 ), stats AS (
 SELECT aa.artist_id,count(DISTINCT a.id) AS artworks,
 count(DISTINCT a.id) FILTER(WHERE a.primary_media_id IS NOT NULL) AS pictures,
 count(DISTINCT a.id) FILTER(WHERE h.artwork_id IS NOT NULL) AS museum_highlights,
 count(DISTINCT a.id) FILTER(WHERE h.artwork_id IS NOT NULL AND a.primary_media_id IS NULL) AS highlights_missing_pictures,
 count(DISTINCT a.id) FILTER(WHERE artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible') AS date_eligible,
 count(DISTINCT a.id) FILTER(WHERE a.object_form='icon') AS icons
 FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id LEFT JOIN h ON h.artwork_id=a.id GROUP BY aa.artist_id
 ) SELECT jsonb_build_object('id',p.id,'name',p.display_name,'slug',p.slug,'status',p.status,
 'popular',coalesce(d.is_popular,false),'artworks',coalesce(s.artworks,0),'pictures',coalesce(s.pictures,0),
 'museum_highlights',coalesce(s.museum_highlights,0),'highlights_missing_pictures',coalesce(s.highlights_missing_pictures,0),
 'date_eligible',coalesce(s.date_eligible,0),'icons',coalesce(s.icons,0))
 FROM artists p LEFT JOIN stats s ON s.artist_id=p.id LEFT JOIN artist_discovery_selection d ON d.artist_id=p.id ORDER BY p.display_name,p.id`)
	if e != nil {
		return e
	}
	defer rows.Close()
	painters := []json.RawMessage{}
	for rows.Next() {
		var b []byte
		if e = rows.Scan(&b); e != nil {
			return e
		}
		painters = append(painters, b)
	}
	if e = rows.Err(); e != nil {
		return e
	}
	var totals []byte
	e = p.QueryRow(ctx, `SELECT jsonb_build_object('artists',(SELECT count(*) FROM artists),'artworks',count(*),'artworks_with_pictures',count(primary_media_id),'published',count(*) FILTER(WHERE status='published'),
 'unlinked_creator_works',count(*) FILTER(WHERE unlinked_creator_label IS NOT NULL AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=artworks.id)),
 'media_assets',(SELECT count(*) FROM media_assets),'museum_highlight_items',(SELECT count(*) FROM curated_collection_items ci JOIN curated_collections c ON c.id=ci.collection_id WHERE c.curator_kind='museum'),
 'owner_selection_items',(SELECT count(*) FROM curated_collection_items ci JOIN curated_collections c ON c.id=ci.collection_id WHERE c.curator_kind='owner')) FROM artworks`).Scan(&totals)
	if e != nil {
		return e
	}
	return save(out, map[string]any{"created_at": time.Now().UTC(), "method": "Full database coverage audit, not an individual art-historical judgement on every artist or artwork. Shared-attribution counts must not be summed across artists.", "totals": json.RawMessage(totals), "painters": painters})
}

// Snapshot the exact target state; any intervening metadata/attribution change
// requires a new selection. primary_media_id/revision are excluded for replay.
const fingerprintSQL = `md5((to_jsonb(a)-ARRAY['primary_media_id','revision','updated_at','updated_by'])::text || coalesce((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id)::text FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]'))`

func candidates(ctx context.Context, p *pgxpool.Pool, source string) (map[string]candidate, error) {
	schemes := []string{"met-object", "european-met-the-met-object"}
	institution := "the-met"
	if source == "cleveland" {
		schemes = []string{"cleveland-object", "european-cleveland-cleveland-museum-of-art-object"}
		institution = "cleveland-museum-of-art"
	}
	rows, e := p.Query(ctx, `SELECT DISTINCT ON(a.id) a.id::text,e.scheme,e.external_id,a.current_institution_id::text,e.source_id::text,a.title,
 coalesce((SELECT string_agg(p.display_name,', ' ORDER BY aa.attribution_role,p.id) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id),a.unlinked_creator_label,''),
 a.primary_media_id IS NOT NULL,EXISTS(SELECT 1 FROM curated_collection_items ci JOIN curated_collections c ON c.id=ci.collection_id WHERE ci.artwork_id=a.id AND c.curator_kind='museum' AND c.status<>'archived'),`+fingerprintSQL+`
 FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id JOIN institutions i ON i.id=a.current_institution_id JOIN sources s ON s.id=e.source_id AND s.is_active
 WHERE e.entity_type='artwork' AND e.scheme=ANY($1::text[]) AND i.slug=$2 AND a.status='review'
 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' ORDER BY a.id,length(e.scheme)`, schemes, institution)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	out := map[string]candidate{}
	for rows.Next() {
		var c candidate
		if e = rows.Scan(&c.ID, &c.Scheme, &c.Object, &c.Institution, &c.SourceID, &c.Title, &c.Artist, &c.HasImage, &c.HasHighlight, &c.Fingerprint); e != nil {
			return nil, e
		}
		out[c.Object] = c
	}
	return out, rows.Err()
}

type fetcher struct {
	client   *http.Client
	last     time.Time
	blocked  map[string]bool
	failures map[string]int
	bytes    int
}

func newFetcher() *fetcher {
	return &fetcher{client: &http.Client{Timeout: 35 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return errors.New("redirect requires review") }}, blocked: map[string]bool{}, failures: map[string]int{}}
}
func (f *fetcher) get(ctx context.Context, raw string, limit int) ([]byte, error) {
	u, e := url.Parse(raw)
	if e != nil || u.Scheme != "https" || u.User != nil || u.Port() != "" {
		return nil, errors.New("unsafe URL")
	}
	allowed := map[string]bool{"collectionapi.metmuseum.org": true, "openaccess-api.clevelandart.org": true, "images.metmuseum.org": true, "openaccess-cdn.clevelandart.org": true,
		"raw.githubusercontent.com": true, "api.nga.gov": true, "www.wikidata.org": true, "commons.wikimedia.org": true, "upload.wikimedia.org": true, "thumb.wikimedia.org": true, "iip.smk.dk": true}
	allowed["api.artic.edu"] = strings.HasPrefix(raw, "https://api.artic.edu/api/v1/artworks?")
	allowed["www.artic.edu"] = strings.HasPrefix(raw, "https://www.artic.edu/iiif/2/")
	allowed["cdn.thenetexperts.info"] = strings.HasPrefix(raw, "https://cdn.thenetexperts.info/image/authenticated/") && strings.HasSuffix(raw, "_CC-BY-SA_BSTGS.jpg")
	for _, fact := range karlsruheImageFacts {
		if raw == "https://www.kunsthalle-karlsruhe.de/wp-content/kunstwerk/jpg/K"+fact.Object+".jpg" {
			allowed["www.kunsthalle-karlsruhe.de"] = true
		}
	}
	for _, fact := range nivaImageFacts {
		if raw == "https://nivaagaard.dk/wp-content/uploads/"+fact.ImagePath {
			allowed["nivaagaard.dk"] = true
		}
	}
	if u.Host == "raw.githubusercontent.com" && raw != ngaImageFeed {
		return nil, errors.New("unapproved static metadata feed")
	}
	if !allowed[u.Host] || f.blocked[u.Host] {
		return nil, errors.New("source outside allowlist or paused")
	}
	if f.bytes+limit > 512<<20 {
		return nil, errors.New("execution transfer budget reached")
	}
	pace := time.Second
	if u.Host == "nivaagaard.dk" || u.Host == "www.kunsthalle-karlsruhe.de" {
		pace = 11 * time.Second
	}
	if wait := pace - time.Since(f.last); wait > 0 {
		t := time.NewTimer(wait)
		select {
		case <-ctx.Done():
			t.Stop()
			return nil, ctx.Err()
		case <-t.C:
		}
	}
	f.last = time.Now()
	req, e := http.NewRequestWithContext(ctx, "GET", raw, nil)
	if e != nil {
		return nil, e
	}
	req.Header.Set("User-Agent", "Artline/1.0 (owner-requested selected museum highlights; local study)")
	res, e := f.client.Do(req)
	var b []byte
	if e == nil {
		defer res.Body.Close()
		if res.StatusCode != 200 {
			e = fmt.Errorf("HTTP %d", res.StatusCode)
			if res.StatusCode == 403 || res.StatusCode == 429 {
				f.blocked[u.Host] = true
			}
		} else {
			b, e = io.ReadAll(io.LimitReader(res.Body, int64(limit)+1))
			f.bytes += len(b)
			if len(b) > limit {
				e = errors.New("transfer ceiling exceeded")
			}
		}
	}
	if e != nil {
		f.failures[u.Host]++
		if f.failures[u.Host] >= 3 {
			f.blocked[u.Host] = true
		}
		return nil, e
	}
	f.failures[u.Host] = 0
	return b, nil
}
func stage(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	s := selection{Version: version, Created: time.Now().UTC(), Entries: []entry{}, Deferred: []string{}}
	fetch := newFetcher()
	add := func(c candidate, w ingest.Work, at time.Time) {
		if w.ID != c.Object || strings.TrimSpace(w.Title) != strings.TrimSpace(c.Title) || w.Eligible() != "eligible" {
			s.Deferred = append(s.Deferred, w.Source+":"+w.ID+": identity/title/date/highlight review required")
			return
		}
		if c.HasImage && c.HasHighlight {
			return
		}
		w.SourceSnapshotAt = at
		s.Entries = append(s.Entries, entry{c, w, at})
	}
	cm, e := candidates(ctx, p, "cleveland")
	if e != nil {
		return e
	}
	for skip := 0; skip < 2000; skip += 100 {
		raw := "https://openaccess-api.clevelandart.org/api/artworks/?" + url.Values{"highlight": {"1"}, "limit": {"100"}, "skip": {fmt.Sprint(skip)}}.Encode()
		b, e := fetch.get(ctx, raw, 16<<20)
		if e != nil {
			s.Deferred = append(s.Deferred, "Cleveland metadata paused: "+e.Error())
			break
		}
		at := time.Now().UTC()
		if e = save(filepath.Join(filepath.Dir(out), "captures", fmt.Sprintf("cleveland-%04d.json", skip)), map[string]any{"url": raw, "retrieved_at": at, "sha256": hash(b), "response": json.RawMessage(b)}); e != nil {
			return e
		}
		var page struct {
			Info struct{ Total int }
			Data []map[string]any
		}
		if e = json.Unmarshal(b, &page); e != nil {
			return e
		}
		if page.Info.Total > 2000 {
			return errors.New("Cleveland selection exceeds bound")
		}
		for _, m := range page.Data {
			w := ingest.NormalizeCleveland(m)
			if c, ok := cm[w.ID]; ok {
				add(c, w, at)
			}
		}
		fmt.Printf("Cleveland highlight records checked: %d/%d\n", skip+len(page.Data), page.Info.Total)
		if skip+len(page.Data) >= page.Info.Total {
			break
		}
		if len(page.Data) == 0 {
			return errors.New("incomplete Cleveland pagination")
		}
	}
	mm, e := candidates(ctx, p, "met")
	if e != nil {
		return e
	}
	path := filepath.Join(root, "content/imports/campaign-met-20260910/objects.csv")
	f, e := os.Open(path)
	if e != nil {
		return e
	}
	defer f.Close()
	h := sha256.New()
	if _, e = io.Copy(h, f); e != nil {
		return e
	}
	if fmt.Sprintf("%x", h.Sum(nil)) != metCSVHash {
		return errors.New("Met metadata snapshot changed")
	}
	if _, e = f.Seek(0, 0); e != nil {
		return e
	}
	r := csv.NewReader(f)
	header, e := r.Read()
	if e != nil {
		return e
	}
	cols := map[string]int{}
	for i, v := range header {
		cols[v] = i
	}
	if _, ok := cols["Is Highlight"]; !ok {
		return errors.New("missing Met highlight column")
	}
	ids := []string{}
	for {
		row, e := r.Read()
		if e == io.EOF {
			break
		}
		if e != nil {
			return e
		}
		id := row[cols["Object ID"]]
		c, ok := mm[id]
		if ok && (!c.HasImage || !c.HasHighlight) && strings.EqualFold(row[cols["Is Highlight"]], "true") {
			ids = append(ids, id)
		}
	}
	sort.Strings(ids)
	if len(ids) > 500 {
		return errors.New("Met selected metadata exceeds 500-object bound")
	}
	for i, id := range ids {
		raw := "https://collectionapi.metmuseum.org/public/collection/v1/objects/" + id
		b, e := fetch.get(ctx, raw, 2<<20)
		if e != nil {
			s.Deferred = append(s.Deferred, "Met "+id+": "+e.Error())
			if fetch.blocked["collectionapi.metmuseum.org"] {
				s.Deferred = append(s.Deferred, fmt.Sprintf("Met stopped with %d selected records unrequested", len(ids)-i-1))
				break
			}
			continue
		}
		at := time.Now().UTC()
		if e = save(filepath.Join(filepath.Dir(out), "captures", "met-"+id+".json"), map[string]any{"url": raw, "retrieved_at": at, "sha256": hash(b), "response": json.RawMessage(b)}); e != nil {
			return e
		}
		var m map[string]any
		if e = json.Unmarshal(b, &m); e != nil {
			return e
		}
		add(mm[id], ingest.NormalizeMet(m), at)
		if i%20 == 0 {
			fmt.Printf("Met selected highlight metadata checked: %d/%d\n", i+1, len(ids))
		}
	}
	if len(s.Entries) > 700 {
		return errors.New("selected batch exceeds bound")
	}
	if e = save(out, s); e != nil {
		return e
	}
	allowed := 0
	for _, x := range s.Entries {
		if !x.Candidate.HasImage && x.Work.ImageAllowed() {
			allowed++
		}
	}
	b, e := os.ReadFile(out)
	if e != nil {
		return e
	}
	fmt.Printf("Staged %d entries, %d permitted missing images, %d deferrals. SHA256 %s. No database writes or image downloads.\n", len(s.Entries), allowed, len(s.Deferred), hash(b))
	return nil
}

func main() {
	mode := flag.String("mode", "audit", "audit, stage, preview, apply")
	root := flag.String("root", "../..", "project root")
	out := flag.String("out", "", "new audit, selection or receipt path")
	input := flag.String("selection", "", "reviewed selection for preview/apply")
	pin := flag.String("sha256", "", "reviewed selection SHA256")
	baseline := flag.String("baseline", "", "Prior read-only image preservation audit")
	flag.Parse()
	if *out == "" {
		log.Fatal("-out required")
	}
	cfg, e := pgxpool.ParseConfig(config.Load().DatabaseURL)
	if e != nil {
		log.Fatal(e)
	}
	local := func(h string) bool {
		return h == "localhost" || h == "127.0.0.1" || h == "::1" || strings.HasPrefix(h, "/")
	}
	if !local(cfg.ConnConfig.Host) {
		log.Fatal("local DB only")
	}
	for _, f := range cfg.ConnConfig.Fallbacks {
		if !local(f.Host) {
			log.Fatal("remote fallback denied")
		}
	}
	ctx := context.Background()
	p, e := pgxpool.NewWithConfig(ctx, cfg)
	if e != nil {
		log.Fatal(e)
	}
	defer p.Close()
	switch *mode {
	case "audit-image-focus":
		e = auditImageFocus(ctx, p, *root, *out, *baseline, *input)
	case "stage-image-focus-smk":
		e = stageSMKReviewed(ctx, p, *root, *out, "content/imports/image-focus-20260912/smk", imageFocusSMKPicks)
	case "stage-athens-icon":
		e = stageAthensIcon(ctx, p, *root, *out)
	case "stage-karlsruhe-next":
		e = stageKarlsruheBatch(ctx, p, *root, *out, "popular-karlsruhe-next")
	case "stage-karlsruhe":
		e = stageKarlsruhe(ctx, p, *root, *out)
	case "stage-pinakothek-durer":
		e = stagePinakothekPicks(ctx, p, *root, *out, durerImagePicks)
	case "stage-pinakothek":
		e = stagePinakothek(ctx, p, *root, *out)
	case "stage-nivaagaard":
		e = stageNivaagaard(ctx, p, *root, *out)
	case "stage-poldi-commons":
		e = stagePoldiCommons(ctx, p, *root, *out)
	case "stage-popular-cycle":
		e = stageCoveragePicks(ctx, p, *root, *out, popularCyclePicks)
	case "preview-nationalmuseum-date", "apply-nationalmuseum-date":
		e = reviewNationalmuseumDate(ctx, p, *root, *out, *mode == "apply-nationalmuseum-date")
	case "stage-popular-smk":
		e = stagePopularSMK(ctx, p, *root, *out)
	case "stage-smk-matisse":
		e = stageSMKReviewed(ctx, p, *root, *out, "content/imports/popular-resume-20260911-1852/smk-matisse", smkMatissePicks)
	case "stage-impressionist-followup-a":
		e = stageCoveragePicks(ctx, p, *root, *out, impressionistFollowupPicks[:50])
	case "stage-impressionist-followup-b":
		e = stageCoveragePicks(ctx, p, *root, *out, impressionistFollowupPicks[50:])
	case "stage-chicago-popular":
		e = stageChicago(ctx, p, *out)
	case "stage-popular-images-a":
		e = stageCoveragePicks(ctx, p, *root, *out, popularImagePicks[:50])
	case "stage-popular-images-b":
		e = stageCoveragePicks(ctx, p, *root, *out, popularImagePicks[50:])
	case "stage-round2":
		e = stageRoundTwo(ctx, p, *root, *out)
	case "stage-coverage":
		e = stageCoverage(ctx, p, *root, *out)
	case "preview-coverage", "apply-coverage":
		e = applyCoverage(ctx, p, *root, *input, *pin, *out, *mode == "apply-coverage")
	case "audit":
		e = audit(ctx, p, *out)
	case "stage":
		e = stage(ctx, p, *root, *out)
	case "preview", "apply":
		e = apply(ctx, p, *root, *input, *pin, *out, *mode == "apply")
	default:
		e = errors.New("invalid mode")
	}
	if e != nil {
		log.Fatal(e)
	}
}
