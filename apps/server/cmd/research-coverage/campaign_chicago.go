package main

import (
	"archive/tar"
	"compress/bzip2"
	"context"
	"encoding/json"
	"fmt"
	"html"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
)

// Read only the resource's licence declaration. Never extract or execute the
// archive's other files (it also contains a Git directory and sample hooks).
func chicagoArtworkLicense(root string) (map[string]any, error) {
	p := filepath.Join(root, "content/imports/campaign-chicago-20260910/metadata.tar.bz2")
	if e := verify(p); e != nil {
		return nil, e
	}
	f, e := os.Open(p)
	if e != nil {
		return nil, e
	}
	defer f.Close()
	r := tar.NewReader(io.LimitReader(bzip2.NewReader(f), 4<<30))
	for n := 0; n < 500000; n++ {
		h, e := r.Next()
		if e != nil {
			return nil, fmt.Errorf("Chicago resource licence missing: %w", e)
		}
		if h.Typeflag != tar.TypeReg || h.Name != "artic-api-data/json/info.json" {
			continue
		}
		if h.Size > 4<<20 {
			return nil, fmt.Errorf("oversize licence metadata")
		}
		var resources map[string]any
		if e = json.NewDecoder(r).Decode(&resources); e != nil {
			return nil, e
		}
		v, ok := resources["artworks"].(map[string]any)
		if !ok || !strings.Contains(str(v, "license_text"), "`description`") || !strings.Contains(str(v, "license_text"), "Attribution 4.0") || !strings.Contains(str(v, "license_text"), "All other data") || !strings.Contains(str(v, "license_text"), "CC0") {
			return nil, fmt.Errorf("Chicago artwork resource licence requires review")
		}
		return v, nil
	}
	return nil, fmt.Errorf("licence archive entry cap reached")
}

var chicagoQualified = regexp.MustCompile(`(?i)\b(after|attributed|formerly|possibly|probably|workshop|studio|school|circle|follower|manner|imitator|copy|copies|publisher|printer|printed|published|engraved by|designed by)\b`)
var chicagoLife = regexp.MustCompile(`\b(1[1-9][0-9]{2})\s*[-–]\s*((?:1|2)[0-9]{3})\b`)
var campaignGroupedTitle = regexp.MustCompile(`(?i)\b(album|sketchbook|portfolio|set of|recto|verso|folio)\b`)
var campaignGroupedInventory = regexp.MustCompile(`[0-9][a-z]-[a-z]|[0-9]-[0-9]`)
var chicagoTags = regexp.MustCompile(`<[^>]*>`)

func chicagoCreator(r map[string]any) (name, life string, ok bool) {
	ids, valid := r["artist_ids"].([]any)
	alts, _ := r["alt_artist_ids"].([]any)
	names, _ := r["artist_titles"].([]any)
	name, display := str(r, "artist_title"), str(r, "artist_display")
	if !valid || len(ids) != 1 || len(alts) != 0 || len(names) != 1 || name == "" || display == "" || chicagoQualified.MatchString(display) {
		return "", "", false
	}
	id, valid := ids[0].(float64)
	if !valid || id <= 0 || int(id) != integer(r, "artist_id") || names[0] != name {
		return "", "", false
	}
	if m := chicagoLife.FindStringSubmatch(display); m != nil {
		life = m[1] + "-" + m[2]
	}
	return name, life, true
}

func chicagoDescription(raw, sourceURL string) string {
	if raw == "" || len(raw) >= 20000 {
		return ""
	}
	// Preserve the source wording as plain quoted text, not active HTML/Markdown.
	s := html.UnescapeString(chicagoTags.ReplaceAllString(raw, " "))
	s = strings.Join(strings.Fields(s), " ")
	s = strings.NewReplacer("\\", "\\\\", "`", "\\`", "*", "\\*", "_", "\\_", "[", "\\[", "]", "\\]", "<", "&lt;", ">", "&gt;").Replace(s)
	return "> " + s + "\n\nDescription: © Art Institute of Chicago, [original record](" + sourceURL + "), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). HTML formatting removed; wording retained. Other artwork metadata: CC0."
}

func assembleChicago(ctx context.Context, root, out string) error {
	license, e := chicagoArtworkLicense(root)
	if e != nil {
		return e
	}
	if e = save(filepath.Join(out, "artworks-license.json"), license); e != nil {
		return e
	}
	index, e := localAuthors(ctx)
	if e != nil {
		return e
	}
	accessions := map[string]int{}
	if e = campaignRecords(root, "chicago", func(r map[string]any) error {
		if inv := str(r, "main_reference_number"); inv != "" {
			accessions[inv]++
		}
		return nil
	}); e != nil {
		return e
	}
	s := campaignSelection("chicago")
	m := campaignMuseum{"Art Institute of Chicago", "Chicago", "art-institute-of-chicago", "US", "https://www.artic.edu/", "www.artic.edu", chicagoExport, "https://api.artic.edu/docs/#licensing"}
	seen := map[string]bool{}
	e = campaignRecords(root, "chicago", func(r map[string]any) error {
		s.Decisions["source_rows"]++
		kind := map[string]string{"Painting": "painting", "Drawing and Watercolor": "drawing", "Print": "print"}[str(r, "artwork_type_title")]
		if kind == "" {
			return nil
		}
		s.Decisions["candidates"]++
		if r["fiscal_year_deaccession"] != nil && integer(r, "fiscal_year_deaccession") != 0 {
			s.Decisions["deaccessioned_review"]++
			return nil
		}
		name, life, ok := chicagoCreator(r)
		if !ok {
			s.Decisions["creator_review"]++
			return nil
		}
		a, ok := matchAuthor(index, name, life)
		if !ok {
			s.Decisions["authority_review"]++
			return nil
		}
		display := str(r, "date_display")
		d, ok := campaignDate(display, integer(r, "date_start"), integer(r, "date_end"))
		if !ok || str(r, "date_qualifier_title") != "" {
			s.Decisions["date_review"]++
			return nil
		}
		if creatorDateConflict(a, d, kind) {
			s.Decisions["creator_date_conflict"]++
			return nil
		}
		id := strconv.Itoa(integer(r, "id"))
		title, inv := str(r, "title"), str(r, "main_reference_number")
		if id == "0" || title == "" || inv == "" || str(r, "api_link") != "https://api.artic.edu/api/v1/artworks/"+id || seen[id] {
			s.Decisions["object_identity_review"]++
			return nil
		}
		seen[id] = true
		if accessions[inv] > 1 {
			s.Decisions["shared_accession_review"]++
			return nil
		}
		if strings.ContainsAny(inv, ",;") || campaignGroupedInventory.MatchString(inv) || campaignGroupedTitle.MatchString(title) {
			s.Decisions["physical_unit_review"]++
			return nil
		}
		u := "https://www.artic.edu/artworks/" + id
		s.addAuthor(name, life, a)
		r["artline_resource_license"] = license
		r["artline_archive_last_modified"] = "2025-02-16T08:32:05Z"
		addCampaignWork(s, m, a, id, title, u, inv, display, kind, str(r, "medium_display"), str(r, "dimensions"), chicagoDescription(str(r, "description"), u), d, r)
		s.Museums[s.Source+"-"+m.Slug]["rights"] = "Artwork metadata CC0 except description, which is CC BY 4.0 with Art Institute of Chicago attribution and licence link in each included description. Source terms: https://www.artic.edu/terms. Image rights are separate; none imported."
		w := s.Works[len(s.Works)-1]
		w["notes"] = "Review only. Chicago export last modified 16 February 2025; retrieved 10 September 2026. Source dates and display flags are historical evidence, not fresh on-view or ownership claims. No masterpiece designation inferred."
		if updated := str(r, "source_updated_at"); len(updated) >= 10 {
			w["source_updated_on"] = updated[:10]
		}
		if titles, ok := r["alt_titles"].([]any); ok {
			aliases := []string{}
			for _, v := range titles {
				if t, ok := v.(string); ok && strings.TrimSpace(t) != "" && len(t) < 1000 {
					aliases = append(aliases, t)
				}
			}
			if len(aliases) > 0 {
				w["aliases"] = aliases
			}
		}
		return nil
	})
	if e != nil {
		return e
	}
	return s.write(out)
}
