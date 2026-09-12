package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"html"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

const nivaPolicy = "https://nivaagaard.dk/en/fri-download/"
const nivaPolicySHA = "9e6b805c40d2bbac1ec6c4e6e7b2e3ae6b59a832cdc92cfacd8a8a37c1f1d89b"
const nivaPD = "https://creativecommons.org/publicdomain/mark/1.0/"
const nivaDir = "content/imports/popular-resume-20260911-1852/nivaagaard"

type nivaImageFact struct {
	Acc, Slug, SHA, Artist, Title, Date, ImagePath, Photographer, Precision string
	First, Last                                                             int
}

var nivaImageFacts = []nivaImageFact{
	{"0001NMK", "anguissola-sofonisba", "750efa857255da538ffb7d0d58fe31d95541f41b601f6f0a1293e7857fa781be", "Sofonisba Anguissola", "Portrait Group with the Artist’s Father Amilcare Anguissola and her siblings Minerva and Asdrubale", "c. 1559", "2023/07/Sofonisba-Anguissola-Familieportraettet.-Portraetgruppe-med-kunstnerens-fader-Amilcare-Anguissola-og-hendes-soeskende-Minerva-og-Astrubale-ca.-1559.jpg", "", "circa", 1559, 1559},
	{"0003NMK", "bellini-giovanni", "0645b4b6576af6623a18c7f79a0721992dedc1b2605fb68ea206a97b0509b6e1", "Giovanni Bellini", "Portrait of a Young Man", "c. 1490", "2023/07/Bellini_Giovanni.jpg", "", "circa", 1490, 1490},
	{"0047NMK", "rijn-rembrandt-harmensz-van", "a0217c7f567d1516e30b127b07d2ee8f6501b5c4b52b70bd2b96aebaa11734bf", "Rembrandt van Rijn", "Portrait of a 39-year-old Woman", "1632", "2016/07/Rembrandt-Harmensz-van-Rijn-Portraet-af-en-39-aarig-kvinde-1632-Foto-David-Kahr-scaled.jpg", "David Kahr", "exact", 1632, 1632},
	{"0261NMK", "gentileschi-artemisia", "1db49e308b9f6631c68b5d75b0a85f78bfb400f57f61d3f458d53e86bee916f8", "Artemisia Gentileschi", "Susanna and the Elders", "1644-48", "2025/09/Artemisia-Gentileschi-Susanna-and-the-Elders1644–48-The-Nivaagaard-Collection.-Photo-Nicholas-Hall-scaled.jpg", "Nicholas Hall", "range", 1644, 1648},
	{"0017NMK", "lucas-cranach-the-elder", "8a6c8c3445cdaa9c7fb52b410d06bdc039eddb1d6175d5fc76c4df43e42d642e", "Lucas Cranach the Elder", "Caritas", "1535", "2024/03/0017NMK-scaled-e1711099916208.jpg", "", "exact", 1535, 1535},
	{"0015NMK", "lorrain-claude", "d48bde5d41bbb99aa8963529645146560d78769ce6f5acbf276fbb16ca714fba", "Claude Lorrain", "Landscape with the Flight into Egypt", "c. 1646", "2023/07/Claude-Lorrain-Landskab-med-Flugten-til-Egypten-ca.-1646.jpg", "", "circa", 1646, 1646},
}

var nivaImagePicks = func() []coveragePick {
	var picks []coveragePick
	for _, f := range nivaImageFacts {
		picks = append(picks, coveragePick{"popular-nivaagaard", f.Acc, f.Artist, "Exact Nivaagaard collection record; full-frame public-domain study image, not a masterpiece designation."})
	}
	return picks
}()

func nivaCredit(f nivaImageFact) string {
	s := f.Artist + ", " + f.Title + ", " + f.Date + ". The Nivaagaard Collection."
	if f.Photographer != "" {
		s += " Photo: " + f.Photographer + "."
	}
	return s + " Public domain. Resized and JPEG-compressed; no crop or retouching."
}

// Read only the unique main image's explicit JPEG fallback. No guessed URLs,
// WordPress crop substitutions, recommendation cards or download redirectors.
func nivaImage(raw string, f nivaImageFact) (string, error) {
	if hash([]byte(raw)) != f.SHA || !strings.Contains(raw, `href="`+nivaPolicy+`"`) || !strings.Contains(raw, ">PUBLIC DOMAIN</span>") {
		return "", errors.New("changed object notice or missing per-object public-domain link")
	}
	imageURL := "https://nivaagaard.dk/wp-content/uploads/" + f.ImagePath
	var found []string
	for _, m := range regexp.MustCompile(`<img\b[^>]+>`).FindAllString(raw, -1) {
		if !strings.Contains(m, `data-src="https://nivaagaard.dk/wp-content/smush-webp/`+f.ImagePath+`.webp"`) {
			continue
		}
		a := regexp.MustCompile(`data-smush-webp-fallback="([^"]+)"`).FindStringSubmatch(m)
		if len(a) != 2 {
			return "", errors.New("missing explicit JPEG fallback")
		}
		var fallback map[string]string
		if err := json.Unmarshal([]byte(html.UnescapeString(a[1])), &fallback); err != nil {
			return "", err
		}
		if fallback["data-src"] != imageURL {
			return "", errors.New("wrong object fallback")
		}
		found = append(found, fallback["data-src"])
	}
	if len(found) != 1 {
		return "", errors.New("ambiguous primary image")
	}
	return found[0], nil
}

func validateNivaagaard(x coverageEntry) error {
	for _, f := range nivaImageFacts {
		if f.Acc != x.Pick.Object {
			continue
		}
		u, err := nivaImage(str(x.Raw, "html"), f)
		if err != nil {
			return err
		}
		page := "https://nivaagaard.dk/en/the-collection/" + f.Slug + "/"
		if x.Accession != f.Acc || x.Candidate.Artist != f.Artist || x.Candidate.Title != f.Title || x.Page != page || x.ImagePage != page || x.ImageURL != u || x.Rights != "public_domain" || x.License != "Public domain" || x.LicenseURL != nivaPD || x.Policy != nivaPolicy || x.Credit != nivaCredit(f) || x.Provider != "The Nivaagaard Collection" || hash([]byte(str(x.Raw, "policy_html"))) != nivaPolicySHA {
			return errors.New("Nivaagaard exact identity or image permission mismatch")
		}
		return nil
	}
	return errors.New("unreviewed Nivaagaard object")
}

func stageNivaagaard(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	s := coverageSelection{Version: coverageVersion, Created: time.Now().UTC(), Entries: []coverageEntry{}, Deferred: []string{}}
	policy, err := os.ReadFile(filepath.Join(root, nivaDir, "public-domain.html"))
	if err != nil {
		return err
	}
	if hash(policy) != nivaPolicySHA {
		return errors.New("changed museum image policy")
	}
	for i, pick := range nivaImagePicks {
		f := nivaImageFacts[i]
		x, err := coverageCandidate(ctx, p, pick)
		if err != nil {
			return fmt.Errorf("%s: %w", pick.Object, err)
		}
		if x.Candidate.HasImage {
			s.Deferred = append(s.Deferred, pick.Object+": existing image preserved")
			continue
		}
		file := filepath.Join(root, nivaDir, f.Slug+".html")
		b, err := os.ReadFile(file)
		if err != nil {
			return err
		}
		sb, err := os.ReadFile(file + ".snapshot.json")
		if err != nil {
			return err
		}
		var snap struct {
			URL string    `json:"url"`
			SHA string    `json:"sha256"`
			At  time.Time `json:"retrieved_at"`
		}
		if err = json.Unmarshal(sb, &snap); err != nil {
			return err
		}
		if snap.URL != x.Page || snap.SHA != f.SHA || hash(b) != f.SHA {
			return errors.New("object capture mismatch")
		}
		var dateMatches bool
		if err = p.QueryRow(ctx, `SELECT creation_year_start=$2 AND creation_year_end=$3 AND date_precision=$4 FROM artworks WHERE id=$1`, x.Candidate.ID, f.First, f.Last, f.Precision).Scan(&dateMatches); err != nil {
			return err
		}
		if !dateMatches {
			return errors.New("local/source creation-date conflict")
		}
		x.ImageURL, err = nivaImage(string(b), f)
		if err != nil {
			return err
		}
		x.ImagePage = x.Page
		x.Provider = "The Nivaagaard Collection"
		x.Rights = "public_domain"
		x.License = "Public domain"
		x.LicenseURL = nivaPD
		x.Policy = nivaPolicy
		x.Credit = nivaCredit(f)
		x.Retrieved = snap.At
		x.Raw = map[string]any{"html": string(b), "policy_html": string(policy), "sha256": snap.SHA, "source_url": snap.URL}
		if err = validateCoverageEntry(x); err != nil {
			return err
		}
		s.Entries = append(s.Entries, x)
	}
	if err = save(out, s); err != nil {
		return err
	}
	b, err := os.ReadFile(out)
	if err != nil {
		return err
	}
	fmt.Printf("Staged %d exact Nivaagaard images. SHA256 %s. No image downloads or DB writes.\n", len(s.Entries), hash(b))
	return nil
}
