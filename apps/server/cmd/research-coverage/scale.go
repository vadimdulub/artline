package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

func ngaScaleAudit(root, out string) error {
	path := filepath.Join(root, "content/imports/nga-catalogue-20260909/objects.csv")
	if e := verify(path); e != nil {
		return e
	}
	counts := map[string]int{}
	dates := map[string]map[string]int{}
	e := csvRows(path, ',', func(r map[string]string) error {
		k := r["classification"]
		counts[k]++
		if dates[k] == nil {
			dates[k] = map[string]int{}
		}
		_, decision := ngaDate(r)
		dates[k][decision]++
		return nil
	})
	if e != nil {
		return e
	}
	fmt.Println(counts)
	return save(filepath.Join(out, "nga-object-audit.json"), map[string]any{"classifications": counts, "creation_date_decisions": dates})
}

// This opt-in bulk path keeps the old painting-only snapshot immutable. It
// selects physical paintings, drawings and prints; never photos or museum totals.
func assembleNGAScale(ctx context.Context, root, out string) error {
	input := filepath.Join(root, "content/imports/nga-catalogue-20260909")
	for _, f := range []string{"objects.csv", "constituents.csv", "objects_constituents.csv", "object_associations.csv", "objects_text_entries.csv"} {
		if e := verify(filepath.Join(input, f)); e != nil {
			return e
		}
	}
	objects := map[string]map[string]string{}
	creators := map[string]map[string]string{}
	links := map[string][]map[string]string{}
	inseparable := map[string]bool{}
	narratives := map[string][]string{}
	e := csvRows(filepath.Join(input, "objects.csv"), ',', func(r map[string]string) error {
		if r["classification"] == "Painting" || r["classification"] == "Drawing" || r["classification"] == "Print" {
			objects[r["objectid"]] = r
		}
		return nil
	})
	if e != nil {
		return e
	}
	e = csvRows(filepath.Join(input, "constituents.csv"), ',', func(r map[string]string) error { creators[r["constituentid"]] = r; return nil })
	if e != nil {
		return e
	}
	e = csvRows(filepath.Join(input, "objects_constituents.csv"), ',', func(r map[string]string) error {
		if objects[r["objectid"]] != nil && r["roletype"] == "artist" {
			links[r["objectid"]] = append(links[r["objectid"]], r)
		}
		return nil
	})
	if e != nil {
		return e
	}
	e = csvRows(filepath.Join(input, "object_associations.csv"), ',', func(r map[string]string) error {
		if r["relationship"] == "inseparable" {
			inseparable[r["childobjectid"]] = true
		}
		return nil
	})
	if e != nil {
		return e
	}
	// CC0 museum narrative is preserved, not newly generated art criticism. Limit
	// displayed text; full immutable CSV remains available for editorial follow-up.
	e = csvRows(filepath.Join(input, "objects_text_entries.csv"), ',', func(r map[string]string) error {
		if objects[r["objectid"]] != nil && (r["texttype"] == "brief_narrative" || r["texttype"] == "visual_description") {
			text := r["text"]
			if text == "" {
				text = r["textentry"]
			}
			if text != "" {
				narratives[r["objectid"]] = append(narratives[r["objectid"]], text)
			}
		}
		return nil
	})
	if e != nil {
		return e
	}
	cfg, e := pgxpool.ParseConfig(config.Load().DatabaseURL)
	if e != nil {
		return e
	}
	local := func(h string) bool {
		return h == "localhost" || h == "127.0.0.1" || h == "::1" || strings.HasPrefix(h, "/")
	}
	if !local(cfg.ConnConfig.Host) {
		return errors.New("local DB only")
	}
	for _, f := range cfg.ConnConfig.Fallbacks {
		if !local(f.Host) {
			return errors.New("local DB only")
		}
	}
	pool, e := pgxpool.NewWithConfig(ctx, cfg)
	if e != nil {
		return e
	}
	defer pool.Close()
	// Preflight identity collisions. No fuzzy names, no silent wrong-QID merges.
	db, e := pool.Query(ctx, `SELECT a.id::text,a.normalized_name,coalesce(e.external_id,'') FROM artists a LEFT JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' WHERE a.status<>'archived'`)
	if e != nil {
		return e
	}
	knownQ := map[string]bool{}
	knownNames := map[string]bool{}
	for db.Next() {
		var id, n, q string
		if e = db.Scan(&id, &n, &q); e != nil {
			return e
		}
		knownNames[n] = true
		if q != "" {
			knownQ[q] = true
		}
	}
	db.Close()
	if e = db.Err(); e != nil {
		return e
	}
	ids := make([]string, 0, len(objects))
	for id := range objects {
		ids = append(ids, id)
	}
	sort.Slice(ids, func(i, j int) bool { a, _ := strconv.Atoi(ids[i]); b, _ := strconv.Atoi(ids[j]); return a < b })
	decisions := map[string]int{}
	kinds := map[string]int{}
	roleCounts := map[string]int{}
	authorDefs := map[string]map[string]any{}
	works := []map[string]any{}
	deferred := []map[string]any{}
	qidRE := regexp.MustCompile(`^Q[1-9][0-9]*$`)
	for _, id := range ids {
		r := objects[id]
		d, decision := ngaDate(r)
		ls := links[id]
		var c map[string]string
		if r["accessioned"] != "1" || r["isvirtual"] != "0" || r["accessionnum"] == "" {
			decision = "not_accessioned_or_virtual"
		}
		if inseparable[id] {
			decision = "inseparable_child_record"
		}
		if len(ls) != 1 {
			decision = "multiple_or_missing_creators"
		} else {
			l := ls[0]
			c = creators[l["constituentid"]]
			roleCounts[l["role"]]++
			makerRole := l["role"] == "artist" || l["role"] == "painter" || l["role"] == "engraver" || l["role"] == "etcher" || l["role"] == "printmaker"
			if decision == "eligible" && (!makerRole || l["prefix"] != "" || l["suffix"] != "" || c["constituenttype"] != "individual" || r["attribution"] != c["forwarddisplayname"]) {
				decision = "qualified_creator_requires_review"
			}
			q := c["wikidataid"]
			if decision == "eligible" && q != "" && !qidRE.MatchString(q) {
				decision = "invalid_creator_qid"
			}
			// Existing exact-name artists without a matching authority need an explicit
			// crosswalk. Unicode normalization is repeated authoritatively by importer.
			if decision == "eligible" && !knownQ[q] && knownNames[strings.ToLower(c["forwarddisplayname"])] {
				decision = "creator_identity_collision"
			}
		}
		if decision == "eligible" && catalog.CreationScope(&d.First, &d.Last, d.Precision) != "eligible" {
			decision = "cutoff_uncertainty_requires_review"
		}
		if decision == "eligible" && !knownQ[c["wikidataid"]] && knownNames[ingest.NormalizeAuthorityName(c["forwarddisplayname"])] {
			decision = "creator_identity_collision"
		}
		decisions[decision]++
		if decision != "eligible" {
			deferred = append(deferred, map[string]any{"source_record_id": id, "title": r["title"], "decision": decision, "date_display": r["displaydate"], "creator": c})
			continue
		}
		aid := c["constituentid"]
		def := authorDefs[aid]
		if def == nil {
			def = map[string]any{"id": aid, "name": c["forwarddisplayname"], "qid": c["wikidataid"], "sort_name": c["preferreddisplayname"], "date_display": c["displaydate"], "source_begin": c["beginyear"], "source_end": c["endyear"], "activity_start": d.First, "activity_end": d.Last, "source_url": "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/" + ngaRevision + "/data/constituents.csv", "raw": c}
			authorDefs[aid] = def
		} else {
			if d.First < def["activity_start"].(int) {
				def["activity_start"] = d.First
			}
			if d.Last > def["activity_end"].(int) {
				def["activity_end"] = d.Last
			}
		}
		objectURL := "https://www.nga.gov/collection/art-object-page." + id + ".html"
		description := fmt.Sprintf("%s — %s. %s.\n\nMedium: %s.\n\nDimensions (museum labels retained): %s.\n\nCollection: National Gallery of Art, Washington. Accession %s. %s.\n\nMuseum holding does not establish current display.\n\nSource: [National Gallery of Art](%s), CC0 collection metadata, retrieved 9 September 2026.", r["title"], c["forwarddisplayname"], r["displaydate"], r["medium"], r["dimensions"], r["accessionnum"], r["creditline"], objectURL)
		if texts := strings.Join(narratives[id], "\n\n"); texts != "" && len(texts) < 30000 {
			description = texts + "\n\n" + description
		}
		kind := strings.ToLower(r["classification"])
		kinds[kind]++
		works = append(works, map[string]any{"painter": aid, "title": r["title"], "institution": "nga", "accession": r["accessionnum"], "url": objectURL, "source_object_id": id, "source_publisher": "National Gallery of Art, Washington", "date_display": r["displaydate"], "creation_date": d, "attribution_role": "primary", "work_type": kind, "description_md": description, "medium": r["medium"], "dimensions": r["dimensions"], "collection": r["creditline"], "notes": "Accessioned physical collection object; single current unqualified source creator. Not automatically a masterpiece or currently on view.", "source_raw": map[string]any{"object": r, "creator": c, "creator_link": ls[0], "dataset_revision": ngaRevision, "metadata_rights": "CC0-1.0"}})
	}
	inst := map[string]string{"id": "nga", "name": "National Gallery of Art", "city": "Washington, DC", "country": "US", "rights": "CC0 metadata; images require individual openaccess=1 flag and separate selected image import.", "data_url": "https://github.com/NationalGalleryOfArt/opendata", "data_route": "Pinned official CSV revision " + ngaRevision, "rights_url": "https://github.com/NationalGalleryOfArt/opendata/blob/main/LICENSE"}
	chunks := []map[string]any{}
	for start := 0; start < len(works); start += 1000 {
		end := min(start+1000, len(works))
		authors := map[string]any{}
		for _, w := range works[start:end] {
			id := w["painter"].(string)
			authors[id] = authorDefs[id]
		}
		name := fmt.Sprintf("nga-%03d.json", start/1000+1)
		path := filepath.Join(out, name)
		if e = save(path, map[string]any{"schema_version": 3, "accessed_on": "2026-09-09", "source": "nga", "revision": ngaRevision, "institutions": []any{inst}, "authors": authors, "works": works[start:end]}); e != nil {
			return e
		}
		sha, n, e := hashFile(path)
		if e != nil {
			return e
		}
		chunks = append(chunks, map[string]any{"file": name, "sha256": sha, "bytes": n, "works": end - start})
	}
	if e = save(filepath.Join(out, "deferred.json"), deferred); e != nil {
		return e
	}
	summary := map[string]any{"source_objects": len(objects), "eligible_objects": len(works), "creators": len(authorDefs), "decisions": decisions, "work_types": kinds, "source_creator_roles": roleCounts, "chunks": chunks, "metadata_revision": ngaRevision}
	if e = save(filepath.Join(out, "manifest.json"), summary); e != nil {
		return e
	}
	b, _ := json.Marshal(summary)
	fmt.Println(string(b))
	return nil
}
