package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

// Exact source authority, title and date checks; no masterpiece status inferred.
var popularSMKPicks = []coveragePick{
	{"smk", "KMSr145", "Amedeo Modigliani", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMS3823", "Edvard Munch", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMS4548", "Giovanni Battista Tiepolo", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMS3674", "Lucas Cranach the Elder", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMSsp718", "Lucas Cranach the Elder", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMSsp720", "Lucas Cranach the Elder", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMSsp722", "Lucas Cranach the Elder", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMSsp726", "Lucas Cranach the Elder", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMSsp731", "Lucas Cranach the Elder", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMS3889", "Nicolas Poussin", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMSsp191", "Peter Paul Rubens", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMSsp197", "Peter Paul Rubens", "Selected museum-connected painting; source-specific image permission reviewed."},
	{"smk", "KMS1384", "Rembrandt van Rijn", "Selected museum-connected painting; source-specific image permission reviewed."},
}
var smkMatissePicks = []coveragePick{
	{"smk", "KMSr171", "Henri Matisse", "Individually reviewed SMK painting and public-domain reproduction; no masterpiece assertion."},
	{"smk", "KMSr73", "Henri Matisse", "Individually reviewed SMK painting and public-domain reproduction; no masterpiece assertion."},
	{"smk", "KMSr75", "Henri Matisse", "Individually reviewed SMK painting and public-domain reproduction; no masterpiece assertion."},
}
var popularSMKFacts = map[string]struct {
	Authority, Title string
	First, Last      int
}{
	"KMS359":   {"1117_person", "A View from Dosseringen near the Sortedam Lake Looking Towards Nørrebro", 1838, 1838},
	"KMS844":   {"1117_person", "Morning View of Østerbro. On the Right \"Rosendal\", in the Background \"Petersborg\"", 1836, 1836},
	"KMS1345":  {"1117_person", "The Transept of Århus Cathedral", 1830, 1830},
	"KMS1662":  {"1117_person", "View from the Loft of the Grain Store at the Bakery in the Citadel of Copenhagen", 1831, 1831},
	"KMS1222":  {"250_person", "The Lifeboat is Taken through the Dunes", 1883, 1883},
	"KMS4002":  {"250_person", "The Sick Girl", 1882, 1882},
	"KMS3820":  {"250_person", "The Girl with the Sunflowers", 1889, 1889},
	"KMS1691":  {"250_person", "The Artist's Wife Reading", 1881, 1881},
	"KMS3696":  {"180_person", "A Room in the Artist's Home in Strandgade, Copenhagen, with the Artist's Wife", 1901, 1901},
	"KMS3697":  {"180_person", "A Room in the Artist's Home in Strandgade, Copenhagen, with the Artist's Wife", 1902, 1902},
	"KMS1542":  {"180_person", "Amalienborg Square, Copenhagen", 1896, 1896},
	"KMS8010":  {"180_person", "Tree Trunks. Arresødal near Frederiksværk, North Zealand", 1904, 1904},
	"KMSr171":  {"897_person", "Portrait of Madame Matisse. The Green Line", 1905, 1905},
	"KMSr73":   {"897_person", "Street at Arcueil", 1899, 1899},
	"KMSr75":   {"897_person", "Place des Lices, Saint-Tropez", 1904, 1904},
	"KMSr145":  {"931_person", "Alice", 1916, 1919},
	"KMS3823":  {"1810_person", "Workers Coming Home", 1914, 1914},
	"KMS4548":  {"1983_person", "Apollo and Marsyas", 1757, 1757},
	"KMS3674":  {"1599_person", "Virgin and Child Adored by the Infant St John", 1512, 1514},
	"KMSsp718": {"1599_person", "The Judgement of Paris", 1527, 1527},
	"KMSsp720": {"1599_person", "Portrait of Martin Luther", 1532, 1532},
	"KMSsp722": {"1599_person", "Melancholy", 1532, 1532},
	"KMSsp726": {"1599_person", "Portrait of the Electress Sibyl of Saxony (1510-1569)", 1533, 1533},
	"KMSsp731": {"1599_person", "The Mystic Marriage of Saint Catherine", 1510, 1512},
	"KMS3889":  {"1857_person", "The Testament of Eudamidas", 1644, 1648},
	"KMSsp191": {"1899_person", "Matthaeus Yrsselius (1541-1629), Abbot of Sint-Michiel's Abbey in Antwerp", 1622, 1625},
	"KMSsp197": {"1899_person", "Francesco I de' Medici (1541-1587)", 1620, 1624},
	"KMS1384":  {"1871_person", "The Crusader", 1659, 1661},
}

func validatePopularSMKMetadata(x coverageEntry) error {
	f, ok := popularSMKFacts[x.Pick.Object]
	if !ok || strings.TrimSpace(x.Candidate.Title) != f.Title {
		return errors.New("unreviewed SMK identity/title")
	}
	ps, _ := x.Raw["production"].([]any)
	ds, _ := x.Raw["production_date"].([]any)
	if len(ps) != 1 || str(obj(ps[0]), "creator_lref") != f.Authority || len(ds) != 1 {
		return errors.New("SMK creator/date changed")
	}
	role := str(obj(ps[0]), "creator_role")
	if role != "" && role != "artist" && role != "Painter" {
		return errors.New("qualified SMK creator")
	}
	for i, k := range []string{"start", "end"} {
		if !strings.HasPrefix(str(obj(ds[0]), k), fmt.Sprintf("%04d-", []int{f.First, f.Last}[i])) {
			return errors.New("SMK source date changed")
		}
	}
	notes, _ := x.Raw["production_dates_notes"].([]any)
	uncertain := regexp.MustCompile("(?i)(udateret|virkeår|levetid|baseret på kunstnerens årstal|tilgået museet|unknown|undated|after|before|efter|før|muligvis|tilskrevet)")
	for _, n := range notes {
		if v, ok := n.(string); !ok || uncertain.MatchString(v) {
			return errors.New("SMK date notes need review")
		}
	}
	titles, _ := x.Raw["titles"].([]any)
	for _, t := range titles {
		if strings.TrimSpace(str(obj(t), "title")) == f.Title {
			return nil
		}
	}
	return errors.New("source title mismatch")
}
func stagePopularSMK(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	return stageSMKReviewed(ctx, p, root, out, "content/imports/popular-smk-20260911", popularSMKPicks)
}
func stageSMKReviewed(ctx context.Context, p *pgxpool.Pool, root, out, captureDir string, picks []coveragePick) error {
	s := coverageSelection{Version: coverageVersion, Created: time.Now().UTC(), Entries: []coverageEntry{}, Deferred: []string{"smk:KMSsp198: source dates partly based on artist years; deferred"}}
	for _, pick := range picks {
		x, err := coverageCandidate(ctx, p, pick)
		if err != nil {
			return err
		}
		file := filepath.Join(root, captureDir, "smk-"+pick.Object+".json")
		b, err := os.ReadFile(file)
		if err != nil {
			return err
		}
		sb, err := os.ReadFile(file + ".snapshot.json")
		if err != nil {
			return err
		}
		var snap struct {
			URL string
			SHA string    `json:"sha256"`
			At  time.Time `json:"retrieved_at"`
		}
		if err = json.Unmarshal(sb, &snap); err != nil {
			return err
		}
		if snap.URL != "https://api.smk.dk/api/v1/art/?object_number="+pick.Object+"&lang=en" || snap.SHA != hash(b) {
			return errors.New("capture identity/hash mismatch")
		}
		var doc struct{ Items []map[string]any }
		if err = json.Unmarshal(b, &doc); err != nil {
			return err
		}
		if len(doc.Items) != 1 {
			return errors.New("ambiguous capture")
		}
		x.Raw = doc.Items[0]
		x.Retrieved = snap.At
		x.Provider = "Statens Museum for Kunst"
		x.ImageURL = str(x.Raw, "image_iiif_id") + "/full/!700,700/0/default.jpg"
		x.ImagePage = x.Page
		x.Rights = "public_domain"
		x.License = "Public Domain Mark 1.0"
		x.LicenseURL = "https://creativecommons.org/publicdomain/mark/1.0/"
		x.Policy = x.LicenseURL
		x.Credit = pick.Artist + ". " + x.Candidate.Title + ". SMK, Copenhagen."
		if err = validateCoverageEntry(x); err != nil {
			return fmt.Errorf("%s: %w", pick.Object, err)
		}
		var first, last int
		if err = p.QueryRow(ctx, "SELECT creation_year_start,creation_year_end FROM artworks WHERE id=$1", x.Candidate.ID).Scan(&first, &last); err != nil {
			return err
		}
		f := popularSMKFacts[pick.Object]
		if first != f.First || last != f.Last {
			return errors.New("database date differs from source")
		}
		if x.Candidate.HasImage {
			s.Deferred = append(s.Deferred, pick.Object+": existing media preserved")
			continue
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
	fmt.Printf("Staged %d images; SHA256 %s. No database writes or image downloads.\n", len(s.Entries), hash(b))
	return nil
}
