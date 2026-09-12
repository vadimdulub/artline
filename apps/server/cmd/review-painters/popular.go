package main

import (
	"bytes"
	"context"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type popularWork struct {
	Work
	Sources         []string
	NGAObject       string
	HoldingEvidence bool
}
type imageLead struct {
	Count int
	URL   string
	Open  bool
}

func popularCreditRole(w Work, artistID string) string {
	for _, credit := range w.Credits {
		if credit.ID == artistID {
			return credit.Role
		}
	}
	return "unresolved attribution"
}

func popularNGALeads(root string) (map[string]imageLead, error) {
	path := filepath.Join(root, "content/imports/painter-coverage-images-20260910/published_images.csv")
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	if digest(b) != "addeee9d135a7bfd7dcac4cfcc4a30d43059b54a635105cff477fc117907e51c" {
		return nil, fmt.Errorf("unreviewed NGA feed")
	}
	r := csv.NewReader(bytes.NewReader(b))
	header, err := r.Read()
	if err != nil {
		return nil, err
	}
	col := map[string]int{}
	for i, k := range header {
		col[k] = i
	}
	for _, k := range []string{"viewtype", "depictstmsobjectid", "iiifurl", "openaccess"} {
		if _, ok := col[k]; !ok {
			return nil, fmt.Errorf("missing feed column")
		}
	}
	out := map[string]imageLead{}
	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}
		if row[col["viewtype"]] != "primary" {
			continue
		}
		id := row[col["depictstmsobjectid"]]
		l := out[id]
		l.Count++
		l.URL = row[col["iiifurl"]]
		l.Open = row[col["openaccess"]] == "1"
		out[id] = l
	}
	return out, nil
}

// Offline popular-only inventory; one repeatable-read traversal, never a public
// endpoint or a query issued once for each artwork. Does not mark research done.
func exportPopular(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	smk, err := popularSMKResearch(root)
	if err != nil {
		return err
	}
	leads, err := popularNGALeads(root)
	if err != nil {
		return err
	}
	var captured struct {
		Works []struct {
			URL, ImageURL string
			Image         string `json:"image_url"`
		}
	}
	b, err := os.ReadFile(filepath.Join(root, "content/imports/popular-marmottan-20260911/popular-facts.json"))
	if err != nil {
		return err
	}
	if err = json.Unmarshal(b, &captured); err != nil {
		return err
	}
	marmottan := map[string]string{}
	chicago := map[string]string{}
	chicagoDownloadState := "Download not attempted."
	if rb, re := os.ReadFile(filepath.Join(root, "output/popular-chicago-followup/apply.json")); re == nil {
		var r struct {
			SelectionSHA string
			Results      []struct{ ImageOutcome string }
		}
		if err = json.Unmarshal(rb, &r); err != nil {
			return err
		}
		if r.SelectionSHA != "279e5c67c3d3fc13735f8e71dfe8b886c4116a801a32bf63dda2e6e78325be10" {
			return fmt.Errorf("Chicago receipt identity changed")
		}
		allDeferred := len(r.Results) == 46
		for _, x := range r.Results {
			allDeferred = allDeferred && x.ImageOutcome == "download_deferred"
		}
		if allDeferred {
			chicagoDownloadState = "Download deferred: image server returned HTTP 403; remaining requests paused. No file added."
		}
	} else if !os.IsNotExist(re) {
		return re
	}
	cb, ce := os.ReadFile(filepath.Join(root, "output/popular-chicago-followup/selection.json"))
	if ce == nil {
		if digest(cb) != "279e5c67c3d3fc13735f8e71dfe8b886c4116a801a32bf63dda2e6e78325be10" {
			return fmt.Errorf("unreviewed Chicago lead selection")
		}
		var s struct {
			Entries []struct{ Page, ImageURL string }
		}
		if err = json.Unmarshal(cb, &s); err != nil {
			return err
		}
		for _, e := range s.Entries {
			chicago[e.Page] = e.ImageURL
		}
	} else if !os.IsNotExist(ce) {
		return ce
	}
	for _, w := range captured.Works {
		marmottan[w.URL] = w.Image
	}
	// The separately captured deposit is included in the reviewed selection.
	var selected struct {
		Works []struct {
			URL string
			Raw struct {
				Image string `json:"image_url"`
			} `json:"source_raw"`
		}
	}
	b, err = os.ReadFile(filepath.Join(root, "docs/research/popular-artists-20260911/marmottan-v2/chunk-001.json"))
	if err != nil {
		return err
	}
	if err = json.Unmarshal(b, &selected); err != nil {
		return err
	}
	for _, w := range selected.Works {
		marmottan[w.URL] = w.Raw.Image
	}
	if err = newSnapshot(out); err != nil {
		return err
	}
	if err = os.Mkdir(filepath.Join(out, "painters"), 0755); err != nil {
		return err
	}
	tx, err := p.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, `SET LOCAL statement_timeout='120s'`); err != nil {
		return err
	}
	var expectedWorks, expectedArtists, expectedLinks int
	if err = tx.QueryRow(ctx, `SELECT count(DISTINCT aa.artwork_id),count(DISTINCT d.artist_id),count(aa.artwork_id) FROM artist_discovery_selection d LEFT JOIN artwork_artists aa ON aa.artist_id=d.artist_id WHERE d.is_popular`).Scan(&expectedWorks, &expectedArtists, &expectedLinks); err != nil {
		return err
	}
	// This is an explicitly bounded offline cohort report, not the scalable
	// full-catalogue export or an API endpoint. Refuse growth beyond its budget.
	if expectedLinks > 50000 || expectedArtists > 200 {
		return fmt.Errorf("popular cohort exceeds offline report budget; use the streaming full ledger")
	}
	rows, err := tx.Query(ctx, `SELECT a.id::text,a.display_name,a.slug FROM artists a JOIN artist_discovery_selection d ON d.artist_id=a.id WHERE d.is_popular ORDER BY a.display_name,a.id`)
	if err != nil {
		return err
	}
	artists := []*Artist{}
	byID := map[string]*Artist{}
	for rows.Next() {
		a := &Artist{}
		if err = rows.Scan(&a.ID, &a.Name, &a.Slug); err != nil {
			return err
		}
		artists = append(artists, a)
		if a.Slug == "" || filepath.Base(a.Slug) != a.Slug || strings.Contains(a.Slug, "..") {
			return fmt.Errorf("unsafe artist filename")
		}
		byID[a.ID] = a
	}
	rows.Close()
	if err = rows.Err(); err != nil {
		return err
	}
	if len(artists) != expectedArtists {
		return fmt.Errorf("incomplete popular artist scope")
	}
	// Retain every source identity, not a title-only match or just one provider.
	query := strings.Replace(ledgerWorksSQL, "ORDER BY coalesce(aa.artist_id::text,''),a.id", `WHERE EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=aa.artist_id AND d.is_popular) ORDER BY coalesce(aa.artist_id::text,''),a.id`, 1)
	query = strings.Replace(query, "'ID',a.id,'Title'", `'Sources',coalesce((SELECT jsonb_agg(DISTINCT canonical_url) FILTER(WHERE canonical_url IS NOT NULL) FROM external_identifiers WHERE entity_type='artwork' AND entity_id=a.id),'[]'),
 'NGAObject',coalesce((SELECT min(external_id) FROM external_identifiers WHERE entity_type='artwork' AND entity_id=a.id AND scheme='european-nga-object'),''),
 'HoldingEvidence',EXISTS(SELECT 1 FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.institution_id=a.current_institution_id AND l.claim_type='holding' AND l.review_state='accepted'),
 'ID',a.id,'Title'`, 1)
	rows, err = tx.Query(ctx, query)
	if err != nil {
		return err
	}
	file, err := os.OpenFile(filepath.Join(out, "artworks.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	defer file.Close()
	enc := json.NewEncoder(file)
	seen := map[string]bool{}
	groups := map[string][]popularWork{}
	counts := map[string]int{"artists": len(artists)}
	// Retain only this bounded popular cohort, not the entire database. Markdown
	// contains per-artist tables; the browser never receives this inventory.
	for rows.Next() {
		var id string
		var raw []byte
		if err = rows.Scan(&id, &raw); err != nil {
			return err
		}
		var w popularWork
		if err = json.Unmarshal(raw, &w); err != nil {
			return err
		}
		w.ImageCheck = imageCheck(root, w.Work)
		groups[id] = append(groups[id], w)
		if !seen[w.ID] {
			seen[w.ID] = true
			counts["artworks"]++
			if w.Image != "" {
				counts["images_present"]++
			}
			if strings.HasPrefix(w.ImageCheck, "file verified") {
				counts["images_verified"]++
			}
			if w.HoldingEvidence {
				counts["accepted_holding_evidence"]++
			}
			if w.NGAObject != "" {
				counts["nga_image_feed_checked"]++
			}
			if err = enc.Encode(w); err != nil {
				return err
			}
		}
	}
	rows.Close()
	if err = rows.Err(); err != nil {
		return err
	}
	if counts["artworks"] != expectedWorks {
		return fmt.Errorf("incomplete popular artwork inventory")
	}
	if err = tx.Commit(ctx); err != nil {
		return err
	}
	if err = file.Close(); err != nil {
		return err
	}
	var index strings.Builder
	fmt.Fprintf(&index, "# Popular artists: museum and image inventory\n\nSnapshot %s. %d currently popular artists; %d distinct database artworks.\n\nEvery linked artwork is listed, including qualified attributions and non-painting works already in the catalogue. Popularity was not changed. Museum association is not proof of ownership or current display. This is not an exhaustive catalogue raisonné or a completed research round.\n\nThe initial Marmottan pass added 232 works and enriched one existing record. Later additions and image batches are documented in the linked findings. Individual source checks are identified per artwork. Other source links are existing database evidence unless explicitly identified below. NGA image candidates were checked against its official pinned 10 September 2026 feed; permission must be revalidated before a future download. Image availability does not confer masterpiece status.\n\n[Research findings and remaining source candidates](../FINDINGS.md) · [Machine-readable inventory](artworks.jsonl)\n\n| Painter | Artworks | Local images | File/evidence checks passed |\n|---|---:|---:|---:|\n", time.Now().UTC().Format(time.RFC3339), len(artists), counts["artworks"])
	for _, a := range artists {
		works := groups[a.ID]
		sort.Slice(works, func(i, j int) bool {
			if works[i].Institution != works[j].Institution {
				return works[i].Institution < works[j].Institution
			}
			if works[i].Date != works[j].Date {
				return works[i].Date < works[j].Date
			}
			return works[i].ID < works[j].ID
		})
		var page strings.Builder
		fmt.Fprintf(&page, "# %s\n\n[Popular artists index](../PAINTERS.md) · Artist ID: `%s`\n\n- [x] All %d current database artworks inventoried.\n- [ ] Museum discovery across the artist's entire oeuvre complete.\n- [ ] Independent artwork/attribution/image research complete for every work.\n\nImage file checks do not complete art-historical review. `Source pending` means this pass has not independently revisited that record. Holding evidence is a collection association, not a current-display claim.\n\n| Artwork / ID | Date / scope | Museum / accession | Sources / holding evidence | Picture investigation |\n|---|---|---|---|---|\n", md(a.Name), a.ID, len(works))
		for _, w := range works {
			if w.Image != "" {
				a.Pictures++
			}
			if strings.HasPrefix(w.ImageCheck, "file verified") {
				a.VerifiedImages++
			}
			links := []string{}
			research := "Source pending; follow the exact museum object link."
			for _, u := range w.Sources {
				links = append(links, link("Catalogue", u))
				if status, ok := nationalmuseumResearch[u]; ok {
					research = status
				}
				if status, ok := smk[u]; ok {
					research = status
				}
				if imageURL, ok := chicago[u]; ok {
					research = "Chicago API identity and public-domain flag checked; " + link("image candidate", imageURL) + ". " + chicagoDownloadState
				}
				if imageURL, ok := marmottan[u]; ok {
					research = "Marmottan notice checked: no artwork image supplied."
					if imageURL != "" && !strings.Contains(imageURL, "no-picture.png") {
						research = "Marmottan notice checked; " + link("image candidate", imageURL) + ". Reuse permission not established; not downloaded."
					}
				}
			}
			if w.NGAObject != "" {
				l := leads[w.NGAObject]
				switch {
				case l.Count != 1:
					research = "NGA feed checked: primary image missing or ambiguous."
				case !l.Open:
					research = "NGA feed checked: primary image not cleared for open reuse."
				default:
					research = "NGA feed checked: " + link("open-access candidate", l.URL) + "; not downloaded unless a local file is listed."
				}
			}
			if w.Image != "" {
				research = md(w.ImageCheck) + "; " + fmt.Sprintf("%d bytes", w.Bytes) + "; [local file](<../../../../../apps/web/public" + w.Image + ">). " + research
			}
			if w.NGAObject != "" && w.Image != "" {
				research = strings.ReplaceAll(research, "not downloaded unless a local file is listed.", "local file listed above; no additional download needed.")
			}
			fmt.Fprintf(&page, "| %s<br><code>%s</code><br>Attribution: %s | %s / %s | %s / %s | %s; accepted holding: %t | %s |\n", md(w.Title), w.ID, md(popularCreditRole(w.Work, a.ID)), md(w.Date), md(w.Scope), md(w.Institution), md(w.Accession), strings.Join(links, " · "), w.HoldingEvidence, research)
		}
		if len(works) == 0 {
			page.WriteString("\nNo works recorded. This is a research gap, not a completed painter.\n")
		}
		if err = save(filepath.Join(out, "painters", a.Slug+".md"), []byte(page.String())); err != nil {
			return err
		}
		fmt.Fprintf(&index, "| [%s](painters/%s.md) | %d | %d | %d |\n", md(a.Name), a.Slug, len(works), a.Pictures, a.VerifiedImages)
	}
	if err = save(filepath.Join(out, "PAINTERS.md"), []byte(index.String())); err != nil {
		return err
	}
	if err = save(filepath.Join(out, "summary.json"), append(encode(counts), '\n')); err != nil {
		return err
	}
	fmt.Println(string(encode(counts)))
	return nil
}
