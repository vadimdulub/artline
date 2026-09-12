package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

type poldiImageFact struct {
	Acc, Artist, Title, Date, Slug, File, APIName, APISHA, MuseumName, MuseumSHA, QID, LegacyAcc, Precision string
	First, Last                                                                                             int
}

var poldiImageFacts = []poldiImageFact{
	{"0445", "Piero della Francesca", "Saint Nicholas of Tolentino", "1454–1469", "san-nicola-da-tolentino", "File:Piero della Francesca - Saint Nicholas of Tolentino - Google Art Project.jpg", "piero", "2e8662a112f04c2c3b29aaccd5980b4cf86cd9542e6fa33fa7e19413091e1c72", "piero-nicholas", "1fe47d91289e3268a99e4130877ea831d69c5b70908f43bc4b07ce545fe49b11", "Q3947720", "Inv. 445", "range", 1454, 1469},
	{"1587", "Giovanni Bellini", "Imago Pietatis", "c. 1457", "imago-pietatis", "File:Giovanni Bellini - Imago Pietatis - Google Art Project.jpg", "bellini", "6b7a5cf11aad1f3e19cb971980c7ae314bbef84bdec75da10b83def9996e95d0", "bellini-pietatis", "1f37637e6e84a37a46843773b00d36bccdb9fa0f2fa9a54c50a0e96a5d2f3fb0", "Q3904394", "Inv. 1587", "circa", 1457, 1457},
}
var poldiImagePicks = func() []coveragePick {
	var picks []coveragePick
	for _, f := range poldiImageFacts {
		picks = append(picks, coveragePick{"popular-poldi", f.Acc, f.Artist, "Exact Poldi Pezzoli object; independently hosted Commons public-domain full-frame reproduction, not museum image permission or masterpiece designation."})
	}
	return picks
}()

func poldiImageInfo(raw string, f poldiImageFact) (map[string]any, error) {
	if hash([]byte(raw)) != f.APISHA {
		return nil, errors.New("changed reviewed Commons snapshot")
	}
	var doc map[string]any
	if err := json.Unmarshal([]byte(raw), &doc); err != nil {
		return nil, err
	}
	pages := obj(obj(doc["query"])["pages"])
	if doc["error"] != nil || len(pages) != 1 {
		return nil, errors.New("Commons error/ambiguous file")
	}
	var page map[string]any
	for _, p := range pages {
		page = obj(p)
	}
	if str(page, "title") != f.File {
		return nil, errors.New("wrong Commons file")
	}
	infos, ok := page["imageinfo"].([]any)
	if !ok || len(infos) != 1 {
		return nil, errors.New("ambiguous image info")
	}
	revs, ok := page["revisions"].([]any)
	if !ok || len(revs) != 1 {
		return nil, errors.New("missing file revision")
	}
	wikitext := str(obj(obj(obj(revs[0])["slots"])["main"]), "*")
	for key, want := range map[string]string{"wikidata": f.QID, "artist_display_name": f.Artist, "collection_display_name": "Museo Poldi Pezzoli", "museum_internal_id": f.LegacyAcc, "title": f.Title} {
		if commonsField(wikitext, key) != want {
			return nil, fmt.Errorf("Commons %s identity mismatch", key)
		}
	}
	info := obj(infos[0])
	cats := metadata(info, "Categories")
	if metadata(info, "LicenseShortName") != "Public domain" || metadata(info, "UsageTerms") != "Public domain" || !strings.EqualFold(metadata(info, "Copyrighted"), "false") || metadata(info, "Restrictions") != "" || !strings.Contains(cats, "PD-Art (PD-old-100-expired)") || !strings.Contains(cats, "Google Art Project works in Museo Poldi Pezzoli") || strings.Contains(cats, "different depicts") {
		return nil, errors.New("file-specific permission conflict")
	}
	imageURL, err := url.Parse(str(info, "thumburl"))
	if err != nil || imageURL.Scheme != "https" || imageURL.Host != "thumb.wikimedia.org" || imageURL.User != nil || !strings.HasPrefix(imageURL.Path, "/wikipedia/commons/thumb/") || !strings.HasSuffix(imageURL.Path, strings.ReplaceAll(strings.TrimPrefix(f.File, "File:"), " ", "_")) {
		return nil, errors.New("wrong bounded full-frame Commons rendition")
	}
	if str(info, "descriptionurl") != "https://commons.wikimedia.org/wiki/"+strings.ReplaceAll(f.File, " ", "_") {
		return nil, errors.New("wrong file rights page")
	}
	return info, nil
}
func poldiImageCredit(f poldiImageFact) string {
	return f.Artist + ", " + f.Title + ", " + f.Date + ". Museo Poldi Pezzoli. Google Art Project reproduction via Wikimedia Commons; public domain per file notice. Resized and JPEG-compressed; no extra crop. Museum catalogue dates retained; legacy Commons dates/dimension units not imported."
}

func validatePoldiCommons(x coverageEntry) error {
	for _, f := range poldiImageFacts {
		if f.Acc != x.Pick.Object {
			continue
		}
		info, err := poldiImageInfo(str(x.Raw, "commons_api_json"), f)
		if err != nil {
			return err
		}
		if hash([]byte(str(x.Raw, "museum_html"))) != f.MuseumSHA || x.Candidate.Title != f.Title || x.Candidate.Artist != f.Artist || x.Accession != f.Acc || x.Page != "https://museopoldipezzoli.it/en/scopri/collezioni/capolavori/opera/"+f.Slug+"/" || x.ImageURL != str(info, "thumburl") || x.ImagePage != str(info, "descriptionurl") || x.Provider != "Wikimedia Commons" || x.Rights != "public_domain" || x.License != "Public domain" || x.LicenseURL != nivaPD || x.Policy != commonsPolicy || x.Credit != poldiImageCredit(f) {
			return errors.New("Poldi exact museum/media/rights crosswalk mismatch")
		}
		return nil
	}
	return errors.New("unreviewed Poldi image")
}

func stagePoldiCommons(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	s := coverageSelection{Version: coverageVersion, Created: time.Now().UTC(), Entries: []coverageEntry{}, Deferred: []string{}}
	for i, pick := range poldiImagePicks {
		f := poldiImageFacts[i]
		x, err := coverageCandidate(ctx, p, pick)
		if err != nil {
			return err
		}
		if x.Candidate.HasImage {
			s.Deferred = append(s.Deferred, pick.Object+": existing media preserved")
			continue
		}
		path := filepath.Join(root, "content/imports/popular-resume-20260911-1852/poldi-commons", f.APIName+".json")
		b, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		sb, err := os.ReadFile(path + ".snapshot.json")
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
		if snap.SHA != f.APISHA || hash(b) != f.APISHA {
			return errors.New("Commons snapshot changed")
		}
		mb, err := os.ReadFile(filepath.Join(root, "content/imports/popular-resume-20260911-1852/poldi", f.MuseumName+".html"))
		if err != nil {
			return err
		}
		var dates bool
		if err = p.QueryRow(ctx, `SELECT creation_year_start=$2 AND creation_year_end=$3 AND date_precision=$4 FROM artworks WHERE id=$1`, x.Candidate.ID, f.First, f.Last, f.Precision).Scan(&dates); err != nil {
			return err
		}
		if !dates {
			return errors.New("source/local dates changed")
		}
		info, err := poldiImageInfo(string(b), f)
		if err != nil {
			return err
		}
		x.ImageURL = str(info, "thumburl")
		x.ImagePage = str(info, "descriptionurl")
		x.Provider = "Wikimedia Commons"
		x.Rights = "public_domain"
		x.License = "Public domain"
		x.LicenseURL = nivaPD
		x.Policy = commonsPolicy
		x.Credit = poldiImageCredit(f)
		x.Retrieved = snap.At
		x.Raw = map[string]any{"commons_api_json": string(b), "museum_html": string(mb), "commons_api_url": snap.URL}
		if err = validateCoverageEntry(x); err != nil {
			return err
		}
		s.Entries = append(s.Entries, x)
	}
	if err := save(out, s); err != nil {
		return err
	}
	b, err := os.ReadFile(out)
	if err != nil {
		return err
	}
	fmt.Printf("Staged %d Poldi Commons images. SHA256 %s. No image downloads or DB writes.\n", len(s.Entries), hash(b))
	return nil
}
