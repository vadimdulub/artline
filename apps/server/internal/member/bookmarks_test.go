package member

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
	"time"
)

type testBookmarks struct {
	users map[string]*LocalBookmarks
	calls int
}

func (s *testBookmarks) user(id string) *LocalBookmarks {
	if s.users == nil {
		s.users = map[string]*LocalBookmarks{}
	}
	if s.users[id] == nil {
		s.users[id] = NewLocalBookmarks(func(_ context.Context, ref BookmarkRef) (Bookmark, error) {
			if strings.HasPrefix(ref.ID, "ffffffff") {
				return Bookmark{}, ErrBookmarkMissing
			}
			return Bookmark{BookmarkRef: ref, Title: "A catalogue record", Href: "/artists/monet", SavedAt: time.Date(2026, 10, 10, 12, 0, 0, 0, time.UTC)}, nil
		})
	}
	return s.users[id]
}
func (s *testBookmarks) Set(ctx context.Context, id string, ref BookmarkRef, saved bool) error {
	s.calls++
	return s.user(id).Set(ctx, id, ref, saved)
}
func (s *testBookmarks) States(ctx context.Context, id string, refs []BookmarkRef) ([]BookmarkRef, error) {
	s.calls++
	return s.user(id).States(ctx, id, refs)
}
func (s *testBookmarks) List(ctx context.Context, id, kind string, cursor BookmarkCursor, limit int) ([]Bookmark, error) {
	s.calls++
	return s.user(id).List(ctx, id, kind, cursor, limit)
}

func bookmarkFixture() (*Handler, *memoryStore, *testBookmarks, *http.ServeMux) {
	h, auth, _, mux := fixture()
	store := &testBookmarks{}
	h.RegisterBookmarks(mux, store)
	return h, auth, store, mux
}
func bookmarkRequest(mux *http.ServeMux, auth *memoryStore, user, method, path, origin string) *httptest.ResponseRecorder {
	r := httptest.NewRequest(method, "/api/v1/member/bookmarks"+path, nil)
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
func TestBookmarksAuthenticationAndCSRF(t *testing.T) {
	_, auth, store, mux := bookmarkFixture()
	ref := "/artwork/11111111-1111-4111-8111-111111111111"
	for _, tc := range []struct {
		user, method, path, origin string
		status                     int
	}{
		{"", "GET", "", "", 401}, {"", "GET", "/state?artist=11111111-1111-4111-8111-111111111111", "", 401},
		{"", "PUT", ref, "https://artlines.org", 401}, {"a", "PUT", ref, "", 403}, {"a", "DELETE", ref, "https://evil.example", 403},
		{"a", "HEAD", "", "", 405},
	} {
		w := bookmarkRequest(mux, auth, tc.user, tc.method, tc.path, tc.origin)
		if w.Code != tc.status {
			t.Fatalf("%s %s got %d", tc.method, tc.path, w.Code)
		}
		if w.Header().Get("Cache-Control") != "private, no-store" {
			t.Fatal("private bookmarks were cacheable")
		}
	}
	if store.calls != 0 {
		t.Fatal("unauthorized request reached bookmarks")
	}
	r := httptest.NewRequest("PUT", "/api/v1/member/bookmarks"+ref, nil)
	r.Header.Set("Origin", "https://artlines.org")
	r.Header.Set("Sec-Fetch-Site", "cross-site")
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, r)
	if w.Code != 403 {
		t.Fatal("cross-site mutation accepted")
	}
}
func TestBookmarksArePrivateIdempotentAndRemovable(t *testing.T) {
	_, auth, _, mux := bookmarkFixture()
	ref := "/artist/11111111-1111-4111-8111-111111111111"
	for i := 0; i < 2; i++ {
		if w := bookmarkRequest(mux, auth, "a", "PUT", ref, "https://artlines.org"); w.Code != 200 {
			t.Fatal(w.Body.String())
		}
	}
	var first BookmarkPage
	w := bookmarkRequest(mux, auth, "a", "GET", "?member_id=b", "")
	json.Unmarshal(w.Body.Bytes(), &first)
	if len(first.Items) != 1 {
		t.Fatalf("duplicate or missing bookmark: %s", w.Body.String())
	}
	w = bookmarkRequest(mux, auth, "b", "GET", "?member_id=a", "")
	var other BookmarkPage
	json.Unmarshal(w.Body.Bytes(), &other)
	if len(other.Items) != 0 {
		t.Fatal("cross-member data leak")
	}
	w = bookmarkRequest(mux, auth, "a", "GET", "/state?artist=11111111-1111-4111-8111-111111111111", "")
	if !strings.Contains(w.Body.String(), `"kind":"artist"`) {
		t.Fatal("saved state lost")
	}
	for i := 0; i < 2; i++ {
		if w = bookmarkRequest(mux, auth, "a", "DELETE", ref, "https://artlines.org"); w.Code != 200 {
			t.Fatal(w.Code)
		}
	}
	w = bookmarkRequest(mux, auth, "a", "GET", "/state?artist=11111111-1111-4111-8111-111111111111", "")
	if w.Body.String() != "{\"saved\":[]}\n" {
		t.Fatal(w.Body.String())
	}
}
func TestBookmarksBoundedPagingWithEqualTimestamps(t *testing.T) {
	_, auth, _, mux := bookmarkFixture()
	for i := 1; i <= 67; i++ {
		kind := "artist"
		if i%2 == 0 {
			kind = "artwork"
		}
		path := fmt.Sprintf("/%s/11111111-1111-4111-8111-%012d", kind, i)
		w := bookmarkRequest(mux, auth, "a", "PUT", path, "https://artlines.org")
		if w.Code != 200 {
			t.Fatal(w.Code)
		}
	}
	for _, kind := range []string{"", "artist", "artwork"} {
		cursor := ""
		seen := map[string]bool{}
		for page := 0; page < 4; page++ {
			w := bookmarkRequest(mux, auth, "a", "GET", "?"+url.Values{"kind": {kind}, "cursor": {cursor}}.Encode(), "")
			if w.Code != 200 {
				t.Fatal(w.Body.String())
			}
			var result BookmarkPage
			json.Unmarshal(w.Body.Bytes(), &result)
			if len(result.Items) > 30 {
				t.Fatal("unbounded bookmarks page")
			}
			for _, item := range result.Items {
				key := item.Kind + item.ID
				if seen[key] || kind != "" && item.Kind != kind {
					t.Fatal("duplicate or wrong-kind bookmark")
				}
				seen[key] = true
			}
			cursor = result.NextCursor
			if cursor == "" {
				break
			}
			mismatch := "artist"
			if kind == "artist" {
				mismatch = "artwork"
			}
			bad := bookmarkRequest(mux, auth, "a", "GET", "?"+url.Values{"kind": {mismatch}, "cursor": {cursor}}.Encode(), "")
			if bad.Code != 400 {
				t.Fatal("cursor reused under different filter")
			}
		}
		want := 67
		if kind == "artist" {
			want = 34
		} else if kind == "artwork" {
			want = 33
		}
		if len(seen) != want {
			t.Fatalf("kind %q returned %d of %d", kind, len(seen), want)
		}
	}
}
func TestBookmarkValidationPrecedesStorage(t *testing.T) {
	_, auth, store, mux := bookmarkFixture()
	for _, path := range []string{"?kind=other", "?cursor=bad", "/state", "/state?artist=not-a-uuid", "/state?" + strings.Repeat("artist=11111111-1111-4111-8111-111111111111&", 101)} {
		if w := bookmarkRequest(mux, auth, "a", "GET", path, ""); w.Code != 400 {
			t.Fatalf("%s got %d", path, w.Code)
		}
	}
	for _, path := range []string{"/museum/11111111-1111-4111-8111-111111111111", "/artist/bad-id"} {
		if w := bookmarkRequest(mux, auth, "a", "PUT", path, "https://artlines.org"); w.Code != 400 {
			t.Fatal(w.Code)
		}
	}
	if store.calls != 0 {
		t.Fatal("invalid query reached storage")
	}
	if w := bookmarkRequest(mux, auth, "a", "PUT", "/artwork/ffffffff-1111-4111-8111-111111111111", "https://artlines.org"); w.Code != 404 {
		t.Fatal("missing/archived record was saved")
	}
}
func TestLocalBookmarksNeedNoAccountOrDatabaseWrites(t *testing.T) {
	h := New(Config{Origin: "http://localhost:3000", LocalDebug: true}, nil)
	reads := 0
	store := NewLocalBookmarks(func(_ context.Context, ref BookmarkRef) (Bookmark, error) {
		reads++
		return Bookmark{BookmarkRef: ref, SavedAt: time.Now()}, nil
	})
	mux := http.NewServeMux()
	h.RegisterBookmarks(mux, store)
	r := httptest.NewRequest("PUT", "/api/v1/member/bookmarks/artist/11111111-1111-4111-8111-111111111111", nil)
	r.RemoteAddr = "127.0.0.1:1"
	r.Header.Set("Origin", "http://localhost:3000")
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, r)
	if w.Code != 200 || reads != 1 {
		t.Fatal(w.Code)
	}
	r.RemoteAddr = "203.0.113.1:1"
	w = httptest.NewRecorder()
	mux.ServeHTTP(w, r)
	if w.Code != 403 || reads != 1 {
		t.Fatal("remote debug bookmark accepted")
	}
}
