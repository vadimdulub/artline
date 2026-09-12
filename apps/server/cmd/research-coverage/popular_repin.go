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

type repinFact struct {
	ID, SHA, Title, Date, Acc, Size string
	First, Last                     int
}

var repinFacts = []repinFact{
	{"zh_4056", "b88433088842232d78b6a9f22aeeb011bf07498cee9ac2907c112d47523cc113", "Barge Haulers on the Volga", "1870–1873", "Ж-4056", "131,5 x 281", 1870, 1873},
	{"zh-4063", "a62a8a3dbb04953befd7ef28723bcd674f135c4577bd57cf5e07c31dfa3dd861", "Self-Portrait", "1878", "Ж-4063", "60,5 x 49,6", 1878, 1878},
	{"zh-4045", "165eaed96671c0b4d6bb4de05c383d1ef5b2fb95d5d516e4ff5d2229408a4acd", "On a Turf Bench", "1876", "Ж-4045", "36 x 55,5", 1876, 1876},
	{"zh-4086", "be547dec3800beade90b96c04b88e0904cdaed9401adb9d380bf142429a15e7c", "Portrait of Vera Repina", "1876", "Ж-4086", "59 x 49", 1876, 1876},
	{"zh_4050", "79f7cd35f7a4142744ae70dbead59ba106c3c21d8a0afa8462f1a665adbc409f", "The Raising of Jairus’s Daughter", "1871", "Ж-4050", "229 х 382", 1871, 1871},
}

func repinField(s, pattern string) string {
	m := regexp.MustCompile(pattern).FindAllStringSubmatch(s, -1)
	if len(m) != 1 {
		return ""
	}
	return athensText(m[0][1])
}
func verifyRepinFact(s string, f repinFact) error {
	start := strings.Index(s, `<div class="work__card--right">`)
	if start < 0 {
		return fmt.Errorf("missing primary museum object card")
	}
	s = s[start:]
	fields := map[string]string{
		`(?s)<div class="work__author">(.*?)</div>`:      "Repin I. E.",
		`(?s)<div class="work__desc">(.*?)</div>`:        "1844, Chuguyev (Kharkiv Province) - 1930, Kuokkala (Finland)",
		`(?s)<h2 class="work__title">(.*?)</h2>`:         f.Title,
		`(?s)<p class="period" title="Period">(.*?)</p>`: f.Date,
		`(?s)<span title="Material">(.*?)</span>`:        "oil on canvas",
		`(?s)<span title="Size">(.*?)</span>`:            f.Size,
		`(?s)<li title="Inventory number">(.*?)</li>`:    f.Acc,
	}
	for pattern, expected := range fields {
		if repinField(s, pattern) != expected {
			return fmt.Errorf("%s fact mismatch: %s", f.ID, pattern)
		}
	}
	return nil
}
func assemblePopularRepin(ctx context.Context, root, out string) error {
	index, err := localAuthors(ctx)
	if err != nil {
		return err
	}
	artists := index[authorityKey("Ilya Repin")]
	if len(artists) != 1 || artists[0].QID != "Q172911" || artists[0].Birth == nil || *artists[0].Birth != 1844 || artists[0].Death == nil || *artists[0].Death != 1930 {
		return fmt.Errorf("Repin authority/lifespan mismatch")
	}
	cohort, err := popularNGCohort(ctx)
	if err != nil {
		return err
	}
	artistID := ""
	for _, a := range cohort {
		if a.QID == "Q172911" {
			artistID = a.ID
		}
	}
	if artistID == "" {
		return fmt.Errorf("Repin no longer popular")
	}
	p, err := pgxpool.New(ctx, config.Load().DatabaseURL)
	if err != nil {
		return err
	}
	defer p.Close()
	s := newSelection("popular-repin")
	s.AccessedOn = "2026-09-11"
	key, slug := "popular-repin-russian-museum", "state-russian-museum"
	s.Museums[key] = map[string]string{"id": key, "name": "State Russian Museum", "country": "RU", "city": "Saint Petersburg", "data_url": "https://rusmuseumvrm.ru/collections/painting/index.php?lang=en", "data_route": "Five individually selected direct Repin painting notices. Factual fields only, not a site/database copy.", "rights": "Factual metadata only. Museum images require a written request and permission; none downloaded.", "rights_url": "https://rusmuseumvrm.ru/terms/index.php?lang=en"}
	s.Definitions[key] = map[string]string{"Host": "rusmuseumvrm.ru", "Slug": slug, "Source": key, "Website": "https://rusmuseum.ru/"}
	s.Crosswalk["Repin I. E.|1844–1930"] = map[string]string{"qid": "Q172911", "local_name": "Ilya Repin", "source_author": "https://rusmuseumvrm.ru/reference/classifier/author/repin_ie/index.php?lang=en", "basis": "Reviewed full painter identity and matching lifespan. Not an initials-only automatic authority join."}
	decisions := []map[string]string{}
	for _, f := range repinFacts {
		file := filepath.Join(root, "content/imports/popular-europe-session-20260911/repin-notices", f.ID+".html")
		if err = verify(file); err != nil {
			return err
		}
		sha, _, e := hashFile(file)
		if e != nil || sha != f.SHA {
			return fmt.Errorf("Repin snapshot changed")
		}
		b, e := os.ReadFile(file)
		if e != nil {
			return e
		}
		if e = verifyRepinFact(string(b), f); e != nil {
			return e
		}
		url := "https://rusmuseumvrm.ru/data/collections/painting/19_20/" + f.ID + "/index.php?lang=en"
		precision := "exact"
		if f.First != f.Last {
			precision = "range"
		}
		d := creationDate{f.First, f.Last, precision}
		if !dateEligible(d) || creatorDateConflict(artists[0], d, "painting") {
			return fmt.Errorf("date invalid")
		}
		var existing int
		err = p.QueryRow(ctx, `SELECT count(*) FROM artworks WHERE id IN (
 SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=$1 OR scheme=$2 AND external_id=$3)
 UNION SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=$1
 UNION SELECT a.id FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug=$4 AND a.accession_number=$3
)`, url, "european-"+key+"-object", f.Acc, slug).Scan(&existing)
		if err != nil {
			return err
		}
		reason := "eligible"
		if existing > 0 {
			reason = "existing exact source/accession preserved"
		} else {
			err = p.QueryRow(ctx, `SELECT count(*) FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=$1 AND lower(regexp_replace(a.title,'[^[:alnum:]]','','g'))=lower(regexp_replace($2,'[^[:alnum:]]','','g'))`, artistID, f.Title).Scan(&existing)
			if err != nil {
				return err
			}
			if existing > 0 {
				reason = "same-painter title identity requires reconciliation"
			}
		}
		decisions = append(decisions, map[string]string{"artist": "Ilya Repin", "title": f.Title, "url": url, "accession": f.Acc, "decision": reason, "image": "deferred: written reproduction permission required"})
		s.Decisions[reason]++
		if reason != "eligible" {
			continue
		}
		description := fmt.Sprintf("%s — Ilya Repin. %s.\n\nOil on canvas; dimensions recorded as %s in the museum notice. Inventory %s.\n\nDocumented collection: State Russian Museum, Saint Petersburg. This is not a current-display assertion; the source warns that gallery placement may have changed.\n\n[Official object notice](%s), accessed 11 September 2026. Only factual catalogue fields are retained here. Images require separate written permission: https://rusmuseumvrm.ru/terms/index.php?lang=en .", f.Title, f.Date, f.Size, f.Acc, url)
		s.Works = append(s.Works, map[string]any{"painter": "Q172911", "title": f.Title, "institution": key, "accession": f.Acc, "url": url, "source_object_id": f.Acc, "source_publisher": "State Russian Museum", "date_display": f.Date, "creation_date": d, "attribution_role": "primary", "work_type": "painting", "medium": "oil on canvas", "dimensions": f.Size, "description_md": description, "source_raw": map[string]string{"snapshot_sha256": sha, "url": url, "scope": "selected factual fields only; no essay or image"}, "notes": "Verified direct attribution, exact inventory and current museum catalogue connection. No image, ownership, display or masterpiece inference."})
	}
	if err = save(filepath.Join(out, "decisions.json"), decisions); err != nil {
		return err
	}
	return s.write(out)
}
