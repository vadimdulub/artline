package member

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestCatalogueAccessRequiresValidSession(t *testing.T) {
	h, store, _, _ := fixture()
	token := strings.Repeat("a", 43)
	for _, path := range []string{"/api/v1/museums", "/api/v1/museums/the-met", "/api/v1/museums/the-met/works", "/api/v1/museums/the-met/works/11111111-1111-4111-8111-111111111111"} {
		for _, state := range []string{"anonymous", "forged", "valid", "revoked", "unavailable"} {
			t.Run(path+"/"+state, func(t *testing.T) {
				reached := false
				next := h.CatalogueAccess(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { reached = true; w.WriteHeader(204) }))
				store.sessions = map[string]User{}
				store.fail = state == "unavailable"
				if state == "valid" {
					store.sessions[hashToken(token)] = User{ID: "member"}
				}
				r := httptest.NewRequest("GET", path, nil)
				r.Header.Set("Authorization", "Bearer pretend-editor")
				r.Header.Set("X-User-ID", "member")
				if state != "anonymous" {
					r.AddCookie(&http.Cookie{Name: "__Host-artline_session", Value: token})
				}
				w := httptest.NewRecorder()
				next.ServeHTTP(w, r)
				want := 401
				if state == "valid" {
					want = 204
				} else if state == "unavailable" {
					want = 503
				}
				if w.Code != want || reached != (state == "valid") {
					t.Fatalf("status=%d reached=%v body=%s", w.Code, reached, w.Body.String())
				}
				if w.Header().Get("Cache-Control") != "private, no-store" {
					t.Fatal("cacheable member response")
				}
			})
		}
	}
}

func TestPublicCatalogueDoesNotLookUpSession(t *testing.T) {
	h := New(Config{}, nil)
	for _, path := range []string{"/api/v1/timeline", "/api/v1/artists", "/api/v1/artists/monet", "/api/v1/artists/monet/identity", "/api/v1/artists/monet/works", "/api/v1/artists/monet/works/work-id", "/api/v1/artworks"} {
		w := httptest.NewRecorder()
		h.CatalogueAccess(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(204) })).ServeHTTP(w, httptest.NewRequest("GET", path, nil))
		if w.Code != 204 {
			t.Fatalf("public path %s gated", path)
		}
	}
}

func TestCatalogueLocalDebugRequiresLoopback(t *testing.T) {
	h := New(Config{LocalDebug: true}, nil)
	for _, address := range []string{"127.0.0.1:1234", "[::1]:1234", "203.0.113.10:1234", "invalid"} {
		r := httptest.NewRequest("GET", "/api/v1/museums", nil)
		r.RemoteAddr = address
		r.Header.Set("X-Forwarded-For", "127.0.0.1")
		w := httptest.NewRecorder()
		h.CatalogueAccess(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(204) })).ServeHTTP(w, r)
		want := 403
		if strings.HasPrefix(address, "127.") || strings.HasPrefix(address, "[::1]") {
			want = 204
		}
		if w.Code != want {
			t.Fatalf("%s: %d", address, w.Code)
		}
	}
}
