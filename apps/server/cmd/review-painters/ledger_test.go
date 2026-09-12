package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestReviewDoesNotInferCompletion(t *testing.T) {
	d := Decision{Kind: "artwork", ID: "work", Fingerprint: "before", Status: "done", Round: 1, Note: "Object and image terms checked", ImageOutcome: "unavailable", CheckedAt: time.Now(), Sources: []string{"https://example.org/object"}}
	ds := Decisions{decisionKey(d.Kind, d.ID, d.Round): d}
	if state(ds, "artwork", "work", "after", 1) != "stale — changed record" {
		t.Fatal("changed record stayed done")
	}
	if state(ds, "artwork", "work", "before", 2) != "pending" {
		t.Fatal("prior round completed another round")
	}
	if state(nil, "artwork", "work", "before", 1) != "pending" {
		t.Fatal("missing evidence marked done")
	}
	page := renderWorks("Works", []Work{{ID: "work", Title: "Test", Fingerprint: "before", ImageCheck: "missing"}}, ds)
	if !strings.Contains(page, "[x] Research 01: done") || !strings.Contains(page, "[ ] Image file: missing") || !strings.Contains(page, "[ ] Research 02: pending") {
		t.Fatal(page)
	}
}
func TestDecisionValidation(t *testing.T) {
	d := Decision{Kind: "artwork", ID: "work", Fingerprint: "fp", Status: "done", Round: 1, Note: "Reviewed", CheckedAt: time.Now(), Sources: []string{"https://example.org/object"}}
	path := filepath.Join(t.TempDir(), "decisions.json")
	if e := save(path, encode([]Decision{d})); e != nil {
		t.Fatal(e)
	}
	if _, e := readDecisions(path); e == nil {
		t.Fatal("done without image decision")
	}
	d.ImageOutcome = "unavailable"
	path = filepath.Join(t.TempDir(), "valid.json")
	save(path, encode([]Decision{d}))
	if _, e := readDecisions(path); e != nil {
		t.Fatal(e)
	}
	path = filepath.Join(t.TempDir(), "dupe.json")
	save(path, encode([]Decision{d, d}))
	if _, e := readDecisions(path); e == nil {
		t.Fatal("duplicate accepted")
	}
}
func TestImageChecksAndSafeMarkdown(t *testing.T) {
	root := t.TempDir()
	dir := filepath.Join(root, "apps/web/public/assets/artworks")
	os.MkdirAll(dir, 0755)
	b := []byte("test fixture")
	save(filepath.Join(dir, "test.jpg"), b)
	w := Work{Image: "/assets/artworks/test.jpg", Checksum: digest(b), Bytes: int64(len(b)), Rights: "cc0", License: "CC0", Evidence: true}
	if !strings.HasPrefix(imageCheck(root, w), "file verified") {
		t.Fatal(imageCheck(root, w))
	}
	w.Image = "/assets/artworks/../../.env"
	if strings.HasPrefix(imageCheck(root, w), "file verified") {
		t.Fatal("traversal")
	}
	if strings.Contains(md("a|[x]<script>"), "<script>") || link("bad", "javascript:alert(1)") != "No verified source link" {
		t.Fatal("unsafe markdown")
	}
}
func TestPinnedGreekManifest(t *testing.T) {
	b, e := os.ReadFile("../../../../docs/research/painter-review/greek-round-01-selection.json")
	if e != nil {
		t.Fatal(e)
	}
	var captured GreekManifest
	if e = json.Unmarshal(b, &captured); e != nil {
		t.Fatal(e)
	}
	m, e := validateGreekAt("../../../..", b, greekPin, captured.Created.Add(time.Minute))
	if e != nil {
		t.Fatal(e)
	}
	if len(m.Artists) != 10 || len(m.Works) != 10 {
		t.Fatal("bounded selection")
	}
	if _, e = validateGreek("../../../..", append(b, ' '), greekPin); e == nil {
		t.Fatal("changed source allowed")
	}
	if _, e = validateGreekAt("../../../..", b, greekPin, captured.Created.Add(25*time.Hour)); e == nil {
		t.Fatal("stale selection accepted")
	}
}
