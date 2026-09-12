package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
)

// Bounded official metadata only. Generated enrichment and image bytes are not fetched.
func captureSMK(ctx context.Context, out string) error {
	total, collected := -1, 0
	pages := []string{}
	for offset := 0; offset < 10000; offset += 100 {
		q := url.Values{"keys": {"*"}, "filters": {"[object_names:Painting],[public_domain:true]"}, "offset": {strconv.Itoa(offset)}, "rows": {"100"}, "lang": {"en"}}
		file := fmt.Sprintf("page-%03d.json", offset/100+1)
		p := filepath.Join(out, file)
		if e := fetch(ctx, p, "https://api.smk.dk/api/v1/art/search/?"+q.Encode(), 8<<20); e != nil {
			return e
		}
		var page struct {
			Offset, Rows, Found int
			Items               []map[string]any
		}
		b, e := os.ReadFile(p)
		if e != nil {
			return e
		}
		if e = json.Unmarshal(b, &page); e != nil {
			return e
		}
		if total < 0 {
			total = page.Found
		}
		if page.Offset != offset || page.Rows != 100 || page.Found != total || len(page.Items) > 100 || len(page.Items) == 0 {
			return fmt.Errorf("SMK pagination drift/incomplete response at %d", offset)
		}
		collected += len(page.Items)
		pages = append(pages, file)
		fmt.Printf("SMK captured %d/%d metadata records\n", collected, total)
		if collected == total {
			return save(filepath.Join(out, "capture.json"), map[string]any{"source": "smk", "found": total, "pages": pages, "scope": "Source Painting + public_domain=true; not every SMK object"})
		}
		if collected > total || len(page.Items) != 100 {
			return fmt.Errorf("SMK partial page")
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(time.Second):
		}
	}
	return fmt.Errorf("SMK metadata cap reached; no complete manifest written")
}

func smkRecords(root string, visit func(map[string]any) error) error {
	dir := filepath.Join(root, "content/imports/europe-smk-20260910")
	b, e := os.ReadFile(filepath.Join(dir, "capture.json"))
	if e != nil {
		return e
	}
	var m struct {
		Found int
		Pages []string
	}
	if json.Unmarshal(b, &m) != nil || m.Found < 1 || m.Found > 10000 || len(m.Pages) > 100 {
		return fmt.Errorf("invalid SMK manifest")
	}
	n := 0
	for _, file := range m.Pages {
		if file != filepath.Base(file) {
			return fmt.Errorf("unsafe SMK file")
		}
		p := filepath.Join(dir, file)
		if e = verify(p); e != nil {
			return e
		}
		b, e = os.ReadFile(p)
		if e != nil {
			return e
		}
		var page struct{ Items []map[string]any }
		if e = json.Unmarshal(b, &page); e != nil {
			return e
		}
		for _, r := range page.Items {
			n++
			if e = visit(r); e != nil {
				return e
			}
		}
	}
	if n != m.Found {
		return fmt.Errorf("incomplete SMK capture")
	}
	return nil
}

var smkObject = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9.-]{0,65}$`)

// Artist career/life bounds and museum accession bounds are not established
// creation dates. Preserve the raw source for review instead of inventing a range.
var smkUncertain = regexp.MustCompile(`(?i)(udateret|virkeår|levetid|baseret på kunstnerens årstal|tilgået museet|unknown|undated|after|before|efter|før|muligvis|tilskrevet)`)

func smkDate(r map[string]any) (creationDate, string, bool) {
	dates, _ := r["production_date"].([]any)
	if len(dates) != 1 {
		return creationDate{}, "", false
	}
	d, ok := dates[0].(map[string]any)
	if !ok {
		return creationDate{}, "", false
	}
	start, end := str(d, "start"), str(d, "end")
	if len(start) < 4 || len(end) < 4 {
		return creationDate{}, "", false
	}
	first, _ := strconv.Atoi(start[:4])
	last, _ := strconv.Atoi(end[:4])
	display := str(d, "period")
	notes, _ := r["production_dates_notes"].([]any)
	for _, v := range notes {
		n, _ := v.(string)
		if smkUncertain.MatchString(n) {
			return creationDate{}, display, false
		}
		if strings.Contains(strings.ToLower(n), "ca.") && !strings.Contains(strings.ToLower(display), "ca.") && !strings.Contains(strings.ToLower(display), "c.") {
			display = "ca. " + display
		}
	}
	date, ok := campaignDate(display, first, last)
	return date, display, ok
}

func assembleSMK(ctx context.Context, root, out string) error {
	index, e := localAuthors(ctx)
	if e != nil {
		return e
	}
	s := campaignSelection("smk")
	m := campaignMuseum{"Statens Museum for Kunst (SMK)", "Copenhagen", "statens-museum-for-kunst", "DK", "https://www.smk.dk/", "open.smk.dk", "https://api.smk.dk/api/v1/docs/", "https://www.smk.dk/en/article/smk-api/"}
	// Duplicate source inventory groups are deferred, never first-record wins.
	inventory := map[string]int{}
	if e = smkRecords(root, func(r map[string]any) error { inventory[str(r, "object_number")]++; return nil }); e != nil {
		return e
	}
	e = smkRecords(root, func(r map[string]any) error {
		s.Decisions["source_rows"]++
		creators, _ := r["production"].([]any)
		if len(creators) != 1 {
			s.Decisions["multiple_creator_review"]++
			return nil
		}
		c, ok := creators[0].(map[string]any)
		if !ok {
			return fmt.Errorf("invalid creator")
		}
		if role := str(c, "creator_role"); role != "" && role != "artist" && role != "Painter" {
			s.Decisions["qualified_creator_review"]++
			return nil
		}
		name := str(c, "creator")
		life := ""
		b, z := str(c, "creator_date_of_birth"), str(c, "creator_date_of_death")
		if len(b) >= 4 && len(z) >= 4 {
			life = b[:4] + "-" + z[:4]
		}
		a, ok := matchAuthor(index, name, life)
		if !ok {
			s.Decisions["authority_review"]++
			return nil
		}
		d, display, ok := smkDate(r)
		if !ok {
			s.Decisions["date_review"]++
			return nil
		}
		if creatorDateConflict(a, d, "painting") {
			s.Decisions["creator_date_conflict"]++
			return nil
		}
		id, u := str(r, "object_number"), str(r, "frontend_url")
		if !smkObject.MatchString(id) || u != "https://open.smk.dk/artwork/image/"+id || inventory[id] != 1 {
			s.Decisions["identity_review"]++
			return nil
		}
		if r["public_domain"] != true || str(r, "rights") != "https://creativecommons.org/publicdomain/mark/1.0/" {
			s.Decisions["rights_review"]++
			return nil
		}
		titles, _ := r["titles"].([]any)
		title := ""
		for _, v := range titles {
			if t, ok := v.(map[string]any); ok {
				if title == "" || str(t, "language") == "engelsk" {
					title = str(t, "title")
				}
			}
		}
		if title == "" || campaignGroupedTitle.MatchString(title) {
			s.Decisions["title_or_unit_review"]++
			return nil
		}
		tech, _ := r["techniques"].([]any)
		medium := []string{}
		for _, v := range tech {
			if t, ok := v.(string); ok {
				medium = append(medium, t)
			}
		}
		s.addAuthor(name, life, a)
		addCampaignWork(s, m, a, id, title, u, id, display, "painting", strings.Join(medium, "; "), "", "", d, r)
		s.Museums["smk-"+m.Slug]["rights"] = "Official factual catalogue metadata; source public_domain=true with Public Domain Mark. No generated enrichment used. Image copying is a separate selected, fresh object-level review."
		if updated := str(r, "modified"); len(updated) >= 10 {
			s.Works[len(s.Works)-1]["source_updated_on"] = updated[:10]
		}
		return nil
	})
	if e != nil {
		return e
	}
	return s.write(out)
}
