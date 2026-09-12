package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

type poldiFact struct {
	File, SHA, Slug, Artist, QID, Heading, Title, Alias, Date, Medium, Size, Acc, Note string
	DateValue                                                                          creationDate
}

var poldiFacts = []poldiFact{
	{"piero-nicholas", "1fe47d91289e3268a99e4130877ea831d69c5b70908f43bc4b07ce545fe49b11", "san-nicola-da-tolentino", "Piero della Francesca", "Q5822", "Piero della Francesca, 1415-1420/1492", "Saint Nicholas of Tolentino", "San Nicola da Tolentino", "1454 - 1469", "Oil on panel", "139.4 cm x 59.2 cm", "0445", "One surviving panel of the dispersed Sant'Agostino polyptych, not the entire altarpiece. The notice supplies the polyptych commission/execution interval; no invented precise year. Source artist birth range differs from local biography; no artist dates changed.", creationDate{1454, 1469, "range"}},
	{"bellini-pietatis", "1f37637e6e84a37a46843773b00d36bccdb9fa0f2fa9a54c50a0e96a5d2f3fb0", "imago-pietatis", "Giovanni Bellini", "Q17169", "Giovanni Bellini, 1430-1516", "Imago Pietatis", "", "ca. 1457", "Tempera on panel", "50 cm x 40.4 cm", "1587", "Exact early Bellini panel; not another Pieta version or a Mantegna work. No current-display claim taken from the room description.", creationDate{1457, 1457, "circa"}},
}

func verifyPoldi(s string, f poldiFact) error {
	url := "https://museopoldipezzoli.it/en/scopri/collezioni/capolavori/opera/" + f.Slug + "/"
	if !strings.Contains(s, `rel="canonical" href="`+url+`"`) {
		return fmt.Errorf("Poldi canonical mismatch")
	}
	for field, want := range map[string]string{"Author": f.Heading, "Date": f.Date, "Material and technique": f.Medium, "Measures": f.Size, "Acquisition": "Gian Giacomo Poldi Pezzoli bequest, 1879", "Inventory number": f.Acc} {
		m := regexp.MustCompile(`(?s)<p>`+regexp.QuoteMeta(field)+`</p>\s*<h6[^>]*>(.*?)</h6>`).FindAllStringSubmatch(s, -1)
		if len(m) != 1 || athensText(m[0][1]) != want {
			return fmt.Errorf("Poldi %s field changed", field)
		}
	}
	var headings []string
	for _, m := range regexp.MustCompile(`(?s)<h1\b[^>]*>(.*?)</h1>`).FindAllStringSubmatch(s, -1) {
		headings = append(headings, athensText(m[1]))
	}
	if len(headings) != 1 || headings[0] != f.Title {
		return fmt.Errorf("Poldi primary title mismatch")
	}
	return nil
}

func assemblePoldi(ctx context.Context, root, out string) error {
	index, err := localAuthors(ctx)
	if err != nil {
		return err
	}
	cohort, err := popularNGCohort(ctx)
	if err != nil {
		return err
	}
	popular := map[string]string{}
	for _, a := range cohort {
		popular[a.QID] = a.ID
	}
	p, err := pgxpool.New(ctx, config.Load().DatabaseURL)
	if err != nil {
		return err
	}
	defer p.Close()
	s := newSelection("popular-poldi")
	s.AccessedOn = "2026-09-11"
	key, slug := "popular-poldi-museum", "museo-poldi-pezzoli"
	s.Museums[key] = map[string]string{"id": key, "name": "Museo Poldi Pezzoli", "city": "Milan", "country": "IT", "data_url": "https://museopoldipezzoli.it/en/scopri/collezioni/capolavori/", "data_route": "Two exact manually reviewed factual notices, not catalogue scraping.", "rights": "Factual metadata only; essays not copied and museum image permission unresolved.", "rights_url": "https://museopoldipezzoli.it/en/"}
	s.Definitions[key] = map[string]string{"Host": "museopoldipezzoli.it", "Slug": slug, "Source": key, "Website": "https://museopoldipezzoli.it/en/"}
	decisions := []map[string]any{}
	for _, f := range poldiFacts {
		path := filepath.Join(root, "content/imports/popular-resume-20260911-1852/poldi", f.File+".html")
		if err = verify(path); err != nil {
			return err
		}
		sha, _, e := hashFile(path)
		if e != nil || sha != f.SHA {
			return fmt.Errorf("Poldi snapshot mismatch")
		}
		b, e := os.ReadFile(path)
		if e != nil {
			return e
		}
		if e = verifyPoldi(string(b), f); e != nil {
			return e
		}
		a := index[authorityKey(f.Artist)]
		if len(a) != 1 || a[0].QID != f.QID || popular[f.QID] == "" || !dateEligible(f.DateValue) || creatorDateConflict(a[0], f.DateValue, "painting") {
			return fmt.Errorf("Poldi creator/date gate")
		}
		url := "https://museopoldipezzoli.it/en/scopri/collezioni/capolavori/opera/" + f.Slug + "/"
		itURL := strings.Replace(url, "/en/", "/", 1)
		var n int
		err = p.QueryRow(ctx, `SELECT count(*) FROM artworks a WHERE
 EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND rtrim(e.canonical_url,'/') IN (rtrim($1,'/'),rtrim($2,'/')))
 OR EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id AND rtrim(c.source_url,'/') IN(rtrim($1,'/'),rtrim($2,'/')))
 OR (a.current_institution_id=(SELECT id FROM institutions WHERE slug=$3) AND ltrim(a.accession_number,'0')=ltrim($4,'0'))`, url, itURL, slug, f.Acc).Scan(&n)
		if err != nil {
			return err
		}
		reason := "eligible"
		if n > 0 {
			reason = "existing exact object preserved"
		} else {
			if err = p.QueryRow(ctx, athensTitleCollisionSQL, f.Title, f.Alias, popular[f.QID]).Scan(&n); err != nil {
				return err
			}
			if n > 0 {
				reason = "same-title identity requires reconciliation"
			}
		}
		decisions = append(decisions, map[string]any{"artist": f.Artist, "title": f.Title, "accession": f.Acc, "url": url, "decision": reason, "notes": f.Note, "image": "deferred: no explicit reusable museum-image licence"})
		s.Decisions[reason]++
		if reason != "eligible" {
			continue
		}
		s.addAuthor(f.Artist, "", a[0])
		aliases := []string{}
		if f.Alias != "" {
			aliases = append(aliases, f.Alias)
		}
		desc := fmt.Sprintf("%s — %s. %s.\n\n%s; %s. Inventory %s.\n\nDocumented holding: Museo Poldi Pezzoli, Milan, Italy. %s\n\n[Official object notice](%s), accessed 11 September 2026. Factual fields only; museum essay and image not reproduced. Collection association is not an ownership, current-display or masterpiece claim.", f.Title, f.Artist, f.Date, f.Medium, f.Size, f.Acc, f.Note, url)
		s.Works = append(s.Works, map[string]any{"painter": f.QID, "title": f.Title, "aliases": aliases, "institution": key, "accession": f.Acc, "url": url, "source_object_id": f.Acc, "source_publisher": "Museo Poldi Pezzoli", "date_display": f.Date, "creation_date": f.DateValue, "attribution_role": "primary", "work_type": "painting", "medium": f.Medium, "dimensions": f.Size, "description_md": desc, "notes": f.Note, "source_raw": map[string]string{"url": url, "snapshot_sha256": sha, "scope": "individually reviewed factual fields only"}})
	}
	if err = save(filepath.Join(out, "decisions.json"), decisions); err != nil {
		return err
	}
	return s.write(out)
}
