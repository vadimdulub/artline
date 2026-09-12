package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"unicode"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"golang.org/x/text/unicode/norm"
)

type knownAuthor struct {
	QID, Name    string
	Birth, Death *int
}

// Candidate crosswalk only: complete normalized token equality, never surname,
// partial or edit-distance matching. Each resulting crosswalk is reviewed/pinned
// before the offline importer can run. Ambiguous aliases fail closed.
func authorityKey(s string) string {
	s = norm.NFD.String(strings.ToLower(s))
	s = strings.Map(func(r rune) rune {
		if unicode.Is(unicode.Mn, r) {
			return -1
		}
		if !unicode.IsLetter(r) && !unicode.IsNumber(r) {
			return ' '
		}
		return r
	}, s)
	p := strings.Fields(s)
	sort.Strings(p)
	return strings.Join(p, " ")
}
func localAuthors(ctx context.Context) (map[string][]knownAuthor, error) {
	cfg, e := pgxpool.ParseConfig(config.Load().DatabaseURL)
	if e != nil {
		return nil, e
	}
	local := func(h string) bool {
		return h == "localhost" || h == "127.0.0.1" || h == "::1" || strings.HasPrefix(h, "/")
	}
	if !local(cfg.ConnConfig.Host) {
		return nil, fmt.Errorf("local DB only")
	}
	for _, f := range cfg.ConnConfig.Fallbacks {
		if !local(f.Host) {
			return nil, fmt.Errorf("remote fallback forbidden")
		}
	}
	pool, e := pgxpool.NewWithConfig(ctx, cfg)
	if e != nil {
		return nil, e
	}
	defer pool.Close()
	rows, e := pool.Query(ctx, `SELECT e.external_id,a.display_name,a.birth_year,a.death_year,n.name FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' CROSS JOIN LATERAL (SELECT a.display_name AS name UNION SELECT a.sort_name UNION SELECT alias FROM artist_aliases WHERE artist_id=a.id) n WHERE a.status<>'archived'`)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	out := map[string][]knownAuthor{}
	for rows.Next() {
		var a knownAuthor
		var name string
		if e = rows.Scan(&a.QID, &a.Name, &a.Birth, &a.Death, &name); e != nil {
			return nil, e
		}
		k := authorityKey(name)
		found := false
		for _, old := range out[k] {
			if old.QID == a.QID {
				found = true
			}
		}
		if !found {
			out[k] = append(out[k], a)
		}
	}
	return out, rows.Err()
}

var lifeLiteral = regexp.MustCompile(`^\s*(\d{4})\s*[-–/]\s*(\d{4})\s*$`)

func matchAuthor(index map[string][]knownAuthor, name, life string) (knownAuthor, bool) {
	k := authorityKey(name)
	if len(strings.Fields(k)) < 2 {
		return knownAuthor{}, false
	}
	a := index[k]
	if len(a) != 1 {
		return knownAuthor{}, false
	}
	if m := lifeLiteral.FindStringSubmatch(life); m != nil {
		b, _ := strconv.Atoi(m[1])
		d, _ := strconv.Atoi(m[2])
		if a[0].Birth != nil && *a[0].Birth != b || a[0].Death != nil && *a[0].Death != d {
			return knownAuthor{}, false
		}
	}
	return a[0], true
}
func dateEligible(d creationDate) bool {
	return d.First >= 1100 && d.Last >= d.First && catalog.CreationScope(&d.First, &d.Last, d.Precision) == "eligible"
}

// A consistency veto, never a replacement date or a narrowed creation range.
func creatorDateConflict(a knownAuthor, d creationDate, kind string) bool {
	return a.Birth != nil && d.Last < *a.Birth || kind == "painting" && a.Death != nil && d.First > *a.Death
}

var frenchPeriod = regexp.MustCompile(`^(?:(1er|1ère|2e|3e|4e) (quart|moitié) (?:du )?)?(\d{2})e siècle$`)

func jocondePeriod(s string) (creationDate, bool) {
	d := creationDate{First: 9999, Precision: "century"}
	for _, p := range strings.Split(s, ";") {
		m := frenchPeriod.FindStringSubmatch(strings.TrimSpace(p))
		if m == nil {
			return d, false
		}
		c, _ := strconv.Atoi(m[3])
		a, b := (c-1)*100, c*100
		if m[1] != "" {
			n, _ := strconv.Atoi(m[1][:1])
			width := 25
			if m[2] == "moitié" {
				width = 50
			}
			if n*width > 100 {
				return d, false
			}
			a += (n - 1) * width
			b = a + width
			d.Precision = "range"
		}
		d.First = min(d.First, a)
		d.Last = max(d.Last, b)
	}
	return d, true
}

var frenchYear = regexp.MustCompile(`^(\d{4})(?:\s*[-/]\s*(\d{4}))?(?:\s*(vers|en))?$`)

func jocondeDate(r map[string]string) (creationDate, string, bool) {
	s := strings.TrimSpace(r["millesime_de_creation"])
	p, pok := jocondePeriod(r["periode_de_creation"])
	if s == "" {
		return p, r["periode_de_creation"], pok && dateEligible(p)
	}
	m := frenchYear.FindStringSubmatch(s)
	if m == nil {
		return creationDate{}, s, false
	}
	a, _ := strconv.Atoi(m[1])
	b := a
	if m[2] != "" {
		b, _ = strconv.Atoi(m[2])
	}
	d := creationDate{a, b, "exact"}
	if a != b {
		d.Precision = "range"
	}
	if m[3] == "vers" {
		d.Precision = "circa"
		if a != b {
			d.Precision = "circa_range"
		}
	}
	// Period is a separate consistency check, not a substitute for a conflicting
	// year. Conservative century boundaries include both boundary years.
	if pok && (a < p.First || b > p.Last) {
		return d, s, false
	}
	return d, s, dateEligible(d)
}

var fourDigit = regexp.MustCompile(`^\d{4}$`)

func sirbecDate(r map[string]string) (creationDate, string, bool) {
	s := strings.TrimSpace(r["dtsi"])
	z := strings.TrimSpace(r["dtsf"])
	v, l := r["dtsv"], r["dtsl"]
	display := strings.TrimSpace(s + " " + v + " – " + z + " " + l)
	d := creationDate{}
	if !fourDigit.MatchString(s) || !fourDigit.MatchString(z) {
		return d, display, false
	}
	// 'ante' as the start / 'post' as the end are open in the unsafe direction.
	allowedStart := v == "" || v == "ca" || v == "ca." || v == "post"
	allowedEnd := l == "" || l == "ca" || l == "ca." || l == "ante"
	if !allowedStart || !allowedEnd {
		return d, display, false
	}
	d.First, _ = strconv.Atoi(s)
	d.Last, _ = strconv.Atoi(z)
	d.Precision = "range"
	if d.First == d.Last {
		if v == "post" || l == "ante" {
			return d, display, false
		}
		d.Precision = "exact"
		qualifier := strings.TrimSpace(v + " " + l)
		if v == l {
			qualifier = v
		}
		display = strings.TrimSpace(s + " " + qualifier)
	}
	if strings.HasPrefix(v, "ca") || strings.HasPrefix(l, "ca") {
		d.Precision = "circa_range"
		if d.First == d.Last {
			d.Precision = "circa"
		}
	}
	return d, display, dateEligible(d)
}

type evidenceSelection struct {
	AccessedOn  string
	Source      string
	Works       []map[string]any
	Museums     map[string]map[string]string
	Definitions map[string]map[string]string
	Crosswalk   map[string]any
	Decisions   map[string]int
}

func newSelection(source string) *evidenceSelection {
	return &evidenceSelection{Source: source, Museums: map[string]map[string]string{}, Definitions: map[string]map[string]string{}, Crosswalk: map[string]any{}, Decisions: map[string]int{}}
}
func (s *evidenceSelection) addAuthor(name, life string, a knownAuthor) {
	s.Crosswalk[name+"|"+life] = map[string]any{"source_name": name, "source_life": life, "qid": a.QID, "local_name": a.Name, "local_birth": a.Birth, "local_death": a.Death, "basis": "full normalized name/alias token equality; no ambiguous match; known literal lifespan conflicts rejected"}
}
func (s *evidenceSelection) write(out string) error {
	sort.Slice(s.Works, func(i, j int) bool { return s.Works[i]["url"].(string) < s.Works[j]["url"].(string) })
	chunks := []any{}
	types := map[string]int{}
	museumCounts := map[string]int{}
	for i := 0; i < len(s.Works); i += 500 {
		works := s.Works[i:min(i+500, len(s.Works))]
		painters := map[string]string{}
		inst := map[string]map[string]string{}
		defs := map[string]map[string]string{}
		for _, w := range works {
			p := w["painter"].(string)
			painters[p] = p
			k := w["institution"].(string)
			inst[k] = s.Museums[k]
			defs[k] = s.Definitions[k]
			types[w["work_type"].(string)]++
			museumCounts[k]++
		}
		keys := []string{}
		for k := range inst {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		museums := []any{}
		for _, k := range keys {
			museums = append(museums, inst[k])
		}
		file := fmt.Sprintf("chunk-%03d.json", i/500+1)
		path := filepath.Join(out, file)
		// 10 September Cyprus captures occurred on 9 September UTC. Date-only
		// evidence uses UTC; do not disable the importer's future-date guard.
		accessed := s.AccessedOn
		if accessed == "" {
			accessed = "2026-09-09"
		}
		if e := save(path, map[string]any{"schema_version": 2, "accessed_on": accessed, "source": s.Source, "painters": painters, "definitions": defs, "institutions": museums, "works": works}); e != nil {
			return e
		}
		sha, _, e := hashFile(path)
		if e != nil {
			return e
		}
		chunks = append(chunks, map[string]any{"file": file, "sha256": sha, "works": len(works)})
	}
	if e := save(filepath.Join(out, "crosswalk.json"), s.Crosswalk); e != nil {
		return e
	}
	if e := save(filepath.Join(out, "summary.json"), map[string]any{"source": s.Source, "selected": len(s.Works), "types": types, "museum_counts": museumCounts, "decisions": s.Decisions}); e != nil {
		return e
	}
	fmt.Printf("%s selected%d museums%d decisions%v\n", s.Source, len(s.Works), len(museumCounts), s.Decisions)
	return save(filepath.Join(out, "manifest.json"), map[string]any{"source": s.Source, "chunks": chunks})
}

var jocondeCreator = regexp.MustCompile(`^([^();]+?)(?: \((\d{4}-\d{4})\))?$`)
var jocondeMuseumExisting = map[string]string{"M5031": "musee-du-louvre", "M5032": "musee-du-louvre"}

func assembleJoconde(ctx context.Context, root, out string) error {
	return assembleJocondeWave(ctx, root, out, nil)
}

// Additional waves are explicit bounded scopes. The existing published source
// selection/pins remain immutable. Name blocking only defers possible overlap;
// it never assigns an artwork identity or merges by title.
type jocondeWave struct {
	Source             string
	Museums            map[string]string
	BlockedAuthorities map[string]bool
	InventoryCounts    map[string]int
	ReviewedNonoverlap map[string]string
}

func assembleJocondeWave(ctx context.Context, root, out string, wave *jocondeWave) error {
	path := filepath.Join(root, "content/imports/joconde-20260910/joconde.csv")
	if e := verify(path); e != nil {
		return e
	}
	index, e := localAuthors(ctx)
	if e != nil {
		return e
	}
	s := newSelection("joconde")
	if wave != nil {
		s = newSelection(wave.Source)
	}
	seen := map[string]bool{}
	e = csvRows(path, '|', func(r map[string]string) error {
		if wave != nil && wave.Museums[r["code_museofile"]] == "" {
			return nil
		}
		kind := ""
		for _, p := range strings.Split(r["domaine"], ";") {
			switch strings.TrimSpace(p) {
			case "peinture":
				kind = "painting"
			case "dessin":
				if kind == "" {
					kind = "drawing"
				}
			case "estampe":
				if kind == "" {
					kind = "print"
				}
			}
		}
		if kind == "" {
			return nil
		}
		if wave != nil && kind != "painting" {
			return nil
		}
		s.Decisions["candidates"]++
		// Source units such as albums, illustration pages, recto/verso and grouped
		// ensembles require physical-object modelling before they can count as works.
		den := r["denomination"]
		if den != "" && den != "tableau" && den != "peinture" && den != "dessin" && den != "estampe" && den != "estampe originale" {
			s.Decisions["not_individual_work"]++
			return nil
		}
		for _, p := range []string{"album", "carnet", "verso", "recto", "ensemble"} {
			if strings.Contains(strings.ToLower(r["titre"]+" "+r["numero_inventaire"]), p) {
				s.Decisions["physical_unit_requires_review"]++
				return nil
			}
		}
		if r["manquant"] != "" || r["manquant_com"] != "" || r["lieu_de_depot"] != "" {
			s.Decisions["missing_or_deposit_review"]++
			return nil
		}
		d, display, valid := jocondeDate(r)
		if !valid {
			s.Decisions["creation_date_review"]++
			return nil
		}
		m := jocondeCreator.FindStringSubmatch(strings.TrimSpace(r["auteur"]))
		if m == nil {
			s.Decisions["qualified_or_multiple_creator"]++
			return nil
		}
		a, ok := matchAuthor(index, m[1], m[2])
		if !ok {
			s.Decisions["authority_review"]++
			return nil
		}
		if creatorDateConflict(a, d, kind) {
			s.Decisions["creator_creation_conflict"]++
			return nil
		}
		if wave != nil && wave.BlockedAuthorities[r["code_museofile"]+"|"+a.QID] &&
			!normandyReviewedNonoverlap(wave, r, a, d) {
			s.Decisions["primary_catalogue_artist_overlap_deferred"]++
			return nil
		}
		code, name, city := r["code_museofile"], r["nom_officiel_musee"], r["ville"]
		if !regexp.MustCompile(`^M[0-9]{4}$`).MatchString(code) || name == "" || city == "" || r["localisation"] == "" || r["numero_inventaire"] == "" || r["titre"] == "" {
			s.Decisions["holding_or_identity_review"]++
			return nil
		}
		// A deposit field was already excluded; still require the stated physical
		// city to agree with the responsible museum's locality.
		if authorityKey(strings.Split(r["localisation"], ";")[0]) != authorityKey(city) {
			s.Decisions["localisation_review"]++
			return nil
		}
		key := "joconde-" + strings.ToLower(code)
		slug := key
		fullName := name + " — " + city
		// Crosswalk for existing French museums is reviewed against Museofile rows.
		normalized := authorityKey(name)
		switch {
		case strings.Contains(normalized, "louvre") && city == "Paris":
			slug = "musee-du-louvre"
		case strings.Contains(normalized, "orsay") && city == "Paris":
			slug = "musee-orsay"
		case strings.Contains(normalized, "orangerie") && city == "Paris":
			slug = "musee-orangerie"
		case strings.Contains(normalized, "marmottan") && city == "Paris":
			slug = "musee-marmottan-monet"
		case city == "Rouen" && strings.Contains(normalized, "beaux"):
			slug = "musee-beaux-arts-rouen"
		case city == "Le Havre" && strings.Contains(normalized, "malraux"):
			slug = "muma-le-havre"
		case city == "Grenoble" && strings.Contains(normalized, "grenoble"):
			slug = "musee-de-grenoble"
		}
		// Prefer the already-imported institution's primary catalogue. Joconde
		// can retain historic national collection allocations and differently
		// formatted inventory aliases; reconcile those in a separate review.
		if wave != nil {
			key = wave.Source + "-" + strings.ToLower(code)
			slug = wave.Museums[code]
			if wave.InventoryCounts[code+"|"+r["numero_inventaire"]] != 1 {
				s.Decisions["shared_inventory_review"]++
				return nil
			}
		} else if slug != key {
			s.Decisions["existing_museum_primary_catalogue_preferred"]++
			return nil
		}
		// Different source departments can be one museum; dedup uses physical holder
		// plus inventory, not a department code or the artwork title.
		identity := slug + "|" + r["numero_inventaire"]
		if seen[identity] {
			s.Decisions["duplicate_inventory"]++
			return nil
		}
		seen[identity] = true
		s.Museums[key] = map[string]string{"id": key, "name": fullName, "city": city, "country": "FR", "data_url": "https://www.data.gouv.fr/datasets/collections-des-musees-de-france-base-joconde", "data_route": "Complete official CSV snapshot, dated September 9 2026; source object/museum IDs retained", "rights": "Joconde downloadable metadata: Licence Ouverte 2.0; photographs not licensed by this import.", "rights_url": "https://pop.culture.gouv.fr/donnees-ouvertes"}
		s.Definitions[key] = map[string]string{"Slug": slug, "Source": key, "Website": "https://pop.culture.gouv.fr/notice/museo/" + code, "Host": "pop.culture.gouv.fr"}
		url := "https://pop.culture.gouv.fr/notice/joconde/" + r["reference"]
		desc := fmt.Sprintf("%s — %s. %s.\n\nMedium: %s. Dimensions: %s.\n\nCollection record: %s, %s. Inventory %s. Holding only; current display unverified.\n\n", r["titre"], a.Name, display, r["materiaux_techniques"], r["mesures"], name, city, r["numero_inventaire"])
		if t := strings.TrimSpace(r["description"]); len(t) > 0 && len(t) < 15000 {
			desc += "Museum catalogue description (French):\n\n" + t + "\n\n"
		}
		desc += fmt.Sprintf("Source: [Joconde — Ministère de la Culture](%s), record updated %s, export 9 September 2026. Metadata reused under Licence Ouverte 2.0. Artline's date normalization and selection are independent adaptations, not museum endorsement.", url, r["date_de_mise_a_jour"])
		s.addAuthor(m[1], m[2], a)
		s.Works = append(s.Works, map[string]any{"painter": a.QID, "title": r["titre"], "institution": key, "accession": r["numero_inventaire"], "url": url, "source_object_id": r["reference"], "source_publisher": "Ministère de la Culture — Joconde", "date_display": display, "creation_date": d, "attribution_role": "primary", "work_type": kind, "medium": r["materiaux_techniques"], "dimensions": r["mesures"], "source_updated_on": r["date_de_mise_a_jour"], "description_md": desc, "notes": "Museum holding; not a masterpiece designation or current display. Date_creation is the catalogue notice date and is never used for creation eligibility.", "source_raw": r})
		return nil
	})
	if e != nil {
		return e
	}
	return s.write(out)
}

var sirbecMuseums = map[string]string{
	"Civiche Raccolte Grafiche e Fotografiche del Castello Sforzesco":    "castello-sforzesco-graphic-collections",
	"Accademia di Belle Arti di Brera":                                   "accademia-brera-collections",
	"Palazzo Moriggia | Museo del Risorgimento":                          "museo-risorgimento-milano",
	"Pinacoteca Ambrosiana":                                              "pinacoteca-ambrosiana",
	"Palazzo Morando | Costume Moda Immagine":                            "palazzo-morando-milano",
	"Museo Poldi Pezzoli":                                                "museo-poldi-pezzoli",
	"Museo Bagatti Valsecchi":                                            "museo-bagatti-valsecchi",
	"Galleria d'Arte Moderna":                                            "galleria-arte-moderna-milano",
	"Raccolte Artistiche del Castello Sforzesco":                         "castello-sforzesco-art-collections",
	"Museo Nazionale della Scienza e della Tecnologia Leonardo da Vinci": "museo-scienza-tecnologia-milano",
	"Villa Necchi Campiglio":                                             "villa-necchi-campiglio",
}

func assembleSirbec(ctx context.Context, root, out string) error {
	path := filepath.Join(root, "content/imports/sirbec-20260910/objects.json")
	if e := verify(path); e != nil {
		return e
	}
	var records []map[string]string
	b, e := os.ReadFile(path)
	if e != nil {
		return e
	}
	if e = json.Unmarshal(b, &records); e != nil {
		return e
	}
	if len(records) >= 50000 {
		return fmt.Errorf("truncated source limit")
	}
	index, e := localAuthors(ctx)
	if e != nil {
		return e
	}
	s := newSelection("sirbec")
	seen := map[string]bool{}
	nationalCounts := map[string]int{}
	for _, r := range records {
		if r["nctn"] != "" {
			nationalCounts[r["nctr"]+"-"+r["nctn"]]++
		}
	}
	for _, r := range records {
		s.Decisions["candidates"]++
		name := r["ldcm"]
		slug := sirbecMuseums[name]
		if slug == "" || r["pvcc"] != "Milano" {
			s.Decisions["museum_review"]++
			continue
		}
		if r["auts"] != "" || strings.Contains(r["autn"], "||") || r["qntn"] != "" && r["qntn"] != "1" {
			s.Decisions["qualified_multiple_or_grouped"]++
			continue
		}
		d, display, ok := sirbecDate(r)
		if !ok {
			s.Decisions["creation_date_review"]++
			continue
		}
		a, ok := matchAuthor(index, r["autn"], r["auta"])
		if !ok {
			s.Decisions["authority_review"]++
			continue
		}
		kind := map[string]string{"dipinto": "painting", "disegno": "drawing", "stampa": "print"}[r["ogtd"]]
		if creatorDateConflict(a, d, kind) {
			s.Decisions["creator_creation_conflict"]++
			continue
		}
		id := r["idk"]
		if id == "" {
			return fmt.Errorf("missing SIRBEC ID")
		}
		identity := id
		if r["nctn"] != "" {
			identity = r["nctr"] + "-" + r["nctn"]
			if nationalCounts[identity] > 1 {
				s.Decisions["shared_national_identity_review"]++
				continue
			}
		}
		if seen[identity] {
			s.Decisions["duplicate_catalogue_identity"]++
			continue
		}
		seen[identity] = true
		title := r["sgtt"]
		if title == "" {
			title = r["sgti"]
		}
		if title == "" {
			s.Decisions["title_review"]++
			continue
		}
		url := strings.Replace(r["url"], "http://", "https://", 1)
		if !strings.HasPrefix(url, "https://www.lombardiabeniculturali.it/opere-arte/schede/") {
			return fmt.Errorf("unexpected SIRBEC URL")
		}
		key := "sirbec-" + slug
		s.Museums[key] = map[string]string{"id": key, "name": name, "city": "Milan", "country": "IT", "data_url": "https://www.dati.lombardia.it/resource/5gfm-gsfr.json", "data_route": "SIRBeC museum-object metadata; explicit reviewed institution crosswalk; Academy of Brera distinct from Pinacoteca di Brera", "rights": "Dataset 5gfm-gsfr: CC0 metadata. Image links are not an image reuse license; no images imported.", "rights_url": "https://dati.comune.milano.it/dataset/ds617_opere_darte_conservate_nei_musei_nel_comune_di_milano"}
		s.Definitions[key] = map[string]string{"Slug": slug, "Source": key, "Website": "https://www.lombardiabeniculturali.it/", "Host": "www.lombardiabeniculturali.it"}
		dimensions := strings.TrimSpace(r["misa"] + " × " + r["misl"] + " " + r["misu"])
		if r["misa"] == "" || r["misl"] == "" {
			dimensions = ""
		}
		desc := fmt.Sprintf("%s — %s. %s.\n\nMedium: %s. Dimensions: %s.\n\nCollection: %s, Milan. SIRBeC catalogue record %s (not a museum inventory number). Holding only; current display unverified.\n\n", title, a.Name, display, r["mtc"], dimensions, name, id)
		if t := strings.TrimSpace(r["deso"]); len(t) > 0 && len(t) < 10000 {
			desc += "Catalogue description (Italian):\n\n" + t + "\n\n"
		}
		if t := strings.TrimSpace(r["nsc"]); len(t) > 0 && len(t) < 15000 {
			desc += "Catalogue note (Italian):\n\n" + t + "\n\n"
		}
		desc += "Source: [Regione Lombardia — SIRBeC](" + url + "), CC0 dataset 5gfm-gsfr retrieved 10 September 2026. Photo rights are separate."
		s.addAuthor(r["autn"], r["auta"], a)
		s.Works = append(s.Works, map[string]any{"painter": a.QID, "title": title, "institution": key, "url": url, "source_object_id": id, "source_publisher": "Regione Lombardia — SIRBeC", "date_display": display, "creation_date": d, "attribution_role": "primary", "work_type": map[string]string{"dipinto": "painting", "disegno": "drawing", "stampa": "print"}[r["ogtd"]], "medium": r["mtc"], "dimensions": dimensions, "description_md": desc, "notes": "SIRBeC physical collection fields establish museum connection, not current display or ownership. Catalogue ID is not an accession number. Author lifespan and catalogue editing years are never used as work dates.", "source_raw": r})
	}
	return s.write(out)
}
