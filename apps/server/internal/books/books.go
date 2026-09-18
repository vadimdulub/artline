// Package books owns catalogue visibility, chronology and bounded reads.
package books

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
)

type Creator struct {
	ID             string  `json:"id"`
	Name           string  `json:"name"`
	Description    string  `json:"description"`
	Birth          *string `json:"birth"`
	Death          *string `json:"death"`
	SourceURL      string  `json:"sourceUrl"`
	SourceRevision *int64  `json:"sourceRevision"`
	Kind           string  `json:"kind"`
	Credit         string  `json:"credit"`
}
type Book struct {
	ID             string    `json:"id"`
	SourceID       string    `json:"sourceId"`
	Title          string    `json:"title"`
	Author         string    `json:"author"`
	Years          string    `json:"years"`
	Era            string    `json:"era"`
	Theme          string    `json:"theme"`
	Description    string    `json:"description"`
	CoverTone      string    `json:"coverTone"`
	CoverInk       string    `json:"coverInk"`
	CoverMark      string    `json:"coverMark"`
	Cover          *Cover    `json:"cover,omitempty"`
	StartYear      *int      `json:"startYear"`
	EndYear        *int      `json:"endYear"`
	Approximate    bool      `json:"approximate"`
	Creators       []Creator `json:"creators"`
	SourceURL      string    `json:"sourceUrl"`
	SourceRevision *int64    `json:"sourceRevision"`
	SelectionBasis string    `json:"selectionBasis"`
	DateBasis      string    `json:"dateBasis"`
	Status         string    `json:"status"`
}
type Range struct {
	Start int `json:"start"`
	End   int `json:"end"`
}
type Period struct {
	Range
	Label string `json:"label"`
}
type DensityPeriod struct {
	Start int `json:"start_year"`
	End   int `json:"end_year"`
	Count int `json:"count"`
}
type Tick struct {
	Year  int    `json:"year"`
	Label string `json:"label"`
}
type Filter struct {
	Range
	Query, After                  string
	Authors                       []string
	Languages, Countries, Regions []string
	Women, Top100                 bool
	Limit                         int
	Preview                       bool
	View                          string
}
type FilterOption struct {
	Slug string `json:"slug"`
	Name string `json:"name"`
}
type SuggestedFilter struct {
	Key   string `json:"key"`
	Value string `json:"value"`
	Name  string `json:"name"`
	Count int    `json:"count"`
}
type Facets struct {
	Languages []FilterOption `json:"languages"`
	Countries []FilterOption `json:"countries"`
	Regions   []FilterOption `json:"regions"`
}
type Response struct {
	Items            []Book            `json:"items"`
	Total            int               `json:"total"`
	SelectionTotal   int               `json:"selectionTotal"`
	UndatedTotal     int               `json:"undatedTotal"`
	HasMore          bool              `json:"hasMore"`
	NextCursor       string            `json:"nextCursor"`
	Range            Range             `json:"range"`
	Bounds           Range             `json:"bounds"`
	Periods          []Period          `json:"periods"`
	Ticks            []Tick            `json:"ticks"`
	Mode             string            `json:"mode"`
	Density          []DensityPeriod   `json:"density"`
	SuggestedFilters []SuggestedFilter `json:"suggested_filters"`
	Authors          []TimelineAuthor  `json:"authors,omitempty"`
	View             string            `json:"view,omitempty"`
}
type AuthorOptions struct {
	Items   []string `json:"items"`
	HasMore bool     `json:"hasMore"`
}

var Bounds = Range{-5000, 2000}
var ErrNotFound = errors.New("book not found")
var ErrUnavailable = errors.New("book catalogue unavailable")

func (f Filter) Validate() error {
	if f.View != "" && f.View != "books" && f.View != "authors" {
		return fmt.Errorf("choose view=books or view=authors")
	}
	if f.Start < Bounds.Start || f.End > Bounds.End || f.Start >= f.End || f.Start == 0 || f.End == 0 {
		return fmt.Errorf("choose an ordered range from 5000 BCE to 2000; there is no year zero")
	}
	if len(f.Query) > 200 || len(f.After) > 512 {
		return fmt.Errorf("book search or cursor is too long")
	}
	if f.Limit < 1 || f.Limit > 100 {
		return fmt.Errorf("limit must be from 1 to 100")
	}
	for _, choices := range [][]string{f.Authors, f.Languages, f.Countries, f.Regions} {
		if len(choices) > 32 {
			return fmt.Errorf("choose up to 32 values per filter")
		}
		for _, choice := range choices {
			if len(choice) > 250 || strings.TrimSpace(choice) == "" {
				return fmt.Errorf("invalid book filter value")
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
	c := cursor{Year: -5001}
	if raw == "" {
		return c, nil
	}
	b, err := base64.RawURLEncoding.DecodeString(raw)
	if err != nil || json.Unmarshal(b, &c) != nil || c.ID == "" || len(c.ID) > 100 || c.Year == 0 || c.Year < Bounds.Start || (c.Year > Bounds.End && c.Year != 2147483647) {
		return c, fmt.Errorf("invalid book cursor")
	}
	return c, nil
}
func encodeCursor(book Book) string {
	year := 2147483647
	if book.StartYear != nil {
		year = *book.StartYear
	}
	b, _ := json.Marshal(cursor{year, book.ID})
	return base64.RawURLEncoding.EncodeToString(b)
}
func YearLabel(year int) string {
	if year < 0 {
		return fmt.Sprintf("%d BCE", -year)
	}
	return fmt.Sprint(year)
}

// Same density intervals as ArtWorks: 50, 25, then 10 years. In a mixed
// overview all BCE years occupy one explicitly labelled opening interval.
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
	presets := []Period{{Bounds, "Full range"}, {Range{Bounds.Start, -1}, "BCE"}, {Range{1, Bounds.End}, "1–2000"}}
	for _, span := range []int{100, 50, 25} {
		start := max(Bounds.Start, min(Bounds.End-span, (r.Start+r.End-span)/2))
		end := start + span
		if start == 0 {
			start = 1
		}
		if end == 0 {
			end = 1
		}
		label := fmt.Sprintf("%d years", span)
		if span == 100 {
			label = "Century"
		}
		presets = append(presets, Period{Range{start, end}, label})
	}
	result := Response{Items: []Book{}, Range: r, Bounds: Bounds, Periods: presets, Density: []DensityPeriod{}, Ticks: []Tick{}, Mode: "individual"}
	span := r.End - r.Start
	tickStart := r.Start
	if r.Start < 0 && r.End > 500 {
		span = r.End
		tickStart = 1
		result.Ticks = append(result.Ticks, Tick{r.Start / 2, "BCE"})
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
	for year := tickStart; year <= r.End; year++ {
		if year != 0 && year%step == 0 {
			result.Ticks = append(result.Ticks, Tick{year, YearLabel(year)})
		}
	}
	return result
}
