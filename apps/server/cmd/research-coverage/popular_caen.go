package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

// Read the already captured, permitted national open dataset. No website crawl,
// images or database writes; retain all Caen painting candidates for review.
func auditPopularCaen(root, out string) error {
	file := filepath.Join(root, "content/imports/joconde-20260910/joconde.csv")
	if err := verify(file); err != nil {
		return err
	}
	rows := []map[string]string{}
	err := csvRows(file, '|', func(r map[string]string) error {
		if r["code_museofile"] != "M0657" || !strings.Contains(r["domaine"], "peinture") {
			return nil
		}
		if len(rows) >= 2000 {
			return fmt.Errorf("Caen candidate ceiling exceeded")
		}
		// Only factual research columns, not narrative essays or photograph URLs.
		v := map[string]string{}
		for _, k := range []string{"reference", "titre", "auteur", "numero_inventaire", "millesime_de_creation", "periode_de_creation", "date_creation", "precisions_sur_l_auteur", "attribution", "denomination", "domaine", "code_museofile", "nom_officiel_musee", "ville", "manquant", "lieu_de_depot", "statut_juridique", "materiaux_techniques", "mesures"} {
			v[k] = r[k]
		}
		rows = append(rows, v)
		return nil
	})
	if err != nil {
		return err
	}
	if err = save(filepath.Join(out, "caen-paintings.json"), rows); err != nil {
		return err
	}
	fmt.Printf("Retained %d Caen painting metadata rows from the verified local Joconde snapshot; research candidates only.\n", len(rows))
	return nil
}

func caenAuthor(raw string, index map[string][]knownAuthor) (knownAuthor, bool) {
	var found knownAuthor
	for _, part := range strings.Split(raw, ";") {
		part = strings.TrimSpace(part)
		for _, role := range []string{"(dit, peintre)", "(dit)", "(peintre)"} {
			part = strings.TrimSpace(strings.ReplaceAll(part, role, ""))
		}
		if part == "" {
			continue
		}
		if strings.ContainsAny(part, "()") {
			return knownAuthor{}, false
		}
		matches := index[authorityKey(part)]
		if len(matches) != 1 || found.QID != "" && matches[0].QID != found.QID {
			return knownAuthor{}, false
		}
		found = matches[0]
	}
	return found, found.QID != ""
}

func assemblePopularCaen(ctx context.Context, root, out string) error {
	index, err := localAuthors(ctx)
	if err != nil {
		return err
	}
	artists, err := popularNGCohort(ctx)
	if err != nil {
		return err
	}
	popular := map[string]popularNGArtist{}
	for _, a := range artists {
		popular[a.QID] = a
	}
	p, err := pgxpool.New(ctx, config.Load().DatabaseURL)
	if err != nil {
		return err
	}
	defer p.Close()
	b, err := os.ReadFile(filepath.Join(root, "docs/research/popular-europe-session-20260911/caen-audit/caen-paintings.json"))
	if err != nil {
		return err
	}
	var records []map[string]string
	if err = json.Unmarshal(b, &records); err != nil {
		return err
	}
	if len(records) > 2000 {
		return fmt.Errorf("Caen candidate ceiling")
	}
	s := newSelection("popular-caen")
	s.AccessedOn = "2026-09-11"
	key := "popular-caen"
	s.Museums[key] = map[string]string{"id": key, "name": "musée des beaux-arts — Caen", "country": "FR", "city": "Caen", "data_url": "https://www.data.gouv.fr/datasets/collections-des-musees-de-france-base-joconde", "data_route": "Selected popular-painter records from verified official Joconde snapshot; compound source names reconciled without surname matching.", "rights": "Licence Ouverte 2.0 factual metadata; no photograph permission inferred.", "rights_url": "https://pop.culture.gouv.fr/donnees-ouvertes"}
	s.Definitions[key] = map[string]string{"Host": "pop.culture.gouv.fr", "Slug": "joconde-m0657", "Source": "joconde-m0657", "Website": "https://mba.caen.fr"}
	decisions := []map[string]string{}
	for _, r := range records {
		a, ok := caenAuthor(r["auteur"], index)
		// The museum explicitly identifies Jacopo Robusti as Le Tintoret on the
		// reviewed accession 17 page. This exact compound spelling is one creator.
		if r["auteur"] == "ROBUSTI Jacopo;LE TINTORET (dit, peintre)" {
			matches := index[authorityKey("Tintoretto")]
			if len(matches) == 1 && matches[0].QID == "Q9319" {
				a, ok = matches[0], true
			}
		}
		if !ok || popular[a.QID].ID == "" {
			continue
		}
		reason := "eligible"
		d, display, valid := jocondeDate(r)
		supplement := ""
		// Only these three individually reviewed object notices resolve the national
		// dataset's comma notation. A comma is NOT generically interpreted as a range.
		type exactDate struct {
			File, SHA, URL, Accession, Literal string
			Date                               creationDate
		}
		reviewed := map[string]exactDate{
			"06570007477": {"caen-perugino-marriage.html", "87526a32102aa8789b483c68ac8a81db3737744d0ced0338f61658d5c2c8eba8", "https://mba.caen.fr/oeuvre/le-mariage-de-la-vierge", "171", "1504", creationDate{1504, 1504, "exact"}},
			"06570008277": {"caen-veronese-antony.html", "424adba787474e5bab90d463d2fb442f38d48c5e5b040824cfb47dcc80906e72", "https://mba.caen.fr/oeuvre/la-tentation-de-saint-antoine", "6", "1552", creationDate{1552, 1552, "exact"}},
			"06570007713": {"caen-tintoretto-descent.html", "58ff8a09df86f526f0fdf1943c81ffa820ba657f89354c8f49a45a88058fd5dc", "https://mba.caen.fr/oeuvre/la-descente-de-croix", "17", "1556–1558", creationDate{1556, 1558, "range"}},
		}
		if v, found := reviewed[r["reference"]]; found {
			file := filepath.Join(root, "content/imports/popular-europe-session-20260911/pages", v.File)
			sha, _, e := hashFile(file)
			if e != nil || sha != v.SHA || r["numero_inventaire"] != v.Accession {
				return fmt.Errorf("reviewed Caen date evidence changed")
			}
			d, display, valid = v.Date, v.Literal, true
			supplement = "\n\nCreation dating checked against the museum's exact-accession notice: [museum record](" + v.URL + "). The national dataset retains its original date notation in the source evidence."
			r["reviewed_date_source_url"] = v.URL
			r["reviewed_date_source_sha256"] = v.SHA
		}
		if !valid {
			reason = "unresolved creation date notation"
		}
		if r["manquant"] != "" {
			reason = "missing or destroyed object; no current holding claim"
		}
		if strings.Contains(strings.ToLower(r["precisions_sur_l_auteur"]), "collaboration") {
			reason = "collaborative attribution needs explicit modelling"
		}
		if r["denomination"] != "" && r["denomination"] != "tableau" && r["denomination"] != "peinture" {
			reason = "physical unit requires review"
		}
		if valid && (a.Birth != nil && d.Last < *a.Birth || a.Death != nil && d.First > *a.Death) {
			reason = "source creation interval outside creator lifespan"
		}
		if r["reference"] == "06570007479" {
			reason = "source-date disagreement: Joconde 1496–1502 versus museum 1498–1502; deferred"
		}
		if r["reference"] == "06570007448" {
			reason = "museum explicitly says avec collaboration; primary-only catalogue mapping deferred"
		}
		if r["reference"] == "000PE024555" {
			reason = "museum/Joconde dimensions conflict and Louvre deposit crosswalk requires review; deferred"
		}
		acc := r["numero_inventaire"]
		url := "https://pop.culture.gouv.fr/notice/joconde/" + r["reference"]
		if acc == "" || strings.Contains(acc, ";") {
			reason = "inventory aliases require exact identity review"
		}
		if reason == "eligible" {
			var count int
			err = p.QueryRow(ctx, `SELECT count(*) FROM artworks WHERE id IN (
    SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=$1 OR scheme LIKE 'european-joconde%' AND external_id=$3)
    UNION SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=$1
    UNION SELECT a.id FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug='joconde-m0657' AND a.accession_number=$2
   )`, url, acc, r["reference"]).Scan(&count)
			if err != nil {
				return err
			}
			if count > 0 {
				reason = "existing exact object preserved"
			}
			if count == 0 {
				err = p.QueryRow(ctx, `SELECT count(*) FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=$1 AND lower(regexp_replace(a.title,'[^[:alnum:]]','','g'))=lower(regexp_replace($2,'[^[:alnum:]]','','g'))`, popular[a.QID].ID, r["titre"]).Scan(&count)
				if err != nil {
					return err
				}
				if count > 0 {
					reason = "same artist/title elsewhere: exact physical identity review"
				}
			}
		}
		if reason == "eligible" && len(s.Works) >= 50 {
			reason = "bounded 50-work batch: queued"
		}
		if reason == "eligible" {
			s.addAuthor(r["auteur"], r["precisions_sur_l_auteur"], a)
			s.Crosswalk[r["auteur"]+"|"+r["precisions_sur_l_auteur"]].(map[string]any)["basis"] = "Compound source aliases resolve to one existing popular artist by full normalized tokens; exact Tintoretto/Robusti crosswalk corroborated by the museum accession-17 notice. Approximate birth-year variants are retained, not silently overwritten."
			s.Works = append(s.Works, map[string]any{"painter": a.QID, "title": r["titre"], "institution": key, "accession": acc, "url": url, "source_object_id": r["reference"], "source_publisher": "Ministère de la Culture, Joconde; Musée des Beaux-Arts de Caen", "date_display": display, "creation_date": d, "attribution_role": "primary", "work_type": "painting", "medium": r["materiaux_techniques"], "dimensions": r["mesures"], "description_md": fmt.Sprintf("%s — %s. %s.\n\nMedium: %s. Dimensions: %s.\n\nMuseum connection: Musée des Beaux-Arts de Caen, accession %s. The national catalogue records a museum association; this does not establish current display.\n\n[Official Joconde record](%s). Factual metadata under Licence Ouverte 2.0; photographs remain separately licensed.", r["titre"], a.Name, display, r["materiaux_techniques"], r["mesures"], acc, url) + supplement, "source_raw": r, "notes": "Compound source names resolve to one existing popular painter. Review-only metadata; no ownership, current-display or masterpiece inference."})
		}
		decisions = append(decisions, map[string]string{"artist": a.Name, "qid": a.QID, "reference": r["reference"], "title": r["titre"], "accession": acc, "date": display, "decision": reason})
		s.Decisions[reason]++
	}
	if err = save(filepath.Join(out, "decisions.json"), decisions); err != nil {
		return err
	}
	fmt.Printf("%d eligible new paintings from %d popular-painter candidate records.\n", len(s.Works), len(decisions))
	return s.write(out)
}
