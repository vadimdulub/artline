package ingest

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

const pradoGoogleSelection = "https://www.museodelprado.es/en/whats-on/new/14-masterpieces-from-the-museo-del-prado-in/220f2fe9-beec-44a2-afdb-8c67ff37256c"
const pradoEducationSelection = "https://www.museodelprado.es/en/whats-on/exhibition/didactic-exhibition-the-prado-in-albuquerque/494d6f01-d05a-4263-86c5-ee6441dd05f7"
const commonsPDPolicy = "https://commons.wikimedia.org/wiki/Commons:Reuse_of_PD-Art_photographs"

// Human-reviewed object crosswalk. Museum dates take precedence over conflicting
// Wikidata/Commons dates; source strings and uncertainty remain intact.
type PradoSelection struct {
	QID       string `json:"qid"`
	ArtistQID string `json:"artist_qid"`
	Accession string `json:"accession"`
	Title     string `json:"title"`
	URL       string `json:"url"`
	First     *int   `json:"first"`
	Last      *int   `json:"last"`
	Date      string `json:"date"`
	Precision string `json:"precision"`
	Medium    string `json:"medium"`
	Selection string `json:"selection"`
	Note      string `json:"note"`
}

func pradoSelectionURL(s string) bool {
	return s == pradoGoogleSelection || s == pradoEducationSelection
}

func claimValues(e wdEntity, property string) []any {
	var out []any
	for _, claim := range e.Claims[property] {
		if value(claim, "rank") == "deprecated" {
			continue
		}
		snak, _ := claim["mainsnak"].(map[string]any)
		if value(snak, "snaktype") != "value" {
			continue
		}
		dv, _ := snak["datavalue"].(map[string]any)
		out = append(out, dv["value"])
	}
	return out
}
func hasClaim(e wdEntity, property, want string) bool {
	for _, v := range claimValues(e, property) {
		if s, ok := v.(string); ok && s == want {
			return true
		}
		if m, ok := v.(map[string]any); ok && value(m, "id") == want {
			return true
		}
	}
	return false
}

func normalizePrado(item PradoSelection, e wdEntity) (Work, error) {
	if e.ID != item.QID || !hasClaim(e, "P170", item.ArtistQID) || len(claimValues(e, "P170")) != 1 || !hasClaim(e, "P195", "Q160112") || !hasClaim(e, "P217", item.Accession) {
		return Work{}, fmt.Errorf("Prado authority/creator/collection/accession conflict: %s", item.Title)
	}
	for _, claim := range e.Claims["P170"] {
		if value(claim, "rank") != "deprecated" {
			if q, _ := claim["qualifiers"].(map[string]any); len(q) > 0 {
				return Work{}, fmt.Errorf("qualified attribution requires review: %s", item.Title)
			}
		}
	}
	selection := pradoGoogleSelection
	reason := "Named in the Prado's 2009 selection of fourteen masterpieces for Google Earth and its one-hour visitor route. Historical selection, not current display evidence."
	if item.Selection == "education-2018" {
		selection = pradoEducationSelection
		reason = "The Prado selected a reproduction of this original for its 2018 educational masterpiece exhibition. This is a designation of the original, not a claim that the original travelled or is currently on view."
	} else if item.Selection != "google-2009" {
		return Work{}, fmt.Errorf("unknown Prado selection")
	}
	w := Work{Source: "prado", ID: item.Accession, Accession: item.Accession, Title: item.Title, URL: item.URL, APIURL: "https://www.wikidata.org/wiki/" + item.QID, ArtistQID: item.ArtistQID,
		First: item.First, Last: item.Last, Date: item.Date, Precision: item.Precision, Type: "painting", Medium: item.Medium, Highlight: true, SelectionURL: selection, SelectionReason: reason + " " + item.Note,
		Raw: map[string]any{"reviewed_prado_record": item, "wikidata": e, "metadata_method": "Museum facts transcribed from public indexed official records; direct museum HTML access returned 403. Identity cross-checked with Wikidata. No museum prose or image-bank assets copied."}}
	if w.Eligible() != "eligible" {
		return Work{}, fmt.Errorf("Prado content gate: %s", w.Eligible())
	}
	return w, nil
}

type commonsInfo struct {
	URL            string `json:"url"`
	ThumbURL       string `json:"thumburl"`
	DescriptionURL string `json:"descriptionurl"`
	Metadata       map[string]struct {
		Value any `json:"value"`
	} `json:"extmetadata"`
}

func (i commonsInfo) text(k string) string { v, _ := i.Metadata[k].Value.(string); return v }
func commonsPublicDomain(i commonsInfo) bool {
	cats := i.text("Categories")
	return i.text("LicenseShortName") == "Public domain" && i.text("UsageTerms") == "Public domain" && strings.EqualFold(i.text("Copyrighted"), "false") && i.text("Restrictions") == "" && (strings.Contains(cats, "PD-Art") || strings.Contains(cats, "PD-old-100"))
}
func pradoImageAllowed(w Work) bool {
	u, err := url.Parse(w.ImageURL)
	if err != nil || u.Scheme != "https" || u.User != nil || u.Port() != "" || (u.Hostname() != "upload.wikimedia.org" && u.Hostname() != "thumb.wikimedia.org") || !strings.HasPrefix(u.Path, "/wikipedia/commons/") {
		return false
	}
	page, err := url.Parse(w.ImageSourceURL)
	if err != nil || page.Scheme != "https" || page.Hostname() != "commons.wikimedia.org" || !strings.HasPrefix(page.Path, "/wiki/File:") {
		return false
	}
	var info commonsInfo
	if json.Unmarshal(rawJSON(w.Raw["commons"]), &info) != nil {
		return false
	}
	return w.Rights == "public_domain" && w.ImagePolicyURL == commonsPDPolicy && commonsPublicDomain(info) && info.ThumbURL == w.ImageURL && info.DescriptionURL == w.ImageSourceURL
}

func (c *Client) pradoImage(ctx context.Context, w *Work, e wdEntity) error {
	images := claimValues(e, "P18")
	if len(images) == 0 {
		return fmt.Errorf("no authority-linked image")
	}
	name, ok := images[0].(string)
	if !ok || len(name) > 500 {
		return fmt.Errorf("invalid image title")
	}
	api := "https://commons.wikimedia.org/w/api.php?" + url.Values{"action": {"query"}, "format": {"json"}, "titles": {"File:" + name}, "prop": {"imageinfo"}, "iiprop": {"url|extmetadata"}, "iiurlwidth": {"1200"}, "maxlag": {"5"}}.Encode()
	var result struct {
		Query struct {
			Pages map[string]struct {
				Title string        `json:"title"`
				Info  []commonsInfo `json:"imageinfo"`
			} `json:"pages"`
		} `json:"query"`
		Error any `json:"error"`
	}
	if _, err := c.JSON(ctx, api, &result); err != nil {
		return err
	}
	if result.Error != nil || len(result.Query.Pages) != 1 {
		return fmt.Errorf("Commons image identity unavailable")
	}
	for _, p := range result.Query.Pages {
		if p.Title != "File:"+name || len(p.Info) != 1 || !commonsPublicDomain(p.Info[0]) {
			return fmt.Errorf("Commons reproduction needs rights review")
		}
		info := p.Info[0]
		w.ImageURL, w.ImageSourceURL, w.ImagePolicyURL, w.ImageProvider = info.ThumbURL, info.DescriptionURL, commonsPDPolicy, "Wikimedia Commons"
		w.Rights = "public_domain"
		w.Credit = "Faithful reproduction via Wikimedia Commons; file-specific public-domain notice (PD-Art). Original held at Museo Nacional del Prado."
		w.Raw["commons"] = info
		w.Raw["commons_api"] = api
		w.SourceSnapshotAt = c.snapshotTime(api)
	}
	if !w.ImageAllowed() {
		return fmt.Errorf("Commons image failed import allowlist")
	}
	return nil
}

func RunPrado(ctx context.Context, c *Client, s Store, o Options, log func(...any)) (runErr error) {
	raw, err := os.ReadFile(filepath.Join(o.Root, "content", "curation", "prado-highlights.json"))
	if err != nil {
		return err
	}
	var items []PradoSelection
	if err = json.Unmarshal(raw, &items); err != nil {
		return err
	}
	if len(items) == 0 || len(items) > 25 {
		return fmt.Errorf("Prado manifest must contain 1–25 reviewed objects")
	}
	ids := []string{}
	seen := map[string]bool{}
	for _, item := range items {
		if !regexp.MustCompile(`^Q[1-9][0-9]*$`).MatchString(item.QID) || seen[item.Accession] {
			return fmt.Errorf("invalid or duplicate Prado identity")
		}
		ids = append(ids, item.QID)
		seen[item.Accession] = true
	}
	entities, err := c.wdEntities(ctx, ids, "labels|claims")
	if err != nil {
		return err
	}
	var job, sid, institution string
	if o.Apply {
		sid, err = s.Source(ctx, "prado")
		if err != nil {
			return err
		}
		job, err = s.Job(ctx, sid, "prado-v1:"+o.Run+":"+checksum(raw), map[string]any{"manifest_sha256": checksum(raw), "works": len(items), "images": o.Images})
		if err != nil {
			return err
		}
		defer func() {
			state := "needs_review"
			if runErr != nil {
				state = "failed"
			}
			s.Finish(context.Background(), job, state, runErr)
		}()
		institution, err = s.Institution(ctx, "prado", sid)
		if err != nil {
			return err
		}
	}
	created, images := 0, 0
	for _, item := range items {
		w, e := normalizePrado(item, entities[item.QID])
		if e != nil {
			return e
		}
		var p Painter
		p.QID = item.ArtistQID
		if err = s.Pool.QueryRow(ctx, `SELECT a.id::text,a.display_name FROM external_identifiers ei JOIN artists a ON a.id=ei.entity_id WHERE ei.entity_type='artist' AND ei.scheme='wikidata' AND ei.external_id=$1 AND a.status<>'archived'`, p.QID).Scan(&p.ID, &p.Name); err != nil {
			return fmt.Errorf("missing painter for %s: %w", item.Title, err)
		}
		// Rights metadata is reproducible even without downloading images.
		note := "Image download not requested."
		imageErr := c.pradoImage(ctx, &w, entities[item.QID])
		if imageErr != nil {
			note = imageErr.Error()
			log("Image metadata deferred: ", item.Title, ": ", imageErr)
		}
		if !o.Apply {
			log("Eligible: ", item.Title, "; image allowed: ", w.ImageAllowed())
			continue
		}
		var img *ImageFile
		if o.Images && imageErr == nil {
			exists, e := s.ExistingMedia(ctx, w)
			if e != nil {
				return e
			}
			if !exists {
				file, e := c.DownloadImage(ctx, w, filepath.Join(o.Root, "apps", "web", "public", "assets", "artworks", "imported"))
				if e != nil {
					note = e.Error()
					log("Image deferred: ", item.Title, ": ", e)
				} else {
					img = &file
					note = "Public-domain image verified."
				}
			} else {
				note = "Existing verified image preserved; no new download."
			}
		}
		fresh, e := s.Work(ctx, job, sid, institution, p, w, img, note)
		if e != nil {
			return e
		}
		if fresh {
			created++
		}
		if img != nil {
			images++
		}
		if err = s.Checkpoint(ctx, job, w); err != nil {
			return err
		}
		log(item.Title, " — ", note)
	}
	log(fmt.Sprintf("Prado selection: %d reviewed works; %d new artworks; %d new local images", len(items), created, images))
	report := map[string]any{"run": o.Run, "selected": len(items), "created": created, "images": images, "completed_at": time.Now().UTC(), "manifest_sha256": checksum(raw), "applied": o.Apply}
	return writeNew(filepath.Join(o.Root, "content", "imports", o.Run, "prado-report-"+time.Now().UTC().Format("20060102T150405.000000000Z")+".json"), rawJSON(report))
}
