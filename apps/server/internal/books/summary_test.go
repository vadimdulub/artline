package books

import (
	"encoding/json"
	"testing"
)

func TestSummaryPreservesTimelineFieldsWithoutDetailPayload(t *testing.T) {
	year := 1890
	full := Book{ID: "work", SourceID: "source", Title: "Title", Author: "Creator", Years: "c. 1890", StartYear: &year, EndYear: &year, Approximate: true, Description: "Full detail", Overview: &Overview{Paragraphs: []string{"Full source paragraph"}}, Creators: []Creator{{ID: "creator", Description: "Biography"}}, Cover: &Cover{}}
	bytes, err := json.Marshal(full)
	if err != nil {
		t.Fatal(err)
	}
	var detail map[string]any
	if err = json.Unmarshal(bytes, &detail); err != nil {
		t.Fatal(err)
	}
	full.Summary = true
	bytes, err = json.Marshal(full)
	if err != nil {
		t.Fatal(err)
	}
	var summary map[string]any
	if err = json.Unmarshal(bytes, &summary); err != nil {
		t.Fatal(err)
	}
	for _, key := range []string{"id", "title", "author", "years", "startYear", "endYear", "approximate"} {
		if summary[key] != detail[key] {
			t.Fatalf("summary changed %s", key)
		}
	}
	for _, key := range []string{"overview", "description", "creators", "sourceId"} {
		if _, ok := summary[key]; ok {
			t.Fatalf("summary contains %s", key)
		}
	}
	if summary["summary"] != true || summary["cover"] == nil || detail["description"] != "Full detail" {
		t.Fatal("summary marker, cover or detail missing")
	}
}
