package ingest

import (
	"bytes"
	"compress/bzip2"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"sort"
	"strconv"
	"strings"
	"unicode"

	"golang.org/x/text/unicode/norm"
)

const PantheonURL = "https://storage.googleapis.com/pantheon-public-data/person_2025_update.csv.bz2"
const PantheonAttribution = "Pantheon 2025 by Datawheel, CC BY-SA 4.0; Yu et al. (2016), Scientific Data 2:150075, doi:10.1038/sdata.2015.75. Adapted selection ranked by HPI; popularity is not artistic quality."

type Painter struct {
	ID         string            `json:"artist_id,omitempty"`
	QID        string            `json:"wikidata_id"`
	Name       string            `json:"name"`
	SourceSlug string            `json:"source_slug"`
	Birth      int               `json:"birth_year"`
	Death      *int              `json:"death_year"`
	Alive      bool              `json:"alive_in_2025_dataset"`
	Country    string            `json:"birth_country"`
	Rank       int               `json:"rank"`
	Score      float64           `json:"hpi"`
	Raw        map[string]string `json:"source_record"`
}

func integer(s string) *int {
	v, e := strconv.ParseFloat(s, 64)
	if e != nil || math.IsNaN(v) || math.IsInf(v, 0) || v != math.Trunc(v) || v < -5000 || v > 2100 {
		return nil
	}
	n := int(v)
	return &n
}

func ReadCohort(compressed []byte, n int) ([]Painter, error) {
	if n < 1 || n > 1000 {
		return nil, fmt.Errorf("painter limit must be 1–1000")
	}
	r := csv.NewReader(io.LimitReader(bzip2.NewReader(bytes.NewReader(compressed)), 128<<20))
	header, err := r.Read()
	if err != nil {
		return nil, err
	}
	seen := map[string]bool{}
	var out []Painter
	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}
		m := map[string]string{}
		for i, h := range header {
			m[h] = row[i]
		}
		// Leonardo is classified INVENTOR in Pantheon. His existing sourced painter
		// profile is an explicit exception to its single-primary-occupation taxonomy.
		if m["occupation"] != "PAINTER" && m["wd_id"] != "Q762" {
			continue
		}
		birth, death := integer(m["birthyear"]), integer(m["deathyear"])
		if birth == nil || *birth >= 1970 || (death != nil && (*death < 1100 || *death < *birth)) || (death == nil && m["alive"] != "TRUE") {
			continue
		}
		qid := m["wd_id"]
		if len(qid) < 2 || qid[0] != 'Q' || seen[qid] {
			continue
		}
		if _, err = strconv.Atoi(qid[1:]); err != nil {
			continue
		}
		score, err := strconv.ParseFloat(m["hpi"], 64)
		if err != nil || math.IsNaN(score) || math.IsInf(score, 0) {
			continue
		}
		seen[qid] = true
		out = append(out, Painter{QID: qid, Name: m["name"], SourceSlug: m["slug"], Birth: *birth, Death: death, Alive: m["alive"] == "TRUE", Country: m["bplace_country"], Score: score, Raw: m})
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Score == out[j].Score {
			return out[i].QID < out[j].QID
		}
		return out[i].Score > out[j].Score
	})
	if len(out) < n {
		return nil, fmt.Errorf("only %d eligible painter candidates; need %d", len(out), n)
	}
	out = out[:n]
	for i := range out {
		out[i].Rank = i + 1
	}
	return out, nil
}

func normalize(s string) string {
	var b strings.Builder
	for _, r := range norm.NFD.String(strings.ToLower(s)) {
		if unicode.Is(unicode.Mn, r) {
			continue
		}
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			b.WriteRune(r)
		} else {
			b.WriteByte(' ')
		}
	}
	return strings.Join(strings.Fields(b.String()), " ")
}
func slug(s string) string {
	s = strings.NewReplacer("ø", "o", "ł", "l", "đ", "d", "æ", "ae", "œ", "oe", "ß", "ss").Replace(normalize(s))
	var b strings.Builder
	for _, r := range s {
		if r >= 'a' && r <= 'z' || r >= '0' && r <= '9' {
			b.WriteRune(r)
		} else {
			b.WriteByte(' ')
		}
	}
	result := strings.Join(strings.Fields(b.String()), "-")
	if result == "" {
		return "record"
	}
	return result
}
func rawJSON(v any) []byte { b, _ := json.Marshal(v); return b }

// Source identities win. Names alone are not an identity merge criterion.
func MatchPainter(w Work, painters []Painter) *Painter {
	if w.ArtistQID != "" {
		for i := range painters {
			if painters[i].QID == w.ArtistQID {
				return &painters[i]
			}
		}
		return nil
	}
	if w.ArtistBirth == nil {
		return nil
	}
	var matched *Painter
	for i := range painters {
		p := &painters[i]
		if normalize(w.ArtistName) == normalize(p.Name) && *w.ArtistBirth == p.Birth {
			if w.ArtistDeath != nil && p.Death != nil && *w.ArtistDeath != *p.Death {
				continue
			}
			if matched != nil {
				return nil
			}
			matched = p
		}
	}
	return matched
}
