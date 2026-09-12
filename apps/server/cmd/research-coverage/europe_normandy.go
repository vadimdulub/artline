package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

// The extractor only captures factual labels. Selection, authority resolution,
// date eligibility and physical-unit validation stay in this offline Go stage.
type normandyFact struct {
	URL, Title, Source, State, Canonical, Artist, Details, Shortlink string
	ArtistDetails                                                    string `json:"artist_details"`
	Lines                                                            []string
	Snapshot                                                         snapshot
	SnapshotFile                                                     string `json:"snapshot_file"`
}

var normandyLife = regexp.MustCompile(`^(.+?)\s*\((\d{4})\s*[-–]\s*(\d{4})\)$`)
var normandyDateRE = regexp.MustCompile(`(?i)^(?:(vers|ca\.|c\.)\s*)?(\d{4})(?:\s*[-–/]\s*(\d{4}))?$`)
var normandyQualified = regexp.MustCompile(`(?i)\b(attribu|atelier|entourage|suiveur|copie|copié|après|d'après|ou|école)\b`)

func normandyDate(literal string) (creationDate, bool) {
	m := normandyDateRE.FindStringSubmatch(strings.TrimSpace(literal))
	if m == nil {
		return creationDate{}, false
	}
	a, _ := strconv.Atoi(m[2])
	b := a
	if m[3] != "" {
		b, _ = strconv.Atoi(m[3])
	}
	d := creationDate{a, b, "exact"}
	if a != b {
		d.Precision = "range"
	}
	if m[1] != "" {
		d.Precision = "circa"
		if a != b {
			d.Precision = "circa_range"
		}
	}
	return d, dateEligible(d)
}

func normandyFields(f normandyFact) (name, life, title, date, medium, dimensions, accession, reason string) {
	if f.State != "extracted" {
		reason = "physical_unit_or_layout_review"
		return
	}
	title = f.Title
	if f.Source == "muma" {
		if len(f.Lines) < 5 {
			reason = "caption_structure_review"
			return
		}
		m := normandyLife.FindStringSubmatch(f.Lines[0])
		if m == nil {
			reason = "creator_label_review"
			return
		}
		name, life = strings.TrimSpace(m[1]), m[2]+"-"+m[3]
		title, date, medium, dimensions = f.Lines[1], f.Lines[2], f.Lines[3], f.Lines[4]
	} else {
		name = f.Artist
		parts := strings.Split(f.ArtistDetails, "|")
		if len(parts) != 2 {
			reason = "inventory_label_review"
			return
		}
		m := normandyLife.FindStringSubmatch(name + " " + strings.TrimSpace(parts[0]))
		if m == nil {
			reason = "creator_label_review"
			return
		}
		life, accession = m[2]+"-"+m[3], strings.TrimSpace(parts[1])
		if accession == "" {
			reason = "missing_inventory"
			return
		}
		parts = strings.Split(f.Details, "|")
		if len(parts) != 2 || !strings.HasPrefix(parts[0], "Date :") || !strings.HasPrefix(strings.TrimSpace(parts[1]), "Technique :") {
			reason = "date_medium_label_review"
			return
		}
		date = strings.TrimSpace(strings.TrimPrefix(parts[0], "Date :"))
		medium = strings.TrimSpace(strings.TrimPrefix(strings.TrimSpace(parts[1]), "Technique :"))
	}
	// "ou" inside an artwork title is commonly an alternate title, not a
	// qualified creator. Only the MuMa heading's creator portion is checked.
	headingCreator := ""
	if f.Source == "muma" {
		headingCreator = strings.Split(f.Title, ",")[0]
	}
	if normandyQualified.MatchString(name) || normandyQualified.MatchString(headingCreator) {
		reason = "qualified_attribution_review"
		return
	}
	if title == "" || strings.Contains(title, " & ") {
		reason = "physical_unit_review"
	}
	return
}

func assembleNormandy(ctx context.Context, root, source, out string) error {
	dir := filepath.Join(root, "content/imports/normandy-primary-20260910")
	b, e := os.ReadFile(filepath.Join(dir, source+"-facts.json"))
	if e != nil {
		return e
	}
	var capture struct {
		Source   string
		Works    []normandyFact
		Complete bool `json:"complete_for_selected_pages"`
	}
	if e = json.Unmarshal(b, &capture); e != nil {
		return e
	}
	if capture.Source != source || !capture.Complete || len(capture.Works) == 0 || len(capture.Works) > 120 {
		return fmt.Errorf("incomplete/unbounded capture")
	}
	index, e := localAuthors(ctx)
	if e != nil {
		return e
	}
	key := "normandy-" + source
	s := newSelection(key)
	s.AccessedOn = "2026-09-10"
	host, slug, city, museum := "www.muma-lehavre.fr", "muma-le-havre", "Le Havre", "MuMa - Musée d’art moderne André Malraux"
	if source == "rouen" {
		host, slug, city, museum = "mbarouen.fr", "musee-beaux-arts-rouen", "Rouen", "Musée des Beaux-Arts de Rouen"
	}
	s.Definitions[key] = map[string]string{"Slug": slug, "Source": key, "Website": "https://" + host, "Host": host}
	s.Museums[key] = map[string]string{"id": key, "name": museum, "city": city, "country": "FR", "data_url": "https://" + host + "/fr/collections", "data_route": "Selected official collection pages; factual labels only, not the full collection", "rights": "Factual metadata and source links only; curatorial texts and reproductions not licensed by this import.", "rights_url": "https://" + host + "/fr/mentions-legales"}
	deferred := []map[string]string{}
	seen := map[string]bool{}
	for _, f := range capture.Works {
		s.Decisions["examined"]++
		u, e := url.Parse(f.URL)
		if e != nil || u.Scheme != "https" || u.Host != host || u.RawQuery != "" || u.Fragment != "" || u.User != nil || seen[f.URL] {
			return fmt.Errorf("unapproved/duplicate object URL")
		}
		seen[f.URL] = true
		canonical, e := u.Parse(f.Canonical)
		if f.State == "extracted" && (e != nil || canonical.String() != f.URL) {
			return fmt.Errorf("canonical identity conflict: %s", f.URL)
		}
		if f.SnapshotFile != filepath.Base(f.SnapshotFile) || f.Snapshot.URL != f.URL {
			return fmt.Errorf("unsafe snapshot identity")
		}
		path := filepath.Join(dir, f.SnapshotFile)
		if e = verify(path); e != nil {
			return e
		}
		h, n, e := hashFile(path)
		if e != nil {
			return e
		}
		if h != f.Snapshot.SHA || n != f.Snapshot.Bytes || f.Snapshot.Retrieved.Format("2006-01-02") != s.AccessedOn {
			return fmt.Errorf("snapshot receipt mismatch")
		}
		name, life, title, literal, medium, dimensions, accession, reason := normandyFields(f)
		a, matched := matchAuthor(index, name, life)
		d, dated := normandyDate(literal)
		kind := ""
		m := strings.ToLower(medium)
		switch {
		case strings.HasPrefix(m, "huile"), strings.HasPrefix(m, "tempera"):
			kind = "painting"
		case strings.HasPrefix(m, "pastel"), strings.HasPrefix(m, "aquarelle"), strings.HasPrefix(m, "crayon"), strings.HasPrefix(m, "fusain"), strings.HasPrefix(m, "sanguine"):
			kind = "drawing"
		}
		if reason == "" && !matched {
			reason = "authority_or_lifespan_review"
		}
		if reason == "" && !dated {
			reason = "creation_date_review"
		}
		if reason == "" && kind == "" {
			reason = "medium_review"
		}
		if reason == "" && creatorDateConflict(a, d, kind) {
			reason = "creator_creation_conflict"
		}
		if reason != "" {
			s.Decisions[reason]++
			deferred = append(deferred, map[string]string{"url": f.URL, "title": f.Title, "reason": reason, "source_artist": name, "source_life": life, "source_date": literal, "source_medium": medium})
			continue
		}
		s.addAuthor(name, life, a)
		desc := fmt.Sprintf("%s — %s. %s.\n\nMedium: %s.", title, a.Name, literal, medium)
		if dimensions != "" {
			desc += " Dimensions: " + dimensions + "."
		}
		desc += fmt.Sprintf("\n\nCollection: %s, %s, France.", museum, city)
		if accession != "" {
			desc += " Inventory: " + accession + "."
		}
		desc += fmt.Sprintf("\n\nFactual labels from the [official museum collection record](%s), checked 10 September 2026. Holding only; current display is unverified. The museum's curatorial essay and photograph have not been reproduced.", f.URL)
		w := map[string]any{"painter": a.QID, "title": title, "institution": key, "accession": accession, "url": f.URL, "source_object_id": strings.TrimPrefix(u.Path, "/fr/"), "source_publisher": museum, "date_display": literal, "creation_date": d, "attribution_role": "primary", "work_type": kind, "medium": medium, "dimensions": dimensions, "description_md": desc, "source_raw": f, "notes": "Selected official collection record. No current-display inference; existing editorial values preserved."}
		if source == "muma" {
			w["museum_highlight_url"] = "https://www.muma-lehavre.fr/fr/collections/oeuvres-commentees/incontournable"
			for _, line := range f.Lines[5:] {
				if strings.HasPrefix(line, "Collection ") {
					w["collection"] = line
				}
			}
			if strings.HasSuffix(f.URL, "/monet-les-nympheas") {
				// The main caption says 89 x 93, but header/HD caption says 89 x 92.
				// Preserve the source conflict, not an arbitrary canonical measurement.
				w["dimensions"] = ""
				w["description_md"] = strings.Replace(desc, " Dimensions: "+dimensions+".", " Dimensions require review: the main caption gives 89 × 93 cm; the header/HD caption gives 89 × 92 cm.", 1)
				w["notes"] = "MuMa caption dimension conflict retained for editorial review: 89 x 93 versus 89 x 92 cm. No current-display inference."
			}
		}
		s.Works = append(s.Works, w)
	}
	if e = save(filepath.Join(out, "deferred.json"), deferred); e != nil {
		return e
	}
	return s.write(out)
}

func assembleNormandyJoconde(ctx context.Context, root, out string) error {
	index, e := localAuthors(ctx)
	if e != nil {
		return e
	}
	w := &jocondeWave{Source: "normandy-joconde", Museums: map[string]string{"M0720": "muma-le-havre", "M0729": "musee-beaux-arts-rouen"}, BlockedAuthorities: map[string]bool{}, InventoryCounts: map[string]int{}}
	// Individually reviewed against the four primary Pissarro pages and the
	// pre-import DB: two separate 1903 port paintings with different inventories,
	// not the 1876/1882/1894/1901 scenes. This is creation, never a title-only merge.
	w.ReviewedNonoverlap = map[string]string{"07200001088": "A 494", "07200001089": "A 495"}
	// Block every uniquely resolvable primary-page creator, including deferred
	// pages with wrong/unknown dates or lifespan labels. No same-artist cross-source
	// accession reconciliation is silently attempted in this supplemental batch.
	for _, source := range []string{"muma", "rouen"} {
		b, e := os.ReadFile(filepath.Join(root, "content/imports/normandy-primary-20260910", source+"-facts.json"))
		if e != nil {
			return e
		}
		var cap struct {
			Works    []normandyFact
			Complete bool `json:"complete_for_selected_pages"`
		}
		if e = json.Unmarshal(b, &cap); e != nil || !cap.Complete {
			return fmt.Errorf("incomplete primary comparison")
		}
		code := "M0720"
		if source == "rouen" {
			code = "M0729"
		}
		for _, f := range cap.Works {
			name := f.Artist
			if source == "muma" && len(f.Lines) > 0 {
				if m := normandyLife.FindStringSubmatch(f.Lines[0]); m != nil {
					name = m[1]
				}
			}
			if a, ok := matchAuthor(index, name, ""); ok {
				w.BlockedAuthorities[code+"|"+a.QID] = true
			}
			// Additional conservative surname exclusion catches grouped MuMa pages
			// and qualified/compound page headings without resolving an attribution.
			if source == "muma" {
				heading := strings.Split(f.Title, ",")[0]
				tokens := strings.Fields(authorityKey(heading))
				for _, authors := range index {
					for _, a := range authors {
						parts := strings.Fields(authorityKey(a.Name))
						for _, t := range tokens {
							if len(t) >= 4 {
								for _, p := range parts {
									if p == t {
										w.BlockedAuthorities[code+"|"+a.QID] = true
									}
								}
							}
						}
					}
				}
			}
		}
	}
	path := filepath.Join(root, "content/imports/joconde-20260910/joconde.csv")
	if e := verify(path); e != nil {
		return e
	}
	if e := csvRows(path, '|', func(r map[string]string) error {
		if w.Museums[r["code_museofile"]] != "" {
			w.InventoryCounts[r["code_museofile"]+"|"+r["numero_inventaire"]]++
		}
		return nil
	}); e != nil {
		return e
	}
	if e := save(filepath.Join(out, "overlap-gates.json"), w); e != nil {
		return e
	}
	return assembleJocondeWave(ctx, root, out, w)
}

func normandyReviewedNonoverlap(w *jocondeWave, r map[string]string, a knownAuthor, d creationDate) bool {
	return w.Source == "normandy-joconde" && r["code_museofile"] == "M0720" && a.QID == "Q134741" &&
		d.First == 1903 && d.Last == 1903 && d.Precision == "exact" && w.ReviewedNonoverlap[r["reference"]] != "" && w.ReviewedNonoverlap[r["reference"]] == r["numero_inventaire"]
}

// Museum discovery and coverage audit reuses complete official open metadata.
// It does not turn directory entries into holdings or create empty museums.
func auditNormandy(root, out string) error {
	paths := []string{"content/imports/museofile-20260909/museofile.csv", "content/imports/joconde-20260910/joconde.csv"}
	for _, p := range paths {
		if e := verify(filepath.Join(root, p)); e != nil {
			return e
		}
	}
	museums := map[string]map[string]any{}
	e := csvRows(filepath.Join(root, paths[0]), '|', func(r map[string]string) error {
		if r["region"] != "Normandie" {
			return nil
		}
		art := strings.Contains(strings.ToLower(r["themes"]+" "+r["domaine_thematique"]), "peinture")
		museums[r["identifiant"]] = map[string]any{"code": r["identifiant"], "name": r["nom_officiel"], "city": r["ville"], "website_as_recorded": r["url"], "source_url": "https://pop.culture.gouv.fr/notice/museo/" + r["identifiant"], "painting_candidate": art, "source_updated": r["date_de_mise_a_jour"], "catalogue_records": 0, "painting_records": 0, "drawing_records": 0, "print_records": 0}
		return nil
	})
	if e != nil {
		return e
	}
	regionalRows := []map[string]string{}
	e = csvRows(filepath.Join(root, paths[1]), '|', func(r map[string]string) error {
		m := museums[r["code_museofile"]]
		if m == nil {
			return nil
		}
		m["catalogue_records"] = m["catalogue_records"].(int) + 1
		for _, pair := range [][2]string{{"peinture", "painting_records"}, {"dessin", "drawing_records"}, {"estampe", "print_records"}} {
			for _, term := range strings.Split(strings.ToLower(r["domaine"]), ";") {
				if strings.TrimSpace(term) == pair[0] {
					m[pair[1]] = m[pair[1]].(int) + 1
					break
				}
			}
		}
		if r["ville"] == "Rouen" || r["ville"] == "Le Havre" {
			if strings.Contains(strings.ToLower(r["domaine"]), "peinture") {
				regionalRows = append(regionalRows, r)
			}
		}
		return nil
	})
	if e != nil {
		return e
	}
	list := []map[string]any{}
	for _, m := range museums {
		list = append(list, m)
	}
	sort.Slice(list, func(i, j int) bool { return list[i]["code"].(string) < list[j]["code"].(string) })
	if e = save(filepath.Join(out, "museum-directory.json"), list); e != nil {
		return e
	}
	if e = save(filepath.Join(out, "joconde-havre-rouen-paintings.json"), regionalRows); e != nil {
		return e
	}
	fmt.Printf("Normandy official register: %d museums; %d Le Havre/Rouen painting candidates for reconciliation, not automatic import\n", len(list), len(regionalRows))
	return nil
}
