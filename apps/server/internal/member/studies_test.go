package member

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"sync"
	"testing"
	"time"
)

type studyTestCatalogue struct{ calls int }

func (c *studyTestCatalogue) Search(_ context.Context, _ string, f StudySearch) (StudySearchPage, error) {
	c.calls++
	return StudySearchPage{Items: []StudyRecord{}}, nil
}
func (c *studyTestCatalogue) Lookup(_ context.Context, refs []BookmarkRef) ([]StudyRecord, error) {
	c.calls++
	out := []StudyRecord{}
	for _, ref := range refs {
		out = append(out, StudyRecord{BookmarkRef: ref, Title: "Source-backed test reference", Date: "1884–86, border added 1888–89", Intervals: []StudyInterval{{1884, 1886}, {1888, 1889}}, CapturedAt: time.Now()})
	}
	return out, nil
}
func studiesFixture() (*memoryStore, *LocalStudies, *studyTestCatalogue, *http.ServeMux) {
	h, auth, _, mux := fixture()
	store := NewLocalStudies()
	catalogue := &studyTestCatalogue{}
	h.RegisterStudies(mux, store, catalogue, &testBookmarks{})
	return auth, store, catalogue, mux
}
func studyTestRequest(mux *http.ServeMux, auth *memoryStore, user, method, path, body, origin string) *httptest.ResponseRecorder {
	r := httptest.NewRequest(method, "/api/v1/member/studies"+path, strings.NewReader(body))
	if user != "" {
		token := strings.Repeat(user, 43)
		auth.sessions[hashToken(token)] = User{ID: user}
		r.AddCookie(&http.Cookie{Name: "__Host-artline_session", Value: token})
	}
	if origin != "" {
		r.Header.Set("Origin", origin)
	}
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, r)
	return w
}
func TestStudiesAuthorizationAndOwnership(t *testing.T) {
	auth, store, catalogue, mux := studiesFixture()
	id := studyID()
	_ = store.Create(context.Background(), "a", Study{ID: id, Title: "Private", Role: "research", Records: []StudyRecord{}})
	for _, tc := range []struct {
		user, method, path, body, origin string
		status                           int
	}{
		{"", "GET", "", "", "", 401}, {"", "GET", "/search?kind=artwork", "", "", 401}, {"", "GET", "/" + id, "", "", 401}, {"", "GET", "/" + id + "/export?format=csv", "", "", 401},
		{"a", "POST", "", `{"title":"x","role":"research"}`, "", 403}, {"a", "PATCH", "/" + id, `{"title":"x"}`, "https://evil.example", 403}, {"a", "HEAD", "/" + id, "", "", 405},
		{"b", "GET", "/" + id, "", "", 404}, {"b", "DELETE", "/" + id, "", "https://artlines.org", 404}, {"b", "POST", "/" + id + "/records", `{"refs":[{"kind":"artwork","id":"11111111-1111-4111-8111-111111111111"}]}`, "https://artlines.org", 404},
		{"b", "PUT", "/" + id + "/records/book/test", `{"note":"stolen"}`, "https://artlines.org", 404}, {"b", "GET", "/" + id + "/export?format=csv", "", "", 404},
	} {
		w := studyTestRequest(mux, auth, tc.user, tc.method, tc.path, tc.body, tc.origin)
		if w.Code != tc.status {
			t.Fatalf("%s %s: %d %s", tc.method, tc.path, w.Code, w.Body.String())
		}
		if w.Header().Get("Cache-Control") != "private, no-store" {
			t.Fatal("private response cacheable")
		}
	}
	if catalogue.calls != 0 {
		t.Fatal("unauthorized catalogue lookup")
	}
}
func TestStudiesLinksDuplicatesNotesAndExport(t *testing.T) {
	auth, store, _, mux := studiesFixture()
	request := func(method, path, body string) *httptest.ResponseRecorder {
		return studyTestRequest(mux, auth, "a", method, path, body, "https://artlines.org")
	}
	w := request("POST", "", `{"title":"My study"}`)
	var summary StudySummary
	if w.Code != 200 || json.Unmarshal(w.Body.Bytes(), &summary) != nil {
		t.Fatal(w.Body.String())
	}
	path := "/" + summary.ID
	for _, bad := range []string{"javascript:alert(1)", "data:text/html,hello", "//evil.example", "https://user:secret@example.org"} {
		body, _ := json.Marshal(map[string]any{"link": map[string]string{"kind": "book", "url": bad}})
		if w := request("POST", path+"/records", string(body)); w.Code != 400 {
			t.Fatalf("unsafe link %s: %d", bad, w.Code)
		}
	}
	for range 2 {
		w = request("POST", path+"/records", `{"link":{"kind":"book","url":"https://example.org/book","title":"=SUM(1,2)","year":1877}}`)
		if w.Code != 200 {
			t.Fatal(w.Body.String())
		}
	}
	s, _ := store.Get(context.Background(), "a", summary.ID)
	if len(s.Records) != 1 || len(s.Records[0].Intervals) != 1 || !s.Records[0].Personal {
		t.Fatal("personal date or idempotency broken")
	}
	ref := s.Records[0]
	w = request("PUT", path+"/records/book/"+ref.ID, `{"note":" \t@SUM(1,2)\n<script>alert(1)</script>"}`)
	if w.Code != 200 {
		t.Fatal(w.Body.String())
	}
	w = request("PATCH", path, `{"role":"teaching"}`)
	if w.Code != 400 {
		t.Fatal(w.Body.String())
	}
	s, _ = store.Get(context.Background(), "a", summary.ID)
	if s.Role != "research" || !strings.Contains(s.Records[0].Note, "<script>") {
		t.Fatal("note persistence or research-only contract broken")
	}
	w = request("GET", path+"/export?format=csv", "")
	rows, err := csv.NewReader(w.Body).ReadAll()
	if err != nil || len(rows) != 2 || rows[1][1] != "'=SUM(1,2)" || !strings.HasPrefix(rows[1][8], "'") {
		t.Fatalf("unsafe CSV: %v %v", rows, err)
	}
	w = request("DELETE", path+"/records/book/"+ref.ID, "")
	if w.Code != 200 {
		t.Fatal(w.Body.String())
	}
	s, _ = store.Get(context.Background(), "a", summary.ID)
	if len(s.Records) != 0 {
		t.Fatal("remove failed")
	}
}
func TestStudyIntervalsKeepGapsAndDisplayedDates(t *testing.T) {
	start, end := 1870, 1880
	intervals, note := studyIntervals("1875–80", &start, &end)
	if len(intervals) != 1 || intervals[0].Start != 1875 || intervals[0].End != 1880 || !strings.Contains(note, "differ") {
		t.Fatal(intervals, note)
	}
	intervals, _ = studyIntervals("1884–86, border added 1888–89", nil, nil)
	if len(intervals) != 2 {
		t.Fatal(intervals)
	}
	r := StudyRecord{BookmarkRef: BookmarkRef{"artwork", "a"}, Title: "Seurat", Date: "1884–86, border added 1888–89", Intervals: intervals}
	for _, tc := range []struct {
		year int
		want bool
	}{{1884, true}, {1886, true}, {1887, false}, {1888, true}, {1889, true}, {1890, false}} {
		if got := studyOverlap(r, &tc.year, &tc.year); got != tc.want {
			t.Fatalf("year %d: %v", tc.year, got)
		}
	}
	for _, label := range []string{"1884 or later", "after 1870", "Unverified date: 1908"} {
		intervals, _ := studyIntervals(label, nil, nil)
		if len(intervals) != 0 {
			t.Fatalf("qualified date was made exact: %s", label)
		}
	}
	s := Study{Records: []StudyRecord{r, {BookmarkRef: BookmarkRef{"book", "b"}, Title: "Book", Intervals: []StudyInterval{{1887, 1887}}}}}
	v, err := studyView(s, url.Values{"kind": {"book"}, "from": {"1887"}, "to": {"1887"}, "q": {"book"}})
	if err != nil || v.Matched != 1 || v.Items[0].Kind != "book" {
		t.Fatal(v, err)
	}
	v, err = studyView(s, url.Values{"kind": {"none"}})
	if err != nil || v.Matched != 0 {
		t.Fatal("all types off", v, err)
	}
	for _, q := range []url.Values{{"from": {"abc"}}, {"from": {"1890"}, "to": {"1870"}}, {"to": {"0"}}} {
		if _, err := studyView(s, q); err == nil {
			t.Fatal("invalid range accepted")
		}
	}
}
func TestStudyAtomicChangesAndBoundedPages(t *testing.T) {
	ctx := context.Background()
	store := NewLocalStudies()
	id := studyID()
	_ = store.Create(ctx, "a", Study{ID: id, Title: "Atomic", Role: "research", Records: []StudyRecord{}})
	var wg sync.WaitGroup
	for i := range 80 {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			_, err := store.Update(ctx, "a", id, func(s *Study) error {
				s.Records = append(s.Records, StudyRecord{BookmarkRef: BookmarkRef{"book", fmt.Sprintf("book-%03d", i)}, Intervals: []StudyInterval{{1877, 1877}}})
				return nil
			})
			if err != nil {
				t.Error(err)
			}
		}(i)
	}
	wg.Wait()
	s, _ := store.Get(ctx, "a", id)
	if len(s.Records) != 80 {
		t.Fatal("lost concurrent addition")
	}
	v, err := studyView(s, url.Values{})
	if err != nil || len(v.Items) != 50 || v.NextCursor == "" {
		t.Fatal(v, err)
	}
	second, err := studyView(s, url.Values{"cursor": {v.NextCursor}})
	if err != nil || len(second.Items) != 30 || second.NextCursor != "" {
		t.Fatal(second, err)
	}
	_, _ = store.Update(ctx, "a", id, func(s *Study) error { s.Title = "must roll back"; return ErrStudyLimit })
	saved, _ := store.Get(ctx, "a", id)
	if saved.Title != "Atomic" {
		t.Fatal("failed mutation persisted")
	}
}
func TestStudiesLocalDebugGuardAndReturnDestination(t *testing.T) {
	h, _, _, mux := fixture()
	h.config.LocalDebug = true
	h.RegisterStudies(mux, NewLocalStudies(), &studyTestCatalogue{}, &testBookmarks{})
	for _, tc := range []struct {
		remote string
		status int
	}{{"127.0.0.1:1234", 200}, {"192.0.2.1:1234", 403}} {
		r := httptest.NewRequest("GET", "/api/v1/member/studies", nil)
		r.RemoteAddr = tc.remote
		w := httptest.NewRecorder()
		mux.ServeHTTP(w, r)
		if w.Code != tc.status {
			t.Fatal(w.Code, w.Body.String())
		}
	}
	path := "/studies/" + studyID() + "?view=gallery"
	if memberReturnTo(path) != path || memberReturnTo("/studies/../auth") != "" {
		t.Fatal("study sign-in destination")
	}
}

func TestPersonalRecordsRequireDatesAndAllowNoURL(t *testing.T) {
	auth, store, _, mux := studiesFixture()
	id := studyID()
	_ = store.Create(context.Background(), "a", Study{ID: id, Title: "Research", Role: "research"})
	path := "/" + id + "/records"
	for _, fields := range []string{
		`"title":"No date"`, `"title":"Only end","end_year":1880`,
		`"title":"Reversed","year":1880,"end_year":1870`,
		`"title":"Zero","year":0`, `"title":"End zero","year":-1,"end_year":0`,
		`"title":"Too early","year":-12001`, `"title":"Too late","year":2001`,
		`"title":"Fraction","year":1875.5`, `"year":1875`,
		`"title":"Bad URL","year":1875,"url":"javascript:alert(1)"`,
	} {
		w := studyTestRequest(mux, auth, "a", "POST", path, `{"link":{"kind":"book",`+fields+`}}`, "https://artlines.org")
		if w.Code != 400 {
			t.Fatalf("invalid record accepted %s: %d", fields, w.Code)
		}
	}
	for _, tc := range []struct {
		kind, title, years, date string
		start, end               int
	}{
		{"book", "Private book", `"year":1875,"end_year":1880`, "1875–1880", 1875, 1880},
		{"book", "Another private book", `"year":1877`, "1877", 1877, 1877},
		{"event", "Ancient event", `"year":-500,"end_year":-450`, "500 BCE–450 BCE", -500, -450},
		{"artwork", "Study", `"year":1960,"end_year":1970`, "1960–1970", 1960, 1970},
	} {
		body := fmt.Sprintf(`{"link":{"kind":%q,"title":%q,%s}}`, tc.kind, tc.title, tc.years)
		w := studyTestRequest(mux, auth, "a", "POST", path, body, "https://artlines.org")
		if w.Code != 200 {
			t.Fatal(w.Body.String())
		}
		s, _ := store.Get(context.Background(), "a", id)
		r := s.Records[len(s.Records)-1]
		if r.Title != tc.title || r.Date != tc.date || r.Href != "" || len(r.Sources) != 0 || len(r.Intervals) != 1 || r.Intervals[0] != (StudyInterval{tc.start, tc.end}) {
			t.Fatalf("bad personal record: %+v", r)
		}
	}
	s, _ := store.Get(context.Background(), "a", id)
	if len(s.Records) != 4 {
		t.Fatal("records without URLs were merged")
	}
	v, err := studyView(s, url.Values{"from": {"1876"}, "to": {"1876"}})
	if err != nil || v.Matched != 1 || v.Items[0].Title != "Private book" {
		t.Fatal("personal range not searchable", v, err)
	}
	w := studyTestRequest(mux, auth, "a", "POST", path, `{"link":{"kind":"artwork","title":"Cross cutoff","year":1960,"end_year":1971}}`, "https://artlines.org")
	if w.Code != 400 {
		t.Fatal("artwork range crossed cutoff")
	}
}
