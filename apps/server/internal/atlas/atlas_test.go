package atlas

import (
	"errors"
	"fmt"
	"net/url"
	"strings"
	"testing"
)

func TestPresetsAndYearPartitions(t *testing.T) {
	presets := Presets()
	if len(presets) != 30 {
		t.Fatalf("want 30 historical lenses, got %d", len(presets))
	}
	seen := map[string]bool{}
	ranges := []Range{Bounds, {-500, -1}, {-1, 1}, {1, 2}, {1699, 1801}, {1910, 1930}, {1914, 1918}, {1999, 2000}}
	for _, p := range presets {
		if seen[p.ID] || p.ID == "" || p.Name == "" || p.Description == "" || len(p.Sources) == 0 {
			t.Fatalf("invalid preset: %+v", p)
		}
		seen[p.ID] = true
		if p.Context.Start > p.Period.Start || p.Context.End < p.Period.End {
			t.Fatalf("context excludes period: %s", p.ID)
		}
		for _, source := range p.Sources {
			u, err := url.Parse(source.URL)
			if err != nil || u.Scheme != "https" || u.Host == "" || source.Name == "" {
				t.Fatalf("missing source: %s", p.ID)
			}
		}
		ranges = append(ranges, p.Context, p.Period)
	}
	for _, r := range ranges {
		f := Filter{Range: r, Limit: 60}
		if err := f.Validate(); err != nil {
			t.Fatalf("range %+v: %v", r, err)
		}
		periods := Periods(r)
		years := map[int]int{}
		for _, p := range periods {
			if p.Start == 0 || p.End == 0 || p.Start > p.End || p.Start < r.Start || p.End > r.End {
				t.Fatalf("bad partition %+v in %+v", p, r)
			}
			for y := p.Start; y <= p.End; y++ {
				years[y]++
			}
		}
		for y := r.Start; y <= r.End; y++ {
			if y != 0 && years[y] != 1 {
				t.Fatalf("year %d occurs %d times in %+v", y, years[y], r)
			}
		}
		ticks := Ticks(r)
		if ticks[0].Year != r.Start || ticks[len(ticks)-1].Year != r.End {
			t.Fatal("lost range endpoints")
		}
		for i, tick := range ticks {
			if tick.Year == 0 || strings.Contains(tick.Label, " CE") || i > 0 && tick.Year <= ticks[i-1].Year {
				t.Fatalf("invalid tick: %+v", ticks)
			}
		}
	}
}
func TestCursorCannotCrossFiltersOrTypes(t *testing.T) {
	f := Filter{Range: Range{1910, 1930}, Limit: 60, Preview: true, Highlights: true, Types: []string{"event", "book"}}
	raw := encodeCursor(Item{ID: "book-one", StartYear: 1914}, f, "book")
	if _, err := decodeCursor(raw, f, "book"); err != nil {
		t.Fatal(err)
	}
	swapped := f
	swapped.Types = []string{"book", "event"}
	if _, err := decodeCursor(raw, swapped, "book"); err != nil {
		t.Fatal("type order changed scope")
	}
	for _, change := range []func(*Filter){func(v *Filter) { v.End = 1931 }, func(v *Filter) { v.Query = "war" }, func(v *Filter) { v.Preview = false }, func(v *Filter) { v.Highlights = false }, func(v *Filter) { v.Region = "eastern-europe" }, func(v *Filter) { v.Limit = 2 }, func(v *Filter) { v.Types = []string{"book"} }} {
		next := f
		change(&next)
		if _, err := decodeCursor(raw, next, "book"); !errors.Is(err, ErrFilter) {
			t.Fatal("cursor crossed filter")
		}
	}
	if _, err := decodeCursor(raw, f, "event"); !errors.Is(err, ErrFilter) {
		t.Fatal("cursor crossed type")
	}
}

func TestSelectionIDsAreBoundedAndScoped(t *testing.T) {
	f := Filter{Range: Bounds, Limit: 60, Selection: true, Picks: map[string][]string{"book": {"book-one", "book-two"}}}
	if err := f.Validate(); err != nil {
		t.Fatal(err)
	}
	raw := encodeCursor(Item{ID: "book-one", StartYear: 1900}, f, "book")
	f.Picks = map[string][]string{"book": {"book-two", "book-one"}}
	if _, err := decodeCursor(raw, f, "book"); err != nil {
		t.Fatal("selection order changed scope")
	}
	f.Picks = map[string][]string{"book": {"book-one"}}
	if _, err := decodeCursor(raw, f, "book"); err == nil {
		t.Fatal("cursor survived selection change")
	}
	for _, ids := range []map[string][]string{{"book": {"a", "a"}}, {"artwork": {"not-a-uuid"}}, {"book": {"bad'id"}}, {"person": {"a"}}} {
		f.Picks = ids
		if f.Validate() == nil {
			t.Fatalf("invalid picks accepted: %v", ids)
		}
	}
	f.Picks = map[string][]string{"book": {}}
	for i := 0; i < 61; i++ {
		f.Picks["book"] = append(f.Picks["book"], fmt.Sprint("book-", i))
	}
	if f.Validate() == nil {
		t.Fatal("unbounded picks")
	}
}
