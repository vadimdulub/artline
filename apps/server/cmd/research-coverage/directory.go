package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type binding map[string]struct {
	Value string `json:"value"`
}
type wdResponse struct {
	Results struct {
		Bindings []binding `json:"bindings"`
	} `json:"results"`
}

func assembleDirectory(root, out string) error {
	base := filepath.Join(root, "docs/research/us-europe-coverage")
	type wdMuseum struct {
		Name         string
		Countries    map[string]bool
		Rows         []binding
		Snapshots    []snapshot
		Closed, Part bool
	}
	museums := map[string]*wdMuseum{}
	coverage := []map[string]any{}
	for _, country := range countries {
		path := filepath.Join(base, "wikidata", "wikidata-"+country+".json")
		method := "detailed"
		if _, e := os.Stat(path); e != nil {
			path = filepath.Join(base, "wikidata-retry", "wikidata-"+country+".json")
			method = "basic (closure, parent and place fields not requested)"
		}
		if _, e := os.Stat(path); e != nil {
			coverage = append(coverage, map[string]any{"country": country, "status": "unavailable", "unique_candidates": nil})
			continue
		}
		if e := verify(path); e != nil {
			return e
		}
		b, e := os.ReadFile(path)
		if e != nil {
			return e
		}
		var response wdResponse
		if e = json.Unmarshal(b, &response); e != nil {
			return e
		}
		if len(response.Results.Bindings) >= 20001 {
			return fmt.Errorf("truncated country result %s", country)
		}
		sb, e := os.ReadFile(path + ".snapshot.json")
		if e != nil {
			return e
		}
		var snap snapshot
		if e = json.Unmarshal(sb, &snap); e != nil {
			return e
		}
		ids := map[string]bool{}
		for _, r := range response.Results.Bindings {
			q := strings.TrimPrefix(r["museum"].Value, "http://www.wikidata.org/entity/")
			if !strings.HasPrefix(q, "Q") || r["iso"].Value != country {
				return fmt.Errorf("invalid source binding %s", country)
			}
			ids[q] = true
			m := museums[q]
			if m == nil {
				m = &wdMuseum{Name: r["museumLabel"].Value, Countries: map[string]bool{}}
				museums[q] = m
			}
			m.Countries[country] = true
			m.Rows = append(m.Rows, r)
			if r["closed"].Value != "" {
				m.Closed = true
			}
			if r["parent"].Value != "" {
				m.Part = true
			}
			if len(m.Snapshots) == 0 || m.Snapshots[len(m.Snapshots)-1].SHA != snap.SHA {
				m.Snapshots = append(m.Snapshots, snap)
			}
		}
		if len(ids) >= 10001 {
			return fmt.Errorf("candidate subquery cap reached %s", country)
		}
		coverage = append(coverage, map[string]any{"country": country, "status": "query_retrieved_not_census", "query_method": method, "unique_candidates": len(ids), "source_rows": len(response.Results.Bindings), "snapshot_sha256": snap.SHA})
	}
	stage := []staged{}
	decisionCounts := map[string]int{}
	for q, m := range museums {
		codes := []string{}
		for code := range m.Countries {
			codes = append(codes, code)
		}
		sort.Strings(codes)
		country := codes[0]
		decision := "discovery_candidate"
		if m.Part {
			decision = "parent_or_branch_requires_review"
		}
		if m.Closed {
			decision = "historical_or_closed_candidate"
		}
		if strings.Contains(" RU TR CY AM AZ GE XK ", " "+country+" ") {
			decision = "boundary_geography_requires_review"
		}
		if len(codes) > 1 {
			country = "MULTI"
			decision = "country_identity_requires_review"
		}
		raw := map[string]any{"countries": codes, "bindings": m.Rows, "snapshots": m.Snapshots, "metadata_rights": "CC0-1.0", "verification": "Wikidata classification candidate only; website and current operation not independently verified; no holdings implied"}
		stage = append(stage, staged{"wikidata", "museum_candidate", q, country, m.Name, "https://www.wikidata.org/wiki/" + q, decision, raw})
		decisionCounts["wikidata/"+decision]++
	}
	france := filepath.Join(root, "content/imports/museofile-20260909/museofile.csv")
	if e := verify(france); e != nil {
		return e
	}
	franceCount, artCount := 0, 0
	e := csvRows(france, '|', func(r map[string]string) error {
		franceCount++
		if r["identifiant"] == "" || r["nom_officiel"] == "" {
			return fmt.Errorf("missing Museofile identity")
		}
		domain := strings.ToLower(r["domaine_thematique"] + " " + r["themes"])
		decision := "museum_subject_requires_review"
		if strings.Contains(domain, "beaux-arts") || strings.Contains(domain, "peinture") || strings.Contains(domain, "arts décoratifs") || strings.Contains(domain, "arts plastiques") {
			decision = "art_collection_candidate"
			artCount++
		}
		raw := map[string]any{"record": r, "metadata_rights": "Licence Ouverte 2.0", "dataset": "https://www.data.gouv.fr/datasets/musees-de-france-base-museofile", "retrieval_snapshot": "content/imports/museofile-20260909/museofile.csv.snapshot.json", "verification": "Official designation directory. Art-keyword classification is a candidate filter, not museum-only identity or proof of active operation. Includes overseas France; location review required for Europe scope."}
		// Overseas France remains explicitly reviewable, not silently counted in Europe.
		country := "FR"
		if strings.HasPrefix(r["code_postal"], "97") || strings.HasPrefix(r["code_postal"], "98") {
			decision = "overseas_geography_requires_review"
		}
		stage = append(stage, staged{"museofile", "museum_directory", r["identifiant"], country, r["nom_officiel"], "https://pop.culture.gouv.fr/notice/museo/" + r["identifiant"], decision, raw})
		decisionCounts["museofile/"+decision]++
		return nil
	})
	if e != nil {
		return e
	}
	registry := "/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv"
	h, _, e := hashFile(registry)
	if e != nil {
		return e
	}
	if h != "25f6fccb27a6a8f0271393b017c9f18d87a8a94a39ea87a5cb79f2e9496c6f30" {
		return fmt.Errorf("supplied registry changed; review required")
	}
	sourceCount := 0
	e = csvRows(registry, ',', func(r map[string]string) error {
		sourceCount++
		stage = append(stage, staged{"supplied-registry", "catalogue_source", r["source_id"], r["country_code"], r["institution_or_network"], r["official_website"], "source_claims_require_verification", r})
		return nil
	})
	if e != nil {
		return e
	}
	sort.Slice(stage, func(i, j int) bool {
		a, b := stage[i], stage[j]
		return a.Country+"/"+a.Name+"/"+a.Source+"/"+a.RecordID < b.Country+"/"+b.Name+"/"+b.Source+"/"+b.RecordID
	})
	summary := map[string]any{"wikidata_unique_candidates": len(museums), "museofile_directory_rows": franceCount, "museofile_art_keyword_candidates_including_overseas": artCount, "supplied_source_registry_rows": sourceCount, "stage_rows": len(stage), "decisions": decisionCounts, "country_coverage": coverage, "limitations": "NOT a complete museum census. Different directory rows can describe the same institution; no fuzzy cross-source merge. France includes mixed-subject and overseas museums. Boundary countries explicitly require venue geography review; zero query matches do not establish absence of museums."}
	if e = save(filepath.Join(out, "museum-directory.json"), stage); e != nil {
		return e
	}
	if e = save(filepath.Join(out, "coverage.json"), summary); e != nil {
		return e
	}
	fmt.Printf("Museum candidates=%d; Museofile=%d; source registry=%d; stage rows=%d\n", len(museums), franceCount, sourceCount, len(stage))
	return nil
}
