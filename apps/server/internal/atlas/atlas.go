// Package atlas composes bounded native chronologies. Each type keeps its own
// dating, visibility and evidence rules; none is inferred from another type.
package atlas

import (
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"regexp"
	"slices"
	"strings"
)

var ErrFilter = errors.New("invalid atlas filter")
var ErrNotFound = errors.New("atlas record not found")
var uuidPattern = regexp.MustCompile(`^[a-fA-F0-9]{8}(-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$`)
var recordIDPattern = regexp.MustCompile(`^[a-zA-Z0-9_-]+$`)

type Range struct {
	Start int `json:"start"`
	End   int `json:"end"`
}

var Bounds = Range{-12000, 2000}

type Definition struct {
	Key       string `json:"key"`
	Name      string `json:"name"`
	Singular  string `json:"singular"`
	DateLabel string `json:"dateLabel"`
	Cutoff    int    `json:"cutoff"`
	Color     string `json:"color"`
}

var Definitions = []Definition{
	{"artwork", "Artworks", "Artwork", "Creation dates", 1970, "#c78168"},
	{"book", "Books", "Book", "Publication dates", 2000, "#c1a579"},
	{"event", "Events", "Event", "Event dates", 2000, "#91a99a"},
}

func ValidType(kind string) bool {
	for _, d := range Definitions {
		if d.Key == kind {
			return true
		}
	}
	return false
}

type Filter struct {
	Range
	Query                 string
	Types                 []string
	Highlights, Preview   bool
	Region                string
	Countries, Continents []string
	Limit                 int
	After                 map[string]string
	Selection             bool
	Picks                 map[string][]string
	Entities              map[string]url.Values
}
type Item struct {
	ID          string `json:"id"`
	Type        string `json:"type"`
	Title       string `json:"title"`
	Context     string `json:"context"`
	StartYear   int    `json:"startYear"`
	EndYear     int    `json:"endYear"`
	Years       string `json:"years"`
	Approximate bool   `json:"approximate"`
}
type Period struct {
	Start int `json:"start_year"`
	End   int `json:"end_year"`
	Count int `json:"count"`
}
type Lane struct {
	Definition
	Total      int      `json:"total"`
	Mode       string   `json:"mode"`
	Items      []Item   `json:"items"`
	Density    []Period `json:"density"`
	NextCursor string   `json:"nextCursor"`
}
type Tick struct {
	Year  int    `json:"year"`
	Label string `json:"label"`
}
type Response struct {
	Range  Range  `json:"range"`
	Bounds Range  `json:"bounds"`
	Lanes  []Lane `json:"lanes"`
	Total  int    `json:"total"`
	Ticks  []Tick `json:"ticks"`
}
type Region struct {
	Key  string `json:"slug"`
	Name string `json:"name"`
}

var Regions = []Region{{"northern-africa", "Northern Africa"}, {"western-africa", "Western Africa"}, {"eastern-africa", "Eastern Africa"}, {"middle-africa", "Middle Africa"}, {"southern-africa", "Southern Africa"}, {"northern-america", "Northern America"}, {"central-america", "Central America"}, {"caribbean", "Caribbean"}, {"south-america", "South America"}, {"central-asia", "Central Asia"}, {"eastern-asia", "Eastern Asia"}, {"southern-asia", "Southern Asia"}, {"south-eastern-asia", "South-eastern Asia"}, {"western-asia", "Western Asia"}, {"eastern-europe", "Eastern Europe"}, {"northern-europe", "Northern Europe"}, {"southern-europe", "Southern Europe"}, {"western-europe", "Western Europe"}, {"australia-and-new-zealand", "Australia and New Zealand"}}

func (f Filter) Validate() error {
	if err := f.validateGeography(); err != nil {
		return err
	}
	if err := f.validateEntities(); err != nil {
		return err
	}
	if f.Start < Bounds.Start || f.End > Bounds.End || f.Start >= f.End || f.Start == 0 || f.End == 0 || len(f.Query) > 200 || f.Limit < 1 || f.Limit > 60 || len(f.Types) > 3 || len(f.After) > 3 {
		return ErrFilter
	}
	totalPicks := 0
	for kind, ids := range f.Picks {
		if !f.Selection || !ValidType(kind) {
			return ErrFilter
		}
		seenIDs := map[string]bool{}
		for _, id := range ids {
			if len(id) < 1 || len(id) > 100 || seenIDs[id] {
				return ErrFilter
			}
			if kind == "artwork" && !uuidPattern.MatchString(id) {
				return ErrFilter
			}
			if !recordIDPattern.MatchString(id) {
				return ErrFilter
			}
			seenIDs[id] = true
			totalPicks++
		}
	}
	if totalPicks > 60 {
		return ErrFilter
	}
	seen := map[string]bool{}
	for _, t := range f.Types {
		if !ValidType(t) || seen[t] {
			return ErrFilter
		}
		seen[t] = true
	}
	if f.Region != "" && !slices.ContainsFunc(Regions, func(r Region) bool { return r.Key == f.Region }) {
		return ErrFilter
	}
	for kind, value := range f.After {
		if !ValidType(kind) || len(value) > 1024 {
			return ErrFilter
		}
		if _, err := decodeCursor(value, f, kind); err != nil {
			return err
		}
	}
	return nil
}
func YearLabel(year int) string {
	if year < 0 {
		return fmt.Sprintf("%d BCE", -year)
	}
	return fmt.Sprint(year)
}
func Ticks(r Range) []Tick {
	span := r.End - r.Start
	step := 1
	for _, n := range []int{1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, 2000} {
		step = n
		if span/n <= 12 {
			break
		}
	}
	out := []Tick{{r.Start, YearLabel(r.Start)}}
	if r.Start < 0 && r.End > 1700 {
		out = append(out, Tick{1, "1"}, Tick{1700, "1700"})
		for y := 1750; y < r.End; y += 50 {
			out = append(out, Tick{y, YearLabel(y)})
		}
	} else {
		for y := (r.Start / step) * step; y < r.End; y += step {
			if y > r.Start && y != 0 {
				out = append(out, Tick{y, YearLabel(y)})
			}
		}
	}
	return append(out, Tick{r.End, YearLabel(r.End)})
}
func Periods(r Range) []Period {
	// Match the atlas' dense modern intervals while retaining one BCE interval.
	out := []Period{}
	from := r.Start
	if from < 0 && r.End > 0 {
		out = append(out, Period{from, -1, 0})
		from = 1
	}
	if from < 1700 && r.End > 1800 {
		out = append(out, Period{from, 1699, 0})
		from = 1700
	}
	span := r.End - from
	step := 2
	for _, n := range []int{2, 5, 10, 25, 50, 100, 250, 500, 1000, 2000} {
		step = n
		if span/n <= 16 {
			break
		}
	}
	for a := from; a <= r.End; a += step {
		b := min(r.End, a+step-1)
		if b == r.End-1 {
			b = r.End
		}
		if b == 0 {
			b = -1
		}
		if a == 0 {
			a = 1
		}
		out = append(out, Period{a, b, 0})
		if b == r.End {
			break
		}
	}
	return out
}

type cursor struct {
	Year  int    `json:"y"`
	ID    string `json:"i"`
	Scope string `json:"s"`
}

func scope(f Filter, kind string) string {
	types := slices.Clone(f.Types)
	slices.Sort(types)
	picks := map[string][]string{}
	for kind, ids := range f.Picks {
		picks[kind] = slices.Clone(ids)
		slices.Sort(picks[kind])
	}
	raw, _ := json.Marshal([]any{f.Range, strings.TrimSpace(f.Query), types, f.Highlights, f.Preview, f.Region, f.Limit, kind, f.Selection, picks, f.Entities, f.Countries, f.Continents})
	return fmt.Sprintf("%x", sha256.Sum256(raw))[:24]
}
func decodeCursor(raw string, f Filter, kind string) (cursor, error) {
	c := cursor{Year: Bounds.Start - 1}
	if raw == "" {
		return c, nil
	}
	data, err := base64.RawURLEncoding.DecodeString(raw)
	if err != nil || json.Unmarshal(data, &c) != nil || c.Scope != scope(f, kind) || c.Year < Bounds.Start || c.Year > Bounds.End || len(c.ID) < 1 || len(c.ID) > 100 {
		return c, ErrFilter
	}
	return c, nil
}
func encodeCursor(item Item, f Filter, kind string) string {
	data, _ := json.Marshal(cursor{item.StartYear, item.ID, scope(f, kind)})
	return base64.RawURLEncoding.EncodeToString(data)
}
