// registry-audit only reads a local CSV and emits a structural audit. It never
// connects to a database, fetches a URL, or enables a source.
package main

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"regexp"
	"strings"
	"time"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "Usage: registry-audit path/to/registry.csv")
		os.Exit(2)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	reader := csv.NewReader(strings.NewReader(string(data)))
	reader.FieldsPerRecord = 28
	rows, err := reader.ReadAll()
	if err != nil {
		panic(err)
	}
	if len(rows) < 2 {
		panic("registry is empty")
	}
	columns := map[string]int{}
	for i, name := range rows[0] {
		columns[name] = i
	}
	for _, key := range []string{"source_id", "source_kind", "priority_tier", "region", "automated_image_download", "verification_status", "last_verified", "api_docs_url", "sample_artwork_url"} {
		if _, ok := columns[key]; !ok {
			panic("missing column: " + key)
		}
	}
	counts := map[string]map[string]int{}
	for _, key := range []string{"source_kind", "priority_tier", "region", "automated_image_download", "verification_status"} {
		counts[key] = map[string]int{}
	}
	issues, missingSamples := []string{}, []string{}
	seen := map[string]bool{}
	sourceID := regexp.MustCompile(`^[a-z0-9]+(?:_[a-z0-9]+)*$`)
	sensitiveParams := map[string]bool{"key": true, "api_key": true, "apikey": true, "access_token": true, "token": true, "secret": true, "client_secret": true, "password": true}
	for n, row := range rows[1:] {
		id := row[columns["source_id"]]
		if id == "" || seen[id] {
			issues = append(issues, fmt.Sprintf("row %d: empty/duplicate source_id", n+2))
		}
		seen[id] = true
		if !sourceID.MatchString(id) {
			issues = append(issues, id+": invalid source identifier")
		}
		if !strings.Contains("ABCD", row[columns["priority_tier"]]) || len(row[columns["priority_tier"]]) != 1 {
			issues = append(issues, id+": invalid priority tier")
		}
		if _, err := time.Parse("2006-01-02", row[columns["last_verified"]]); err != nil {
			issues = append(issues, id+": invalid verification date")
		}
		for key := range counts {
			counts[key][row[columns[key]]]++
		}
		if row[columns["sample_artwork_url"]] == "" {
			missingSamples = append(missingSamples, id)
		}
		if row[columns["priority_tier"]] == "A" && row[columns["api_docs_url"]] == "" {
			issues = append(issues, id+": tier A has no API documentation URL")
		}
		for i, value := range row {
			trimmed := strings.TrimSpace(value)
			if len(trimmed) > 0 && strings.ContainsAny(trimmed[:1], "=+-@") {
				issues = append(issues, id+": formula-leading field "+rows[0][i])
			}
			if strings.HasPrefix(value, "http") {
				u, err := url.Parse(value)
				if err != nil || u.Scheme != "https" || u.Hostname() == "" || u.User != nil {
					issues = append(issues, id+": unsafe URL in "+rows[0][i])
					continue
				}
				for key := range u.Query() {
					if sensitiveParams[strings.ToLower(key)] {
						issues = append(issues, id+": review credential-like URL parameter "+key)
					}
				}
			}
		}
	}
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(map[string]any{"rows": len(rows) - 1, "columns": len(rows[0]), "unique_sources": len(seen), "sha256": fmt.Sprintf("%x", sha256.Sum256(data)), "counts": counts, "missing_sample_links": missingSamples, "issues_to_review": issues, "scope": "Structural review only; endpoint health and rights claims are not verified."}); err != nil {
		panic(err)
	}
}
