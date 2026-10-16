// Package guides searches an immutable projection of the editorial guide files.
// Refresh with: python3 ops/build-guide-search-index.py (from the repo root).
// Guide releases must validate --check and deploy the matching projection. No
// account or catalogue data enters this index; its digest binds paging cursors.
package guides

import (
	"crypto/sha256"
	_ "embed"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"net/url"
	"regexp"
	"slices"
	"sort"
	"strings"
	"unicode"
	"unicode/utf8"

	"golang.org/x/text/unicode/norm"
)

//go:embed index.json
var raw []byte

const PageSize = 24

type Entry struct {
	Slug      string `json:"slug"`
	Kind      string `json:"kind"`
	Href      string `json:"href"`
	Title     string `json:"title"`
	Label     string `json:"label"`
	Location  string `json:"location"`
	Subtitle  string `json:"subtitle"`
	Image     string `json:"image"`
	Count     int    `json:"count"`
	Languages int    `json:"languages"`
}
type document struct {
	Entry
	Search       string   `json:"search"`
	Institutions []string `json:"institutions"`
	name, text   string
}
type Index struct {
	entries []document
	version string
}
type Page struct {
	Items      []Entry        `json:"items"`
	Total      int            `json:"total"`
	Matched    int            `json:"matched"`
	Counts     map[string]int `json:"counts"`
	NextCursor string         `json:"next_cursor"`
}
type cursor struct {
	Index int    `json:"i"`
	Score int    `json:"s"`
	Scope string `json:"q"`
}

var Default = load(raw)
var institutionSlug = regexp.MustCompile(`^[a-z0-9]+(?:[-_][a-z0-9]+)*$`)

func load(raw []byte) *Index {
	var data struct {
		Entries []document `json:"entries"`
	}
	if err := json.Unmarshal(raw, &data); err != nil {
		panic(err)
	}
	for i := range data.Entries {
		data.Entries[i].name = fold(data.Entries[i].Label)
		data.Entries[i].text = fold(data.Entries[i].Search)
		data.Entries[i].Search = ""
	}
	sum := sha256.Sum256(raw)
	return &Index{entries: data.Entries, version: hex.EncodeToString(sum[:])}
}
func fold(value string) string {
	var b strings.Builder
	for _, r := range norm.NFKD.String(strings.ToLower(value)) {
		if unicode.Is(unicode.Mn, r) {
			continue
		}
		if unicode.IsLetter(r) || unicode.IsNumber(r) {
			b.WriteRune(r)
		} else {
			b.WriteByte(' ')
		}
	}
	return strings.Join(strings.Fields(b.String()), " ")
}
func (index *Index) Search(q url.Values) (Page, error) {
	page := Page{Items: []Entry{}, Counts: map[string]int{"all": 0, "artist": 0, "museum": 0, "using": 0}}
	for _, key := range []string{"q", "kind", "cursor", "institution"} {
		if len(q[key]) > 1 {
			return page, errors.New("Use one value for each guide filter.")
		}
	}
	query, kind := strings.TrimSpace(q.Get("q")), q.Get("kind")
	institution := q.Get("institution")
	if institution != "" && (len(institution) > 100 || !institutionSlug.MatchString(institution)) {
		return page, errors.New("Choose a valid museum.")
	}
	if utf8.RuneCountInString(query) > 200 {
		return page, errors.New("Keep searches under 200 characters.")
	}
	if kind != "" && kind != "artist" && kind != "museum" && kind != "using" {
		return page, errors.New("Choose artist guides, museum guides or using Artline.")
	}
	query = fold(query)
	scopeHash := sha256.Sum256([]byte(index.version + "\x00" + query + "\x00" + kind + "\x00" + institution))
	scope := hex.EncodeToString(scopeHash[:16])
	after := cursor{Index: -1}
	if value := q.Get("cursor"); value != "" {
		if len(value) > 512 {
			return page, errors.New("This page link is no longer valid. Show the first guides.")
		}
		raw, err := base64.RawURLEncoding.DecodeString(value)
		if err != nil || json.Unmarshal(raw, &after) != nil || after.Scope != scope || after.Index < 0 || after.Index >= len(index.entries) || after.Score < 0 || after.Score > 2 {
			return page, errors.New("This page link is no longer valid. Show the first guides.")
		}
	}
	type match struct{ position, score int }
	matches := []match{}
	for i, d := range index.entries {
		if institution != "" && !slices.Contains(d.Institutions, institution) {
			continue
		}
		page.Total++
		found := true
		for _, word := range strings.Fields(query) {
			if !strings.Contains(d.text, word) {
				found = false
				break
			}
		}
		if !found {
			continue
		}
		page.Counts[d.Kind]++
		page.Counts["all"]++
		if kind != "" && kind != d.Kind {
			continue
		}
		page.Matched++
		score := 0
		if query != "" {
			if d.name == query {
				score = 2
			} else if strings.Contains(d.name, query) {
				score = 1
			}
		}
		if after.Index >= 0 && (score > after.Score || score == after.Score && i <= after.Index) {
			continue
		}
		matches = append(matches, match{i, score})
	}
	sort.SliceStable(matches, func(i, j int) bool { return matches[i].score > matches[j].score })
	for _, item := range matches[:min(PageSize, len(matches))] {
		page.Items = append(page.Items, index.entries[item.position].Entry)
	}
	if len(matches) > PageSize {
		last := matches[PageSize-1]
		raw, _ := json.Marshal(cursor{last.position, last.score, scope})
		page.NextCursor = base64.RawURLEncoding.EncodeToString(raw)
	}
	return page, nil
}
