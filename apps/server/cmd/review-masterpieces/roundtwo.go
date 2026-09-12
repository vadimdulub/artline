package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

// Explicit museum-connected study choices, not masterpiece designations.
// KMS3192 (career/acquisition dating) and KMS8604 (conflicting inscription)
// were researched but deliberately excluded from the image selection.
var roundTwoPicks = []coveragePick{
	{"smk", "KMS9107", "Anna Ancher", "Mother and child: selected domestic subject in the SMK collection."},
	{"smk", "KMS1433", "Anna Ancher", "A Funeral: selected multi-figure interior for comparison with Ancher's intimate domestic scenes."},
	{"smk", "KMS3827", "Anna Ancher", "A Young Girl Plaiting her Hair: selected figure and interior study."},
	{"smk", "KMS3879", "Anna Ancher", "Vilhelm Kyhn portrait: selected artist portrait, distinct from the sitter's own works."},
	{"smk", "KMS1845", "Anna Ancher", "Plucking the Geese: selected domestic labour subject."},
	{"smk", "KMS8654", "Anna Ancher", "Ane Hedvig Brondum in the Red Room: selected interior and family portrait."},
	{"smk", "KMS1093", "Elisabeth Jerichau-Baumann", "Jens Adolf Jerichau: selected portrait of the artist's sculptor husband."},
	{"smk", "KMS6699", "Elisabeth Jerichau-Baumann", "Holger Aagaard Hammerich: selected childhood portrait."},
	{"smk", "KMS8605", "Elisabeth Jerichau-Baumann", "Portrait sketch: preserve the museum's probable sitter identification and approximate dating."},
	{"smk", "KMS852", "Elisabeth Jerichau-Baumann", "A Wounded Danish Soldier: selected narrative painting."},
	{"smk", "KMS9034", "Elisabeth Jerichau-Baumann", "Thorald Laessoe: selected artist portrait; parenthesized source date retained in evidence."},
	{"smk", "KMS9035", "Elisabeth Jerichau-Baumann", "Valkyries: selected mythological subject; parenthesized source date retained in evidence."},
	{"smk", "KMS8589", "Elisabeth Jerichau-Baumann", "An Egyptian Fellah Woman with her Baby: selected work with the museum's historical title preserved."},
	{"smk", "KMS9033", "Elisabeth Jerichau-Baumann", "L'Aspetta: selected late figurative painting."},
	{"cleveland", "129386", "El Greco", "Christ on the Cross: selected devotional painting by the Greek-born artist in an independently documented museum collection."},
	{"cleveland", "108541", "El Greco", "The Holy Family with Mary Magdalen: selected multi-figure devotional composition."},
}

var roundTwoDates = map[string][2]int{
	"KMS9107": {1888, 1888}, "KMS1433": {1891, 1891}, "KMS3827": {1901, 1901},
	"KMS3879": {1903, 1903}, "KMS1845": {1904, 1904}, "KMS8654": {1909, 1909},
	"KMS1093": {1846, 1846}, "KMS6699": {1849, 1849}, "KMS8605": {1858, 1861},
	"KMS852": {1865, 1865}, "KMS9034": {1868, 1868}, "KMS9035": {1871, 1871},
	"KMS8589": {1872, 1872}, "KMS9033": {1878, 1878},
	"129386": {1600, 1610}, "108541": {1590, 1595},
}

func validateRoundTwoMetadata(x coverageEntry) error {
	expect, ok := roundTwoDates[x.Pick.Object]
	if !ok {
		return errors.New("unreviewed round-two object")
	}
	if x.Pick.Source == "cleveland" {
		w := ingest.NormalizeCleveland(x.Raw)
		cs, _ := x.Raw["creators"].([]any)
		if len(cs) != 1 || obj(cs[0])["id"] != float64(2391) || obj(cs[0])["qualifier"] != nil || w.First == nil || w.Last == nil || *w.First != expect[0] || *w.Last != expect[1] {
			return errors.New("Cleveland creator/date evidence changed")
		}
		return nil
	}
	ps, _ := x.Raw["production"].([]any)
	ds, _ := x.Raw["production_date"].([]any)
	authority := "249_person"
	if x.Pick.Artist == "Elisabeth Jerichau-Baumann" {
		authority = "238_person"
	}
	if len(ps) != 1 || str(obj(ps[0]), "creator_lref") != authority || len(ds) != 1 {
		return errors.New("SMK creator/date evidence changed")
	}
	for i, k := range []string{"start", "end"} {
		v := str(obj(ds[0]), k)
		if !strings.HasPrefix(v, fmt.Sprintf("%04d-", expect[i])) {
			return errors.New("SMK date bounds changed")
		}
	}
	titles, _ := x.Raw["titles"].([]any)
	for _, title := range titles {
		if strings.TrimSpace(str(obj(title), "title")) == strings.TrimSpace(x.Candidate.Title) {
			return nil
		}
	}
	return errors.New("SMK title changed")
}

// Offline staging from today's exact-object captures. Reuses the existing Go
// rights gates, pinned preview/apply and per-work transactional attachment path.
func stageRoundTwo(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	s := coverageSelection{Version: coverageVersion, Created: time.Now().UTC(), Entries: []coverageEntry{}, Deferred: []string{
		"smk:KMS3192: date bounds based on artist years and museum accession, not established creation dates",
		"smk:KMS8604: creator field and Prossalendi 1868 inscription need attribution reconciliation",
	}}
	for _, pick := range roundTwoPicks {
		x, err := coverageCandidate(ctx, p, pick)
		if err != nil {
			return fmt.Errorf("%s: %w", pick.Object, err)
		}
		file := filepath.Join(root, "content/imports/painter-review-round02-20260911", pick.Source+"-"+pick.Object+".json")
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
		u := "https://api.smk.dk/api/v1/art/?object_number=" + pick.Object + "&lang=en"
		if pick.Source == "cleveland" {
			u = "https://openaccess-api.clevelandart.org/api/artworks/" + pick.Object
		}
		if snap.URL != u || snap.SHA != hash(b) {
			return errors.New("capture identity/hash mismatch")
		}
		var doc map[string]any
		if err = json.Unmarshal(b, &doc); err != nil {
			return err
		}
		x.Retrieved = snap.At
		if pick.Source == "smk" {
			items, _ := doc["items"].([]any)
			if len(items) != 1 {
				return errors.New("ambiguous SMK capture")
			}
			x.Raw = obj(items[0])
			x.Provider = "Statens Museum for Kunst"
			x.ImageURL = str(x.Raw, "image_iiif_id") + "/full/!700,700/0/default.jpg"
			x.ImagePage = x.Page
			x.Rights = "public_domain"
			x.License = "Public Domain Mark 1.0"
			x.LicenseURL = "https://creativecommons.org/publicdomain/mark/1.0/"
			x.Policy = x.LicenseURL
			x.Credit = pick.Artist + ". " + x.Candidate.Title + ". SMK, Copenhagen."
		} else {
			x.Raw = obj(doc["data"])
			w := ingest.NormalizeCleveland(x.Raw)
			x.Provider = "Cleveland Museum of Art"
			x.ImageURL = w.ImageURL
			x.ImagePage = w.URL
			x.Rights = w.Rights
			x.License = "CC0 1.0"
			x.LicenseURL = "https://creativecommons.org/publicdomain/zero/1.0/"
			x.Policy = "https://www.clevelandart.org/open-access"
			x.Credit = w.Credit + ". " + x.Provider + "."
		}
		if err = validateCoverageEntry(x); err != nil {
			return fmt.Errorf("%s: %w", pick.Object, err)
		}
		var first, last int
		if err = p.QueryRow(ctx, "SELECT creation_year_start,creation_year_end FROM artworks WHERE id=$1", x.Candidate.ID).Scan(&first, &last); err != nil {
			return err
		}
		if [2]int{first, last} != roundTwoDates[pick.Object] {
			return errors.New("database date differs from reviewed source")
		}
		if x.Candidate.HasImage {
			s.Deferred = append(s.Deferred, pick.Source+":"+pick.Object+": existing media preserved; reviewed separately")
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
	fmt.Printf("Staged %d images; %d deferrals. SHA256 %s. No downloads or database writes.\n", len(s.Entries), len(s.Deferred), hash(b))
	return nil
}
