package member

import (
	"context"
	"encoding/json"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestStudySharingReadOnlyLifecycle(t *testing.T) {
	auth, store, _, mux := studiesFixture()
	request := func(method, path, body string) *httptest.ResponseRecorder {
		return studyTestRequest(mux, auth, "a", method, path, body, "https://artlines.org")
	}
	shared := func(method, token, query string) *httptest.ResponseRecorder {
		r := httptest.NewRequest(method, "/api/v1/shared/studies/"+token+query, strings.NewReader(`{"title":"stolen","public":true}`))
		w := httptest.NewRecorder()
		mux.ServeHTTP(w, r)
		if w.Header().Get("Cache-Control") != "private, no-store" {
			t.Fatal("shared data must not be cached")
		}
		return w
	}
	w := request("POST", "", `{"title":"Research to share"}`)
	var summary StudySummary
	if w.Code != 200 || json.Unmarshal(w.Body.Bytes(), &summary) != nil || summary.Public {
		t.Fatal(w.Body.String())
	}
	path := "/" + summary.ID
	if shared("GET", summary.ID, "").Code != 404 {
		t.Fatal("private study exposed through its ID")
	}
	for _, body := range []string{
		`{"link":{"kind":"book","title":"First edition","year":1877}}`,
		`{"refs":[{"kind":"artwork","id":"11111111-1111-4111-8111-111111111111"},{"kind":"artwork","id":"22222222-2222-4222-8222-222222222222"}]}`,
	} {
		if w := request("POST", path+"/records", body); w.Code != 200 {
			t.Fatal(w.Body.String())
		}
	}
	s, _ := store.Get(context.Background(), "a", summary.ID)
	if w := request("PUT", path+"/records/book/"+s.Records[0].ID, `{"note":"Shared research note"}`); w.Code != 200 {
		t.Fatal(w.Body.String())
	}
	for _, user := range []string{"", "b"} {
		w := studyTestRequest(mux, auth, user, "PATCH", path, `{"public":true}`, "https://artlines.org")
		if user == "" && w.Code != 401 || user == "b" && w.Code != 404 {
			t.Fatal("non-owner could publish", w.Code)
		}
	}
	if w := studyTestRequest(mux, auth, "a", "PATCH", path, `{"public":true}`, "https://evil.example"); w.Code != 403 {
		t.Fatal("cross-origin publication allowed")
	}
	if w := request("PATCH", path, `{"public":true}`); w.Code != 200 {
		t.Fatal(w.Body.String())
	}
	var owned StudyView
	w = request("GET", path, "")
	if json.Unmarshal(w.Body.Bytes(), &owned) != nil || !owned.Public || !bookmarkID.MatchString(owned.ShareToken) || owned.ShareToken == summary.ID {
		t.Fatal(w.Body.String())
	}
	token := owned.ShareToken
	w = shared("GET", token, "")
	var public StudyView
	if w.Code != 200 || json.Unmarshal(w.Body.Bytes(), &public) != nil || public.Count != 3 || !public.Public || public.ID != token || public.ShareToken != "" || public.Keys != nil || !strings.Contains(w.Body.String(), "Shared research note") || strings.Contains(w.Body.String(), summary.ID) {
		t.Fatal(w.Body.String())
	}
	for _, method := range []string{"POST", "PATCH", "PUT", "DELETE", "HEAD"} {
		if shared(method, token, "").Code != 405 {
			t.Fatal("public endpoint accepted mutation", method)
		}
	}
	for _, method := range []string{"PATCH", "DELETE"} {
		if w := studyTestRequest(mux, auth, "b", method, path, `{"public":false}`, "https://artlines.org"); w.Code != 404 {
			t.Fatal("sharing weakened ownership", method, w.Code)
		}
	}
	// Existing public filtering retains disjoint date intervals and bounded comparisons.
	w = shared("GET", token, "?from=1887&to=1887")
	if json.Unmarshal(w.Body.Bytes(), &public) != nil || public.Matched != 0 {
		t.Fatal("interval gap lost", w.Body.String())
	}
	w = shared("GET", token, "?compare=artwork:11111111-1111-4111-8111-111111111111&compare=artwork:22222222-2222-4222-8222-222222222222")
	if json.Unmarshal(w.Body.Bytes(), &public) != nil || len(public.Artworks) != 2 || len(public.Artworks[0].Intervals) != 2 {
		t.Fatal("public comparison failed", w.Body.String())
	}
	if w := request("PATCH", path, `{"public":true,"title":"Updated research"}`); w.Code != 200 {
		t.Fatal(w.Body.String())
	}
	w = shared("GET", token, "")
	if w.Code != 200 || !strings.Contains(w.Body.String(), "Updated research") {
		t.Fatal("idempotent publication rotated link or hid updates")
	}
	if w := request("PATCH", path, `{"public":false}`); w.Code != 200 {
		t.Fatal(w.Body.String())
	}
	if shared("GET", token, "").Code != 404 {
		t.Fatal("revoked link remains readable")
	}
	w = request("GET", path, "")
	owned = StudyView{}
	if json.Unmarshal(w.Body.Bytes(), &owned) != nil || owned.Public || owned.ShareToken != "" || owned.Count != 3 {
		t.Fatal("revocation changed private records", w.Body.String())
	}
	if w := request("PATCH", path, `{"public":true}`); w.Code != 200 {
		t.Fatal(w.Body.String())
	}
	s, _ = store.Get(context.Background(), "a", summary.ID)
	if s.ShareToken == token || shared("GET", token, "").Code != 404 || shared("GET", s.ShareToken, "").Code != 200 {
		t.Fatal("republishing resurrected an old link")
	}
	if w := request("DELETE", path, ""); w.Code != 200 {
		t.Fatal(w.Body.String())
	}
	if shared("GET", s.ShareToken, "").Code != 404 {
		t.Fatal("deleted study remains shared")
	}
}
