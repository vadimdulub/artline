package main

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestCycleCheckpointCannotChangeInventoryOrRawFacts(t *testing.T) {
	out := t.TempDir()
	if err := os.MkdirAll(filepath.Join(out, "captures"), 0755); err != nil {
		t.Fatal(err)
	}
	a := cycleArtist{ID: "fixture", Name: "Monet", Slug: "monet"}
	w := popularWork{Work: Work{ID: "one", Title: "Example"}}
	raw := map[string]any{"id": "1"}
	body := encode(map[string]any{"data": []map[string]any{raw}})
	if err := os.WriteFile(filepath.Join(out, "captures/fixture.json"), body, 0600); err != nil {
		t.Fatal(err)
	}
	r := cycleReport{Version: cycleVersion, ArtistID: a.ID, Artist: a.Name, Slug: a.Slug, Fingerprint: "fp", AutomatedPassDone: true, Works: []cycleWork{{popularWork: w}}, Discovery: cycleDiscovery{
		URL:   "https://openaccess-api.clevelandart.org/api/artworks/?artists=Monet&limit=20&skip=0&type=Painting",
		State: "bounded_catalogue_search_checked", Capture: "captures/fixture.json", SHA: digest(body), Candidates: []cycleCandidate{{Raw: raw}},
	}}
	if err := validateCycleCheckpoint(out, a, "fp", []popularWork{w}, r); err != nil {
		t.Fatal(err)
	}
	r.Works[0].Title = "changed"
	if err := validateCycleCheckpoint(out, a, "fp", []popularWork{w}, r); err == nil {
		t.Fatal("accepted changed artwork")
	}
	r.Works[0].Title = w.Title
	r.Discovery.Candidates[0].Raw = map[string]any{"id": "another"}
	if err := validateCycleCheckpoint(out, a, "fp", []popularWork{w}, r); err == nil {
		t.Fatal("accepted changed source facts")
	}
}

func TestCycleEmptySearchIsNotResearchComplete(t *testing.T) {
	c := newCycleClient()
	c.client.Transport = cycleTransport(func(*http.Request) (*http.Response, error) {
		return &http.Response{StatusCode: 200, Body: io.NopCloser(strings.NewReader(`{"info":{"total":0},"data":[]}`)), Header: http.Header{}}, nil
	})
	out := t.TempDir()
	if err := os.MkdirAll(filepath.Join(out, "captures"), 0755); err != nil {
		t.Fatal(err)
	}
	d, err := c.discover(context.Background(), cycleArtist{ID: "empty", Name: "Empty"}, out, nil)
	if err != nil || d.State != "bounded_catalogue_search_checked" || len(d.Candidates) != 0 {
		t.Fatal(d, err)
	}
}

type cycleTransport func(*http.Request) (*http.Response, error)

func (f cycleTransport) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestCycleSourcePauseAndBoundedRequest(t *testing.T) {
	calls := 0
	c := newCycleClient()
	c.client.Transport = cycleTransport(func(r *http.Request) (*http.Response, error) {
		calls++
		if r.URL.Host != "openaccess-api.clevelandart.org" || r.URL.Query().Get("limit") != "20" || r.URL.Query().Get("type") != "Painting" {
			t.Fatal("unbounded source request")
		}
		return &http.Response{StatusCode: 403, Body: io.NopCloser(strings.NewReader("denied")), Header: http.Header{}}, nil
	})
	a := cycleArtist{ID: "fixture", Name: "Monet"}
	for i := 0; i < 2; i++ {
		d, err := c.discover(context.Background(), a, t.TempDir(), nil)
		if err != nil {
			t.Fatal(err)
		}
		if i == 1 && d.State != "source_paused" {
			t.Fatal("lost host pause")
		}
	}
	if calls != 1 {
		t.Fatal("retried blocked source")
	}
}

func TestCycleClassificationDoesNotConflateDatesFilesAndResearch(t *testing.T) {
	w := popularWork{Work: Work{ID: "one", Scope: "eligible", ImageCheck: "missing"}, NGAObject: "1", HoldingEvidence: true}
	x := classifyCycleWork(w, map[string]imageLead{"1": {Count: 1, Open: true}})
	if x.ReviewState != "source_review_pending" || x.ImageState != "cached_NGA_open_image_lead_requires_fresh_check" {
		t.Fatal(x)
	}
	w.Scope = "unknown"
	if classifyCycleWork(w, nil).ReviewState != "date_review_required" {
		t.Fatal("invented creation date")
	}
	w.Sources = []string{"https://www.artic.edu/artworks/1"}
	if !strings.Contains(classifyCycleWork(w, nil).ImageState, "paused") {
		t.Fatal("ignored recorded image block")
	}
}

func TestCycleExactCandidateAndQualifiedCreator(t *testing.T) {
	b, err := os.ReadFile("../../../../content/imports/painter-review-round02-20260911/cleveland-129386.json")
	if err != nil {
		t.Fatal(err)
	}
	var doc struct{ Data map[string]any }
	if err = json.Unmarshal(b, &doc); err != nil {
		t.Fatal(err)
	}
	a := cycleArtist{Name: "El Greco", Names: []string{"El Greco"}}
	c := cycleCandidateFrom(a, doc.Data, nil)
	if c.State != "new_candidate_requires_review" {
		t.Fatal(c.State)
	}
	known := map[string]popularWork{"work": {Work: Work{ID: "work", Title: c.Title, Accession: c.Accession, Scope: "eligible"}, Sources: []string{c.URL}}}
	if cycleCandidateFrom(a, doc.Data, known).State != "existing_CC0_image_candidate" {
		t.Fatal("exact identity not matched")
	}
	w := known["work"]
	w.Accession = "different"
	known["work"] = w
	if cycleCandidateFrom(a, doc.Data, known).State != "existing_metadata_conflict" {
		t.Fatal("accepted conflicting accession")
	}
	creator := doc.Data["creators"].([]any)[0].(map[string]any)
	creator["qualifier"] = "workshop of"
	if cycleCandidateFrom(a, doc.Data, nil).State != "creator_review_required" {
		t.Fatal("accepted workshop as primary artist")
	}
}

func TestCycleCachedCaptureCannotBeSubstituted(t *testing.T) {
	dir := t.TempDir()
	if err := os.Mkdir(filepath.Join(dir, "captures"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "captures/fixture.json"), []byte(`{"data":[]}`), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "captures/fixture.json.snapshot.json"), []byte(`{"SHA":"wrong"}`), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := newCycleClient().discover(context.Background(), cycleArtist{ID: "fixture", Name: "Monet"}, dir, nil); err == nil {
		t.Fatal("accepted changed capture")
	}
}
