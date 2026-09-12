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

type durerFact struct {
	ID, SHA, Title, Acc, Date, Branch string
	First, Last                       int
	Precision                         string
}

var durerFacts = []durerFact{
	{"Y0GRY2XLRX", "3536bec1ece3cbdae06ed96cedf522ac9f430ef9b87c014eba4e89961365fbec", `Beweinung Christi ("Glimsche Beweinung")`, "704", "um 1500", "alte", 1500, 1500, "circa"},
	{"Pdxz0KvGw5", "58d6728f70d4cc687d54437dd5c83de7b6876f9b9f13cf45ae983ed5b5c429d9", "Maria als Schmerzensmutter", "709", "1495/98", "alte", 1495, 1498, "range"},
	{"QrLWeqA4NO", "b883a0415d782f780a8cb6ab9fd5d2b3ecc09abccc9b098073708ee65e6c4fe3", "Die Muttergottes mit der Nelke", "4772", "1516", "alte", 1516, 1516, "exact"},
	{"o5xrQgP47X", "2284223feb0d6f0fba503162323db7b9b2edcd6593edba729bafb2851d83d2db", "Bildnis eines jungen Mannes", "694", "1500", "alte", 1500, 1500, "exact"},
	{"k2xnBjAxPd", "2c8772a53e45b20174bfe1fa5bba4e90bc4cc7015a88423508afc326bac049fb", "Selbstmord der Lucretia", "705", "1518", "alte", 1518, 1518, "exact"},
	{"02LAWJX4yk", "d888a013cd2e3512f19ab7d97b7bece61ad14047c03227462733c5c79c6e2a28", "Herkules im Kampf mit den Harpyen", "5379", "1500", "gnm", 1500, 1500, "exact"},
	{"M0xyZ1VLpl", "0dba76ae87428045c557719745d1d57306483ac3f639008498a16037686d2fa0", "Bildnis Michael Wolgemut", "700", "1516", "gnm", 1516, 1516, "exact"},
	{"8MLv2rZLz3", "12b303aaf3c554c670bcc33657e6765435e3332aa70b17fda3bb394fc2e86319", "Bildnis Jakob Fugger der Reiche", "717", "um 1520", "augsburg", 1520, 1520, "circa"},
}

func museumHTMLFact(s, pattern string) string {
	m := regexp.MustCompile(pattern).FindAllStringSubmatch(s, -1)
	if len(m) != 1 {
		return ""
	}
	return strings.Join(strings.Fields(html.UnescapeString(m[0][1])), " ")
}
func durerFields(s string, f durerFact) (map[string]string, error) {
	start, end := strings.Index(s, `id="artwork-detailpage"`), strings.Index(s, "<!-- Rahmen -->")
	if start < 0 || end <= start {
		return nil, fmt.Errorf("missing primary artwork section")
	}
	s = s[start:end]
	if museumHTMLFact(s, `(?s)<h1 class='artwork__title'>\s*(.*?)\s*</h1>`) != f.Title+"," || museumHTMLFact(s, `(?s)class='artwork__artist'>\s*(.*?)\s*</a>`) != "Albrecht Dürer" || !strings.Contains(s, "<span class='artwork__dates'>"+f.Date+"</span>") || museumHTMLFact(s, `(?s)Inventarnummer\s*</div>\s*([^<]+)`) != f.Acc || !strings.Contains(s, `class="artwork__action action--creativecommons" href="https://creativecommons.org/licenses/by-sa/4.0/"`) || !strings.Contains(s, `/de/genre/malerei">Malerei</a>`) {
		return nil, fmt.Errorf("pinned direct-creator/object/date/licence/painting mismatch: %s", f.ID)
	}
	fields := map[string]string{}
	for name, label := range map[string]string{"medium": "Material / Technik / Bildträger", "dimensions": "Maße des Objekts", "collection": "Bestand"} {
		fields[name] = museumHTMLFact(s, `(?s)`+regexp.QuoteMeta(label)+`\s*</div>\s*([^<]+)`)
		if fields[name] == "" {
			return nil, fmt.Errorf("missing %s", name)
		}
	}
	expected := map[string]string{"alte": "Bayerische Staatsgemäldesammlungen – Alte Pinakothek München", "gnm": "Bayerische Staatsgemäldesammlungen (als Dauerleihgabe im Germanischen Nationalmuseum Nürnberg)", "augsburg": "Bayerische Staatsgemäldesammlungen – Staatsgalerie in der Katharinenkirche Augsburg"}
	if fields["collection"] != expected[f.Branch] {
		return nil, fmt.Errorf("holding/loan mapping changed")
	}
	return fields, nil
}

func assemblePopularDurer(ctx context.Context, root, out string) error {
	index, err := localAuthors(ctx)
	if err != nil {
		return err
	}
	a := index[authorityKey("Albrecht Dürer")]
	if len(a) != 1 || a[0].QID != "Q5580" {
		return fmt.Errorf("ambiguous artist")
	}
	cohort, err := popularNGCohort(ctx)
	if err != nil {
		return err
	}
	artistID := ""
	for _, p := range cohort {
		if p.QID == "Q5580" {
			artistID = p.ID
		}
	}
	if artistID == "" {
		return fmt.Errorf("artist not popular")
	}
	p, err := pgxpool.New(ctx, config.Load().DatabaseURL)
	if err != nil {
		return err
	}
	defer p.Close()
	museums := map[string]campaignMuseum{
		"alte":     {Name: "Alte Pinakothek", City: "Munich", Slug: "alte-pinakothek", Country: "DE", Website: "https://www.pinakothek.de/de/alte-pinakothek"},
		"gnm":      {Name: "Germanisches Nationalmuseum", City: "Nuremberg", Slug: "germanisches-nationalmuseum", Country: "DE", Website: "https://www.gnm.de"},
		"augsburg": {Name: "Staatsgalerie in der Katharinenkirche Augsburg", City: "Augsburg", Slug: "staatsgalerie-katharinenkirche-augsburg", Country: "DE", Website: "https://www.pinakothek.de/de/staatsgalerien"},
	}
	s := newSelection("popular-durer")
	s.AccessedOn = "2026-09-11"
	decisions := []map[string]string{}
	for _, f := range durerFacts {
		path := filepath.Join(root, "content/imports/popular-europe-session-20260911/durer/durer-"+f.ID+".html")
		if err = verify(path); err != nil {
			return err
		}
		sha, _, e := hashFile(path)
		if e != nil || sha != f.SHA {
			return fmt.Errorf("Dürer reviewed snapshot changed")
		}
		b, e := os.ReadFile(path)
		if e != nil {
			return e
		}
		facts, e := durerFields(string(b), f)
		if e != nil {
			return e
		}
		url := "https://www.sammlung.pinakothek.de/de/artwork/" + f.ID
		m := museums[f.Branch]
		key := s.Source + "-" + m.Slug
		var count int
		err = p.QueryRow(ctx, `SELECT count(*) FROM artworks WHERE id IN (
   SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=$1 OR canonical_url LIKE $1||'/%' OR scheme='european-alte-object' AND external_id=$2)
   UNION SELECT entity_id FROM citations WHERE entity_type='artwork' AND (source_url=$1 OR source_url LIKE $1||'/%')
   UNION SELECT a.id FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug=$3 AND a.accession_number=$2
  )`, url, f.Acc, m.Slug).Scan(&count)
		if err != nil {
			return err
		}
		reason := "eligible"
		if count > 0 {
			reason = "existing exact source/accession preserved"
		} else {
			err = p.QueryRow(ctx, `SELECT count(*) FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=$1 AND lower(regexp_replace(a.title,'[^[:alnum:]]','','g'))=lower(regexp_replace($2,'[^[:alnum:]]','','g'))`, artistID, f.Title).Scan(&count)
			if err != nil {
				return err
			}
			if count > 0 {
				reason = "same-artist title identity requires reconciliation"
			}
		}
		if reason == "eligible" {
			s.Museums[key] = map[string]string{"id": key, "name": m.Name, "country": "DE", "city": m.City, "data_url": url, "data_route": "Eight selected object notices, individually verified against pinned official metadata; source collection/loan branch retained.", "rights": "This object is individually marked CC BY-SA 4.0; images are selected and verified separately.", "rights_url": "https://www.sammlung.pinakothek.de/de/usage"}
			s.Definitions[key] = map[string]string{"Host": "www.sammlung.pinakothek.de", "Slug": m.Slug, "Source": key, "Website": m.Website}
			d := creationDate{f.First, f.Last, f.Precision}
			desc := fmt.Sprintf("%s — Albrecht Dürer. %s.\n\nMaterial / support: %s. Dimensions: %s.\n\nSource collection statement: %s. Accession %s. Collection affiliation or documented permanent loan, not current display.\n\n[Official object record](%s), accessed 11 September 2026. Factual metadata, individually licensed CC BY-SA 4.0. © Bayerische Staatsgemäldesammlungen.", f.Title, f.Date, facts["medium"], facts["dimensions"], facts["collection"], f.Acc, url)
			if f.Branch == "augsburg" {
				desc += "\n\nThe institution's current branch guide reports closure since spring 2022: https://www.pinakothek.de/de/staatsgalerien . The collection link is not a claim that the work is available to visit."
			}
			w := map[string]any{"painter": "Q5580", "title": f.Title, "institution": key, "accession": f.Acc, "url": url, "source_object_id": f.Acc, "source_publisher": "Bayerische Staatsgemäldesammlungen", "date_display": f.Date, "creation_date": d, "attribution_role": "primary", "work_type": "painting", "medium": facts["medium"], "dimensions": facts["dimensions"], "description_md": desc, "collection": facts["collection"], "source_raw": map[string]any{"html": string(b), "sha256": sha, "facts": facts}, "notes": "Selected exact official museum painting. Collection affiliation and permanent loan are distinct from ownership and display. No masterpiece inference."}
			if f.Branch == "gnm" {
				w["custody"] = "Permanent loan to Germanisches Nationalmuseum Nürnberg from Bayerische Staatsgemäldesammlungen, explicitly stated by the source."
			}
			s.Works = append(s.Works, w)
		}
		decisions = append(decisions, map[string]string{"title": f.Title, "accession": f.Acc, "url": url, "museum": m.Slug, "date": f.Date, "decision": reason})
		s.Decisions[reason]++
	}
	if err = save(filepath.Join(out, "decisions.json"), decisions); err != nil {
		return err
	}
	return s.write(out)
}
