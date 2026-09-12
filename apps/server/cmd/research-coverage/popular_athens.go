package main

import (
	"context"
	"fmt"
	"html"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

// A selected factual notice batch, not a website crawl or an image permission grant.
type athensFact struct {
	Slug, SHA, Artist, QID, Heading, Title, Translation, Date, Medium, Dimensions string
	Year                                                                          int
}

var athensFacts = []athensFact{
	{"kandinsky-wassily-both-striped", "d1bfa0a98264ef6efeadf32f6c98c7c54c4a11e7d29f52181e1e591da601d68e", "Wassily Kandinsky", "Q61064", "Wassily Kandinsky (1866 - 1944)", "Beide gestreift", "Both Striped", "1932", "Oil and gouache on board", "79.5 × 70 cm", 1932},
	{"klee-paul-dynamics-of-a-head", "80f79211d79eaba47da065c13aad14579c0a3eccbf0635409f2a8a06f6d2b021", "Paul Klee", "Q44007", "Paul Klee (1879 - 1940)", "Dynamik eines Kopfes", "Dynamics of a Head", "1934", "Oil on canvas", "65.5 × 50.5 cm", 1934},
	{"monet-claude-rouen-cathedral-pink-dominant", "2020dc1fe8dad6d0cda0caf2c3e1289b9a25b458c6ba2732c83dff3452e5d268", "Claude Monet", "Q296", "Claude Monet (1840 - 1926)", "La cathédrale de Rouen le matin (dominante rose)", "Rouen Cathedral in the Morning (Pink Dominant)", "1894", "Oil on canvas", "100.3 × 65.5 cm", 1894},
	{"ernst-max-while-the-earth-sleeps", "1204e724a7beb245297cdb8d95b7b9687687167184bcd8cd17c912651d9e4d79", "Max Ernst", "Q154842", "Max Ernst (1891 - 1976)", "Pendant que la Terre dort", "While the Earth Sleeps", "1956", "Oil on canvas", "89 × 116 cm", 1956},
	{"miro-joan-the-grasshopper", "1b93431426b205aa86aa18a567d45d60b87f42a6589e04c9993de70d225e51ad", "Joan Miró", "Q152384", "Joan Miró (1893 - 1983)", "La sauterelle", "The Grasshopper", "1926", "Oil on canvas", "114 × 147 cm", 1926},
}

func athensText(s string) string {
	s = regexp.MustCompile(`(?s)<!--.*?-->`).ReplaceAllString(s, "")
	s = regexp.MustCompile(`<[^>]*>`).ReplaceAllString(s, " ")
	return strings.Join(strings.Fields(html.UnescapeString(s)), " ")
}
func athensField(s, field string) string {
	m := regexp.MustCompile(`(?s)<(?:div|span) class="artwork__`+regexp.QuoteMeta(field)+`(?: [^"]*)?">(.*?)</(?:div|span)>`).FindAllStringSubmatch(s, -1)
	if len(m) != 1 {
		return ""
	}
	return athensText(m[0][1])
}
func verifyAthensFact(s string, f athensFact) error {
	url := "https://goulandris.gr/en/artwork/" + f.Slug
	if !strings.Contains(s, `<link rel="canonical" href="`+url+`"/>`) {
		return fmt.Errorf("canonical object mismatch")
	}
	for field, expected := range map[string]string{"artist": f.Heading, "title": f.Title, "original-title": f.Translation, "title-date": f.Date, "media": f.Medium, "dimensions": f.Dimensions, "info-exhibition-Building": "Basil & Elise Goulandris Foundation, Athens"} {
		if athensField(s, field) != expected {
			return fmt.Errorf("%s: %s changed or ambiguous", f.Slug, field)
		}
	}
	if f.Date != fmt.Sprint(f.Year) || !dateEligible(creationDate{f.Year, f.Year, "exact"}) {
		return fmt.Errorf("unreviewed date")
	}
	return nil
}

func assemblePopularAthens(ctx context.Context, root, out string, national bool) error {
	return assemblePopularAthensBatch(ctx, root, out, national, false)
}

func assemblePopularAthensBatch(ctx context.Context, root, out string, national, entombment bool) error {
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
	source, host, slug, name, website := "popular-goulandris", "goulandris.gr", "basil-elise-goulandris-athens", "Basil & Elise Goulandris Foundation, Athens", "https://goulandris.gr/en/visit/be-athens"
	if national {
		source, host, slug, name, website = "popular-athens-national", "www.nationalgallery.gr", "national-gallery-greece", "National Gallery – Alexandros Soutsos Museum", "https://www.nationalgallery.gr/en/"
	}
	if entombment {
		source = "popular-athens-entombment"
	}
	s := newSelection(source)
	s.AccessedOn = "2026-09-11"
	key := source + "-museum"
	s.Museums[key] = map[string]string{"id": key, "name": name, "country": "GR", "city": "Athens", "data_url": website, "data_route": "Individually selected factual object notices, exact title/creator/date/holding review. Not bulk extraction.", "rights": "Factual metadata only; no essays or images reproduced. Image reuse permission unresolved.", "rights_url": website}
	s.Definitions[key] = map[string]string{"Host": host, "Slug": slug, "Source": key, "Website": website}
	decisions := []map[string]string{}
	add := func(artist, qid, title, translation, acc, url, objectID, date, medium, dimensions, sha string, d creationDate) error {
		a := index[authorityKey(artist)]
		if len(a) != 1 || a[0].QID != qid || popular[qid] == "" || creatorDateConflict(a[0], d, "painting") || !dateEligible(d) {
			return fmt.Errorf("creator/popularity/lifespan/date gate: %s", artist)
		}
		var exact int
		err := p.QueryRow(ctx, `SELECT count(*) FROM artworks WHERE id IN (
 SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=$1 OR canonical_url=rtrim($1,'/') OR scheme=$2 AND external_id=$3)
 UNION SELECT entity_id FROM citations WHERE entity_type='artwork' AND (source_url=$1 OR source_url=rtrim($1,'/'))
 UNION SELECT a.id FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug=$4 AND a.accession_number=$5 AND $5<>''
)`, url, "european-"+key+"-object", objectID, slug, acc).Scan(&exact)
		if err != nil {
			return err
		}
		reason := "eligible"
		if exact > 0 {
			reason = "existing exact object preserved"
		} else {
			// Strong identifiers above are checked globally. Generic titles alone
			// are not identities: the reviewed global hits for Saint Peter are
			// other painters, and The Grasshopper hits are Pozzatti prints (1954).
			// Keep same-painter and unassigned-title cases pending reconciliation.
			err = p.QueryRow(ctx, athensTitleCollisionSQL, title, translation, popular[qid]).Scan(&exact)
			if err != nil {
				return err
			}
			if exact > 0 {
				reason = "same-title identity requires reconciliation"
			}
		}
		decisions = append(decisions, map[string]string{"artist": artist, "qid": qid, "title": title, "url": url, "date": date, "decision": reason, "image": "deferred: no verified reproduction licence"})
		s.Decisions[reason]++
		if reason != "eligible" {
			return nil
		}
		s.addAuthor(artist, "", a[0])
		description := fmt.Sprintf("%s — %s. %s.\n\nMedium: %s. Dimensions: %s.\n\nDocumented museum holding: %s. Museum affiliation is not ownership or a current-display claim.\n\n[Official object notice](%s), accessed 11 September 2026. Selected factual metadata only; image reuse permission remains unresolved.", title, artist, date, medium, dimensions, name, url)
		aliases := []string{}
		if translation != "" && translation != title {
			aliases = append(aliases, translation)
		}
		s.Works = append(s.Works, map[string]any{"painter": qid, "title": title, "aliases": aliases, "institution": key, "accession": acc, "url": url, "source_object_id": objectID, "source_publisher": name, "date_display": date, "creation_date": d, "attribution_role": "primary", "work_type": "painting", "medium": medium, "dimensions": dimensions, "description_md": description, "source_raw": map[string]string{"snapshot_sha256": sha, "url": url, "scope": "selected factual fields only; no narrative essay or image"}, "notes": "Exact source notice and whole-database dedup checked. No masterpiece, ownership or display inference. Empty accession means unpublished, not a fabricated museum number."})
		return nil
	}
	if entombment {
		path := filepath.Join(root, "content/imports/popular-resume-20260911-1852/athens-entombment/entombment.html")
		if err = verify(path); err != nil {
			return err
		}
		b, e := os.ReadFile(path)
		if e != nil {
			return e
		}
		sha, _, e := hashFile(path)
		if e != nil {
			return e
		}
		if e = verifyEntombment(b); e != nil {
			return e
		}
		if err = add("El Greco", "Q301", "The Entombment of Christ", "", "Π.9979", "https://www.nationalgallery.gr/en/artwork/the-entombment-of-christ/", "the-entombment-of-christ", "ca 1568-1570", "Oil and tempera on panel", "51.5 x 42.9 cm", sha, creationDate{1568, 1570, "circa_range"}); err != nil {
			return err
		}
	} else if national {
		path := filepath.Join(root, "content/imports/popular-europe-session-20260911/athens-preflight/nationalgallery-peter.html")
		sha, _, e := hashFile(path)
		if e != nil {
			return e
		}
		if e = verify(path); e != nil {
			return e
		}
		if sha != "2e5b642f15e26e9abfb6f01344827de975eeaaaaa06f071ea93e3bef3a8a4076" {
			return fmt.Errorf("St Peter snapshot changed")
		}
		b, e := os.ReadFile(path)
		if e != nil {
			return e
		}
		text := athensText(string(b))
		for _, v := range []string{"Theotokopoulos Domenicos (1541 - 1614)", "St. Peter, ca 1600-1607", "Oil on canvas, 68,5 x 53 cm", "Inv. Number Π.9027"} {
			if !strings.Contains(text, v) {
				return fmt.Errorf("St Peter fact changed: %s", v)
			}
		}
		if err = add("El Greco", "Q301", "St. Peter", "Saint Peter", "Π.9027", "https://www.nationalgallery.gr/en/artwork/st-peter/", "st-peter", "ca 1600-1607", "Oil on canvas", "68,5 x 53 cm", sha, creationDate{1600, 1607, "circa_range"}); err != nil {
			return err
		}
	} else {
		for _, f := range athensFacts {
			path := filepath.Join(root, "content/imports/popular-europe-session-20260911/athens-objects", f.Slug+".html")
			if err = verify(path); err != nil {
				return err
			}
			sha, _, e := hashFile(path)
			if e != nil || sha != f.SHA {
				return fmt.Errorf("reviewed Athens snapshot changed")
			}
			b, e := os.ReadFile(path)
			if e != nil {
				return e
			}
			if e = verifyAthensFact(string(b), f); e != nil {
				return e
			}
			if err = add(f.Artist, f.QID, f.Title, f.Translation, "", "https://goulandris.gr/en/artwork/"+f.Slug, f.Slug, f.Date, f.Medium, f.Dimensions, sha, creationDate{f.Year, f.Year, "exact"}); err != nil {
				return err
			}
		}
		for _, d := range []map[string]string{
			{"artist": "El Greco", "url": "https://goulandris.gr/en/artwork/el-greco-the-holy-face", "decision": "deferred: early-1580s interval needs explicit representation; no invented exact bounds"},
			{"artist": "Marc Chagall", "url": "https://goulandris.gr/en/artwork/chagall-marc-portrait-of-elise-goulandris", "decision": "deferred: collection member, explicitly not on display; exact current holding branch unresolved"},
			{"artist": "Pierre Bonnard", "url": "https://goulandris.gr/en/artwork/bonnard-pierre-getting-out-of-the-bath", "decision": "deferred: not in the current popular cohort; do not silently expand batch scope"},
		} {
			decisions = append(decisions, d)
			s.Decisions[d["decision"]]++
		}
	}
	if err = save(filepath.Join(out, "decisions.json"), decisions); err != nil {
		return err
	}
	return s.write(out)
}
