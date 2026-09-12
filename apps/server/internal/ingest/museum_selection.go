package ingest

import (
	"context"
	"encoding/json"
	"fmt"
	"html"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

// These are bounded, human-reviewed crosswalks, not a general museum scraper.
// Image permission is deliberately NOT inferred from artwork age or a holding.
type MuseumSelection struct {
	QID          string   `json:"qid"`
	ArtistQID    string   `json:"artist_qid"`
	Accession    string   `json:"accession"`
	WDInventory  []string `json:"wd_inventory"`
	Title        string   `json:"title"`
	URL          string   `json:"url"`
	First        *int     `json:"first"`
	Last         *int     `json:"last"`
	Date         string   `json:"date"`
	Precision    string   `json:"precision"`
	Medium       string   `json:"medium"`
	Dimensions   string   `json:"dimensions"`
	Kind         string   `json:"selection_kind"`
	SelectionURL string   `json:"selection_url"`
	Reason       string   `json:"reason"`
	SourceChecks []string `json:"source_checks"`
	Note         string   `json:"note"`
}

type reviewedMuseum struct {
	Collection, Manifest, ImageDeferral string
	FetchOfficial                       bool
}

var reviewedMuseums = map[string]reviewedMuseum{
	"uffizi": {"Q51252", "uffizi-selection.json", "Image permission pending: the Uffizi specifies a separate reproduction authorization process, including for images already held by applicants. No museum or Commons image downloaded. https://www.uffizi.it/en/professional-services/publications", true},
	"mam":    {"Q3032842", "mam-highlights.json", "Image permission pending: no explicit reusable-image grant verified for this work. The museum's catalogue image is not an open licence. No image downloaded.", false},
}

func reviewedMuseumURL(key, raw string) bool {
	u, err := url.Parse(raw)
	if err != nil || u.Scheme != "https" || u.User != nil || u.Port() != "" || u.RawQuery != "" || u.Fragment != "" {
		return false
	}
	switch key {
	case "uffizi":
		return u.Hostname() == "www.uffizi.it" && regexp.MustCompile(`^/en/artworks/[a-z0-9-]+$`).MatchString(u.Path)
	case "mam":
		return raw == "https://mam.inba.gob.mx/destacadas.html"
	}
	return false
}

func reviewedMuseumSelectionURL(key, raw string) bool {
	return reviewedMuseumURL(key, raw) || (key == "uffizi" && raw == "https://www.uffizi.it/en/news/the-glorification-of-the-virgin-by-fra-angelico")
}

func normalizeMuseumSelection(key string, item MuseumSelection, e wdEntity) (Work, error) {
	def, ok := reviewedMuseums[key]
	qid := regexp.MustCompile(`^Q[1-9][0-9]*$`)
	if !ok || !qid.MatchString(item.QID) || !qid.MatchString(item.ArtistQID) || e.ID != item.QID || len(claimValues(e, "P170")) != 1 || !hasClaim(e, "P170", item.ArtistQID) || !hasClaim(e, "P195", def.Collection) {
		return Work{}, fmt.Errorf("museum authority/creator/collection conflict: %s", item.Title)
	}
	for _, c := range e.Claims["P170"] {
		if value(c, "rank") != "deprecated" {
			if q, _ := c["qualifiers"].(map[string]any); len(q) > 0 {
				return Work{}, fmt.Errorf("qualified attribution requires review: %s", item.Title)
			}
		}
	}
	for _, inventory := range item.WDInventory {
		if inventory == "" || !hasClaim(e, "P217", inventory) {
			return Work{}, fmt.Errorf("authority inventory changed: %s", item.Title)
		}
	}
	if item.Kind != "owner" && item.Kind != "museum" {
		return Work{}, fmt.Errorf("selection must distinguish museum and owner")
	}
	if !reviewedMuseumURL(key, item.URL) || !reviewedMuseumSelectionURL(key, item.SelectionURL) || len(item.SourceChecks) < 3 || strings.TrimSpace(item.Reason) == "" || strings.TrimSpace(item.Date) == "" {
		return Work{}, fmt.Errorf("incomplete reviewed source evidence: %s", item.Title)
	}
	for _, check := range item.SourceChecks {
		if strings.TrimSpace(check) == "" {
			return Work{}, fmt.Errorf("empty source check")
		}
	}
	switch item.Precision {
	case "exact", "circa", "range", "circa_range", "before", "after", "decade", "century":
	default:
		return Work{}, fmt.Errorf("date precision requires review")
	}
	w := Work{Source: key, ID: item.QID, ArtistQID: item.ArtistQID, Accession: item.Accession, Title: item.Title, URL: item.URL,
		APIURL: "https://www.wikidata.org/wiki/" + item.QID, First: item.First, Last: item.Last, Date: item.Date, Precision: item.Precision,
		Type: "painting", Medium: item.Medium, Dimensions: item.Dimensions, Highlight: item.Kind == "museum", SelectionKind: item.Kind,
		SelectionURL: item.SelectionURL, SelectionReason: item.Reason + " " + item.Note,
		Raw: map[string]any{"reviewed_museum_record": item, "wikidata": e, "image_deferral": def.ImageDeferral}}
	if w.Eligible() != "eligible" {
		return Work{}, fmt.Errorf("museum content gate: %s (%s)", item.Title, w.Eligible())
	}
	return w, nil
}

var htmlTags = regexp.MustCompile(`<[^>]*>`)

func checkMuseumPage(raw []byte, checks []string) error {
	// Only validate short, reviewed factual markers. Never copy museum essays.
	plain := strings.Join(strings.Fields(html.UnescapeString(htmlTags.ReplaceAllString(string(raw), " "))), " ")
	for _, check := range checks {
		if !strings.Contains(plain, check) {
			return fmt.Errorf("official page no longer contains reviewed marker %q", check)
		}
	}
	return nil
}

func RunReviewedMuseum(ctx context.Context, c *Client, s Store, o Options, log func(...any)) (runErr error) {
	key := o.OnlySource
	def, ok := reviewedMuseums[key]
	if !ok {
		return fmt.Errorf("unapproved reviewed museum")
	}
	raw, err := os.ReadFile(filepath.Join(o.Root, "content", "curation", def.Manifest))
	if err != nil {
		return err
	}
	var items []MuseumSelection
	if err = json.Unmarshal(raw, &items); err != nil {
		return err
	}
	if len(items) < 1 || len(items) > 25 {
		return fmt.Errorf("museum manifest must contain 1–25 reviewed objects")
	}
	ids, seen := []string{}, map[string]bool{}
	for _, item := range items {
		if !regexp.MustCompile(`^Q[1-9][0-9]*$`).MatchString(item.QID) || seen[item.QID] {
			return fmt.Errorf("invalid or duplicate museum identity")
		}
		seen[item.QID] = true
		ids = append(ids, item.QID)
	}
	entities, err := c.wdEntities(ctx, ids, "labels|claims")
	if err != nil {
		return err
	}
	// Preflight the whole small batch before any database writes.
	works, painters := make([]Work, 0, len(items)), make([]Painter, 0, len(items))
	for _, item := range items {
		w, e := normalizeMuseumSelection(key, item, entities[item.QID])
		if e != nil {
			return e
		}
		if def.FetchOfficial {
			body, e := c.Get(ctx, item.URL, 2<<20)
			if e != nil {
				return e
			}
			if e = checkMuseumPage(body, item.SourceChecks); e != nil {
				return fmt.Errorf("%s: %w", item.Title, e)
			}
			w.Raw["official_snapshot_sha256"] = checksum(body)
			w.Raw["official_snapshot_at"] = c.snapshotTime(item.URL)
			w.Raw["metadata_method"] = "Reviewed official museum facts, checked against the cached museum HTML and independent Wikidata creator/collection/inventory crosswalk."
		} else {
			w.Raw["metadata_method"] = "Official highlighted-work facts reviewed in the public indexed museum page on 2026-09-08. Direct HTML returned 403; no access restriction bypassed. Wikidata creator and collection independently checked."
		}
		var p Painter
		p.QID = item.ArtistQID
		if err = s.Pool.QueryRow(ctx, `SELECT a.id::text,a.display_name FROM external_identifiers ei JOIN artists a ON a.id=ei.entity_id WHERE ei.entity_type='artist' AND ei.scheme='wikidata' AND ei.external_id=$1 AND a.status<>'archived'`, p.QID).Scan(&p.ID, &p.Name); err != nil {
			return fmt.Errorf("missing painter for %s: %w", item.Title, err)
		}
		works, painters = append(works, w), append(painters, p)
		log("Eligible: ", item.Title, "; selection: ", item.Kind, "; image: pending permission")
	}
	created := 0
	if o.Apply {
		sid, err := s.Source(ctx, key)
		if err != nil {
			return err
		}
		job, err := s.Job(ctx, sid, "reviewed-museum-v1:"+key+":"+o.Run+":"+checksum(raw), map[string]any{"manifest_sha256": checksum(raw), "works": len(items), "images_requested": o.Images, "images_allowed": false})
		if err != nil {
			return err
		}
		defer func() {
			state := "needs_review"
			if runErr != nil {
				state = "failed"
			}
			if e := s.Finish(context.Background(), job, state, runErr); e != nil && runErr == nil {
				runErr = e
			}
		}()
		institution, err := s.Institution(ctx, key, sid)
		if err != nil {
			return err
		}
		for i, w := range works {
			fresh, e := s.Work(ctx, job, sid, institution, painters[i], w, nil, def.ImageDeferral)
			if e != nil {
				return e
			}
			if fresh {
				created++
			}
			if err = s.Checkpoint(ctx, job, w); err != nil {
				return err
			}
		}
	}
	log(fmt.Sprintf("%s: %d reviewed works; %d new artworks; 0 images (permission pending)", key, len(items), created))
	report := map[string]any{"run": o.Run, "source": key, "selected": len(items), "created": created, "images": 0, "image_deferral": def.ImageDeferral, "completed_at": time.Now().UTC(), "manifest_sha256": checksum(raw), "applied": o.Apply}
	return writeNew(filepath.Join(o.Root, "content", "imports", o.Run, key+"-report-"+time.Now().UTC().Format("20060102T150405.000000000Z")+".json"), rawJSON(report))
}
