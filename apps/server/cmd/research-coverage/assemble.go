package main

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

type staged struct {
	Source   string `json:"source"`
	Kind     string `json:"kind"`
	RecordID string `json:"record_id"`
	Country  string `json:"country"`
	Name     string `json:"name"`
	URL      string `json:"source_url"`
	Decision string `json:"decision"`
	Raw      any    `json:"raw"`
}

func csvRows(path string, delimiter rune, visit func(map[string]string) error) error {
	f, e := os.Open(path)
	if e != nil {
		return e
	}
	defer f.Close()
	r := csv.NewReader(f)
	r.Comma = delimiter
	h, e := r.Read()
	if e != nil {
		return e
	}
	for {
		row, e := r.Read()
		if errors.Is(e, io.EOF) {
			return nil
		}
		if e != nil {
			return e
		}
		v := map[string]string{}
		for i, k := range h {
			v[strings.ToLower(strings.TrimPrefix(k, "\ufeff"))] = row[i]
		}
		if e = visit(v); e != nil {
			return e
		}
	}
}

func verify(path string) error {
	b, e := os.ReadFile(path + ".snapshot.json")
	if e != nil {
		return e
	}
	var s snapshot
	if e = json.Unmarshal(b, &s); e != nil {
		return e
	}
	h, n, e := hashFile(path)
	if e != nil {
		return e
	}
	if h != s.SHA || n != s.Bytes {
		return fmt.Errorf("changed input %s", path)
	}
	return nil
}

var literalDate = regexp.MustCompile(`^(c\. |ca\. |circa |about )?(\d{4})(?:\s*[-/]\s*(\d{2}|\d{4}))?$`)
var decadeDate = regexp.MustCompile(`^(early |mid-?|late )?(\d{3})0s$`)

type creationDate struct {
	First     int    `json:"first"`
	Last      int    `json:"last"`
	Precision string `json:"precision"`
}

// Never use NGA search years when the literal is absent: those numbers may be
// the creator's lifetime. Disjunctive, open or conflicting dates stay in staging.
func ngaDate(row map[string]string) (creationDate, string) {
	d := creationDate{}
	s := strings.ReplaceAll(strings.TrimSpace(row["displaydate"]), "–", "-")
	m := literalDate.FindStringSubmatch(s)
	if m != nil {
		d.First, _ = strconv.Atoi(m[2])
		d.Last = d.First
		d.Precision = "exact"
		if m[3] != "" {
			d.Last, _ = strconv.Atoi(m[3])
			if len(m[3]) == 2 {
				d.Last += (d.First / 100) * 100
			}
			d.Precision = "range"
		}
		if m[1] != "" {
			if d.Precision == "range" {
				d.Precision = "circa_range"
			} else {
				d.Precision = "circa"
			}
		}
	} else if m = decadeDate.FindStringSubmatch(s); m != nil {
		d.First, _ = strconv.Atoi(m[2] + "0")
		d.Last = d.First + 9
		d.Precision = "decade"
	} else {
		return d, "date_literal_requires_review"
	}
	if d.First < 1100 || d.Last < d.First {
		return d, "date_outside_atlas_or_invalid"
	}
	if d.First > 1970 {
		return d, "after_1970"
	}
	if d.Last > 1970 {
		return d, "date_crosses_1970"
	}
	a, e1 := strconv.Atoi(row["beginyear"])
	b, e2 := strconv.Atoi(row["endyear"])
	if e1 != nil || e2 != nil || a < 1 || b < a {
		return d, "numeric_date_requires_review"
	}
	if d.Precision == "decade" {
		if a < d.First || b > d.Last {
			return d, "date_literal_numeric_conflict"
		}
	} else if a != d.First || b != d.Last {
		return d, "date_literal_numeric_conflict"
	}
	return d, "eligible"
}

func assembleNGA(ctx context.Context, root, out string) error {
	input := filepath.Join(root, "content/imports/nga-catalogue-20260909")
	rows := map[string]map[string]string{}
	total := 0
	for _, f := range []string{"objects.csv", "constituents.csv", "objects_constituents.csv", "objects_terms.csv", "object_associations.csv", "objects_text_entries.csv"} {
		if e := verify(filepath.Join(input, f)); e != nil {
			return e
		}
	}
	e := csvRows(filepath.Join(input, "objects.csv"), ',', func(r map[string]string) error {
		total++
		if strings.EqualFold(r["classification"], "painting") {
			if rows[r["objectid"]] != nil {
				return errors.New("duplicate object")
			}
			rows[r["objectid"]] = r
		}
		return nil
	})
	if e != nil {
		return e
	}
	creators := map[string]map[string]string{}
	e = csvRows(filepath.Join(input, "constituents.csv"), ',', func(r map[string]string) error { creators[r["constituentid"]] = r; return nil })
	if e != nil {
		return e
	}
	links := map[string][]map[string]string{}
	texts := map[string][]map[string]string{}
	terms := map[string][]map[string]string{}
	associations := map[string][]map[string]string{}
	for _, f := range []string{"objects_constituents.csv", "objects_terms.csv", "objects_text_entries.csv", "object_associations.csv"} {
		e = csvRows(filepath.Join(input, f), ',', func(r map[string]string) error {
			id := r["objectid"]
			if f == "object_associations.csv" {
				id = r["childobjectid"]
				if rows[id] != nil {
					associations[id] = append(associations[id], r)
				}
				id = r["parentobjectid"]
				if rows[id] != nil {
					associations[id] = append(associations[id], r)
				}
				return nil
			}
			if rows[id] == nil {
				return nil
			}
			switch f {
			case "objects_constituents.csv":
				links[id] = append(links[id], r)
			case "objects_terms.csv":
				terms[id] = append(terms[id], r)
			case "objects_text_entries.csv":
				texts[id] = append(texts[id], r)
			}
			return nil
		})
		if e != nil {
			return e
		}
	}
	cfg, e := pgxpool.ParseConfig(config.Load().DatabaseURL)
	if e != nil {
		return e
	}
	local := func(s string) bool {
		return s == "localhost" || s == "127.0.0.1" || s == "::1" || strings.HasPrefix(s, "/")
	}
	if !local(cfg.ConnConfig.Host) {
		return errors.New("local DB only")
	}
	for _, fb := range cfg.ConnConfig.Fallbacks {
		if !local(fb.Host) {
			return errors.New("local DB only")
		}
	}
	pool, e := pgxpool.NewWithConfig(ctx, cfg)
	if e != nil {
		return e
	}
	defer pool.Close()
	dbRows, e := pool.Query(ctx, `SELECT e.external_id FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme='wikidata' AND a.status<>'archived'`)
	if e != nil {
		return e
	}
	cohort := map[string]bool{}
	for dbRows.Next() {
		var q string
		if e = dbRows.Scan(&q); e != nil {
			return e
		}
		cohort[q] = true
	}
	dbRows.Close()
	if e = dbRows.Err(); e != nil {
		return e
	}
	ids := []string{}
	for id := range rows {
		ids = append(ids, id)
	}
	sort.Slice(ids, func(i, j int) bool { a, _ := strconv.Atoi(ids[i]); b, _ := strconv.Atoi(ids[j]); return a < b })
	works := []any{}
	stage := []staged{}
	painters := map[string]string{}
	reasons := map[string]int{}
	for _, id := range ids {
		r := rows[id]
		d, decision := ngaDate(r)
		creatorLinks := []map[string]string{}
		for _, link := range links[id] {
			if link["roletype"] == "artist" {
				creatorLinks = append(creatorLinks, link)
			}
		}
		var c map[string]string
		if r["accessioned"] != "1" || r["isvirtual"] != "0" || r["accessionnum"] == "" {
			decision = "accession_or_virtual_requires_review"
		}
		for _, a := range associations[id] {
			if a["childobjectid"] == id && a["relationship"] == "inseparable" {
				decision = "inseparable_child_record"
			}
		}
		if len(creatorLinks) != 1 {
			decision = "multiple_or_missing_creators"
		} else {
			link := creatorLinks[0]
			c = creators[link["constituentid"]]
			if decision == "eligible" && ((link["role"] != "painter" && link["role"] != "artist") || link["prefix"] != "" || link["suffix"] != "" || c["constituenttype"] != "individual" || r["attribution"] != c["forwarddisplayname"]) {
				decision = "qualified_creator_requires_review"
			}
			if decision == "eligible" && !cohort[c["wikidataid"]] {
				decision = "creator_authority_requires_review"
			}
		}
		raw := map[string]any{"object": r, "creator_links": creatorLinks, "creator": c, "relationships": links[id], "terms": terms[id], "text_entries": texts[id], "object_associations": associations[id], "dataset_revision": ngaRevision, "metadata_rights": "CC0-1.0", "images_downloaded": false}
		objectURL := "https://www.nga.gov/collection/art-object-page." + id + ".html"
		stage = append(stage, staged{"nga", "catalogue_object", id, "US", r["title"], objectURL, decision, raw})
		reasons[decision]++
		if decision != "eligible" {
			continue
		}
		q := c["wikidataid"]
		painters[q] = q
		place := []string{}
		for _, term := range terms[id] {
			if term["termtype"] == "Place Executed" {
				place = append(place, term["term"])
			}
		}
		updated := r["lastdetectedmodification"]
		if len(updated) >= 10 {
			updated = updated[:10]
		} else {
			updated = ""
		}
		works = append(works, map[string]any{"painter": q, "title": r["title"], "institution": "nga", "accession": r["accessionnum"], "url": objectURL, "source_object_id": id, "source_publisher": "National Gallery of Art, Washington", "source_updated_on": updated, "date_display": r["displaydate"], "creation_date": d, "attribution_role": "primary", "medium": r["medium"], "dimensions": r["dimensions"], "creation_place_text": strings.Join(place, "; "), "collection": r["creditline"], "access": "Official NGA CC0 bulk metadata, pinned Git revision " + ngaRevision, "notes": "Museum accessioned painting; no museum-highlight designation or current-display claim. Source Wikidata creator identity matched exactly. Dataset textual dates checked against numeric search dates. Full provenance, inscriptions, terms and catalogue text preserved in the separate research staging record.", "source_raw": raw})
	}
	manifest := map[string]any{"schema_version": 2, "accessed_on": "2026-09-09", "painters": painters, "definitions": map[string]any{"nga": map[string]string{"Slug": "national-gallery-of-art", "Source": "nga-open-data", "Website": "https://www.nga.gov", "Host": "www.nga.gov"}}, "institutions": []any{map[string]string{"id": "nga", "name": "National Gallery of Art", "city": "Washington, DC", "country": "US", "rights": "Metadata CC0-1.0. Image links are not permission to reuse images; no images downloaded.", "data_url": "https://github.com/NationalGalleryOfArt/opendata", "data_route": "Official bulk CSV at pinned revision " + ngaRevision, "rights_url": "https://github.com/NationalGalleryOfArt/opendata/blob/main/LICENSE"}}, "works": works}
	if e = save(filepath.Join(out, "inventory.json"), manifest); e != nil {
		return e
	}
	if e = save(filepath.Join(out, "staging.json"), stage); e != nil {
		return e
	}
	summary := map[string]any{"source_objects": total, "painting_catalogue_records": len(rows), "eligible_existing_authorities": len(works), "painters": len(painters), "decisions": reasons, "revision": ngaRevision}
	if e = save(filepath.Join(out, "summary.json"), summary); e != nil {
		return e
	}
	b, _ := json.Marshal(summary)
	fmt.Println(string(b))
	return nil
}
