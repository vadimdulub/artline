package events

import (
	"encoding/base64"
	"encoding/json"
	"testing"
)

func TestHistoricalFilterBoundsAndCursor(t *testing.T) {
	valid := Filter{Range: Bounds, Limit: 100}
	if err := valid.Validate(); err != nil {
		t.Fatal(err)
	}
	for _, r := range []Range{{0, 2000}, {-12001, 2000}, {1900, 2001}, {1900, 1900}, {2000, 1900}} {
		f := valid
		f.Range = r
		if f.Validate() == nil {
			t.Fatalf("accepted invalid range %+v", r)
		}
	}
	for _, raw := range []string{"broken", "e30", base64.RawURLEncoding.EncodeToString([]byte(`{"year":2001,"id":"event-q1"}`))} {
		f := valid
		f.After = raw
		if f.Validate() == nil {
			t.Fatal("invalid cursor accepted")
		}
	}
	y := -12000
	c, err := decodeCursor(encodeCursor(Event{ID: "event-q1", StartYear: &y}))
	if err != nil || c.Year != y {
		t.Fatalf("BCE cursor failed: %+v %v", c, err)
	}
	c, err = decodeCursor(encodeCursor(Event{ID: "event-q2"}))
	if err != nil || c.Year != 2147483647 {
		t.Fatalf("undated cursor failed: %+v %v", c, err)
	}
}
func TestDensityPeriodsCoverScopeWithoutYearZero(t *testing.T) {
	for _, r := range []Range{Bounds, {-200, -1}, {-10, 10}, {1700, 2000}, {1939, 1945}, {1999, 2000}} {
		p := densityPeriods(r)
		if p[0].Start != r.Start || p[len(p)-1].End != r.End {
			t.Fatalf("missing boundary %+v", r)
		}
		for i, v := range p {
			if v.Start == 0 || v.End == 0 || v.Start > v.End {
				t.Fatalf("invalid period %+v", v)
			}
			if i > 0 {
				next := p[i-1].End + 1
				if next == 0 {
					next = 1
				}
				if next != v.Start {
					t.Fatalf("gap or overlap %+v", p)
				}
			}
		}
	}
	p := densityPeriods(Bounds)
	if p[0].End != -1 || p[1].Start != 1 || p[1].End != 49 || p[2].Start != 50 || p[2].End != 99 {
		t.Fatal("changed shared atlas interval convention")
	}
	for _, tick := range metadata(Bounds).Ticks {
		if tick.Year == 0 || tick.Label == "2000 CE" {
			t.Fatal("invalid era label")
		}
	}
}
func validEvent() Event {
	y := 1789
	return Event{ID: "event-q6534", SourceID: "Q6534", SourceRevision: 1, SourceURL: "https://www.wikidata.org/wiki/Q6534", Title: "French Revolution", StartYear: &y, EndYear: &y, Years: "1789", Kind: "Event", Topics: []string{"Politics and society"}, Countries: []string{}, Regions: []string{}, DateBasis: "Recorded date", SelectionBasis: "Research evidence", Status: "review"}
}
func TestImportPreservesUnknownsAndRejectsInventedOrUnsafeRecords(t *testing.T) {
	unknown := validEvent()
	unknown.StartYear = nil
	unknown.EndYear = nil
	unknown.Years = "Date not established"
	if err := ValidateImport([]Event{unknown}, 1); err != nil {
		t.Fatal(err)
	}
	for name, change := range map[string]func(*Event){
		"publication": func(e *Event) { e.Status = "published" }, "future": func(e *Event) { y := 2001; e.EndYear = &y }, "zero": func(e *Event) { y := 0; e.StartYear = &y }, "partial": func(e *Event) { e.EndYear = nil },
		"source": func(e *Event) { e.SourceURL = "https://example.org/" }, "unsafe link": func(e *Event) { e.Sources = []Link{{"Bad", "javascript:alert(1)"}} }, "false identity": func(e *Event) { e.ID = "event-q1" }, "no editorial basis": func(e *Event) { e.Top100 = true },
	} {
		t.Run(name, func(t *testing.T) {
			e := validEvent()
			change(&e)
			if ValidateImport([]Event{e}, 1) == nil {
				t.Fatal("invalid import accepted")
			}
		})
	}
	e := validEvent()
	if ValidateImport([]Event{e, e}, 2) == nil {
		t.Fatal("duplicate source accepted")
	}
	if ValidateImport([]Event{e}, 10000) == nil {
		t.Fatal("partial batch accepted")
	}
	raw, _ := json.Marshal(unknown)
	var round Event
	if json.Unmarshal(raw, &round) != nil || round.StartYear != nil || round.EndYear != nil {
		t.Fatal("unknown chronology was invented")
	}
}
