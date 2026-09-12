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
)

const athensIconAPIPath = "content/imports/data-collection-20260912/athens-icon-commons/crucifixion.json"
const athensIconAPISHA = "3826ccc7b8046cd395cfbd8f3b09a8208475867fa6b4a498d92a3c6d378762aa"
const athensIconMuseumPath = "content/imports/icons-primary-20260910/529bd7e7c238bcd6ee85b2e0f9393286a1043c20674cae2681653769fe562659.html"
const athensIconMuseumSHA = "2414d7bb39e13111318b7e5df7f823c24596807c1450a0c776c3e987b4ef8f35"
const athensIconPage = "https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=33"
const athensIconFile = "File:Double-side icon with Crucifixion and Hodegetria (14th century, Byzantine museum)-.jpg"
const athensIconLicense = "https://creativecommons.org/licenses/by-sa/4.0/"
const athensIconCredit = "Workshops of Constantinople, Crucifixion (front of double-sided icon), 14th century. Byzantine and Christian Museum, Athens, ΒΧΜ 01354. Photograph by Yair-haklai, via Wikimedia Commons, CC BY-SA 4.0. Full photographic frame resized and JPEG-compressed; no crop, perspective correction or retouching. Derivative remains CC BY-SA 4.0. Photograph made in 2024; artwork creation date is unchanged."

var athensIconPick = coveragePick{"icons-athens-commons", "33", "Workshops of Constantinople", "Exact double-sided icon ΒΧΜ 01354; separately licensed photographer's full front-side view, not museum photo permission or a masterpiece designation."}

// Scoped alternate path for this reviewed anonymous/workshop icon only. Do not
// invent a painter or bypass an existing hidden/archived artist relationship.
func athensIconCandidate(ctx context.Context, p *pgxpool.Pool) (coverageEntry, error) {
	x := coverageEntry{Pick: athensIconPick}
	c := &x.Candidate
	err := p.QueryRow(ctx, `SELECT a.id::text,e.scheme,e.external_id,a.current_institution_id::text,e.source_id::text,a.title,a.unlinked_creator_label,a.primary_media_id IS NOT NULL,`+fingerprintSQL+`,a.accession_number,e.canonical_url
 FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id JOIN sources s ON s.id=e.source_id AND s.is_active JOIN institutions i ON i.id=a.current_institution_id
 WHERE e.entity_type='artwork' AND e.scheme='european-icons-athens-object' AND e.external_id='33'
 AND a.id='de1c163d-25b8-4772-9de7-f0987ae92525' AND a.status='review' AND a.title='Crucifixion'
 AND a.unlinked_creator_label='Workshops of Constantinople' AND a.accession_number='ΒΧΜ 01354'
 AND a.work_type='painting' AND a.object_form='icon' AND a.creation_year_start=1301 AND a.creation_year_end=1400 AND a.date_precision='century'
 AND i.slug='byzantine-christian-museum-athens' AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id)
 AND EXISTS(SELECT 1 FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.institution_id=i.id AND l.claim_type='holding' AND l.review_state='accepted')`).Scan(&c.ID, &c.Scheme, &c.Object, &c.Institution, &c.SourceID, &c.Title, &c.Artist, &c.HasImage, &c.Fingerprint, &x.Accession, &x.Page)
	return x, err
}

func athensIconInfo(raw string) (map[string]any, error) {
	if hash([]byte(raw)) != athensIconAPISHA {
		return nil, errors.New("changed reviewed icon file evidence")
	}
	var doc map[string]any
	if err := json.Unmarshal([]byte(raw), &doc); err != nil {
		return nil, err
	}
	pages := obj(obj(doc["query"])["pages"])
	if doc["error"] != nil || len(pages) != 1 {
		return nil, errors.New("ambiguous icon file")
	}
	var page map[string]any
	for _, v := range pages {
		page = obj(v)
	}
	infos, ok := page["imageinfo"].([]any)
	if str(page, "title") != athensIconFile || !ok || len(infos) != 1 {
		return nil, errors.New("wrong icon photo")
	}
	i := obj(infos[0])
	if metadata(i, "LicenseShortName") != "CC BY-SA 4.0" || metadata(i, "LicenseUrl") != "https://creativecommons.org/licenses/by-sa/4.0" || metadata(i, "Restrictions") != "" || metadata(i, "AttributionRequired") != "true" || !strings.Contains(metadata(i, "Artist"), "User:Yair-haklai") || !strings.Contains(metadata(i, "Credit"), "Own work") || str(i, "sha1") != "044350dfb5345742199a261fe6c7f5b62799cecd" {
		return nil, errors.New("photo creator/license conflict")
	}
	return i, nil
}

func validateAthensIcon(x coverageEntry) error {
	i, err := athensIconInfo(str(x.Raw, "commons_api_json"))
	if err != nil {
		return err
	}
	if x.Pick != athensIconPick || x.Candidate.ID != "de1c163d-25b8-4772-9de7-f0987ae92525" || x.Candidate.Title != "Crucifixion" || x.Accession != "ΒΧΜ 01354" || x.Page != athensIconPage || x.ImageURL != str(i, "thumburl") || x.ImagePage != str(i, "descriptionurl") || x.Rights != "cc_by_sa" || x.License != "CC BY-SA 4.0" || x.LicenseURL != athensIconLicense || x.Provider != "Wikimedia Commons" || x.Policy != commonsPolicy || x.Credit != athensIconCredit || hash([]byte(str(x.Raw, "museum_html"))) != athensIconMuseumSHA {
		return errors.New("icon identity or attribution/rights mismatch")
	}
	return nil
}

func stageAthensIcon(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	x, err := coverageCandidate(ctx, p, athensIconPick)
	if err != nil {
		return err
	}
	if x.Candidate.HasImage {
		return errors.New("existing icon image preserved")
	}
	b, err := os.ReadFile(filepath.Join(root, athensIconAPIPath))
	if err != nil {
		return err
	}
	mb, err := os.ReadFile(filepath.Join(root, athensIconMuseumPath))
	if err != nil {
		return err
	}
	sb, err := os.ReadFile(filepath.Join(root, athensIconAPIPath+".snapshot.json"))
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
	if snap.SHA != athensIconAPISHA {
		return errors.New("changed icon source receipt")
	}
	i, err := athensIconInfo(string(b))
	if err != nil {
		return err
	}
	x.ImageURL = str(i, "thumburl")
	x.ImagePage = str(i, "descriptionurl")
	x.Provider = "Wikimedia Commons"
	x.Rights = "cc_by_sa"
	x.License = "CC BY-SA 4.0"
	x.LicenseURL = athensIconLicense
	x.Policy = commonsPolicy
	x.Credit = athensIconCredit
	x.Retrieved = snap.At
	x.Raw = map[string]any{"commons_api_json": string(b), "commons_api_url": snap.URL, "museum_html": string(mb), "identity_review": "Official accession, workshop label, century and double-sided object matched to the Commons exact-object category. Full front-side photograph visually reviewed; no artwork creator inferred from photographer.", "category_url": "https://commons.wikimedia.org/wiki/Category:Double-side_icon_with_Crucifixion_and_Hodegetria_(14th_century,_Byzantine_museum)", "museum_source_captured_at": "2026-09-10T17:38:19.302Z", "museum_notice_rechecked_on": "2026-09-12"}
	if err = validateCoverageEntry(x); err != nil {
		return err
	}
	selection := coverageSelection{Version: coverageVersion, Created: time.Now().UTC(), Entries: []coverageEntry{x}, Deferred: []string{}}
	if err = save(out, selection); err != nil {
		return err
	}
	result, err := os.ReadFile(out)
	if err != nil {
		return err
	}
	fmt.Printf("Staged 1 workshop-attributed icon image. SHA256 %s. No DB writes.\n", hash(result))
	return nil
}
