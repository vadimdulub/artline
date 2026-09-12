package main

import (
	"context"
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

// Closed source literals only. Numeric search fields can widen a circa date
// conservatively, but cannot supply a missing literal or turn it into exactness.
func campaignDate(display string, first, last int) (creationDate, bool) {
	s := strings.ToLower(strings.TrimSpace(display))
	s = strings.NewReplacer("–", "-", "—", "-", "c.", "c. ", "ca.", "ca. ").Replace(s)
	s = strings.Join(strings.Fields(s), " ")
	d, reason := ngaDate(map[string]string{"displaydate": s, "beginyear": strconv.Itoa(first), "endyear": strconv.Itoa(last)})
	if reason == "eligible" {
		return d, dateEligible(d)
	}
	if reason == "date_literal_numeric_conflict" && (d.Precision == "circa" || d.Precision == "circa_range") && first <= d.First && last >= d.Last && d.First-first <= 10 && last-d.Last <= 10 {
		d.First, d.Last = first, last
		if first != last {
			d.Precision = "circa_range"
		}
		return d, dateEligible(d)
	}
	return d, false
}

func campaignSelection(source string) *evidenceSelection {
	s := newSelection(source)
	s.AccessedOn = "2026-09-10"
	return s
}

type campaignMuseum struct{ Name, City, Slug, Country, Website, Host, DataURL, RightsURL string }

func addCampaignWork(s *evidenceSelection, m campaignMuseum, a knownAuthor, id, title, objectURL, accession, display, kind, medium, dimensions, description string, d creationDate, raw map[string]any) {
	key := s.Source + "-" + m.Slug
	s.Museums[key] = map[string]string{"id": key, "name": m.Name, "city": m.City, "country": m.Country, "data_url": m.DataURL, "data_route": "Official metadata export; complete captured source scanned offline, creation/creator/physical-object gates applied; review only", "rights": "Source dataset metadata is CC0. Images require separate asset-level review; none imported by this job.", "rights_url": m.RightsURL}
	s.Definitions[key] = map[string]string{"Slug": m.Slug, "Source": key, "Website": m.Website, "Host": m.Host}
	desc := fmt.Sprintf("%s — %s. %s.\n\nMedium: %s. Dimensions: %s.\n\nCollection record: %s, %s. Museum connection according to this source; current display unverified.\n\n", title, a.Name, display, medium, dimensions, m.Name, m.City)
	if description != "" && len(description) < 20000 {
		desc += description + "\n\n"
	}
	desc += "Source: [official collection record](" + objectURL + "). Metadata selected and normalized by Artline from the source export, accessed 10 September 2026; no museum endorsement. Reproduction rights are separate."
	s.Works = append(s.Works, map[string]any{"painter": a.QID, "title": title, "institution": key, "accession": accession, "url": objectURL, "source_object_id": id, "source_publisher": m.Name, "date_display": display, "creation_date": d, "attribution_role": "primary", "work_type": kind, "medium": medium, "dimensions": dimensions, "description_md": desc, "notes": "Source attribution requires editorial validation. No inferred masterpiece or current-display claim. Source object IDs are not substituted for accession numbers.", "source_raw": raw})
}

// Exact, source-backed institution/city crosswalk. Never collapse departments by
// a fuzzy name or equate an academy with a separate namesake painting gallery.
var regionalMuseums = map[string]string{
	"Bergamo|Accademia Carrara":                                         "accademia-carrara",
	"Pavia|Musei Civici di Pavia":                                       "musei-civici-pavia",
	"Lovere|Accademia di Belle Arti Tadini":                             "accademia-tadini",
	"Gallarate|Museo MA*GA":                                             "museo-maga-gallarate",
	"Brescia|Musei Civici di Arte e Storia":                             "musei-civici-arte-storia-brescia",
	"Sondrio|Museo Valtellinese di Storia e Arte":                       "museo-valtellinese-storia-arte",
	"Como|Musei Civici di Como":                                         "musei-civici-como",
	"Maccagno con Pino e Veddasca|Civico Museo Parisi Valle":            "museo-parisi-valle",
	"Suzzara|Galleria Civica di Arte Contemporanea":                     "galleria-civica-suzzara",
	"Cremona|Museo Civico Ala Ponzone":                                  "museo-civico-ala-ponzone",
	"Montichiari|Sistema Museale Montichiari Musei":                     "montichiari-musei",
	"Breno|CaMus - Museo Camuno":                                        "camus-museo-camuno",
	"Chiari|Fondazione Biblioteca Morcelli-Pinacoteca Repossi":          "pinacoteca-repossi-chiari",
	"Bergamo|Galleria d'Arte Moderna e Contemporanea (GAMeC)":           "gamec-bergamo",
	"Gazoldo degli Ippoliti|Museo d'Arte Moderna e Contemporanea":       "museo-arte-moderna-gazoldo",
	"San Benedetto Po|Museo Civico Polironiano di San Benedetto Po":     "museo-civico-polironiano",
	"Monza|Musei Civici di Monza":                                       "musei-civici-monza",
	"Soncino|Museo della Stampa di Soncino":                             "museo-stampa-soncino",
	"Asola|Museo Civico G. Bellini":                                     "museo-civico-bellini-asola",
	"Sant'Angelo Lodigiano|Museo Morando Bolognini":                     "museo-morando-bolognini",
	"Busto Arsizio|Civiche Raccolte d'Arte di Palazzo Marliani Cicogna": "palazzo-marliani-cicogna",
	"Vimercate|MUST Museo del territorio vimercatese":                   "must-vimercate",
	"Bormio|Museo Civico di Bormio":                                     "museo-civico-bormio",
	"Medole|Museo Torre Civica di Medole":                               "museo-torre-civica-medole",
	"Bergamo|Museo delle Storie di Bergamo":                             "museo-storie-bergamo",
	"Lissone|Museo d'Arte Contemporanea di Lissone":                     "museo-arte-contemporanea-lissone",
	"Romano di Lombardia|M.A.C.S. - Museo d'Arte e Cultura Sacra":       "macs-romano-lombardia",
}

func assembleLombardia(ctx context.Context, root, out string) error {
	index, e := localAuthors(ctx)
	if e != nil {
		return e
	}
	s := campaignSelection("lombardia")
	national := map[string]int{}
	seen := map[string]bool{}
	e = campaignRecords(root, "lombardia", func(r map[string]any) error {
		if n := str(r, "nctn"); n != "" {
			national[str(r, "nctr")+"|"+n]++
		}
		return nil
	})
	if e != nil {
		return e
	}
	e = campaignRecords(root, "lombardia", func(raw map[string]any) error {
		s.Decisions["candidates"]++
		r := map[string]string{}
		for k, v := range raw {
			if x, ok := v.(string); ok {
				r[k] = x
			}
		}
		if r["pvcc"] == "Milano" {
			s.Decisions["milan_subset_already_processed"]++
			return nil
		}
		slug := regionalMuseums[r["pvcc"]+"|"+r["ldcm"]]
		if slug == "" {
			s.Decisions["museum_review"]++
			return nil
		}
		kind := map[string]string{"dipinto": "painting", "disegno": "drawing", "stampa": "print"}[r["ogtd"]]
		if kind == "" {
			s.Decisions["work_type_review"]++
			return nil
		}
		if r["auts"] != "" || strings.Contains(r["autn"], "||") || r["qntn"] != "" && r["qntn"] != "1" {
			s.Decisions["qualified_multiple_grouped"]++
			return nil
		}
		d, display, ok := sirbecDate(r)
		if !ok {
			s.Decisions["date_review"]++
			return nil
		}
		a, ok := matchAuthor(index, r["autn"], r["auta"])
		if !ok {
			s.Decisions["authority_review"]++
			return nil
		}
		if creatorDateConflict(a, d, kind) {
			s.Decisions["creator_date_conflict"]++
			return nil
		}
		if r["nctn"] != "" && national[r["nctr"]+"|"+r["nctn"]] > 1 {
			s.Decisions["shared_national_identity_review"]++
			return nil
		}
		id := r["idk"]
		u := "https://www.lombardiabeniculturali.it/opere-arte/schede/" + id
		if id == "" || seen[id] || strings.TrimSuffix(strings.Replace(r["url"], "http://", "https://", 1), "/") != u {
			return fmt.Errorf("invalid Lombardia identity %s", id)
		}
		seen[id] = true
		title := r["sgtt"]
		if title == "" {
			title = r["sgti"]
		}
		if title == "" {
			s.Decisions["title_review"]++
			return nil
		}
		museum := campaignMuseum{r["ldcm"], r["pvcc"], slug, "IT", "https://www.lombardiabeniculturali.it/", "www.lombardiabeniculturali.it", "https://www.dati.lombardia.it/resource/ay8b-p38f.json", "https://www.dati.lombardia.it/api/views/ay8b-p38f.json"}
		dim := ""
		if r["misa"] != "" && r["misl"] != "" {
			dim = r["misa"] + " × " + r["misl"] + " " + r["misu"]
		}
		desc := ""
		for _, k := range []string{"deso", "nsc"} {
			if t := r[k]; len(t) > 0 && len(t) < 8000 {
				desc += t + "\n\n"
			}
		}
		s.addAuthor(r["autn"], r["auta"], a)
		addCampaignWork(s, museum, a, id, title, u, "", display, kind, r["mtc"], dim, desc, d, raw)
		return nil
	})
	if e != nil {
		return e
	}
	return s.write(out)
}

var sourceQID = regexp.MustCompile(`^https?://www.wikidata.org/(?:wiki/|entity/)(Q[1-9][0-9]*)$`)

func campaignAuthor(index map[string][]knownAuthor, byQID map[string]knownAuthor, name, life, qidURL string) (knownAuthor, bool) {
	if qidURL == "" {
		return matchAuthor(index, name, life)
	}
	m := sourceQID.FindStringSubmatch(qidURL)
	if m == nil {
		return knownAuthor{}, false
	}
	// A source QID is stronger than spelling. Still fail on source/local name or
	// lifespan contradiction when a full-name match resolves a different artist.
	found := byQID[m[1]]
	if found.QID == "" {
		return found, false
	}
	if a, ok := matchAuthor(index, name, life); ok && a.QID != found.QID {
		return found, false
	}
	if m := lifeLiteral.FindStringSubmatch(life); m != nil {
		b, _ := strconv.Atoi(m[1])
		d, _ := strconv.Atoi(m[2])
		if found.Birth != nil && *found.Birth != b || found.Death != nil && *found.Death != d {
			return found, false
		}
	}
	return found, true
}

func assembleMet(ctx context.Context, root, out string) error {
	index, e := localAuthors(ctx)
	if e != nil {
		return e
	}
	s := campaignSelection("met")
	accessions := map[string]int{}
	if e = campaignRecords(root, "met", func(r map[string]any) error {
		if inv := str(r, "object number"); inv != "" {
			accessions[inv]++
		}
		return nil
	}); e != nil {
		return e
	}
	byQID := map[string]knownAuthor{}
	for _, values := range index {
		for _, a := range values {
			byQID[a.QID] = a
		}
	}
	seen := map[string]bool{}
	m := campaignMuseum{"The Metropolitan Museum of Art", "New York", "the-met", "US", "https://www.metmuseum.org/", "www.metmuseum.org", metExport, "https://github.com/metmuseum/openaccess"}
	e = campaignRecords(root, "met", func(r map[string]any) error {
		s.Decisions["source_rows"]++
		kind := map[string]string{"Paintings": "painting", "Drawings": "drawing", "Prints": "print"}[str(r, "classification")]
		if kind == "" {
			return nil
		}
		s.Decisions["candidates"]++
		name := str(r, "artist display name")
		role := str(r, "artist role")
		if name == "" || str(r, "artist prefix") != "" || str(r, "artist suffix") != "" || strings.Contains(name, "|") || strings.Contains(role, "|") || !map[string]bool{"Artist": true, "Painter": true, "Printmaker": true, "Maker": true, "Draughtsman": true}[role] {
			s.Decisions["creator_role_or_qualification_review"]++
			return nil
		}
		first, _ := strconv.Atoi(str(r, "object begin date"))
		last, _ := strconv.Atoi(str(r, "object end date"))
		display := str(r, "object date")
		d, ok := campaignDate(display, first, last)
		if !ok {
			s.Decisions["date_review"]++
			return nil
		}
		a, ok := campaignAuthor(index, byQID, name, str(r, "artist begin date")+"-"+str(r, "artist end date"), str(r, "artist wikidata url"))
		if !ok {
			s.Decisions["authority_review"]++
			return nil
		}
		if creatorDateConflict(a, d, kind) {
			s.Decisions["creator_date_conflict"]++
			return nil
		}
		id, title, inv := str(r, "object id"), str(r, "title"), str(r, "object number")
		if accessions[inv] > 1 {
			s.Decisions["shared_accession_review"]++
			return nil
		}
		u := strings.Replace(str(r, "link resource"), "http://", "https://", 1)
		if id == "" || title == "" || inv == "" || u != "https://www.metmuseum.org/art/collection/search/"+id {
			s.Decisions["object_identity_review"]++
			return nil
		}
		// Multi-component accessions and source albums/sets require physical-unit
		// reconciliation; a CSV row is not automatically an individual artwork.
		if strings.ContainsAny(inv, ",;") || regexp.MustCompile(`[0-9][a-z]-[a-z]|[0-9]-[0-9]`).MatchString(inv) || regexp.MustCompile(`(?i)\b(album|sketchbook|portfolio|set of|recto|verso)\b`).MatchString(title+" "+str(r, "object name")) {
			s.Decisions["physical_unit_review"]++
			return nil
		}
		if seen[inv] {
			s.Decisions["duplicate_inventory"]++
			return nil
		}
		seen[inv] = true
		s.addAuthor(name, str(r, "artist begin date")+"-"+str(r, "artist end date"), a)
		if qidURL := str(r, "artist wikidata url"); qidURL != "" {
			s.Crosswalk[name+"|"+str(r, "artist begin date")+"-"+str(r, "artist end date")] = map[string]any{"source_name": name, "source_qid_url": qidURL, "qid": a.QID, "local_name": a.Name, "source_birth": str(r, "artist begin date"), "source_death": str(r, "artist end date"), "local_birth": a.Birth, "local_death": a.Death, "basis": "explicit source Wikidata authority; existing active local QID; name and known literal lifespan conflict checks"}
		}
		addCampaignWork(s, m, a, id, title, u, inv, display, kind, str(r, "medium"), str(r, "dimensions"), "Credit line: "+str(r, "credit line")+".\n\nThis is a museum catalogue record, not a current-display assertion.", d, r)
		return nil
	})
	if e != nil {
		return e
	}
	return s.write(out)
}

func assembleCleveland(ctx context.Context, root, out string) error {
	index, e := localAuthors(ctx)
	if e != nil {
		return e
	}
	s := campaignSelection("cleveland")
	seen := map[string]bool{}
	m := campaignMuseum{"The Cleveland Museum of Art", "Cleveland", "cleveland-museum-of-art", "US", "https://www.clevelandart.org/", "clevelandart.org", clevelandExport, "https://github.com/ClevelandMuseumArt/openaccess"}
	e = campaignRecords(root, "cleveland", func(r map[string]any) error {
		s.Decisions["source_rows"]++
		kind := map[string]string{"Painting": "painting", "Drawing": "drawing", "Print": "print"}[str(r, "type")]
		if kind == "" {
			return nil
		}
		s.Decisions["candidates"]++
		creators, ok := r["creators"].([]any)
		if !ok || len(creators) != 1 {
			s.Decisions["creator_review"]++
			return nil
		}
		c, ok := creators[0].(map[string]any)
		if !ok {
			return fmt.Errorf("invalid source creator")
		}
		if str(c, "qualifier") != "" || str(c, "extent") != "" || str(c, "role") != "artist" {
			s.Decisions["qualified_creator_review"]++
			return nil
		}
		name := strings.Split(str(c, "description"), " (")[0]
		a, ok := matchAuthor(index, name, str(c, "birth_year")+"-"+str(c, "death_year"))
		if !ok {
			s.Decisions["authority_review"]++
			return nil
		}
		display := str(r, "creation_date")
		d, ok := campaignDate(display, integer(r, "creation_date_earliest"), integer(r, "creation_date_latest"))
		if !ok {
			s.Decisions["date_review"]++
			return nil
		}
		if creatorDateConflict(a, d, kind) {
			s.Decisions["creator_date_conflict"]++
			return nil
		}
		id := strconv.Itoa(integer(r, "id"))
		title, inv, u := str(r, "title"), str(r, "accession_number"), str(r, "url")
		if id == "0" || title == "" || inv == "" || u != "https://clevelandart.org/art/"+inv {
			s.Decisions["object_identity_review"]++
			return nil
		}
		related, _ := r["related_works"].([]any)
		if len(related) > 0 || strings.ContainsAny(inv, ",;") || regexp.MustCompile(`[0-9][a-z]-[a-z]|[0-9]-[0-9]`).MatchString(inv) || regexp.MustCompile(`(?i)\b(album|sketchbook|portfolio|set of|recto|verso|folio)\b`).MatchString(title) {
			s.Decisions["physical_unit_review"]++
			return nil
		}
		if seen[inv] {
			s.Decisions["duplicate_inventory"]++
			return nil
		}
		seen[inv] = true
		s.addAuthor(name, str(c, "birth_year")+"-"+str(c, "death_year"), a)
		addCampaignWork(s, m, a, id, title, u, inv, display, kind, str(r, "technique"), str(r, "measurements"), str(r, "description"), d, r)
		updated := str(r, "updated_at")
		if len(updated) >= 10 {
			s.Works[len(s.Works)-1]["source_updated_on"] = updated[:10]
		}
		if native := str(r, "title_in_original_language"); native != "" {
			s.Works[len(s.Works)-1]["aliases"] = []string{native}
		}
		return nil
	})
	if e != nil {
		return e
	}
	return s.write(out)
}
