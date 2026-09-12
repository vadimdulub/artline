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

const pinakothekPolicy = "https://www.sammlung.pinakothek.de/de/usage"
const pinakothekLicense = "https://creativecommons.org/licenses/by-sa/4.0/"

type pinakothekFact struct {
	File, SHA, Page, Title, Creator, Date, Branch string
	Year                                          int
}

var pinakothekFacts = map[string]pinakothekFact{
	"704": {"../durer/durer-Y0GRY2XLRX.html","3536bec1ece3cbdae06ed96cedf522ac9f430ef9b87c014eba4e89961365fbec","Y0GRY2XLRX",`Beweinung Christi ("Glimsche Beweinung")`,"Albrecht Dürer","um 1500","Alte",1500},
	"709": {"../durer/durer-Pdxz0KvGw5.html","58d6728f70d4cc687d54437dd5c83de7b6876f9b9f13cf45ae983ed5b5c429d9","Pdxz0KvGw5","Maria als Schmerzensmutter","Albrecht Dürer","1495/98","Alte",1495},
	"4772": {"../durer/durer-QrLWeqA4NO.html","b883a0415d782f780a8cb6ab9fd5d2b3ecc09abccc9b098073708ee65e6c4fe3","QrLWeqA4NO","Die Muttergottes mit der Nelke","Albrecht Dürer","1516","Alte",1516},
	"694": {"../durer/durer-o5xrQgP47X.html","2284223feb0d6f0fba503162323db7b9b2edcd6593edba729bafb2851d83d2db","o5xrQgP47X","Bildnis eines jungen Mannes","Albrecht Dürer","1500","Alte",1500},
	"705": {"../durer/durer-k2xnBjAxPd.html","2c8772a53e45b20174bfe1fa5bba4e90bc4cc7015a88423508afc326bac049fb","k2xnBjAxPd","Selbstmord der Lucretia","Albrecht Dürer","1518","Alte",1518},
	"5379": {"../durer/durer-02LAWJX4yk.html","d888a013cd2e3512f19ab7d97b7bece61ad14047c03227462733c5c79c6e2a28","02LAWJX4yk","Herkules im Kampf mit den Harpyen","Albrecht Dürer","1500","GNM",1500},
	"700": {"../durer/durer-M0xyZ1VLpl.html","0dba76ae87428045c557719745d1d57306483ac3f639008498a16037686d2fa0","M0xyZ1VLpl","Bildnis Michael Wolgemut","Albrecht Dürer","1516","GNM",1516},
	"717": {"../durer/durer-8MLv2rZLz3.html","12b303aaf3c554c670bcc33657e6765435e3332aa70b17fda3bb394fc2e86319","8MLv2rZLz3","Bildnis Jakob Fugger der Reiche","Albrecht Dürer","um 1520","Augsburg",1520},
	"537":   {"pinakothek-durer-self.html", "6442d5e808364b9acc6198daa471de6d9c9b8b7cb0ca5fc548239626eb644ebf", "Qlx2QpQ4Xq", "Selbstbildnis im Pelzrock", "Albrecht Dürer", "1500", "Alte", 1500},
	"8699":  {"pinakothek-pissarro-street.html", "261aa469d181a7be582400e1e07ce6017587a2e3530706da2ec9bf497f2697db", "PdxzrBExw5", "Straße in Upper Norwood", "Camille Pissarro", "1871", "Neue", 1871},
	"890":   {"pinakothek-rubens-judgment.html", "e7b784ec381f0012b78bf6a6515771188bab5893295334e1c4597ee3136ebc59", "Dj4mkQbL5A", "Das Große Jüngste Gericht", "Peter Paul Rubens", "um 1617", "Alte", 1617},
	"11427": {"pinakothek-rembrandt-self.html", "11bb3470ce7ee18493363d3d4e6dd2f5b20b11fa1702d3f029b5aeef504f1a4b", "y7GE1PmGPV", "Jugendliches Selbstbildnis", "Rembrandt (Harmensz. van Rijn)", "1629", "Alte", 1629},
	"8672":  {"pinakothek-vangogh-sunflowers.html", "ebdacb00c5bfefcd7e07dade5863c420b11f3b1fcc3683269db764a22bfbfff2", "Y0GR9B7LRX", "Sonnenblumen", "Vincent van Gogh", "1888", "Neue", 1888},
}
var durerImagePicks=[]coveragePick{
 {"pinakothek-durer-alte","704","Albrecht Dürer","Exact Glim Lamentation; selected full-frame museum reproduction, not a masterpiece designation."},
 {"pinakothek-durer-alte","709","Albrecht Dürer","Exact accession 709 devotional panel; selected full-frame reproduction, not an entire altarpiece."},
 {"pinakothek-durer-alte","4772","Albrecht Dürer","Exact Carnation Madonna; selected full-frame museum reproduction, not a masterpiece designation."},
 {"pinakothek-durer-alte","694","Albrecht Dürer","Exact Munich young-man portrait; selected full-frame museum reproduction."},
 {"pinakothek-durer-alte","705","Albrecht Dürer","Exact Lucretia painting, not a print after its composition; selected full-frame reproduction."},
 {"pinakothek-durer-gnm","5379","Albrecht Dürer","Exact Hercules painting documented on permanent loan to Nuremberg; selected full-frame reproduction."},
 {"pinakothek-durer-gnm","700","Albrecht Dürer","Exact Wolgemut portrait documented on permanent loan to Nuremberg; selected full-frame reproduction."},
 {"pinakothek-durer-augsburg","717","Albrecht Dürer","Exact Fugger portrait associated with Augsburg's collection; no currently-open or on-view claim."},
}

func pinakothekCollection(branch string) string {
 switch branch {
 case "GNM": return "Bayerische Staatsgemäldesammlungen (als Dauerleihgabe im Germanischen Nationalmuseum Nürnberg)"
 case "Augsburg": return "Bayerische Staatsgemäldesammlungen – Staatsgalerie in der Katharinenkirche Augsburg"
 default: return "Bayerische Staatsgemäldesammlungen – "+branch+" Pinakothek München"
 }
}
var pinakothekPicks = []coveragePick{
	{"pinakothek-alte", "537", "Albrecht Dürer", "Exact Munich self-portrait; selected European image-gap repair, not a new masterpiece designation."},
	{"pinakothek-neue", "8699", "Camille Pissarro", "Exact Upper Norwood painting; selected European image-gap repair, not a new masterpiece designation."},
	{"pinakothek-alte", "890", "Peter Paul Rubens", "Exact large Last Judgment painting; selected European image-gap repair, not a new masterpiece designation."},
	{"pinakothek-alte", "11427", "Rembrandt van Rijn", "Exact youthful self-portrait; selected European image-gap repair, not a new masterpiece designation."},
	{"pinakothek-neue", "8672", "Vincent van Gogh", "Exact Munich Sunflowers version; selected European image-gap repair, not a new masterpiece designation."},
}

func pinakothekMatch(s, pattern string) string {
	m := regexp.MustCompile(pattern).FindAllStringSubmatch(s, -1)
	if len(m) != 1 {
		return ""
	}
	return strings.Join(strings.Fields(html.UnescapeString(m[0][1])), " ")
}

// Only the main object area is examined; recommendation cards cannot grant rights
// or supply a different object's picture. The full page is pinned and retained.
func pinakothekImage(s string, facts pinakothekFact, accession string) (string, error) {
	start := strings.Index(s, `id="artwork-detailpage"`)
	end := strings.Index(s, "<!-- Rahmen -->")
	if start < 0 || end <= start {
		return "", errors.New("missing primary object area")
	}
	s = s[start:end]
	if pinakothekMatch(s, `(?s)<h1 class='artwork__title'>\s*(.*?)\s*</h1>`) != facts.Title+"," ||
		pinakothekMatch(s, `(?s)class='artwork__artist'>\s*(.*?)\s*</a>`) != facts.Creator ||
		!strings.Contains(s, "<span class='artwork__dates'>"+facts.Date+"</span>") ||
		pinakothekMatch(s, `(?s)Inventarnummer\s*</div>\s*([^<]+)`) != accession ||
		pinakothekMatch(s, `(?s)Bestand\s*</div>\s*([^<]+)`) != pinakothekCollection(facts.Branch) ||
		!strings.Contains(s, `class="artwork__action action--creativecommons" href="`+pinakothekLicense+`"`) {
		return "", errors.New("exact identity, collection or per-object licence mismatch")
	}
	image := pinakothekMatch(s, `(?s)<picture class="artwork__image">.*?<img src="([^"]+)"`)
	if !regexp.MustCompile(`^https://cdn\.thenetexperts\.info/image/authenticated/s--[A-Za-z0-9_-]+--/q_60/artworks/[A-Z0-9_-]+_CC-BY-SA_BSTGS\.jpg$`).MatchString(image) || !strings.Contains(image, "-"+accession+"_") {
		return "", errors.New("no exact unmodified official full-frame image URL")
	}
	return image, nil
}

func validatePinakothek(x coverageEntry) error {
	facts, ok := pinakothekFacts[x.Pick.Object]
	if !ok {
		return errors.New("not a reviewed Pinakothek object")
	}
	page := "https://www.sammlung.pinakothek.de/de/artwork/" + facts.Page
	raw := str(x.Raw, "html")
	image, err := pinakothekImage(raw, facts, x.Pick.Object)
	if err != nil {
		return err
	}
	if hash([]byte(raw)) != facts.SHA || x.Accession != x.Pick.Object || x.Candidate.Title != facts.Title || x.Page != page || x.ImagePage != page || x.ImageURL != image || x.Rights != "licensed" || x.License != "CC BY-SA 4.0" || x.LicenseURL != pinakothekLicense || x.Policy != pinakothekPolicy || x.Provider != "Bayerische Staatsgemäldesammlungen" || x.Credit != "© "+pinakothekCollection(facts.Branch)+". "+facts.Creator+", "+facts.Title+", "+facts.Date+". "+page {
		return errors.New("Pinakothek pinned identity/credit/rights mismatch")
	}
	return nil
}

func stagePinakothek(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	return stagePinakothekPicks(ctx,p,root,out,pinakothekPicks)
}

func stagePinakothekPicks(ctx context.Context,p *pgxpool.Pool,root,out string,picks []coveragePick) error {
	s := coverageSelection{Version: coverageVersion, Created: time.Now().UTC(), Entries: []coverageEntry{}, Deferred: []string{}}
	for _, pick := range picks {
		x, err := coverageCandidate(ctx, p, pick)
		if err != nil {
			return fmt.Errorf("%s: %w", pick.Object, err)
		}
		if x.Candidate.HasImage {
			s.Deferred = append(s.Deferred, pick.Object+": existing image preserved")
			continue
		}
		facts := pinakothekFacts[pick.Object]
		file := filepath.Join(root, "content/imports/popular-europe-session-20260911/pages", facts.File)
		b, err := os.ReadFile(file)
		if err != nil {
			return err
		}
		snapBytes, err := os.ReadFile(file + ".snapshot.json")
		if err != nil {
			return err
		}
		var snap struct {
			URL string    `json:"url"`
			SHA string    `json:"sha256"`
			At  time.Time `json:"retrieved_at"`
		}
		if err = json.Unmarshal(snapBytes, &snap); err != nil {
			return err
		}
		if snap.URL != x.Page || snap.SHA != hash(b) || snap.SHA != facts.SHA {
			return errors.New("source snapshot mismatch")
		}
		var dateMatches bool
		precision := "exact"
		last:=facts.Year
		if strings.HasPrefix(facts.Date, "um ") {
			precision = "circa"
		}
		if facts.Date=="1495/98" { last=1498; precision="range" }
		if err = p.QueryRow(ctx, `SELECT creation_year_start=$2 AND creation_year_end=$4 AND date_precision=$3 FROM artworks WHERE id=$1`, x.Candidate.ID, facts.Year, precision,last).Scan(&dateMatches); err != nil {
			return err
		}
		if !dateMatches {
			return errors.New("local/source date conflict")
		}
		x.ImageURL, err = pinakothekImage(string(b), facts, pick.Object)
		if err != nil {
			return err
		}
		x.ImagePage = x.Page
		x.Provider = "Bayerische Staatsgemäldesammlungen"
		x.Rights = "licensed"
		x.License = "CC BY-SA 4.0"
		x.LicenseURL = pinakothekLicense
		x.Policy = pinakothekPolicy
		x.Credit = "© " + pinakothekCollection(facts.Branch) + ". " + facts.Creator + ", " + facts.Title + ", " + facts.Date + ". " + x.Page
		x.Retrieved = snap.At
		x.Raw = map[string]any{"html": string(b), "sha256": snap.SHA, "source_url": snap.URL, "policy_url": pinakothekPolicy}
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
	fmt.Printf("Staged %d exact Pinakothek images. SHA256 %s. No images downloaded or DB writes.\n", len(s.Entries), hash(b))
	return nil
}
