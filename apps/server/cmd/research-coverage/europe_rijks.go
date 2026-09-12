package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

var rijksID = regexp.MustCompile(`^https://id\.rijksmuseum\.nl/([0-9]{1,30})$`)
var rijksQueries = []string{"Rembrandt", "Vermeer", "Frans Hals", "Vincent van Gogh", "Claude Monet", "Camille Pissarro", "Jheronimus Bosch", "El Greco"}

func maps(r map[string]any, key string) []map[string]any {
	out := []map[string]any{}
	values, _ := r[key].([]any)
	for _, v := range values {
		if m, ok := v.(map[string]any); ok {
			out = append(out, m)
		}
	}
	return out
}
func rijksEnglish(r map[string]any) bool {
	for _, l := range maps(r, "language") {
		if str(l, "id") == "http://vocab.getty.edu/aat/300388277" {
			return true
		}
	}
	return false
}
func rijksClass(r map[string]any, id string) bool {
	for _, c := range maps(r, "classified_as") {
		if str(c, "id") == "http://vocab.getty.edu/aat/"+id {
			return true
		}
	}
	return false
}
func readMap(p string) (map[string]any, error) {
	b, e := os.ReadFile(p)
	if e != nil {
		return nil, e
	}
	var r map[string]any
	e = json.Unmarshal(b, &r)
	return r, e
}

// Eight explicit creator searches, painting records only. No images and no
// recursive traversal of related objects. A cap is an incomplete capture, not success.
func captureRijks(ctx context.Context, out string) error {
	ids := map[string]bool{}
	for n, creator := range rijksQueries {
		q := url.Values{"creator": {creator}, "type": {"painting"}, "imageAvailable": {"true"}}
		path := filepath.Join(out, fmt.Sprintf("search-%02d.json", n+1))
		if e := fetch(ctx, path, "https://data.rijksmuseum.nl/search/collection?"+q.Encode(), 2<<20); e != nil {
			return e
		}
		r, e := readMap(path)
		if e != nil {
			return e
		}
		part, _ := r["partOf"].(map[string]any)
		total, _ := part["totalItems"].(float64)
		items := maps(r, "orderedItems")
		if total > 100 || r["next"] != nil || int(total) != len(items) {
			return fmt.Errorf("Rijks selected query %s requires pagination; stop for review", creator)
		}
		for _, item := range items {
			id := str(item, "id")
			if !rijksID.MatchString(id) {
				return fmt.Errorf("invalid Rijks ID")
			}
			ids[id] = true
		}
		fmt.Printf("Rijks %s: %d object references\n", creator, len(items))
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(time.Second):
		}
	}
	keys := []string{}
	for id := range ids {
		keys = append(keys, id)
	}
	sort.Strings(keys)
	if len(keys) > 120 {
		return fmt.Errorf("selected object cap exceeded")
	}
	for i, id := range keys {
		number := rijksID.FindStringSubmatch(id)[1]
		p := filepath.Join(out, "object-"+number+".json")
		if e := fetch(ctx, p, "https://data.rijksmuseum.nl/"+number+"?_profile=la-framed", 2<<20); e != nil {
			return e
		}
		r, e := readMap(p)
		if e != nil || str(r, "id") != id || str(r, "type") != "HumanMadeObject" {
			return fmt.Errorf("Rijks object identity mismatch %s", id)
		}
		fmt.Printf("Rijks resolved %d/%d\n", i+1, len(keys))
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(time.Second):
		}
	}
	return save(filepath.Join(out, "capture.json"), map[string]any{"source": "rijks", "ids": keys, "queries": rijksQueries, "scope": "Complete results of eight selected painting+image-available creator queries; not the whole collection"})
}

var rijksQualified = regexp.MustCompile(`(?i)(attributed|workshop|circle of|school of|possibly|follower|after:|copy after|toegeschreven|atelier|omgeving|mogelijk|naar:|navolger)`)

func assembleRijks(ctx context.Context, root, out string) error {
	index, e := localAuthors(ctx)
	if e != nil {
		return e
	}
	byQID := map[string]knownAuthor{}
	for _, as := range index {
		for _, a := range as {
			byQID[a.QID] = a
		}
	}
	dir := filepath.Join(root, "content/imports/europe-rijks-20260910")
	b, e := os.ReadFile(filepath.Join(dir, "capture.json"))
	if e != nil {
		return e
	}
	var cap struct{ IDs []string }
	if json.Unmarshal(b, &cap) != nil || len(cap.IDs) > 120 {
		return fmt.Errorf("invalid Rijks capture")
	}
	s := campaignSelection("rijks")
	m := campaignMuseum{"Rijksmuseum", "Amsterdam", "rijksmuseum", "NL", "https://www.rijksmuseum.nl/", "www.rijksmuseum.nl", "https://data.rijksmuseum.nl/docs/search", "https://data.rijksmuseum.nl/about/"}
	for _, id := range cap.IDs {
		if !rijksID.MatchString(id) {
			return fmt.Errorf("invalid Rijks ID")
		}
		number := rijksID.FindStringSubmatch(id)[1]
		p := filepath.Join(dir, "object-"+number+".json")
		if e = verify(p); e != nil {
			return e
		}
		r, e := readMap(p)
		if e != nil {
			return e
		}
		s.Decisions["source_rows"]++
		if str(r, "id") != id || str(r, "type") != "HumanMadeObject" {
			return fmt.Errorf("object identity mismatch")
		}
		painting := false
		for _, c := range maps(r, "classified_as") {
			for _, eq := range maps(c, "equivalent") {
				painting = painting || str(eq, "id") == "http://vocab.getty.edu/aat/300033618"
			}
		}
		if !painting {
			s.Decisions["type_review"]++
			continue
		}
		prod, _ := r["produced_by"].(map[string]any)
		parts := maps(prod, "part")
		if len(parts) != 1 || len(maps(parts[0], "carried_out_by")) != 1 {
			s.Decisions["creator_review"]++
			continue
		}
		part := parts[0]
		qualified := false
		for _, note := range maps(part, "referred_to_by") {
			qualified = qualified || rijksQualified.MatchString(str(note, "content"))
		}
		if qualified {
			s.Decisions["qualified_creator_review"]++
			continue
		}
		creator := maps(part, "carried_out_by")[0]
		qids := []string{}
		for _, eq := range maps(creator, "equivalent") {
			u := str(eq, "id")
			if strings.HasPrefix(u, "http://www.wikidata.org/entity/") {
				qids = append(qids, strings.TrimPrefix(u, "http://www.wikidata.org/entity/"))
			}
		}
		if len(qids) != 1 {
			s.Decisions["authority_review"]++
			continue
		}
		a, ok := byQID[qids[0]]
		if !ok {
			s.Decisions["authority_review"]++
			continue
		}
		span, _ := prod["timespan"].(map[string]any)
		start, end := str(span, "begin_of_the_begin"), str(span, "end_of_the_end")
		display := ""
		for _, n := range maps(span, "identified_by") {
			if rijksEnglish(n) {
				display = str(n, "content")
			}
		}
		if len(start) < 4 || len(end) < 4 {
			s.Decisions["date_review"]++
			continue
		}
		first, _ := strconv.Atoi(start[:4])
		last, _ := strconv.Atoi(end[:4])
		d, ok := campaignDate(display, first, last)
		if !ok || creatorDateConflict(a, d, "painting") {
			s.Decisions["date_review"]++
			continue
		}
		title, accession, page, medium, dimensions := "", "", "", "", ""
		for _, n := range maps(r, "identified_by") {
			if str(n, "type") == "Name" && rijksEnglish(n) && rijksClass(n, "300417200") {
				title = str(n, "content")
			}
			if str(n, "type") == "Identifier" && rijksClass(n, "300312355") {
				accession = str(n, "content")
			}
		}
		for _, n := range maps(r, "subject_of") {
			for _, c := range maps(n, "digitally_carried_by") {
				for _, ap := range maps(c, "access_point") {
					u := str(ap, "id")
					if strings.HasPrefix(u, "https://www.rijksmuseum.nl/") && strings.Contains(u, "/collectie/object/") {
						page = u
					}
				}
			}
		}
		for _, n := range maps(r, "referred_to_by") {
			if rijksEnglish(n) && rijksClass(n, "300435429") {
				medium = str(n, "content")
			}
			if rijksEnglish(n) && rijksClass(n, "300435430") {
				dimensions = str(n, "content")
			}
		}
		if title == "" || accession == "" || page == "" || campaignGroupedTitle.MatchString(title) {
			s.Decisions["identity_title_review"]++
			continue
		}
		s.Crosswalk[qids[0]] = map[string]any{"source_creator": creator, "local_name": a.Name, "qid": a.QID, "basis": "Exact museum-supplied Wikidata identifier, existing authority only"}
		addCampaignWork(s, m, a, number, title, page, accession, display, "painting", medium, dimensions, "", d, r)
		s.Museums["rijks-rijksmuseum"]["data_route"] = "Eight selected creator searches and their complete official Linked Art object records; not a whole-collection scan"
	}
	return s.write(out)
}
