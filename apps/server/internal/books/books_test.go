package books

import (
	"strings"
	"testing"
)

func TestPeriodsMatchArtworksAndKeepBCECompact(t *testing.T) {
	p := densityPeriods(Bounds)
	if p[0].Start != -5000 || p[0].End != -1 || p[1].Start != 1 || p[1].End != 49 {
		t.Fatalf("opening intervals: %+v", p[:2])
	}
	for _, period := range p[2 : len(p)-1] {
		if period.End-period.Start+1 != 50 {
			t.Fatalf("wide interval: %+v", period)
		}
	}
	if p[len(p)-1].End != Bounds.End {
		t.Fatal("last year lost")
	}
	for _, r := range []Range{{1100, 1250}, {1100, 1500}, {-1, 20}, {-200, -100}} {
		p := densityPeriods(r)
		if p[0].Start != r.Start || p[len(p)-1].End != r.End {
			t.Fatalf("period coverage: %+v", p)
		}
		for i, period := range p {
			if period.Start == 0 || period.End == 0 {
				t.Fatal("year zero")
			}
			if i > 0 {
				next := p[i-1].End + 1
				if next == 0 {
					next = 1
				}
				if period.Start != next {
					t.Fatal("period gap")
				}
			}
		}
	}
	if p := densityPeriods(Range{1700, 2000}); p[0].End != 1724 {
		t.Fatal("expected 25-year intervals")
	}
	if p := densityPeriods(Range{1900, 2000}); p[0].End != 1909 {
		t.Fatal("expected 10-year intervals")
	}
}
func TestBookLabelsOmitCEAndZero(t *testing.T) {
	for _, r := range []Range{Bounds, {-1, 1}, {-800, -700}, {1900, 2000}} {
		for _, tick := range metadata(r).Ticks {
			if tick.Year == 0 || strings.Contains(tick.Label, " CE") {
				t.Fatalf("invalid label %+v", tick)
			}
		}
	}
	if YearLabel(-1) != "1 BCE" || YearLabel(1) != "1" {
		t.Fatal("year formatting")
	}
}
func TestCursorPreservesUnknownDatesAndTies(t *testing.T) {
	year := 1900
	for _, book := range []Book{{ID: "a", StartYear: &year}, {ID: "b", StartYear: nil}} {
		c, err := decodeCursor(encodeCursor(book))
		if err != nil || c.ID != book.ID {
			t.Fatal("cursor roundtrip")
		}
		if book.StartYear == nil && c.Year != 2147483647 {
			t.Fatal("unknown dates must sort last")
		}
	}
	for _, raw := range []string{"invalid", "e30", strings.Repeat("x", 600)} {
		if err := (Filter{Range: Bounds, After: raw, Limit: 100}).Validate(); err == nil {
			t.Fatal("malformed cursor accepted")
		}
	}
}
func TestImportPreservesReviewAndUnknownData(t *testing.T) {
	book := Book{ID: "wd-q1", SourceID: "Q1", Title: "A sourced title", Author: "Creator not recorded", SourceURL: "https://www.wikidata.org/wiki/Q1", Status: "review", SelectionBasis: "Sourced selection", DateBasis: "Unknown"}
	if err := ValidateImport([]Book{book}, 1); err != nil {
		t.Fatal(err)
	}
	if err := ValidateImport([]Book{book, book}, 2); err == nil {
		t.Fatal("duplicate identity accepted")
	}
	book.Status = "published"
	if err := ValidateImport([]Book{book}, 1); err == nil {
		t.Fatal("import must not publish")
	}
	book.Status = "review"
	later := 2001
	book.StartYear, book.EndYear = &later, &later
	if err := ValidateImport([]Book{book}, 1); err != nil {
		t.Fatalf("display cutoff invalidated a preserved review source: %v", err)
	}
	zero := 0
	book.StartYear = &zero
	book.EndYear = &zero
	if err := ValidateImport([]Book{book}, 1); err == nil {
		t.Fatal("invented zero date accepted")
	}
	book.StartYear = nil
	book.EndYear = &zero
	if err := ValidateImport([]Book{book}, 1); err == nil {
		t.Fatal("partial interval accepted")
	}
}
