package main

import (
	"context"
	"encoding/json"
	"errors"
	"net/url"
	"regexp"
	"strings"
	"time"
)

type authorityLink struct{ Work, Artist, Inventory string }

var commonsLinks = map[string]authorityLink{
	"437442": {"Q19912134", "Q172911", "1972.145.2"},
	"437671": {"Q19905454", "Q151573", "1976.201.19"},
	"488319": {"Q19919146", "Q61064", "49.70.1"},
}

func obj(v any) map[string]any { m, _ := v.(map[string]any); return m }
func claims(e map[string]any, key string) []any {
	list, _ := obj(e["claims"])[key].([]any)
	out := []any{}
	for _, v := range list {
		c := obj(v)
		if str(c, "rank") == "deprecated" {
			continue
		}
		snak := obj(c["mainsnak"])
		if str(snak, "snaktype") != "value" {
			continue
		}
		out = append(out, obj(snak["datavalue"])["value"])
	}
	return out
}
func claimIs(e map[string]any, key, want string) bool {
	for _, v := range claims(e, key) {
		if s, ok := v.(string); ok && s == want {
			return true
		}
		if str(obj(v), "id") == want {
			return true
		}
	}
	return false
}
func metadata(info map[string]any, key string) string {
	return str(obj(obj(info["extmetadata"])[key]), "value")
}
func validateAuthority(entity map[string]any, link authorityLink) error {
	if str(entity, "id") != link.Work || len(claims(entity, "P170")) != 1 || !claimIs(entity, "P170", link.Artist) || !claimIs(entity, "P195", "Q160236") || !claimIs(entity, "P217", link.Inventory) || len(claims(entity, "P18")) != 1 {
		return errors.New("ambiguous or changed object/creator/collection/inventory/image authority")
	}
	list, _ := obj(entity["claims"])["P170"].([]any)
	for _, v := range list {
		c := obj(v)
		if str(c, "rank") != "deprecated" && len(obj(c["qualifiers"])) > 0 {
			return errors.New("qualified attribution needs separate review")
		}
	}
	return nil
}
func stageCommons(ctx context.Context, f *fetcher, x *coverageEntry) error {
	link, ok := commonsLinks[x.Pick.Object]
	if !ok {
		return errors.New("no reviewed object crosswalk")
	}
	wdURL := "https://www.wikidata.org/w/api.php?" + url.Values{"action": {"wbgetentities"}, "ids": {link.Work}, "props": {"claims"}, "format": {"json"}, "maxlag": {"5"}}.Encode()
	b, e := f.get(ctx, wdURL, 2<<20)
	if e != nil {
		return e
	}
	var wd map[string]any
	if e = json.Unmarshal(b, &wd); e != nil {
		return e
	}
	if wd["error"] != nil {
		return errors.New("authority provider requested pause")
	}
	entity := obj(obj(wd["entities"])[link.Work])
	if e = validateAuthority(entity, link); e != nil {
		return e
	}
	file, ok := claims(entity, "P18")[0].(string)
	if !ok || file == "" || len(file) > 500 {
		return errors.New("invalid authority image name")
	}
	api := "https://commons.wikimedia.org/w/api.php?" + url.Values{"action": {"query"}, "format": {"json"}, "titles": {"File:" + file}, "prop": {"imageinfo|revisions"}, "iiprop": {"url|extmetadata"}, "iiurlwidth": {"700"}, "rvprop": {"ids|timestamp|content"}, "rvslots": {"main"}, "maxlag": {"5"}}.Encode()
	b, e = f.get(ctx, api, 2<<20)
	if e != nil {
		return e
	}
	var response map[string]any
	if e = json.Unmarshal(b, &response); e != nil {
		return e
	}
	if response["error"] != nil {
		return errors.New("Commons provider requested pause")
	}
	pages := obj(obj(response["query"])["pages"])
	if len(pages) != 1 {
		return errors.New("image identity ambiguous")
	}
	var info map[string]any
	var revision map[string]any
	for _, p := range pages {
		page := obj(p)
		if str(page, "title") != "File:"+file {
			return errors.New("image file name changed")
		}
		list, _ := page["imageinfo"].([]any)
		if len(list) != 1 {
			return errors.New("image record absent")
		}
		info = obj(list[0])
		if revisions, ok := page["revisions"].([]any); ok && len(revisions) == 1 {
			revision = obj(revisions[0])
		}
	}
	x.Raw = map[string]any{"wikidata": entity, "commons": info, "commons_revision": revision, "file_title": "File:" + file, "authority_api": wdURL, "commons_api": api}
	x.ImageURL = str(info, "thumburl")
	x.ImagePage = str(info, "descriptionurl")
	x.Retrieved = time.Now().UTC()
	x.Provider = "Wikimedia Commons"
	x.Rights = "public_domain"
	x.License = "Public domain (Commons PD-Art)"
	x.Policy = commonsPolicy
	x.LicenseURL = commonsPolicy
	x.Credit = x.Candidate.Artist + ". " + x.Candidate.Title + ". Wikimedia Commons, faithful reproduction marked PD-Art. Original: The Metropolitan Museum of Art, " + x.Accession + "."
	if commonsCC0(info) {
		x.Rights = "cc0"
		x.License = "CC0 1.0 (Met donation via Wikimedia Commons)"
		x.LicenseURL = "https://creativecommons.org/publicdomain/zero/1.0/"
		x.Policy = "https://commons.wikimedia.org/wiki/Commons:Met"
		x.Credit = x.Candidate.Artist + ". " + x.Candidate.Title + ". Met Open Access donation via Wikimedia Commons, " + x.Accession + "."
	}
	return validateCommons(*x)
}

func commonsCC0(info map[string]any) bool {
	// CC0 is an explicit waiver: MediaWiki's generic Copyrighted=True flag
	// does not negate it. Require the exact dedication AND museum donation.
	return metadata(info, "LicenseShortName") == "CC0" && metadata(info, "License") == "cc0" && metadata(info, "UsageTerms") == "Creative Commons Zero, Public Domain Dedication" && metadata(info, "Restrictions") == "" && strings.Contains(metadata(info, "Categories"), "CC-Zero") && strings.Contains(metadata(info, "Categories"), "Images from Metropolitan Museum of Art") && strings.Contains(metadata(info, "Credit"), "Commons:Met")
}

func commonsField(wikitext, field string) string {
	// Do not accept inventory/source fields inside the donor's commented legacy
	// metadata, or ambiguous duplicate fields. Only the live template counts.
	wikitext = regexp.MustCompile(`(?s)<!--.*?-->`).ReplaceAllString(wikitext, "")
	pattern := regexp.MustCompile(`(?m)^\s*\|\s*` + regexp.QuoteMeta(field) + `\s*=\s*([^\r\n]*)`)
	matches := pattern.FindAllStringSubmatch(wikitext, -1)
	if len(matches) != 1 {
		return ""
	}
	return strings.TrimSpace(matches[0][1])
}

func commonsDonationIdentity(x coverageEntry, link authorityLink) bool {
	revision := obj(x.Raw["commons_revision"])
	wikitext := str(obj(obj(revision["slots"])["main"]), "*")
	source := commonsField(wikitext, "source")
	return str(revision, "timestamp") != "" && (source == x.Page || source == x.Page+"{{Template:TheMet}}") && commonsField(wikitext, "accession number") == link.Inventory && commonsField(wikitext, "wikidata") == link.Work && commonsField(wikitext, "title") == x.Candidate.Title && commonsField(wikitext, "permission") == "{{Cc-zero}}"
}

func validateCommons(x coverageEntry) error {
	link, ok := commonsLinks[x.Candidate.Object]
	if !ok || x.Accession != link.Inventory || x.Page != "https://www.metmuseum.org/art/collection/search/"+x.Candidate.Object {
		return errors.New("Commons database crosswalk conflict")
	}
	entity := obj(x.Raw["wikidata"])
	if e := validateAuthority(entity, link); e != nil {
		return e
	}
	file, _ := claims(entity, "P18")[0].(string)
	if str(x.Raw, "file_title") != "File:"+file {
		return errors.New("Commons image is not authority-linked")
	}
	info := obj(x.Raw["commons"])
	cats := metadata(info, "Categories")
	cc0 := commonsCC0(info)
	if !cc0 && (metadata(info, "LicenseShortName") != "Public domain" || metadata(info, "UsageTerms") != "Public domain" || !strings.EqualFold(metadata(info, "Copyrighted"), "false") || metadata(info, "Restrictions") != "" || (!strings.Contains(cats, "PD-Art") && !strings.Contains(cats, "PD-old-100"))) {
		return errors.New("file-specific public-domain reuse not established")
	}
	if strings.Contains(cats, "Artworks with digital representation of different depicts") {
		return errors.New("Commons depicts conflict requires visual/structured-data review")
	}
	// Require the file's own credit to link to the same official museum object.
	// Donated files may expose only the partnership in Credit. In that case,
	// require the file's own live source/inventory/title/authority/CC0 template.
	// The independent P18/file crosswalk is still exact.
	if !strings.Contains(metadata(info, "Credit"), x.Page) && !(cc0 && commonsDonationIdentity(x, link)) {
		return errors.New("file credit does not identify exact museum object")
	}
	rights, policy, license := "public_domain", commonsPolicy, commonsPolicy
	if cc0 {
		rights, policy, license = "cc0", "https://commons.wikimedia.org/wiki/Commons:Met", "https://creativecommons.org/publicdomain/zero/1.0/"
	}
	if x.ImageURL != str(info, "thumburl") || x.ImagePage != str(info, "descriptionurl") || x.Rights != rights || x.Policy != policy || x.LicenseURL != license || x.Provider != "Wikimedia Commons" {
		return errors.New("Commons evidence/attachment mismatch")
	}
	u, e := url.Parse(x.ImageURL)
	if e != nil || u.Scheme != "https" || u.User != nil || u.Port() != "" || (u.Host != "upload.wikimedia.org" && u.Host != "thumb.wikimedia.org") || !strings.HasPrefix(u.Path, "/wikipedia/commons/") {
		return errors.New("unsafe image URL")
	}
	page, e := url.Parse(x.ImagePage)
	if e != nil || page.Scheme != "https" || page.Host != "commons.wikimedia.org" || page.User != nil || page.Port() != "" || !strings.HasPrefix(page.Path, "/wiki/File:") {
		return errors.New("unsafe licence page")
	}
	if strings.ReplaceAll(page.Path, " ", "_") != "/wiki/File:"+strings.ReplaceAll(file, " ", "_") {
		return errors.New("licence page belongs to a different file")
	}
	return nil
}
