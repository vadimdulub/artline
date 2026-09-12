package main

// Joconde's creation-of-notice date is NOT the object's creation date. This
// metadata-only audit never opens a database or downloads image binaries.
import (
	"fmt"
	"path/filepath"
	"sort"
	"strings"
)

func jocondeAudit(root, out string) error {
	path := filepath.Join(root, "content/imports/joconde-20260910/joconde.csv")
	if e := verify(path); e != nil {
		return e
	}
	counts := map[string]int{}
	authors := map[string]int{}
	fields := map[string]map[string]int{}
	samples := []map[string]string{}
	museums := map[string]map[string]string{}
	total, art := 0, 0
	e := csvRows(path, '|', func(r map[string]string) error {
		total++
		domain := r["domaine"]
		kind := ""
		for _, part := range strings.Split(domain, ";") {
			switch strings.TrimSpace(strings.ToLower(part)) {
			case "peinture":
				kind = "painting"
			case "dessin":
				if kind == "" {
					kind = "drawing"
				}
			case "estampe":
				if kind == "" {
					kind = "print"
				}
			}
		}
		if kind == "" {
			return nil
		}
		art++
		counts[kind]++
		authors[r["auteur"]]++
		for _, key := range []string{"millesime_de_creation", "periode_de_creation", "denomination", "manquant", "lieu_de_depot", "code_museofile"} {
			if fields[key] == nil {
				fields[key] = map[string]int{}
			}
			fields[key][r[key]]++
		}
		if len(samples) < 50 {
			samples = append(samples, r)
		}
		code := r["code_museofile"]
		if code != "" {
			museums[code] = map[string]string{"name": r["nom_officiel_musee"], "city": r["ville"], "localisation": r["localisation"]}
		}
		return nil
	})
	if e != nil {
		return e
	}
	type frequency struct {
		Value string
		Count int
	}
	top := func(m map[string]int, limit int) []frequency {
		v := []frequency{}
		for k, n := range m {
			v = append(v, frequency{k, n})
		}
		sort.Slice(v, func(i, j int) bool {
			if v[i].Count != v[j].Count {
				return v[i].Count > v[j].Count
			}
			return v[i].Value < v[j].Value
		})
		if len(v) > limit {
			v = v[:limit]
		}
		return v
	}
	stats := map[string]any{}
	for k, v := range fields {
		stats[k] = top(v, 100)
	}
	fmt.Printf("Joconde records=%d painting/drawing/print candidates=%d types=%v\n", total, art, counts)
	return save(filepath.Join(out, "audit.json"), map[string]any{"total_records": total, "art_candidates": art, "types": counts, "fields": stats, "authors": top(authors, 200), "museums": museums, "samples": samples})
}
