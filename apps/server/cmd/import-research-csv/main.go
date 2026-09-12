// import-research-csv prepares lossless research staging batches. A six-column
// export cannot establish object identity, work type, or a painter authority;
// this command deliberately does not manufacture catalogue entities.
package main

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/url"
	"os"
	"path/filepath"
	"reflect"
	"regexp"
	"sort"
	"strconv"
	"strings"

	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

var header = []string{"Painter", "artwork", "year", "museum", "country", "hasPicture"}
var unidentified = regexp.MustCompile(`(?i)unknown|anonym|an[oó]nim|inconnu|non registrato|not recorded|unident|ubekendt|tiedossa|sconosci|ignot[oa]|non ident|unbekannt|tuntematon|desconocido|desconhecido|onbekend|okänd|ukendt|неизвестн|άγνωστ|agnost`)
var attribution = regexp.MustCompile(`(?i)workshop|atelier|bottega|school|scuola|école|ecole|ma[iî]tre|master of|maestro|ambito|cerchia|seguace|follower|circle of|d'après|after |attribu|atribuid|tilskrevet|maniera|imitat|monogram|pseudo |copia|kopi|copyist|copy after|manner of|;|\?|\|`)
var collective = regexp.MustCompile(`(?i)\b(inc|ltd|company|factory|manufactur\w*|publisher|press|studio|workshops|brothers)\b`)
var genericCreator = regexp.MustCompile(`(?i)^(pittore\s+(lombard\w*|cremon\w*|bergam\w*|nordico|olandese|fiamming\w*|pavese|veneto|giottesco|pisano|toscano|romano|veneziano|emiliano|napoletano|siciliano)|various artists|several artists|multiple artists|cultura |culture |meister )|\bdynast(y|ie|ies)\b`)
var singleDate = regexp.MustCompile(`^(\d{3,4})$`)
var closedDate = regexp.MustCompile(`^(\d{3,4})\s*[-–]\s*(\d{3,4})$`)
var geography = regexp.MustCompile(`(?i)^(japan|china|india|france|italy|germany|england|spain|russia|iran|persia|tibet|nepal|korea|egypt|indonesia|mexico|peru|british|french|italian|japanese|chinese|indian|european|american|german|dutch|flemish|persian|tibetan|spanish|russian|byzantine)(\b.*)?$`)

type entry struct {
	Cells []string `json:"cells"`
	Rows  []int    `json:"csv_record_numbers"`
}
type chunk struct {
	File    string `json:"file"`
	SHA     string `json:"sha256"`
	Records int    `json:"records"`
}
type report struct {
	InputSHA    string         `json:"input_sha256"`
	BaselineSHA string         `json:"baseline_sha256"`
	SourceURL   string         `json:"source_url"`
	Counts      map[string]int `json:"counts"`
	Chunks      []chunk        `json:"chunks"`
	Limitations []string       `json:"limitations"`
}

func digest(b []byte) string    { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func key(cells []string) string { b, _ := json.Marshal(cells); return string(b) }
func readCSV(path string) ([]entry, string, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, "", err
	}
	if len(b) > 128<<20 {
		return nil, "", fmt.Errorf("CSV exceeds 128 MiB")
	}
	r := csv.NewReader(strings.NewReader(string(b)))
	r.FieldsPerRecord = len(header)
	h, err := r.Read()
	if err != nil || !reflect.DeepEqual(h, header) {
		return nil, "", fmt.Errorf("unexpected CSV header")
	}
	var rows []entry
	for n := 2; ; n++ {
		v, e := r.Read()
		if e == io.EOF {
			break
		}
		if e != nil {
			return nil, "", fmt.Errorf("record %d: %w", n, e)
		}
		for i, cell := range v {
			if len(cell) > 16000 || (i < 2 && strings.TrimSpace(cell) == "") {
				return nil, "", fmt.Errorf("invalid cell at record %d, column %d", n, i)
			}
		}
		if v[5] != "true" && v[5] != "false" {
			return nil, "", fmt.Errorf("invalid hasPicture at record %d", n)
		}
		rows = append(rows, entry{Cells: v, Rows: []int{n}})
		if len(rows) > 1000000 {
			return nil, "", fmt.Errorf("row budget exceeded")
		}
	}
	return rows, digest(b), nil
}

// Conservative name screening is not authority verification. Ambiguous labels
// remain in the review ledger, never silently rewritten into primary creators.
func creatorDecision(name string) string {
	if unidentified.MatchString(name) {
		return "excluded_unidentified_creator"
	}
	if attribution.MatchString(name) || collective.MatchString(name) || geography.MatchString(name) || genericCreator.MatchString(name) {
		return "deferred_creator_attribution"
	}
	if len(strings.Fields(name)) < 2 || len(name) > 500 {
		return "deferred_creator_identity"
	}
	return "named_candidate"
}
func dateDecision(s string) string {
	s = strings.TrimSpace(s)
	if m := singleDate.FindStringSubmatch(s); m != nil {
		y, _ := strconv.Atoi(m[1])
		if y > 1970 {
			return "excluded_after_1970"
		}
		return "staged_needs_source_identity_and_type"
	}
	if m := closedDate.FindStringSubmatch(s); m != nil {
		a, _ := strconv.Atoi(m[1])
		b, _ := strconv.Atoi(m[2])
		if a > b {
			return "staged_needs_date_review"
		}
		if a > 1970 {
			return "excluded_after_1970"
		}
		if b <= 1970 {
			return "staged_needs_source_identity_and_type"
		}
	}
	// Century wording, approximate and open dates stay verbatim for review.
	return "staged_needs_date_review"
}
func save(path string, v any) error {
	b, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return e
	}
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	_, e = f.Write(append(b, '\n'))
	c := f.Close()
	if e != nil {
		return e
	}
	return c
}
func prepare(input, baseline, sourceURL, out string) error {
	u, e := url.Parse(sourceURL)
	if e != nil || u.Scheme != "https" || u.Host != "storage.googleapis.com" || !strings.HasPrefix(u.Path, "/artline-508319-images/research/") || u.RawQuery != "" || u.Fragment != "" || u.User != nil {
		return fmt.Errorf("source must be the immutable private research object in the Artline bucket")
	}
	rows, sha, e := readCSV(input)
	if e != nil {
		return e
	}
	if !strings.Contains(u.Path, sha) {
		return fmt.Errorf("source object path must contain CSV SHA256")
	}
	old, baseSHA, e := readCSV(baseline)
	if e != nil {
		return e
	}
	counts := map[string]int{"input_rows": len(rows), "baseline_rows": len(old)}
	baselineCounts := map[string]int{}
	for _, r := range old {
		baselineCounts[key(r.Cells)]++
	}
	unique := map[string]*entry{}
	var ordered []*entry
	for _, r := range rows {
		k := key(r.Cells)
		if baselineCounts[k] > 0 {
			baselineCounts[k]--
			counts["existing_rows"]++
			continue
		}
		counts["added_rows"]++
		if v := unique[k]; v != nil {
			v.Rows = append(v.Rows, r.Rows[0])
			counts["repeated_added_rows"]++
			continue
		}
		v := r
		unique[k] = &v
		ordered = append(ordered, &v)
	}
	for _, n := range baselineCounts {
		if n != 0 {
			return fmt.Errorf("input does not contain complete baseline; refusing an unreliable delta")
		}
	}
	if e = os.Mkdir(out, 0700); e != nil {
		return e
	}
	var staged []ingest.ResearchRecord
	var deferred []map[string]any
	names := map[string]bool{}
	for _, r := range ordered {
		d := creatorDecision(r.Cells[0])
		if d == "named_candidate" {
			d = dateDecision(r.Cells[2])
		}
		counts[d] += len(r.Rows)
		if !strings.HasPrefix(d, "staged_") {
			deferred = append(deferred, map[string]any{"decision": d, "record": r})
			continue
		}
		names[r.Cells[0]] = true
		raw, _ := json.Marshal(map[string]any{"csv": r, "input_sha256": sha, "date_review": d, "identity": "CSV row fingerprint; not a museum object ID", "image_claim": "hasPicture is supplied metadata, not an available or rights-cleared image"})
		staged = append(staged, ingest.ResearchRecord{Source: "supplied-registry", Kind: "catalogue_object", RecordID: digest([]byte(key(r.Cells))), Name: r.Cells[0] + " — " + r.Cells[1], URL: sourceURL, Decision: d, Raw: raw})
	}
	counts["staged_distinct_csv_rows"] = len(staged)
	counts["staged_creator_labels"] = len(names)
	rep := report{InputSHA: sha, BaselineSHA: baseSHA, SourceURL: sourceURL, Counts: counts, Limitations: []string{"Staging only; no catalogue artists/artworks or images created, updated, or published.", "CSV repetitions may be distinct museum objects; multiplicity and original record numbers retained.", "Named candidate labels are not verified painter identities. Source IDs, URLs, work types and attribution evidence are required for promotion.", "CSV country is preserved in raw data as supplied museum country; no painter nationality inferred.", "Unparsed, approximate and crossing-cutoff dates require review; no creation years invented."}}
	for i := 0; i < len(staged); i += 5000 {
		end := min(i+5000, len(staged))
		file := fmt.Sprintf("chunk-%03d.json", i/5000+1)
		if e = save(filepath.Join(out, file), staged[i:end]); e != nil {
			return e
		}
		b, e := os.ReadFile(filepath.Join(out, file))
		if e != nil {
			return e
		}
		rep.Chunks = append(rep.Chunks, chunk{file, digest(b), end - i})
	}
	if e = save(filepath.Join(out, "deferred.json"), deferred); e != nil {
		return e
	}
	if e = save(filepath.Join(out, "review.json"), rep); e != nil {
		return e
	}
	keys := make([]string, 0, len(counts))
	for k := range counts {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		fmt.Printf("%s: %d\n", k, counts[k])
	}
	return nil
}
func main() {
	input := flag.String("file", "", "Expanded six-column CSV")
	baseline := flag.String("baseline", "", "Original exported CSV")
	source := flag.String("source-url", "", "Private GCS evidence object URL containing SHA256")
	out := flag.String("out", "", "New review directory (never overwritten)")
	flag.Parse()
	if e := prepare(*input, *baseline, *source, *out); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(1)
	}
}
