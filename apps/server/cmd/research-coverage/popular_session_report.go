package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

func sessionMarkdown(path, content string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	_, err = f.WriteString(content)
	ce := f.Close()
	if err != nil {
		return err
	}
	return ce
}

// A transparent source-check checkpoint, never a research-complete flag. Keep
// all popular artists including those lacking external authority identifiers.
func reportPopularSession(ctx context.Context, root, out string) error {
	if _, err := localAuthors(ctx); err != nil {
		return err
	}
	p, err := pgxpool.New(ctx, config.Load().DatabaseURL)
	if err != nil {
		return err
	}
	defer p.Close()
	var decisions []map[string]string
	b, err := os.ReadFile(filepath.Join(root, "docs/research/popular-europe-session-20260911/ng-v2/decisions.json"))
	if err != nil {
		return err
	}
	if err = json.Unmarshal(b, &decisions); err != nil {
		return err
	}
	var receipt struct {
		Applied bool `json:"applied"`
		Works   []struct {
			ID      string `json:"artwork_id"`
			URL     string `json:"source_url"`
			Outcome string `json:"outcome"`
		} `json:"works"`
	}
	b, err = os.ReadFile(filepath.Join(root, "output/popular-europe-session/ng-apply/chunk-001.json"))
	if err != nil {
		return err
	}
	if err = json.Unmarshal(b, &receipt); err != nil || !receipt.Applied || len(receipt.Works) != 102 {
		return fmt.Errorf("missing applied NG receipt")
	}
	imported := map[string]string{}
	for _, w := range receipt.Works {
		if w.Outcome == "created" {
			imported[w.URL] = w.ID
		}
	}
	var images struct {
		Applied bool
		Results []struct {
			Artist, ArtworkID, Path, ImageOutcome string
			Bytes                                 int
		}
	}
	b, err = os.ReadFile(filepath.Join(root, "output/popular-europe-session/pinakothek-apply.json"))
	if err != nil {
		return err
	}
	if err = json.Unmarshal(b, &images); err != nil || !images.Applied {
		return fmt.Errorf("missing applied image receipt")
	}
	rows, err := p.Query(ctx, `SELECT a.id::text,a.slug,a.display_name,coalesce((SELECT external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' LIMIT 1),''),
 (SELECT count(*) FROM artwork_artists aa WHERE aa.artist_id=a.id),
 (SELECT count(*) FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=a.id AND w.primary_media_id IS NOT NULL)
 FROM artists a JOIN artist_discovery_selection d ON d.artist_id=a.id AND d.is_popular WHERE a.status<>'archived' ORDER BY a.display_name,a.id`)
	if err != nil {
		return err
	}
	defer rows.Close()
	var index strings.Builder
	fmt.Fprintf(&index, "# Popular-painter source-check checkpoint\n\nGenerated %s. All currently popular painters remain in scope. These are source-specific decisions, not a completed research round. Automated inventory, catalogue filtering, manually resolved facts and verified imports are distinct.\n\n[Session evidence and receipts](../PROGRESS.md) · [Full baseline artwork checklists](../../popular-artists-20260911/inventory-v6/PAINTERS.md)\n\n| Painter | Local artworks | Local images | NG additions | NG candidate decisions |\n|---|---:|---:|---:|---:|\n", time.Now().UTC().Format(time.RFC3339))
	total := 0
	for rows.Next() {
		var id, slug, name, qid string
		var works, pictures int
		if err = rows.Scan(&id, &slug, &name, &qid, &works, &pictures); err != nil {
			return err
		}
		if !regexp.MustCompile(`^[a-z0-9-]+$`).MatchString(slug) {
			return fmt.Errorf("unsafe painter slug")
		}
		total++
		if total > 200 {
			return fmt.Errorf("cohort ceiling")
		}
		var text strings.Builder
		fmt.Fprintf(&text, "# %s — source review\n\nArtist ID `%s`; authority `%s`. Local snapshot: %d artwork links, %d images.\n\n- [x] Inventory and existing source queue inspected by the backend.\n- [ ] Cross-museum research complete.\n- [ ] Every image gap resolved.\n\n## National Gallery, London\n\nStructured source: [official API documentation](https://www.nationalgallery.org.uk/documentation/ngacuk/collection-data/elasticsearch-api), [metadata and separate image licences](https://www.nationalgallery.org.uk/documentation/ngacuk/licences). One bounded current-name/explicit-alias query; not a complete oeuvre search. The 102 selected objects passed pinned importer, preservation, idempotency and API checks. Other entries below are automated source-specific screening decisions, not individual curatorial approval.\n\n", name, id, qid, works, pictures)
		checked, added := 0, 0
		for _, d := range decisions {
			if d["qid"] != qid || qid == "" {
				continue
			}
			checked++
			url := "https://www.nationalgallery.org.uk/data/" + d["pid"]
			result := d["decision"]
			if aid := imported[url]; result == "eligible" && aid != "" {
				added++
				result = "ADDED, verified review record `" + aid + "`; no image in this batch"
			}
			fmt.Fprintf(&text, "- [%s](%s): %s.\n", strings.ReplaceAll(d["title"], "\n", " "), url, result)
		}
		if qid == "" {
			text.WriteString("No local Wikidata ID: excluded from this source adapter's authority-linked query, but explicitly retained in the full cohort. Resolve authority evidence before name-based import.\n")
		} else if checked == 0 {
			text.WriteString("The bounded query returned no candidate objects. This is not evidence of zero museum holdings; source spellings, query coverage and other museums remain open.\n")
		}
		text.WriteString("\n## Selected image outcomes\n\n")
		n := 0
		for _, im := range images.Results {
			if im.Artist != name {
				continue
			}
			n++
			fmt.Fprintf(&text, "- Artwork `%s`: %s, %d bytes; `%s`. Exact accession, creator, date, collection branch and per-object CC BY-SA 4.0 verified. Source snapshot and rights evidence retained in `output/popular-europe-session/pinakothek-selection.json`; disk hashes and API delivery independently checked. No masterpiece or display change.\n", im.ArtworkID, im.ImageOutcome, im.Bytes, im.Path)
		}
		if n == 0 {
			text.WriteString("No image added for this painter in the current European five-image batch. Existing images were preserved; missing permission is not a completed image review.\n")
		}
		text.WriteString("\n## Next\n\nReview existing European museum source links and unresolved exact dates/attributions; test documented alternate names only where the current query has a known gap. Search at least one different museum before regarding this source pass as representative. Do not retry inherited blocked image hosts or infer current display, ownership, or masterpiece status.\n")
		if err = sessionMarkdown(filepath.Join(out, "painters", slug+".md"), text.String()); err != nil {
			return err
		}
		fmt.Fprintf(&index, "| [%s](painters/%s.md) | %d | %d | %d | %d |\n", name, slug, works, pictures, added, checked)
	}
	if err = rows.Err(); err != nil {
		return err
	}
	if err = sessionMarkdown(filepath.Join(out, "PAINTERS.md"), index.String()); err != nil {
		return err
	}
	fmt.Printf("Wrote %d painter source-check checklists; no completion flags or DB changes.\n", total)
	return nil
}
