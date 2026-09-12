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

type nivaFact struct {
	Slug, SHA, Artist, QID, Heading, Title, Date, MediumLine, Medium, Size, Acc, Acquisition string
	First, Last                                                                              int
	Precision                                                                                string
}

var nivaFacts = []nivaFact{
	{"anguissola-sofonisba", "750efa857255da538ffb7d0d58fe31d95541f41b601f6f0a1293e7857fa781be", "Sofonisba Anguissola", "Q236038", "Sofonisba Anguissola", "Portrait Group with the Artist’s Father Amilcare Anguissola and her siblings Minerva and Asdrubale", "c. 1559", "Oil on canvas, 157 x 122 cm.", "Oil on canvas", "157 x 122 cm", "0001NMK", "Bestowed, 1908", 1559, 1559, "circa"},
	{"bellini-giovanni", "0645b4b6576af6623a18c7f79a0721992dedc1b2605fb68ea206a97b0509b6e1", "Giovanni Bellini", "Q17169", "Giovanni Bellini", "Portrait of a Young Man", "c. 1490", "Oil on panel. 29,5 x 23 cm.", "Oil on panel", "29.5 x 23 cm", "0003NMK", "Bestowed, 1908", 1490, 1490, "circa"},
	{"rijn-rembrandt-harmensz-van", "a0217c7f567d1516e30b127b07d2ee8f6501b5c4b52b70bd2b96aebaa11734bf", "Rembrandt van Rijn", "Q5598", "Rembrandt Harmensz van Rijn", "Portrait of a 39-year-old Woman", "1632", "Oil on panel, 76,5 × 58,5 cm", "Oil on panel", "76.5 x 58.5 cm", "0047NMK", "Bestowed, 1908", 1632, 1632, "exact"},
	{"gentileschi-artemisia", "1db49e308b9f6631c68b5d75b0a85f78bfb400f57f61d3f458d53e86bee916f8", "Artemisia Gentileschi", "Q212657", "Artemisia Gentileschi", "Susanna and the Elders", "1644-48", "Oil on canvas, 200 x 150 cm", "Oil on canvas", "200 x 150 cm", "0261NMK", "Acquired in 2025 with support from the New Carlsberg Foundation and Aage og Johanne Louis-Hansens Fond", 1644, 1648, "range"},
	{"lucas-cranach-the-elder", "8a6c8c3445cdaa9c7fb52b410d06bdc039eddb1d6175d5fc76c4df43e42d642e", "Lucas Cranach the Elder", "Q191748", "Lucas Cranach the Elder", "Caritas", "1535", "Oil on panel, 50 x 34 cm.", "Oil on panel", "50 x 34 cm", "0017NMK", "Bestowed, 1908", 1535, 1535, "exact"},
	{"lorrain-claude", "d48bde5d41bbb99aa8963529645146560d78769ce6f5acbf276fbb16ca714fba", "Claude Lorrain", "Q214074", "Claude Lorrain", "Landscape with the Flight into Egypt", "c. 1646", "Oil on canvas, 100 x 130 cm.", "Oil on canvas", "100 x 130 cm", "0015NMK", "Bestowed, 1908", 1646, 1646, "circa"},
}

func nivaHeading(s string) []string {
	var found []string
	for _, m := range regexp.MustCompile(`(?s)<h6>(.*?)</h6>`).FindAllStringSubmatch(s, -1) {
		if !strings.Contains(m[1], "Inventory number:") {
			continue
		}
		if found != nil {
			return nil
		}
		for _, line := range regexp.MustCompile(`<br\s*/?>`).Split(m[1], -1) {
			found = append(found, athensText(line))
		}
	}
	return found
}
func verifyNivaFact(s string, f nivaFact) error {
	url := "https://nivaagaard.dk/en/the-collection/" + f.Slug + "/"
	if !strings.Contains(s, `<link rel="canonical" href="`+url+`" />`) {
		return fmt.Errorf("wrong canonical page")
	}
	got := nivaHeading(s)
	want := []string{f.Heading, f.Title + ", " + f.Date, f.MediumLine, "Inventory number: " + f.Acc, f.Acquisition}
	if len(got) != len(want) {
		return fmt.Errorf("ambiguous primary object heading")
	}
	for i := range want {
		// Formatting spans can leave whitespace before punctuation, not new facts.
		if strings.ReplaceAll(got[i], " ,", ",") != want[i] {
			return fmt.Errorf("%s primary field %d changed: %q", f.Acc, i, got[i])
		}
	}
	if !strings.Contains(s, `href="https://nivaagaard.dk/en/fri-download/"`) || !strings.Contains(s, ">PUBLIC DOMAIN</span>") {
		return fmt.Errorf("object public-domain link missing")
	}
	return nil
}

func assembleNivaagaard(ctx context.Context, root, out string) error {
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
	s := newSelection("popular-nivaagaard")
	s.AccessedOn = "2026-09-11"
	key, slug := "popular-nivaagaard-museum", "nivaagaards-malerisamling"
	s.Museums[key] = map[string]string{"id": key, "name": "The Nivaagaard Collection", "country": "DK", "city": "Nivå", "data_url": "https://nivaagaard.dk/en/the-collection/", "data_route": "Six individually reviewed factual object notices, not a whole-collection extraction.", "rights": "Factual catalogue fields only. Each selected object links the museum public-domain image policy; image acquisition is separately reviewed.", "rights_url": "https://nivaagaard.dk/en/fri-download/"}
	s.Definitions[key] = map[string]string{"Host": "nivaagaard.dk", "Slug": slug, "Source": key, "Website": "https://nivaagaard.dk/en/"}
	decisions := []map[string]any{}
	for _, f := range nivaFacts {
		file := filepath.Join(root, "content/imports/popular-resume-20260911-1852/nivaagaard", f.Slug+".html")
		if err = verify(file); err != nil {
			return err
		}
		sha, _, e := hashFile(file)
		if e != nil || sha != f.SHA {
			return fmt.Errorf("changed Nivaagaard snapshot")
		}
		b, e := os.ReadFile(file)
		if e != nil {
			return e
		}
		if e = verifyNivaFact(string(b), f); e != nil {
			return e
		}
		a := index[authorityKey(f.Artist)]
		d := creationDate{f.First, f.Last, f.Precision}
		if len(a) != 1 || a[0].QID != f.QID || popular[f.QID] == "" || !dateEligible(d) || creatorDateConflict(a[0], d, "painting") {
			return fmt.Errorf("authority/popularity/date mismatch: %s", f.Artist)
		}
		url := "https://nivaagaard.dk/en/the-collection/" + f.Slug + "/"
		var exact int
		err = p.QueryRow(ctx, `SELECT count(*) FROM artworks WHERE id IN (
 SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=$1 OR (canonical_url LIKE '%nivaagaard.dk/%' AND external_id=$2))
 UNION SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=$1
 UNION SELECT id FROM artworks WHERE accession_number=$2
)`, url, f.Acc).Scan(&exact)
		if err != nil {
			return err
		}
		reason := "eligible"
		if exact > 0 {
			reason = "existing identity/accession preserved"
		}
		collisions := []map[string]string{}
		if exact == 0 {
			rows, e := p.Query(ctx, `SELECT a.id::text,a.title,coalesce(a.accession_number,''),coalesce(i.slug,'') FROM artworks a LEFT JOIN institutions i ON i.id=a.current_institution_id
 WHERE (lower(regexp_replace(a.title,'[^[:alnum:]]','','g'))=lower(regexp_replace($1,'[^[:alnum:]]','','g')) OR lower(regexp_replace(coalesce(a.alternate_title,''),'[^[:alnum:]]','','g'))=lower(regexp_replace($1,'[^[:alnum:]]','','g')))
 AND (EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id AND aa.artist_id=$2) OR NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id)) LIMIT 101`, f.Title, popular[f.QID])
			if e != nil {
				return e
			}
			for rows.Next() {
				var id, title, acc, museum string
				if e = rows.Scan(&id, &title, &acc, &museum); e != nil {
					rows.Close()
					return e
				}
				decision := "unresolved title identity"
				// Same generic title and approximate date, distinct current museum
				// objects: NGA323, Kress1939 vs Nivaagaard0003NMK, bestowed1908.
				if f.Acc == "0003NMK" && id == "e0bb35b4-a280-4e68-a529-a4d2aca8288f" && acc == "1939.1.182" && museum == "national-gallery-of-art" {
					decision = "reviewed distinct NGA323 Kress provenance; not Nivaagaard0003NMK"
				} else {
					reason = "defer title collision"
				}
				collisions = append(collisions, map[string]string{"id": id, "title": title, "accession": acc, "museum": museum, "decision": decision})
			}
			e = rows.Err()
			rows.Close()
			if e != nil {
				return e
			}
			if len(collisions) > 100 {
				return fmt.Errorf("title collision review cap")
			}
		}
		note := "Museum holding documented by current collection notice; no ownership, current display or masterpiece inferred."
		if f.QID == "Q236038" {
			note += " Painter birth date varies between source1532 and local1535; full identity is reviewed, no artist dates changed."
		}
		if f.QID == "Q5598" {
			note += " Museum records the hand and prayer book as a later artist's addition; the painting is not claimed entirely untouched."
		}
		decisions = append(decisions, map[string]any{"artist": f.Artist, "title": f.Title, "url": url, "accession": f.Acc, "decision": reason, "collisions": collisions, "notes": note})
		s.Decisions[reason]++
		if reason != "eligible" {
			continue
		}
		s.Crosswalk[f.Heading] = map[string]string{"qid": f.QID, "local_name": f.Artist, "source_author": url, "basis": "Individually reviewed full creator identity, not surname matching; source/local birth-date uncertainty retained in notes."}
		description := fmt.Sprintf("%s — %s. %s.\n\n%s; %s. Inventory %s.\n\nDocumented collection: The Nivaagaard Collection, Nivå, Denmark. %s\n\n[Official catalogue record](%s), accessed 11 September 2026. Factual catalogue details only; no museum essay reproduced.", f.Title, f.Artist, f.Date, f.Medium, f.Size, f.Acc, note, url)
		s.Works = append(s.Works, map[string]any{"painter": f.QID, "title": f.Title, "institution": key, "accession": f.Acc, "url": url, "source_object_id": f.Acc, "source_publisher": "The Nivaagaard Collection", "date_display": f.Date, "creation_date": d, "attribution_role": "primary", "work_type": "painting", "medium": f.Medium, "dimensions": f.Size, "description_md": description, "notes": note, "source_raw": map[string]string{"snapshot_sha256": sha, "url": url, "catalogue_acquisition": f.Acquisition, "scope": "selected factual fields only"}})
	}
	if err = save(filepath.Join(out, "decisions.json"), decisions); err != nil {
		return err
	}
	return s.write(out)
}
