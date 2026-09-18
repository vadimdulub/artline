package events

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
)

type Range struct {
	Start int `json:"start"`
	End   int `json:"end"`
}
type Link struct {
	Name string `json:"name"`
	URL  string `json:"url"`
}
type Event struct {
	ID                string             `json:"id"`
	SourceID          string             `json:"sourceId"`
	SourceRevision    int64              `json:"sourceRevision"`
	SourceURL         string             `json:"sourceUrl"`
	Title             string             `json:"title"`
	Description       string             `json:"description"`
	DescriptionSource *DescriptionSource `json:"descriptionSource,omitempty"`
	Significance      string             `json:"significance"`
	SearchTerms       string             `json:"searchTerms"`
	Years             string             `json:"years"`
	StartYear         *int               `json:"startYear"`
	EndYear           *int               `json:"endYear"`
	Approximate       bool               `json:"approximate"`
	DateBasis         string             `json:"dateBasis"`
	Kind              string             `json:"kind"`
	Topics            []string           `json:"topics"`
	Countries         []string           `json:"countries"`
	Regions           []string           `json:"regions"`
	GeographyBasis    string             `json:"geographyBasis"`
	Locations         []Link             `json:"locations"`
	People            []Link             `json:"people"`
	Sources           []Link             `json:"sources"`
	Connections       []string           `json:"connections"`
	Top100            bool               `json:"top100"`
	SelectionBasis    string             `json:"selectionBasis"`
	Status            string             `json:"status"`
}
type Filter struct {
	Range
	Query, After                      string
	Topics, Countries, Regions, Kinds []string
	Top100, Preview                   bool
	Limit                             int
}
type Tick struct {
	Year  int    `json:"year"`
	Label string `json:"label"`
}
type DensityPeriod struct {
	Start int `json:"start_year"`
	End   int `json:"end_year"`
	Count int `json:"count"`
}
type Option struct {
	Slug string `json:"slug"`
	Name string `json:"name"`
}
type Facets struct {
	Topics    []Option `json:"topics"`
	Countries []Option `json:"countries"`
	Regions   []Option `json:"regions"`
	Kinds     []Option `json:"kinds"`
}
type Suggestion struct {
	Key   string `json:"key"`
	Value string `json:"value"`
	Name  string `json:"name"`
	Count int    `json:"count"`
}
type Response struct {
	Items          []Event         `json:"items"`
	Total          int             `json:"total"`
	SelectionTotal int             `json:"selectionTotal"`
	UndatedTotal   int             `json:"undatedTotal"`
	HasMore        bool            `json:"hasMore"`
	NextCursor     string          `json:"nextCursor"`
	Range          Range           `json:"range"`
	Bounds         Range           `json:"bounds"`
	Ticks          []Tick          `json:"ticks"`
	Mode           string          `json:"mode"`
	Density        []DensityPeriod `json:"density"`
	Suggestions    []Suggestion    `json:"suggested_filters"`
}

var Bounds = Range{-12000, 2000}
var ErrNotFound = errors.New("event not found")
var ErrUnavailable = errors.New("events unavailable")

func (f Filter) Validate() error {
	if f.Start < Bounds.Start || f.End > Bounds.End || f.Start >= f.End || f.Start == 0 || f.End == 0 {
		return fmt.Errorf("choose an ordered range from 12000 BCE to 2000; there is no year zero")
	}
	if len(f.Query) > 200 || len(f.After) > 512 {
		return fmt.Errorf("event search or cursor is too long")
	}
	if f.Limit < 1 || f.Limit > 100 {
		return fmt.Errorf("limit must be from 1 to 100")
	}
	for _, choices := range [][]string{f.Topics, f.Countries, f.Regions, f.Kinds} {
		if len(choices) > 32 {
			return fmt.Errorf("choose up to 32 values per filter")
		}
		for _, choice := range choices {
			if len(choice) > 250 || strings.TrimSpace(choice) == "" {
				return fmt.Errorf("invalid event filter value")
			}
		}
	}
	_, err := decodeCursor(f.After)
	return err
}

type cursor struct {
	Year int    `json:"year"`
	ID   string `json:"id"`
}

func decodeCursor(raw string) (cursor, error) {
	c := cursor{Year: Bounds.Start - 1}
	if raw == "" {
		return c, nil
	}
	b, err := base64.RawURLEncoding.DecodeString(raw)
	if err != nil || json.Unmarshal(b, &c) != nil || c.ID == "" || len(c.ID) > 100 || c.Year == 0 || c.Year < Bounds.Start || (c.Year > Bounds.End && c.Year != 2147483647) {
		return c, fmt.Errorf("invalid event cursor")
	}
	return c, nil
}
func encodeCursor(e Event) string {
	year := 2147483647
	if e.StartYear != nil {
		year = *e.StartYear
	}
	b, _ := json.Marshal(cursor{year, e.ID})
	return base64.RawURLEncoding.EncodeToString(b)
}
func YearLabel(y int) string {
	if y < 0 {
		return fmt.Sprintf("%d BCE", -y)
	}
	return fmt.Sprint(y)
}

// Match ArtWorks and Books: 50-, 25-, then 10-year density intervals.
func densityPeriods(r Range) []DensityPeriod {
	width := 10
	if r.End-r.Start > 200 {
		width = 25
	}
	if r.End-r.Start > 500 {
		width = 50
	}
	periods := []DensityPeriod{}
	start := r.Start
	if start < 0 && r.End > 0 {
		periods = append(periods, DensityPeriod{start, -1, 0})
		start = 1
	}
	for start <= r.End {
		end := start + width - 1
		if start == 1 {
			end = width - 1
		}
		if end >= r.End-1 {
			end = r.End
		}
		if end == 0 {
			end = -1
		}
		periods = append(periods, DensityPeriod{start, end, 0})
		start = end + 1
		if start == 0 {
			start = 1
		}
	}
	return periods
}
func metadata(r Range) Response {
	out := Response{Items: []Event{}, Range: r, Bounds: Bounds, Ticks: []Tick{}, Mode: "individual", Density: []DensityPeriod{}, Suggestions: []Suggestion{}}
	span, start := r.End-r.Start, r.Start
	if r.Start < 0 && r.End > 500 {
		span = r.End
		start = 1
		out.Ticks = append(out.Ticks, Tick{r.Start / 2, "BCE"})
	}
	step := 1
	switch {
	case span > 500:
		step = 100
	case span > 200:
		step = 50
	case span > 80:
		step = 25
	case span > 35:
		step = 10
	case span > 10:
		step = 5
	}
	for y := start; y <= r.End; y++ {
		if y != 0 && y%step == 0 {
			out.Ticks = append(out.Ticks, Tick{y, YearLabel(y)})
		}
	}
	return out
}
