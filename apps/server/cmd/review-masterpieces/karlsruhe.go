package main

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"html"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/jackc/pgx/v5/pgxpool"
)

const karlsruhePolicy = "https://www.kunsthalle-karlsruhe.de/en/cc0/"
const karlsruhePolicySHA = "7ca1109657155b49feb626b7730bd8a374c2a407e0e4e76ce18768a2192f80ae"
const karlsruheCC0 = "https://creativecommons.org/publicdomain/zero/1.0/"
const karlsruheImageDir = "content/imports/popular-resume-20260911-1852/karlsruhe"

func karlsruheImageCaptureDir(f karlsruheImageFact) string {
	if strings.HasPrefix(f.File, "next-") {
		return "content/imports/data-collection-20260911-2016/karlsruhe-next"
	}
	return karlsruheImageDir
}
func karlsruheImageSource(f karlsruheImageFact) string {
	if strings.HasPrefix(f.File, "next-") {
		return "popular-karlsruhe-next"
	}
	return "popular-karlsruhe"
}

type karlsruheImageFact struct {
	File, SHA, Object, Acc, Artist, Title, Slug, Date, Precision string
	First, Last                                                  int
}

var karlsruheImageFacts = []karlsruheImageFact{
	{"next-boucher-shepherd", "bf9e42d457afc7e638a285a570b6d9bd7a2fdb3cbe26d9c888459a5c2a67e6a1", "9691F6DF4A05F5B63AAA6C948846690E", "479", "François Boucher", "Schäfer und Schäferin", "Fran-ois-Boucher/Sch%C3%A4fer-und-Sch%C3%A4ferin", "1760", "exact", 1760, 1760},
	{"next-boucher-two", "cc9890ea3740c71e261d5fab64535e3f74df79b99096368128fac72d6dd2413c", "7F77FF604604E535FEB4DD933D15D82B", "480", "François Boucher", "Zwei Schäferinnen", "Fran-ois-Boucher/Zwei-Sch%C3%A4ferinnen", "1760", "exact", 1760, 1760},
	{"next-pissarro-rouen", "50c4c4905a9008eb90f0813cb046e03c8050b38141acf7b39432dbbe79a94876", "8F81E0C1497EE8F69F83898D8C72C126", "2488", "Camille Pissarro", "Blick auf die Grosse Brücke zu Rouen bei Regenstimmung", "Camille-Pissarro/Blick-auf-die-Grosse-Br%C3%BCcke-zu-Rouen-bei-Regenstimmung", "1896", "exact", 1896, 1896},
	{"next-rubens-constantinople", "7982bbd59e940370ae93b5f9ed044255280befe6a5cb246bd0dae04d7b77577e", "6336539F49C73E6486A6528246DD7026", "2759", "Peter Paul Rubens", "Die Gründung Konstantinopels", "Peter-Paul-Rubens/Die-Gr%C3%BCndung-Konstantinopels", "c.1622–1623", "circa_range", 1622, 1623},
	{"klee-anna", "4586de2d7c7902f5c54da81a46adf91d573de7651255de5ecedd538194af6876", "E148B51E444ABE7CD2530581C8E05E39", "1955-1", "Paul Klee", "Anna und Leopold", "Paul-Klee/Anna-und-Leopold", "1918", "exact", 1918, 1918},
	{"klee-river", "353f6bd2e4427532e9fab56db0c13a83218a82890102a35641556b48fbc115eb", "188A74D2AC1C482D9FCBBE8112ADB1D1", "2361", "Paul Klee", "Flussbaulandschaft", "Paul-Klee/Flussbaulandschaft", "1924", "exact", 1924, 1924},
	{"friedrich-reef", "8113d48646b53bc8c20e0ad6a96399425c185d9ac8c67b23900e263d724402e2", "0C3519DA4BC388DB571C6A8C3849C9B6", "2261", "Caspar David Friedrich", "Felsenriff am Meeresstrand", "Caspar-David-Friedrich/Felsenriff-am-Meeresstrand", "1824", "exact", 1824, 1824},
	{"gauguin-houses", "c77a81b2b27d107649e40ce1cd07f174c08913a053eae91b242a5733b6246e4e", "A80F0323437B4793605003B5612B2854", "2503", "Paul Gauguin", "Häuser in Le Pouldu", "Paul-Gauguin/H%C3%A4user-in-Le-Pouldu", "1890", "exact", 1890, 1890},
	{"cezanne-estaque", "58399bf10d596d703b6142ce092b92e1ca7eb910b0a1f45369dc6050f04041c0", "662299E04C2A03FEAC450DB1CD0D0BD1", "2450", "Paul Cézanne", "Blick auf das Meer bei L'Estaque", "Paul-Cezanne/Blick-auf-das-Meer-bei-L-Estaque", "1883–1885", "range", 1883, 1885},
	{"degas-jeantaud", "65483fe9c3e9164becd6d2f327704eea5e26b8c7139b895be23d95d5f2789441", "0147A51A406583D3FC38049178ABBB14", "2493", "Edgar Degas", "Bildnis Madame Jeantaud", "Edgar-Degas/Bildnis-Madame-Jeantaud", "c.1877", "circa", 1877, 1877},
	{"monet-seine", "8dad3d3f35248b64992b6e6b3e1b517c451cf6c5f0567955a6436e3cf9da29ac", "E6F223D04821161F32098BB6AFFA6E2F", "2502", "Claude Monet", "Die Seine bei Rouen", "Claude-Monet/Die-Seine-bei-Rouen", "1874", "exact", 1874, 1874},
}
var karlsruheImagePicks = func() []coveragePick {
	var picks []coveragePick
	for _, f := range karlsruheImageFacts {
		picks = append(picks, coveragePick{karlsruheImageSource(f), f.Object, f.Artist, "Exact Karlsruhe catalogue object with per-object Public Domain mark and CC0 museum policy. Full composition, not a masterpiece designation."})
	}
	return picks
}()

func karlsruheCredit(f karlsruheImageFact) string {
	return f.Artist + ", " + f.Title + ", " + f.Date + ". Staatliche Kunsthalle Karlsruhe. CC0 1.0. Resized and JPEG-compressed; no crop or retouching."
}
func karlsruheImage(raw string, f karlsruheImageFact) (string, error) {
	if hash([]byte(raw)) != f.SHA || !strings.Contains(raw, `href="/CCO/"`) || !strings.Contains(raw, `class="creative-commons-text">Public Domain</span>`) {
		return "", errors.New("changed object or missing per-object CC0 evidence")
	}
	// Unique primary image before the viewer, not recommendation cards or alternate views.
	pattern := `(?s)<div id="K` + regexp.QuoteMeta(f.Object) + `"[^>]*data-id="` + regexp.QuoteMeta(f.Object) + `"[^>]*>\s*(<img\b[^>]*>)`
	m := regexp.MustCompile(pattern).FindAllStringSubmatch(raw, -1)
	if len(m) != 1 {
		return "", errors.New("ambiguous main composition")
	}
	src := regexp.MustCompile(`\bsrc="([^"]+)"`).FindStringSubmatch(m[0][1])
	alt := regexp.MustCompile(`\balt="([^"]+)"`).FindStringSubmatch(m[0][1])
	wantAlt := f.Artist + " - " + f.Title
	if f.File == "cezanne-estaque" {
		wantAlt = strings.ReplaceAll(wantAlt, "'", "")
	}
	if len(src) != 2 || len(alt) != 2 || html.UnescapeString(alt[1]) != wantAlt {
		return "", errors.New("main image creator/title mismatch")
	}
	u := html.UnescapeString(src[1])
	if u != "https://www.kunsthalle-karlsruhe.de/wp-content/kunstwerk/jpg/K"+f.Object+".jpg" {
		return "", errors.New("unexpected exact primary image URL")
	}
	return u, nil
}

func validateKarlsruhe(x coverageEntry) error {
	for _, f := range karlsruheImageFacts {
		if f.Object != x.Pick.Object {
			continue
		}
		raw, e := karlsruheRawHTML(x.Raw)
		if e != nil {
			return e
		}
		u, e := karlsruheImage(raw, f)
		if e != nil {
			return e
		}
		page := "https://www.kunsthalle-karlsruhe.de/kunstwerke/" + f.Slug + "/" + f.Object + "/"
		if x.Pick.Source != karlsruheImageSource(f) || x.Accession != f.Acc || x.Candidate.Artist != f.Artist || x.Candidate.Title != f.Title || x.Page != page || x.ImagePage != page || x.ImageURL != u || x.Policy != karlsruhePolicy || x.LicenseURL != karlsruheCC0 || x.License != "CC0 1.0" || x.Rights != "public_domain" || x.Provider != "Staatliche Kunsthalle Karlsruhe" || x.Credit != karlsruheCredit(f) || hash([]byte(str(x.Raw, "policy_html"))) != karlsruhePolicySHA {
			return errors.New("Karlsruhe exact identity/rights mismatch")
		}
		return nil
	}
	return errors.New("unreviewed Karlsruhe image")
}

// A museum canonical slug has a broken UTF-8 byte. Preserve exact raw evidence
// through JSON; replacing that byte silently would invalidate the capture hash.
func karlsruheRawHTML(raw map[string]any) (string, error) {
	if encoded := str(raw, "html_base64"); encoded != "" {
		if str(raw, "html") != "" {
			return "", errors.New("ambiguous HTML encodings")
		}
		b, e := base64.StdEncoding.DecodeString(encoded)
		return string(b), e
	}
	return str(raw, "html"), nil
}

func stageKarlsruhe(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	return stageKarlsruheBatch(ctx, p, root, out, "popular-karlsruhe")
}
func stageKarlsruheBatch(ctx context.Context, p *pgxpool.Pool, root, out, source string) error {
	s := coverageSelection{Version: coverageVersion, Created: time.Now().UTC(), Entries: []coverageEntry{}, Deferred: []string{}}
	policy, e := os.ReadFile(filepath.Join(root, karlsruheImageDir, "cc0.html"))
	if e != nil {
		return e
	}
	if hash(policy) != karlsruhePolicySHA {
		return errors.New("changed Karlsruhe policy")
	}
	for i, pick := range karlsruheImagePicks {
		if pick.Source != source {
			continue
		}
		f := karlsruheImageFacts[i]
		x, e := coverageCandidate(ctx, p, pick)
		if e != nil {
			return e
		}
		if x.Candidate.HasImage {
			s.Deferred = append(s.Deferred, pick.Object+": existing image preserved")
			continue
		}
		file := filepath.Join(root, karlsruheImageCaptureDir(f), f.File+".html")
		b, e := os.ReadFile(file)
		if e != nil {
			return e
		}
		sb, e := os.ReadFile(file + ".snapshot.json")
		if e != nil {
			return e
		}
		var snap struct {
			URL string
			SHA string    `json:"sha256"`
			At  time.Time `json:"retrieved_at"`
		}
		if e = json.Unmarshal(sb, &snap); e != nil {
			return e
		}
		if snap.URL != x.Page || snap.SHA != f.SHA || hash(b) != f.SHA {
			return errors.New("Karlsruhe source receipt mismatch")
		}
		var dateMatches bool
		if e = p.QueryRow(ctx, `SELECT creation_year_start=$2 AND creation_year_end=$3 AND date_precision=$4 FROM artworks WHERE id=$1`, x.Candidate.ID, f.First, f.Last, f.Precision).Scan(&dateMatches); e != nil {
			return e
		}
		if !dateMatches {
			return errors.New("local/source date conflict")
		}
		x.ImageURL, e = karlsruheImage(string(b), f)
		if e != nil {
			return e
		}
		x.ImagePage = x.Page
		x.Provider = "Staatliche Kunsthalle Karlsruhe"
		x.Rights = "public_domain"
		x.License = "CC0 1.0"
		x.LicenseURL = karlsruheCC0
		x.Policy = karlsruhePolicy
		x.Credit = karlsruheCredit(f)
		x.Retrieved = snap.At
		x.Raw = map[string]any{"html": string(b), "policy_html": string(policy), "source_url": snap.URL, "sha256": snap.SHA}
		if !utf8.Valid(b) {
			delete(x.Raw, "html")
			x.Raw["html_base64"] = base64.StdEncoding.EncodeToString(b)
		}
		if e = validateCoverageEntry(x); e != nil {
			return e
		}
		s.Entries = append(s.Entries, x)
	}
	if e = save(out, s); e != nil {
		return e
	}
	b, e := os.ReadFile(out)
	if e != nil {
		return e
	}
	fmt.Printf("Staged %d Karlsruhe images. SHA256 %s. No downloads or DB writes.\n", len(s.Entries), hash(b))
	return nil
}
