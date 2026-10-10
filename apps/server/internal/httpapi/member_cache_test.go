package httpapi

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/member"
)

type cacheMemberStore struct{ active bool }

func (s *cacheMemberStore) Session(context.Context, string) (member.User, error) {
	if s.active {
		return member.User{ID: "member"}, nil
	}
	return member.User{}, member.ErrNoSession
}
func (*cacheMemberStore) Login(context.Context, member.Identity, string, string, time.Time) error {
	return nil
}
func (*cacheMemberStore) Logout(context.Context, string) error { return nil }

func TestMemberAccessPrecedesWarmCatalogueCache(t *testing.T) {
	for _, path := range []string{"/api/v1/museums", "/api/v1/museums/the-met/works"} {
		t.Run(path, func(t *testing.T) {
			store := &cacheMemberStore{active: true}
			members := member.New(member.Config{ClientID: "client", ClientSecret: "secret", CookieKey: strings.Repeat("k", 32), Origin: "https://artlines.org"}, store)
			revisions, queries := 0, 0
			cache := newCatalogueCache(func(context.Context) (string, error) { revisions++; return "1", nil })
			api := &API{}
			handler := members.CatalogueAccess(api.cacheCatalogue(cache, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				queries++
				writeJSON(w, 200, map[string]string{"record": "member catalogue"})
			})))
			call := func(cookie bool) *httptest.ResponseRecorder {
				r := httptest.NewRequest("GET", path, nil)
				if cookie {
					r.AddCookie(&http.Cookie{Name: "__Host-artline_session", Value: strings.Repeat("a", 43)})
				}
				w := httptest.NewRecorder()
				handler.ServeHTTP(w, r)
				return w
			}
			if w := call(true); w.Code != 200 {
				t.Fatal(w.Code)
			}
			if w := call(true); w.Code != 200 || queries != 1 {
				t.Fatal("member cache not reused")
			}
			before := revisions
			store.active = false
			for _, cookie := range []bool{false, true} {
				w := call(cookie)
				if w.Code != 401 || strings.Contains(w.Body.String(), "member catalogue") || revisions != before || queries != 1 {
					t.Fatalf("cached response bypassed auth: %d %s", w.Code, w.Body.String())
				}
			}
		})
	}
}

func TestAnonymousProtectedRouterRequestsNeverReachDatabase(t *testing.T) {
	handler := New(config.Config{}, nil)
	for _, path := range []string{"/api/v1/museums", "/api/v1/museums/the-met", "/api/v1/museums/the-met/works", "/api/v1/museums/the-met/works/11111111-1111-4111-8111-111111111111"} {
		for _, method := range []string{"GET", "HEAD"} {
			w := httptest.NewRecorder()
			handler.ServeHTTP(w, httptest.NewRequest(method, path, nil))
			if w.Code != 401 {
				t.Fatalf("%s %s: %d", method, path, w.Code)
			}
		}
	}
}
