// research-csv exports manually reviewed research facts and performs bounded,
// read-only candidate matching. It cannot import, publish, or download images.
package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
)

type row map[string]string
type dataset struct {
	CheckedOn    string         `json:"checked_on"`
	Painters     []row          `json:"painters"`
	Institutions map[string]row `json:"institutions"`
	Artworks     []row          `json:"artworks"`
	Deferred     []row          `json:"deferred"`
}

var painterHeaders = strings.Split("painter_key,name,original_name,alternate_names,birth_date_display,birth_year,death_date_display,death_year,cultural_affiliations,active_places,movements,authority_url,source_url,verification_status,notes", ",")
var artworkHeaders = strings.Split("artwork_key,painter_key,creator_display,attribution_qualifier,title_original,title_english,alternate_titles,creation_date_display,creation_year_start,creation_year_end,date_precision,work_type,medium,dimensions_display,institution_name,institution_city,institution_country_code,holding_type,accession_number,source_object_id,object_url,source_url,source_locator,description,image_page_url,image_url,image_rights_statement,image_rights_url,museum_highlight_source_url,verification_status,eligibility_status,existing_catalogue_match,checked_on,notes", ",")
var evidenceHeaders = strings.Split("evidence_key,entity_type,entity_key,field_name,source_url,publisher,source_locator,evidence_summary,accessed_on", ",")
var deferredHeaders = strings.Split("candidate_key,creator_display,title,institution_name,source_url,reason,missing_evidence,next_action", ",")

func validURL(s string) bool {
	u, e := url.Parse(s)
	return e == nil && u.Scheme == "https" && u.Hostname() != "" && u.User == nil
}

func prepare(d *dataset) error {
	if _, e := time.Parse("2006-01-02", d.CheckedOn); e != nil {
		return e
	}
	if len(d.Artworks) == 0 || len(d.Artworks) > 100 {
		return fmt.Errorf("batch must contain 1–100 artworks")
	}
	ps := map[string]row{}
	for _, p := range d.Painters {
		k := p["painter_key"]
		if k == "" || ps[k] != nil || p["name"] == "" || !validURL(p["source_url"]) {
			return fmt.Errorf("invalid painter %q", k)
		}
		ps[k] = p
	}
	keys, identities := map[string]bool{}, map[string]bool{}
	for _, a := range d.Artworks {
		k := a["artwork_key"]
		if k == "" || keys[k] || ps[a["painter_key"]] == nil {
			return fmt.Errorf("duplicate key or missing painter for %q", k)
		}
		keys[k] = true
		i, ok := d.Institutions[a["institution_key"]]
		if !ok {
			return fmt.Errorf("missing institution for %s", k)
		}
		for _, f := range []string{"institution_name", "institution_city", "institution_country_code"} {
			a[f] = i[f]
		}
		if a["source_url"] == "" {
			a["source_url"] = a["object_url"]
		}
		if !validURL(a["source_url"]) || a["title_original"] == "" || a["creator_display"] == "" {
			return fmt.Errorf("missing factual identity/source for %s", k)
		}
		if a["object_url"] != "" && !validURL(a["object_url"]) {
			return fmt.Errorf("invalid object URL")
		}
		identity := a["object_url"]
		if identity == "" {
			identity = a["source_url"] + "|" + a["source_locator"]
		}
		if identities[identity] {
			return fmt.Errorf("duplicate source object %s", k)
		}
		identities[identity] = true
		if a["date_precision"] == "exact" || a["date_precision"] == "range" {
			first, e1 := strconv.Atoi(a["creation_year_start"])
			last, e2 := strconv.Atoi(a["creation_year_end"])
			if e1 != nil || e2 != nil || first > last || last > 1970 || a["date_precision"] == "exact" && first != last {
				return fmt.Errorf("invalid dates for %s", k)
			}
		} else if a["creation_year_start"] != "" || a["creation_year_end"] != "" {
			return fmt.Errorf("this staging exporter requires uncertain numeric bounds to remain blank: %s", k)
		}
		a["checked_on"] = d.CheckedOn
		if a["holding_type"] == "" {
			a["holding_type"] = "documented_collection"
		}
		if a["verification_status"] != "verified_candidate" && a["verification_status"] != "needs_review" {
			return fmt.Errorf("missing explicit source verification for %s", k)
		}
	}
	return nil
}

func csvBytes(headers []string, data []row) ([]byte, error) {
	var b bytes.Buffer
	w := csv.NewWriter(&b)
	if e := w.Write(headers); e != nil {
		return nil, e
	}
	for _, r := range data {
		v := make([]string, len(headers))
		for i, h := range headers {
			v[i] = r[h]
		}
		if e := w.Write(v); e != nil {
			return nil, e
		}
	}
	w.Flush()
	if e := w.Error(); e != nil {
		return nil, e
	}
	// Independently parse every exported record, including embedded commas/quotes.
	reader := csv.NewReader(bytes.NewReader(b.Bytes()))
	reader.FieldsPerRecord = len(headers)
	n := 0
	for {
		_, e := reader.Read()
		if e == io.EOF {
			break
		}
		if e != nil {
			return nil, e
		}
		n++
	}
	if n != len(data)+1 {
		return nil, fmt.Errorf("CSV row count mismatch")
	}
	return b.Bytes(), nil
}

func exclusiveWrite(path string, b []byte) error {
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	_, e = f.Write(b)
	ce := f.Close()
	if e != nil {
		return e
	}
	return ce
}

func run(ctx context.Context, input, out, db string) error {
	b, e := os.ReadFile(input)
	if e != nil {
		return e
	}
	var d dataset
	decoder := json.NewDecoder(bytes.NewReader(b))
	decoder.DisallowUnknownFields()
	if e = decoder.Decode(&d); e != nil {
		return e
	}
	if e = prepare(&d); e != nil {
		return e
	}
	// Creating a fresh directory prevents replacement of prior research exports.
	if e = os.Mkdir(out, 0700); e != nil {
		return e
	}
	conn, e := pgx.Connect(ctx, db)
	if e != nil {
		return e
	}
	defer conn.Close(ctx)
	tx, e := conn.BeginTx(ctx, pgx.TxOptions{AccessMode: pgx.ReadOnly, IsoLevel: pgx.RepeatableRead})
	if e != nil {
		return e
	}
	defer tx.Rollback(ctx)
	if _, e = tx.Exec(ctx, "SET LOCAL statement_timeout = '15s'"); e != nil {
		return e
	}
	var totalWorks, totalArtists int
	if e = tx.QueryRow(ctx, "SELECT (SELECT count(*) FROM artworks), (SELECT count(*) FROM artists)").Scan(&totalWorks, &totalArtists); e != nil {
		return e
	}
	evidence, matches, painterMatches := []row{}, []row{}, []row{}
	counts := map[string]int{}
	for _, p := range d.Painters {
		names := append([]string{p["name"], p["original_name"]}, strings.Split(p["alternate_names"], "|")...)
		rs, err := tx.Query(ctx, `SELECT DISTINCT ar.id::text, ar.display_name FROM artists ar
 WHERE ar.display_name=ANY($1::text[]) OR ar.id IN (SELECT artist_id FROM artist_aliases WHERE alias=ANY($1::text[])) ORDER BY ar.id::text LIMIT 21`, names)
		if err != nil {
			return err
		}
		n := 0
		for rs.Next() {
			var id, name string
			if e = rs.Scan(&id, &name); e != nil {
				rs.Close()
				return e
			}
			n++
			painterMatches = append(painterMatches, row{"painter_key": p["painter_key"], "artist_id": id, "display_name": name, "decision": "name candidate only; authority reconciliation required"})
		}
		err = rs.Err()
		rs.Close()
		if err != nil {
			return err
		}
		if n == 0 {
			painterMatches = append(painterMatches, row{"painter_key": p["painter_key"], "decision": "no exact name/alias match; not proof of a new identity"})
		}
		if n > 20 {
			return fmt.Errorf("painter candidate ceiling")
		}
	}
	for _, a := range d.Artworks {
		u := a["object_url"]
		urls := []string{}
		if u != "" {
			urls = append(urls, u, strings.TrimSuffix(u, "/")+"/")
		}
		titles := []string{a["title_original"]}
		if a["title_english"] != "" {
			titles = append(titles, a["title_english"])
		}
		if a["alternate_titles"] != "" {
			titles = append(titles, strings.Split(a["alternate_titles"], "|")...)
		}
		// Full-catalogue candidates, not just records already linked to this painter.
		// Shared collection URLs are deliberately excluded from object-identity joins.
		rs, err := tx.Query(ctx, `WITH candidates AS (
 SELECT entity_id AS id, 'object_url' AS basis FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY($1::text[])
 UNION SELECT entity_id, 'object_citation' FROM citations WHERE entity_type='artwork' AND source_url=ANY($1::text[])
 UNION SELECT a.id, 'institution_accession' FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.name=$2 AND a.accession_number=$3 AND $3<>''
 UNION SELECT id, 'exact_title_candidate' FROM artworks WHERE title=ANY($4::text[])
 ) SELECT a.id::text,a.title,coalesce(i.name,''),coalesce(a.accession_number,''),string_agg(DISTINCT c.basis,'|' ORDER BY c.basis)
 FROM candidates c JOIN artworks a ON a.id=c.id LEFT JOIN institutions i ON i.id=a.current_institution_id
 GROUP BY a.id,i.name ORDER BY a.id LIMIT 1001`, urls, a["institution_name"], a["accession_number"], titles)
		if err != nil {
			return err
		}
		strong, n := false, 0
		for rs.Next() {
			var id, title, institution, accession, basis string
			if e = rs.Scan(&id, &title, &institution, &accession, &basis); e != nil {
				rs.Close()
				return e
			}
			n++
			if basis != "exact_title_candidate" {
				strong = true
			}
			matches = append(matches, row{"artwork_key": a["artwork_key"], "artwork_id": id, "title": title, "institution": institution, "accession": accession, "match_basis": basis, "decision": "candidate evidence only; no automatic merge or import"})
		}
		err = rs.Err()
		rs.Close()
		if err != nil {
			return err
		}
		if n > 1000 {
			return fmt.Errorf("match ceiling reached; narrow batch rather than truncate")
		}
		decision := "no_match_in_live_database_checks"
		if n > 0 {
			decision = "possible_match_needs_review"
		}
		if strong {
			decision = "source_or_accession_match_needs_review"
		}
		a["existing_catalogue_match"] = decision
		counts[decision]++
		for _, f := range []string{"creator_display", "title_original", "creation_date_display", "medium", "dimensions_display", "institution_name", "accession_number"} {
			if a[f] == "" {
				continue
			}
			evidence = append(evidence, row{"evidence_key": a["artwork_key"] + "-" + f, "entity_type": "artwork", "entity_key": a["artwork_key"], "field_name": f, "source_url": a["source_url"], "publisher": a["institution_name"], "source_locator": a["source_locator"], "evidence_summary": a[f], "accessed_on": d.CheckedOn})
		}
	}
	if e = tx.Commit(ctx); e != nil {
		return e
	}
	files := []struct {
		name    string
		headers []string
		rows    []row
	}{
		{"painters.csv", painterHeaders, d.Painters}, {"artworks.csv", artworkHeaders, d.Artworks}, {"evidence.csv", evidenceHeaders, evidence}, {"deferred.csv", deferredHeaders, d.Deferred},
		{"database-matches.csv", strings.Split("artwork_key,artwork_id,title,institution,accession,match_basis,decision", ","), matches},
		{"painter-matches.csv", strings.Split("painter_key,artist_id,display_name,decision", ","), painterMatches},
	}
	receipts := map[string]any{}
	for _, f := range files {
		data, err := csvBytes(f.headers, f.rows)
		if err != nil {
			return err
		}
		if err = exclusiveWrite(filepath.Join(out, f.name), data); err != nil {
			return err
		}
		sum := sha256.Sum256(data)
		receipts[f.name] = map[string]any{"rows": len(f.rows), "sha256": hex.EncodeToString(sum[:])}
	}
	sum := sha256.Sum256(b)
	report := map[string]any{"generated_at": time.Now().UTC(), "input_sha256": hex.EncodeToString(sum[:]), "database_artworks": totalWorks, "database_artists": totalArtists, "match_outcomes": counts, "files": receipts, "database_mutations": 0, "images_downloaded": 0, "limits": "Exact URL/accession/title/name candidate checks only. No fuzzy or all-language identity resolution; zero matches is not proof of uniqueness. Read-only transaction. Source research is manual, not performed by this exporter."}
	data, e := json.MarshalIndent(report, "", "  ")
	if e != nil {
		return e
	}
	if e = exclusiveWrite(filepath.Join(out, "verification.json"), append(data, '\n')); e != nil {
		return e
	}
	fmt.Println(string(data))
	return nil
}

func main() {
	input := flag.String("input", "", "reviewed JSON facts")
	out := flag.String("out", "", "new output directory; parent must exist")
	flag.Parse()
	if *input == "" || *out == "" || os.Getenv("DATABASE_URL") == "" {
		log.Fatal("-input, -out and DATABASE_URL are required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()
	if e := run(ctx, *input, *out, os.Getenv("DATABASE_URL")); e != nil {
		log.Fatal(e)
	}
}
