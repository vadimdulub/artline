package member

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"strings"
	"testing"
	"time"
)

func TestStudyLibraryPagingSearchAndIsolation(t *testing.T) {
	auth, store, _, mux := studiesFixture()
	ctx := context.Background()
	now := time.Now().UTC().Truncate(time.Microsecond)
	for i := range 157 {
		// Identical title/date keys cross page boundaries: UUID must break ties.
		s := Study{ID: studyID(), Title: fmt.Sprintf("Paris research %03d", i/3), Role: "research", UpdatedAt: now.Add(time.Duration(i/3) * time.Second)}
		if err := store.Create(ctx, "a", s); err != nil {
			t.Fatal(err)
		}
	}
	_ = store.Create(ctx, "b", Study{ID: studyID(), Title: "Paris private to another account", Role: "research", UpdatedAt: now})
	for _, order := range []string{"recent", "title"} {
		cursor := ""
		seen := map[string]bool{}
		var last StudySummary
		for {
			q := url.Values{"sort": {order}, "cursor": {cursor}}
			w := studyTestRequest(mux, auth, "a", "GET", "?"+q.Encode(), "", "")
			var page StudyListPage
			if w.Code != 200 || json.Unmarshal(w.Body.Bytes(), &page) != nil {
				t.Fatal(w.Body.String())
			}
			if page.Total != 157 || page.Matched != 157 || len(page.Items) > 24 {
				t.Fatalf("incorrect bounds: %+v", page)
			}
			for _, s := range page.Items {
				if seen[s.ID] {
					t.Fatal("duplicate across pages")
				}
				seen[s.ID] = true
				if last.ID != "" {
					if order == "title" && strings.ToLower(last.Title) > strings.ToLower(s.Title) {
						t.Fatal("title order")
					}
					if order == "recent" && last.UpdatedAt.Before(s.UpdatedAt) {
						t.Fatal("recent order")
					}
				}
				last = s
			}
			if page.NextCursor == "" {
				break
			}
			cursor = page.NextCursor
			for _, other := range []struct{ owner, query, sort string }{{"b", "", order}, {"a", "Paris", order}, {"a", "", "invalid"}} {
				changed := url.Values{"q": {other.query}, "sort": {other.sort}, "cursor": {cursor}}
				if r := studyTestRequest(mux, auth, other.owner, "GET", "?"+changed.Encode(), "", ""); r.Code != 400 {
					t.Fatalf("cursor reused with other scope: %d", r.Code)
				}
			}
		}
		if len(seen) != 157 {
			t.Fatalf("lost studies: %d", len(seen))
		}
	}
	f := StudyListFilter{Query: "PARIS research 001", Sort: "title"}
	page, err := store.List(ctx, "a", f)
	if err != nil || page.Matched != 3 || page.Total != 157 || len(page.Items) != 3 {
		t.Fatalf("search counts: %+v %v", page, err)
	}
	page, err = store.List(ctx, "a", StudyListFilter{Query: "%", Sort: "recent"})
	if err != nil || page.Matched != 0 {
		t.Fatal("literal search became wildcard")
	}
	for _, q := range []string{"?cursor=bad", "?sort=invalid"} {
		if r := studyTestRequest(mux, auth, "a", "GET", q, "", ""); r.Code != 400 {
			t.Fatal(r.Body.String())
		}
	}
}

func TestResearchOnlyCreationAndCollectionBound(t *testing.T) {
	auth, store, _, mux := studiesFixture()
	for _, role := range []string{"teaching", "exhibitions"} {
		r := studyTestRequest(mux, auth, "a", "POST", "", `{"title":"Title","role":"`+role+`"}`, "https://artlines.org")
		if r.Code != 400 {
			t.Fatal("non-research mode accepted")
		}
	}
	title := strings.Repeat("画", 180)
	body, _ := json.Marshal(map[string]string{"title": title})
	w := studyTestRequest(mux, auth, "a", "POST", "", string(body), "https://artlines.org")
	var created StudySummary
	if w.Code != 200 || json.Unmarshal(w.Body.Bytes(), &created) != nil || created.Role != "research" {
		t.Fatal(w.Body.String())
	}
	for range studyCollectionLimit - 1 {
		if err := store.Create(context.Background(), "a", Study{ID: studyID(), Title: "Study", Role: "research", UpdatedAt: time.Now()}); err != nil {
			t.Fatal(err)
		}
	}
	if err := store.Create(context.Background(), "a", Study{ID: studyID()}); err != ErrStudyLimit {
		t.Fatal("missing account bound", err)
	}
	if err := store.Create(context.Background(), "b", Study{ID: studyID()}); err != nil {
		t.Fatal("bound leaked across accounts", err)
	}
}
