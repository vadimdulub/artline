package main

import (
	"context"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

const karlsruheDir = "content/imports/popular-resume-20260911-1852/karlsruhe"
const karlsruheNextDir = "content/imports/data-collection-20260911-2016/karlsruhe-next"

func karlsruheCaptureDir(file string) string {
	if strings.HasPrefix(file, "next-") {
		return karlsruheNextDir
	}
	return karlsruheDir
}

type karlsruheFact struct {
	File, SHA, Artist, QID, Title, Translation, Date, Acc, Material, Technique, SizeField, Size, Kind string
	Dates                                                                                             creationDate
}

var karlsruheFacts = []karlsruheFact{
	{"klee-anna", "4586de2d7c7902f5c54da81a46adf91d573de7651255de5ecedd538194af6876", "Paul Klee", "Q44007", "Anna und Leopold", "Anna and Leopold", "1918", "1955-1", "Papier gelblich aufgezogen", "Feder in schwärzlichem Blau", "Maße Blatt", "H 28,9 cm B 22,0 cm", "Zeichnung", creationDate{1918, 1918, "exact"}},
	{"klee-river", "353f6bd2e4427532e9fab56db0c13a83218a82890102a35641556b48fbc115eb", "Paul Klee", "Q44007", "Flussbaulandschaft", "River Construction Landscape", "1924", "2361", "Leinwand", "Ölfarbe", "Maße Bildträger", "H 36,0 cm B 53,7 cm", "Gemälde", creationDate{1924, 1924, "exact"}},
	{"friedrich-reef", "8113d48646b53bc8c20e0ad6a96399425c185d9ac8c67b23900e263d724402e2", "Caspar David Friedrich", "Q104884", "Felsenriff am Meeresstrand", "Rocky Reef on the Sea Shore", "1824", "2261", "Leinwand", "Ölfarbe", "Maße Bildträger", "H 22,0 cm B 31,0 cm", "Gemälde", creationDate{1824, 1824, "exact"}},
	{"gauguin-houses", "c77a81b2b27d107649e40ce1cd07f174c08913a053eae91b242a5733b6246e4e", "Paul Gauguin", "Q37693", "Häuser in Le Pouldu", "Houses in Le Pouldu", "1890", "2503", "Leinwand", "Ölfarbe", "Maße Bildträger", "H 92,0 cm B 73,0 cm", "Gemälde", creationDate{1890, 1890, "exact"}},
	{"cezanne-estaque", "58399bf10d596d703b6142ce092b92e1ca7eb910b0a1f45369dc6050f04041c0", "Paul Cézanne", "Q35548", "Blick auf das Meer bei L'Estaque", "View of the Sea at L'Estaque", "1883-1885", "2450", "Leinwand", "Ölfarbe", "Maße Bildträger", "H 100,0 cm B 81,0 cm", "Gemälde", creationDate{1883, 1885, "range"}},
	{"degas-jeantaud", "65483fe9c3e9164becd6d2f327704eea5e26b8c7139b895be23d95d5f2789441", "Edgar Degas", "Q46373", "Bildnis Madame Jeantaud", "Portrait of Madame Jeantaud", "um 1877", "2493", "Leinwand", "Ölfarbe", "Maße Bildträger", "H 83,0 cm B 75,5 cm", "Gemälde", creationDate{1877, 1877, "circa"}},
	{"monet-seine", "8dad3d3f35248b64992b6e6b3e1b517c451cf6c5f0567955a6436e3cf9da29ac", "Claude Monet", "Q296", "Die Seine bei Rouen", "The Seine at Rouen", "1874", "2502", "Leinwand", "Ölfarbe", "Maße Bildträger", "H 50,5 cm B 65,5 cm", "Gemälde", creationDate{1874, 1874, "exact"}},
}

func karlsruhePage(f karlsruheFact) string {
	for _, p := range append(append([]popularPage{}, karlsruhePages...), karlsruheNextPages...) {
		if p.File == f.File+".html" {
			return p.URL
		}
	}
	return ""
}

func karlsruheFields(s string) (map[string]string, error) {
	fields := map[string]string{}
	for _, m := range regexp.MustCompile(`(?s)<tr>\s*<th>(.*?)</th>\s*<td>(.*?)</td>\s*</tr>`).FindAllStringSubmatch(s, -1) {
		key := athensText(m[1])
		if key == "" {
			continue
		}
		if _, ok := fields[key]; ok {
			return nil, fmt.Errorf("duplicate Karlsruhe field: %s", key)
		}
		fields[key] = athensText(m[2])
	}
	return fields, nil
}

func verifyKarlsruhe(s string, f karlsruheFact) error {
	canonical, err := url.PathUnescape(karlsruhePage(f))
	if err != nil {
		return err
	}
	if f.File == "cezanne-estaque" {
		canonical = strings.Replace(canonical, "Paul-Cezanne/Blick-auf-das-Meer-bei-L-Estaque", "Paul-Cézanne/Blick-auf-das-Meer-bei-L'Estaque", 1)
	}
	if strings.HasPrefix(f.File, "next-boucher-") {
		// Museum's own canonical slug contains an incomplete UTF-8 byte; object UUID and
		// complete catalogue fields, not that damaged name slug, establish identity.
		canonical = strings.Replace(canonical, "Fran-ois-Boucher/", "Fran\xc3-ois-Boucher/", 1)
	}
	if !strings.Contains(s, `rel="canonical" href="`+canonical+`"`) {
		return fmt.Errorf("Karlsruhe canonical mismatch")
	}
	fields, err := karlsruheFields(s)
	if err != nil {
		return err
	}
	for key, want := range map[string]string{"Titel": f.Title, "Künstler*in": f.Artist, "Entstehungszeit": f.Date, "Inventarnummer": f.Acc, "Material": f.Material, "Technik": f.Technique, f.SizeField: f.Size, "Gattung": f.Kind} {
		if fields[key] != want {
			return fmt.Errorf("%s %s: got %q want %q", f.File, key, fields[key], want)
		}
	}
	return nil
}

func assembleKarlsruhe(ctx context.Context, root, out string) error {
	return assembleKarlsruheBatch(ctx, root, out, "popular-karlsruhe", karlsruheFacts)
}

func assembleKarlsruheBatch(ctx context.Context, root, out, source string, facts []karlsruheFact) error {
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
	s := newSelection(source)
	s.AccessedOn = "2026-09-11"
	key, slug := source+"-museum", "staatliche-kunsthalle-karlsruhe"
	s.Museums[key] = map[string]string{"id": key, "name": "Staatliche Kunsthalle Karlsruhe", "city": "Karlsruhe", "country": "DE", "data_url": "https://www.kunsthalle-karlsruhe.de/sammlung/", "data_route": "Seven individually reviewed factual catalogue notices. No essays or exhibition-loan inference.", "rights": "Factual fields only. Image rights checked separately against exact Public Domain marks and CC0 policy.", "rights_url": "https://www.kunsthalle-karlsruhe.de/en/cc0/"}
	s.Definitions[key] = map[string]string{"Host": "www.kunsthalle-karlsruhe.de", "Slug": slug, "Source": key, "Website": "https://www.kunsthalle-karlsruhe.de/"}
	if source == "popular-karlsruhe-next" {
		s.Museums[key]["data_route"] = "Four individually reviewed factual catalogue notices. No essays or exhibition-loan inference."
	}
	decisions := []map[string]any{}
	for _, f := range facts {
		file := filepath.Join(root, karlsruheCaptureDir(f.File), f.File+".html")
		if err = verify(file); err != nil {
			return err
		}
		sha, _, e := hashFile(file)
		if e != nil || sha != f.SHA {
			return fmt.Errorf("Karlsruhe pinned snapshot mismatch: %s", f.File)
		}
		b, e := os.ReadFile(file)
		if e != nil {
			return e
		}
		if e = verifyKarlsruhe(string(b), f); e != nil {
			return e
		}
		a := index[authorityKey(f.Artist)]
		kind := "painting"
		if f.Kind == "Zeichnung" {
			kind = "drawing"
		}
		if len(a) != 1 || a[0].QID != f.QID || popular[f.QID] == "" || !dateEligible(f.Dates) || creatorDateConflict(a[0], f.Dates, kind) {
			return fmt.Errorf("Karlsruhe creator/date gate: %s", f.File)
		}
		page := karlsruhePage(f)
		parts := strings.Split(strings.TrimRight(page, "/"), "/")
		objectID := parts[len(parts)-1]
		var n int
		err = p.QueryRow(ctx, `SELECT count(*) FROM artworks a WHERE
 EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.canonical_url ILIKE $1)
 OR EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id AND c.source_url ILIKE $1)
 OR (a.accession_number=$2 AND EXISTS(SELECT 1 FROM institutions i WHERE i.id=a.current_institution_id AND (i.slug=$3 OR i.name ILIKE '%Kunsthalle%Karlsruhe%')))`, "%kunsthalle-karlsruhe.de/%"+objectID+"%", f.Acc, slug).Scan(&n)
		if err != nil {
			return err
		}
		reason := "eligible"
		if n > 0 {
			reason = "existing exact object preserved"
		} else {
			if err = p.QueryRow(ctx, athensTitleCollisionSQL, f.Title, f.Translation, popular[f.QID]).Scan(&n); err != nil {
				return err
			}
			if n > 0 {
				reason = "same-title identity requires reconciliation"
			}
		}
		decisions = append(decisions, map[string]any{"artist": f.Artist, "title": f.Title, "accession": f.Acc, "source": page, "decision": reason, "image": "separate exact-image rights/identity review required"})
		s.Decisions[reason]++
		if reason != "eligible" {
			continue
		}
		s.addAuthor(f.Artist, "", a[0])
		desc := fmt.Sprintf("%s — %s. %s.\n\n%s; %s. %s. Inventory %s.\n\nDocumented holding: Staatliche Kunsthalle Karlsruhe, Germany.\n\n[Official object notice](%s), accessed 11 September 2026. Factual catalogue fields only; no copied essay. English alternate title is a research translation. No current-display, ownership or masterpiece claim inferred from exhibition history.", f.Title, f.Artist, f.Date, f.Technique, f.Material, f.Size, f.Acc, page)
		s.Works = append(s.Works, map[string]any{"painter": f.QID, "title": f.Title, "aliases": []string{f.Translation}, "institution": key, "accession": f.Acc, "url": page, "source_object_id": objectID, "source_publisher": "Staatliche Kunsthalle Karlsruhe", "date_display": f.Date, "creation_date": f.Dates, "attribution_role": "primary", "work_type": kind, "medium": f.Technique + "; " + f.Material, "dimensions": f.Size, "description_md": desc, "source_raw": map[string]string{"url": page, "snapshot_sha256": sha, "scope": "individually reviewed factual catalogue fields"}})
	}
	if err = save(filepath.Join(out, "decisions.json"), decisions); err != nil {
		return err
	}
	return s.write(out)
}

var karlsruhePages = []popularPage{
	{"robots.txt", "https://www.kunsthalle-karlsruhe.de/robots.txt"},
	{"cc0.html", "https://www.kunsthalle-karlsruhe.de/en/cc0/"},
	{"legal.html", "https://www.kunsthalle-karlsruhe.de/haftungsausschluss/"},
	{"klee-anna.html", "https://www.kunsthalle-karlsruhe.de/kunstwerke/Paul-Klee/Anna-und-Leopold/E148B51E444ABE7CD2530581C8E05E39/"},
	{"klee-river.html", "https://www.kunsthalle-karlsruhe.de/kunstwerke/Paul-Klee/Flussbaulandschaft/188A74D2AC1C482D9FCBBE8112ADB1D1/"},
	{"friedrich-reef.html", "https://www.kunsthalle-karlsruhe.de/kunstwerke/Caspar-David-Friedrich/Felsenriff-am-Meeresstrand/0C3519DA4BC388DB571C6A8C3849C9B6/"},
	{"gauguin-houses.html", "https://www.kunsthalle-karlsruhe.de/kunstwerke/Paul-Gauguin/H%C3%A4user-in-Le-Pouldu/A80F0323437B4793605003B5612B2854/"},
	{"cezanne-estaque.html", "https://www.kunsthalle-karlsruhe.de/kunstwerke/Paul-Cezanne/Blick-auf-das-Meer-bei-L-Estaque/662299E04C2A03FEAC450DB1CD0D0BD1/"},
	{"degas-jeantaud.html", "https://www.kunsthalle-karlsruhe.de/kunstwerke/Edgar-Degas/Bildnis-Madame-Jeantaud/0147A51A406583D3FC38049178ABBB14/"},
	{"monet-seine.html", "https://www.kunsthalle-karlsruhe.de/kunstwerke/Claude-Monet/Die-Seine-bei-Rouen/E6F223D04821161F32098BB6AFFA6E2F/"},
}

func karlsruhePageAllowed(raw string) bool {
	for _, p := range append(append([]popularPage{}, karlsruhePages...), karlsruheNextPages...) {
		if p.URL == raw {
			return true
		}
	}
	return false
}

// Separate closed batch; the original selection and capture hashes remain intact.
var karlsruheNextPages = []popularPage{
	{"next-boucher-shepherd.html", "https://www.kunsthalle-karlsruhe.de/kunstwerke/Fran-ois-Boucher/Sch%C3%A4fer-und-Sch%C3%A4ferin/9691F6DF4A05F5B63AAA6C948846690E/"},
	{"next-boucher-two.html", "https://www.kunsthalle-karlsruhe.de/kunstwerke/Fran-ois-Boucher/Zwei-Sch%C3%A4ferinnen/7F77FF604604E535FEB4DD933D15D82B/"},
	{"next-pissarro-rouen.html", "https://www.kunsthalle-karlsruhe.de/kunstwerke/Camille-Pissarro/Blick-auf-die-Grosse-Br%C3%BCcke-zu-Rouen-bei-Regenstimmung/8F81E0C1497EE8F69F83898D8C72C126/"},
	{"next-rubens-constantinople.html", "https://www.kunsthalle-karlsruhe.de/kunstwerke/Peter-Paul-Rubens/Die-Gr%C3%BCndung-Konstantinopels/6336539F49C73E6486A6528246DD7026/"},
}

var karlsruheNextFacts = []karlsruheFact{
	{"next-boucher-shepherd", "bf9e42d457afc7e638a285a570b6d9bd7a2fdb3cbe26d9c888459a5c2a67e6a1", "François Boucher", "Q180932", "Schäfer und Schäferin", "Shepherd and Shepherdess", "1760", "479", "Leinwand", "Ölfarbe", "Maße Bildträger", "H 64,5 cm B 81,0 cm", "Gemälde", creationDate{1760, 1760, "exact"}},
	{"next-boucher-two", "cc9890ea3740c71e261d5fab64535e3f74df79b99096368128fac72d6dd2413c", "François Boucher", "Q180932", "Zwei Schäferinnen", "Two Shepherdesses", "1760", "480", "Leinwand", "Ölfarbe", "Maße Bildträger", "H 64,0 cm B 80,5 cm", "Gemälde", creationDate{1760, 1760, "exact"}},
	{"next-pissarro-rouen", "50c4c4905a9008eb90f0813cb046e03c8050b38141acf7b39432dbbe79a94876", "Camille Pissarro", "Q134741", "Blick auf die Grosse Brücke zu Rouen bei Regenstimmung", "View of the Great Bridge at Rouen in Rainy Weather", "1896", "2488", "Leinwand", "Ölfarbe", "Maße Bildträger", "H 73,0 cm B 92,0 cm", "Gemälde", creationDate{1896, 1896, "exact"}},
	{"next-rubens-constantinople", "7982bbd59e940370ae93b5f9ed044255280befe6a5cb246bd0dae04d7b77577e", "Peter Paul Rubens", "Q5599", "Die Gründung Konstantinopels", "The Foundation of Constantinople", "um 1622-1623", "2759", "Eichenholz", "Ölfarbe", "Maße Bildträger", "H 41,3 cm B 40,7 cm", "Gemälde", creationDate{1622, 1623, "circa_range"}},
}
