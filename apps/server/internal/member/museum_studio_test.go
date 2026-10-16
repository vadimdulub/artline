package member

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func studioFixture() (*Handler, *LocalMuseumStudio, *http.ServeMux) {
	s := &LocalMuseumStudio{lookup: func(_ context.Context, slug string) (StudioMuseum, error) {
		if slug != "museum-a" && slug != "museum-b" {
			return StudioMuseum{}, ErrPublicationMissing
		}
		return StudioMuseum{ID: slug, Slug: slug, Name: slug}, nil
	}, staff: map[string]bool{}, items: map[string]localPublication{}}
	h := New(Config{LocalDebug: true, Origin: "http://localhost:3000"}, nil)
	mux := http.NewServeMux()
	h.RegisterMuseumStudio(mux, s)
	return h, s, mux
}
func studioCall(mux http.Handler, method, path string, body any) *httptest.ResponseRecorder {
	raw, _ := json.Marshal(body)
	r := httptest.NewRequest(method, path, strings.NewReader(string(raw)))
	r.RemoteAddr = "127.0.0.1:9876"
	r.Header.Set("Origin", "http://localhost:3000")
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, r)
	return w
}
func TestMuseumVerifiedWorkDomain(t *testing.T) {
	for _, tc := range []struct{ email, hd, want string }{
		{"curator@museum.org", "museum.org", "museum.org"}, {"Curator@MUSEUM.ORG", "MUSEUM.ORG", "museum.org"},
		{"curator@museum.org", "", ""}, {"curator@gmail.com", "museum.org", ""}, {"curator@fake-museum.org", "museum.org", ""},
		{"curator@sub.museum.org", "museum.org", ""}, {"a@b@museum.org", "museum.org", ""},
	} {
		if got := museumDomain(User{Email: tc.email, HostedDomain: tc.hd}); got != tc.want {
			t.Errorf("%+v: %q", tc, got)
		}
	}
}
func TestMuseumPublishingLifecycleAndTenantIsolation(t *testing.T) {
	_, _, mux := studioFixture()
	base := "/api/v1/member/museum-studio/museum-a"
	in := PublicationWrite{Kind: "artwork", Action: "save", Document: MuseumDocument{Title: "A contemporary painting", DateLabel: "2024–2026"}}
	if w := studioCall(mux, "POST", base+"/content", in); w.Code != 403 {
		t.Fatal(w.Code, w.Body.String())
	}
	if w := studioCall(mux, "POST", base+"/claim", nil); w.Code != 200 {
		t.Fatal(w.Code, w.Body.String())
	}
	w := studioCall(mux, "POST", base+"/content", in)
	if w.Code != 200 {
		t.Fatal(w.Code, w.Body.String())
	}
	var item MuseumPublication
	json.Unmarshal(w.Body.Bytes(), &item)
	public := "/api/v1/museum-publications/museum-a/" + item.ID
	if w = studioCall(mux, "GET", public, nil); w.Code != 404 {
		t.Fatal("draft leaked", w.Code)
	}
	in.Version = item.Version
	in.Action = "publish"
	w = studioCall(mux, "PUT", base+"/content/"+item.ID, in)
	if w.Code != 200 {
		t.Fatal(w.Body.String())
	}
	json.Unmarshal(w.Body.Bytes(), &item)
	in.Version = item.Version
	in.Action = "save"
	in.Document.Title = "Private changed title"
	w = studioCall(mux, "PUT", base+"/content/"+item.ID, in)
	if w.Code != 200 {
		t.Fatal(w.Body.String())
	}
	json.Unmarshal(w.Body.Bytes(), &item)
	w = studioCall(mux, "GET", public, nil)
	if w.Code != 200 || strings.Contains(w.Body.String(), "Private changed title") || !strings.Contains(w.Body.String(), "A contemporary painting") || strings.Contains(w.Body.String(), "version") {
		t.Fatal("published snapshot changed or private metadata leaked", w.Body.String())
	}
	if w = studioCall(mux, "PUT", base+"/content/"+item.ID, in); w.Code != 409 {
		t.Fatal("stale write accepted", w.Code)
	}
	studioCall(mux, "POST", "/api/v1/member/museum-studio/museum-b/claim", nil)
	in.Version = item.Version
	if w = studioCall(mux, "PUT", "/api/v1/member/museum-studio/museum-b/content/"+item.ID, in); w.Code != 409 {
		t.Fatal("cross-museum write accepted", w.Code)
	}
	if w = studioCall(mux, "GET", "/api/v1/museum-publications/museum-b/"+item.ID, nil); w.Code != 404 {
		t.Fatal("cross-museum read accepted")
	}
	in.Action = "unpublish"
	w = studioCall(mux, "PUT", base+"/content/"+item.ID, in)
	if w.Code != 200 {
		t.Fatal(w.Body.String())
	}
	if w = studioCall(mux, "GET", public, nil); w.Code != 404 {
		t.Fatal("unpublished record leaked")
	}
}
func TestMuseumStudioOriginAndLoopback(t *testing.T) {
	_, _, mux := studioFixture()
	for _, tc := range []struct{ address, origin string }{{"203.0.113.4:8765", "http://localhost:3000"}, {"127.0.0.1:8765", "https://other.example"}} {
		r := httptest.NewRequest("POST", "/api/v1/member/museum-studio/museum-a/claim", nil)
		r.RemoteAddr = tc.address
		r.Header.Set("Origin", tc.origin)
		r.Header.Set("X-Forwarded-For", "127.0.0.1")
		w := httptest.NewRecorder()
		mux.ServeHTTP(w, r)
		if w.Code != 403 {
			t.Fatal(tc, w.Code)
		}
	}
	h := New(Config{}, nil)
	_, s, _ := studioFixture()
	private := http.NewServeMux()
	h.RegisterMuseumStudio(private, s)
	if w := studioCall(private, "GET", "/api/v1/member/museum-studio", nil); w.Code != 401 {
		t.Fatal("anonymous studio accepted")
	}
	// Public reading does not require session or loopback identity.
	r := httptest.NewRequest("GET", "/api/v1/museum-publications/museum-a?kind=artwork", nil)
	w := httptest.NewRecorder()
	private.ServeHTTP(w, r)
	if w.Code != 200 {
		t.Fatal("anonymous reading blocked", w.Code)
	}
}
func TestMuseumDocumentValidation(t *testing.T) {
	start, end := 2026, 2020
	for _, tc := range []struct {
		kind string
		doc  MuseumDocument
	}{
		{"artwork", MuseumDocument{Title: "Work"}},
		{"artwork", MuseumDocument{Title: "Work", DateLabel: "2020–2026", YearStart: &start, YearEnd: &end}},
		{"guide", MuseumDocument{Title: "Guide", ImageURL: "javascript:alert(1)"}},
		{"guide", MuseumDocument{Title: "Guide", ImageURL: "https://museum.org/image.jpg"}},
		{"guide", MuseumDocument{Title: "Guide", SourceURL: "https://user:pass@museum.org"}},
		{"exhibition", MuseumDocument{Title: "Show", StartDate: "2026-05-01", EndDate: "2026-04-01"}},
	} {
		if validateMuseumDocument(tc.kind, tc.doc) == "" {
			t.Errorf("invalid document accepted: %+v", tc)
		}
	}
	for _, tc := range []struct {
		kind string
		doc  MuseumDocument
	}{
		{"artwork", MuseumDocument{Title: "Work", DateLabel: "Date unknown"}},
		{"guide", MuseumDocument{Title: "Οδηγός", Body: strings.Repeat("α", 20000)}},
		{"artwork", MuseumDocument{Title: "Work", DateLabel: "2026", YearStart: &start}},
		{"exhibition", MuseumDocument{Title: "Current exhibition", StartDate: "2026-10-12"}},
	} {
		if err := validateMuseumDocument(tc.kind, tc.doc); err != "" {
			t.Fatal(err)
		}
	}
}
func TestMuseumPublicPagingAndProfileUniqueness(t *testing.T) {
	_, s, mux := studioFixture()
	u := User{ID: "local-debug"}
	ctx := context.Background()
	s.Claim(ctx, u, "museum-a")
	for i := 0; i < 30; i++ {
		_, err := s.Write(ctx, u, "museum-a", "", PublicationWrite{Kind: "guide", Action: "publish", Document: MuseumDocument{Title: fmt.Sprintf("Guide %02d", i)}})
		if err != nil {
			t.Fatal(err)
		}
	}
	var page PublicationPage
	w := studioCall(mux, "GET", "/api/v1/museum-publications/museum-a?kind=guide", nil)
	json.Unmarshal(w.Body.Bytes(), &page)
	if len(page.Items) != 24 || page.NextCursor == "" {
		t.Fatal("unbounded or broken first page", w.Body.String())
	}
	seen := map[string]bool{}
	for _, p := range page.Items {
		seen[p.ID] = true
	}
	w = studioCall(mux, "GET", "/api/v1/museum-publications/museum-a?kind=guide&cursor="+page.NextCursor, nil)
	json.Unmarshal(w.Body.Bytes(), &page)
	if len(page.Items) != 6 || page.NextCursor != "" {
		t.Fatal("broken second page", w.Body.String())
	}
	for _, p := range page.Items {
		if seen[p.ID] {
			t.Fatal("duplicate page item")
		}
	}
	w = studioCall(mux, "GET", "/api/v1/museum-publications/museum-a?kind=guide&q=Guide+29", nil)
	json.Unmarshal(w.Body.Bytes(), &page)
	if len(page.Items) != 1 {
		t.Fatal("search failed")
	}
	in := PublicationWrite{Kind: "profile", Action: "save", Document: MuseumDocument{Title: "Museum"}}
	s.Write(ctx, u, "museum-a", "", in)
	if _, err := s.Write(ctx, u, "museum-a", "", in); err != ErrPublicationConflict {
		t.Fatal("multiple museum profiles accepted")
	}
}
