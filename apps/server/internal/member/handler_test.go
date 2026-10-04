package member

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
	"time"
)

type memoryStore struct {
	sessions map[string]User
	logins   int
	previous string
	fail     bool
}

func (s *memoryStore) Login(_ context.Context, i Identity, hash, previous string, _ time.Time) error {
	if s.fail {
		return errors.New("database down")
	}
	s.logins++
	s.previous = previous
	delete(s.sessions, previous)
	s.sessions[hash] = User{ID: "member", Name: i.Name, Email: i.Email}
	return nil
}
func (s *memoryStore) Session(_ context.Context, hash string) (User, error) {
	if s.fail {
		return User{}, errors.New("database down")
	}
	u, ok := s.sessions[hash]
	if !ok {
		return u, ErrNoSession
	}
	return u, nil
}
func (s *memoryStore) Logout(_ context.Context, hash string) error {
	if s.fail {
		return errors.New("database down")
	}
	delete(s.sessions, hash)
	return nil
}

type fakeGoogle struct {
	calls           int
	nonce, verifier string
	fail            bool
}

func (g *fakeGoogle) AuthURL(state, nonce, verifier string) string {
	g.nonce = nonce
	g.verifier = verifier
	return "https://accounts.google.com/auth?state=" + state
}
func (g *fakeGoogle) Exchange(_ context.Context, code, verifier, nonce string) (Identity, error) {
	g.calls++
	if g.fail || code != "valid" || verifier != g.verifier || nonce != g.nonce {
		return Identity{}, errors.New("invalid identity")
	}
	return Identity{Subject: "google-123", Email: "reader@example.org", Name: "Reader"}, nil
}

func fixture() (*Handler, *memoryStore, *fakeGoogle, *http.ServeMux) {
	store := &memoryStore{sessions: map[string]User{}}
	h := New(Config{ClientID: "client", ClientSecret: "secret", CookieKey: strings.Repeat("k", 32), Origin: "https://artlines.org"}, store)
	google := &fakeGoogle{}
	h.google = google
	mux := http.NewServeMux()
	h.Register(mux)
	return h, store, google, mux
}
func request(mux *http.ServeMux, method, path, origin string, cookies ...*http.Cookie) *httptest.ResponseRecorder {
	r := httptest.NewRequest(method, path, nil)
	if origin != "" {
		r.Header.Set("Origin", origin)
	}
	for _, c := range cookies {
		r.AddCookie(c)
	}
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, r)
	return w
}
func begin(t *testing.T, mux *http.ServeMux) (*http.Cookie, string) {
	t.Helper()
	w := request(mux, "POST", "/api/v1/auth/google/start", "https://artlines.org")
	if w.Code != 303 {
		t.Fatalf("start: %d %s", w.Code, w.Body.String())
	}
	u, _ := url.Parse(w.Header().Get("Location"))
	return w.Result().Cookies()[0], u.Query().Get("state")
}
func TestLoginSessionLogout(t *testing.T) {
	_, store, _, mux := fixture()
	flow, state := begin(t, mux)
	if !flow.Secure || !flow.HttpOnly || flow.SameSite != http.SameSiteLaxMode || flow.Domain != "" || flow.Path != "/" || !strings.HasPrefix(flow.Name, "__Host-") {
		t.Fatal("unsafe flow cookie")
	}
	previous := &http.Cookie{Name: "__Host-artline_session", Value: strings.Repeat("p", 43)}
	store.sessions[hashToken(previous.Value)] = User{ID: "old"}
	w := request(mux, "GET", "/api/v1/auth/google/callback?state="+state+"&code=valid", "", flow, previous)
	if w.Code != 303 || w.Header().Get("Location") != "https://artlines.org/account" || store.logins != 1 {
		t.Fatalf("callback: %d %s", w.Code, w.Header())
	}
	var session *http.Cookie
	for _, c := range w.Result().Cookies() {
		if c.Name == "__Host-artline_session" {
			session = c
		}
	}
	if session == nil || len(session.Value) != 43 || !session.Secure || !session.HttpOnly || session.MaxAge != 2592000 {
		t.Fatal("invalid session cookie")
	}
	if _, ok := store.sessions[session.Value]; ok {
		t.Fatal("raw session token stored")
	}
	if _, ok := store.sessions[hashToken(previous.Value)]; ok {
		t.Fatal("previous session not revoked")
	}
	w = request(mux, "GET", "/api/v1/auth/session", "", session)
	if w.Code != 200 || !strings.Contains(w.Body.String(), "reader@example.org") || w.Header().Get("Cache-Control") != "private, no-store" {
		t.Fatal("session missing or cacheable")
	}
	w = request(mux, "POST", "/api/v1/auth/logout", "https://artlines.org", session)
	if w.Code != 303 || len(store.sessions) != 0 {
		t.Fatal("logout did not revoke session")
	}
	w = request(mux, "GET", "/api/v1/auth/session", "", session)
	if !strings.Contains(w.Body.String(), `"user":null`) {
		t.Fatal("revoked session still active")
	}
}
func TestRejectForgedExpiredAndCancelledLogin(t *testing.T) {
	for _, kind := range []string{"missing", "state", "tampered", "expired", "cancelled", "provider", "database", "missing-code"} {
		t.Run(kind, func(t *testing.T) {
			h, store, google, mux := fixture()
			cookie, state := begin(t, mux)
			code := "valid"
			extra := ""
			switch kind {
			case "missing":
				cookie = &http.Cookie{Name: "unrelated", Value: "value"}
			case "state":
				state = "wrong"
			case "tampered":
				cookie.Value += "changed"
			case "expired":
				now := time.Now().Add(11 * time.Minute)
				h.now = func() time.Time { return now }
			case "cancelled":
				extra = "&error=access_denied"
			case "provider":
				google.fail = true
			case "database":
				store.fail = true
			case "missing-code":
				code = ""
			}
			w := request(mux, "GET", "/api/v1/auth/google/callback?state="+state+"&code="+code+extra, "", cookie)
			if w.Code != 303 || w.Header().Get("Location") != "https://artlines.org/account?error=google_signin" || store.logins != 0 {
				t.Fatal("unsafe callback accepted")
			}
			for _, c := range w.Result().Cookies() {
				if c.Name == "__Host-artline_session" {
					t.Fatal("session issued on failure")
				}
			}
			if kind != "provider" && kind != "database" && google.calls != 0 {
				t.Fatal("exchanged code before validating flow")
			}
		})
	}
}
func TestMutationsRequireSameOrigin(t *testing.T) {
	_, _, _, mux := fixture()
	for _, path := range []string{"google/start", "logout"} {
		for _, origin := range []string{"", "null", "https://evil.example", "https://artlines.org.evil.example"} {
			if w := request(mux, "POST", "/api/v1/auth/"+path, origin); w.Code != 403 {
				t.Fatalf("accepted origin %q", origin)
			}
		}
	}
	if w := request(mux, "GET", "/api/v1/auth/logout", ""); w.Code != 405 {
		t.Fatal("GET logout allowed")
	}
	if w := request(mux, "HEAD", "/api/v1/auth/google/callback", ""); w.Code != 405 {
		t.Fatal("HEAD callback allowed")
	}
}
func TestSessionUnavailableAndDisabled(t *testing.T) {
	h, store, _, mux := fixture()
	store.fail = true
	c := &http.Cookie{Name: "__Host-artline_session", Value: strings.Repeat("x", 43)}
	if w := request(mux, "GET", "/api/v1/auth/session", "", c); w.Code != 503 {
		t.Fatal("database error hidden")
	}
	if w := request(mux, "POST", "/api/v1/auth/logout", "https://artlines.org", c); w.Code != 503 || len(w.Result().Cookies()) != 0 {
		t.Fatal("failed revocation reported as success")
	}
	h.config = Config{}
	if w := request(mux, "GET", "/api/v1/auth/session", "", c); w.Code != 200 || !strings.Contains(w.Body.String(), `"enabled":false`) {
		t.Fatal("disabled state failed")
	}
}

func TestGoogleAuthorizationUsesPKCEAndMinimalScopes(t *testing.T) {
	g := newGoogle("client", "secret", "https://artlines.org")
	u, err := url.Parse(g.AuthURL("state", "nonce", strings.Repeat("v", 43)))
	if err != nil {
		t.Fatal(err)
	}
	q := u.Query()
	if q.Get("code_challenge_method") != "S256" || q.Get("code_challenge") == "" || q.Get("nonce") != "nonce" || q.Get("scope") != "openid email profile" || q.Get("redirect_uri") != "https://artlines.org/api/auth/google/callback" || q.Get("access_type") == "offline" {
		t.Fatal("incorrect OAuth request")
	}
}

func TestLocalDebugNeedsNoGoogleCookiesOrDatabase(t *testing.T) {
	// A nil store/provider deliberately fails if local mode touches either.
	h := New(Config{LocalDebug: true, Origin: "http://localhost:3000"}, nil)
	h.google = nil
	mux := http.NewServeMux()
	h.Register(mux)
	for _, path := range []string{"session", "google/start", "google/callback", "logout"} {
		method := "GET"
		if path == "logout" || path == "google/start" {
			method = "POST"
		}
		r := httptest.NewRequest(method, "/api/v1/auth/"+path, nil)
		r.RemoteAddr = "127.0.0.1:54321"
		r.Header.Set("Origin", "http://localhost:3000")
		w := httptest.NewRecorder()
		mux.ServeHTTP(w, r)
		if len(w.Result().Cookies()) != 0 || w.Header().Get("Cache-Control") != "private, no-store" {
			t.Fatal("local debug issued cookies or became cacheable")
		}
		if path == "session" {
			var session struct {
				LocalDebug  bool `json:"local_debug"`
				AllFeatures bool `json:"all_features"`
				User        User `json:"user"`
			}
			if json.Unmarshal(w.Body.Bytes(), &session) != nil || w.Code != 200 || !session.LocalDebug || !session.AllFeatures || session.User.ID != "local-debug" {
				t.Fatal("local features were not available without sign-in")
			}
		} else if w.Code != 303 || w.Header().Get("Location") != "http://localhost:3000/account" {
			t.Fatal("local mode attempted an external login")
		}
	}
	r := httptest.NewRequest("GET", "/api/v1/auth/session", nil)
	r.RemoteAddr = "203.0.113.10:1234"
	r.Header.Set("X-Forwarded-For", "127.0.0.1")
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, r)
	if w.Code != 403 {
		t.Fatal("remote request gained local privileges through forwarded headers")
	}
	h.config.LocalDebug = false
	r.RemoteAddr = "127.0.0.1:1234"
	w = httptest.NewRecorder()
	mux.ServeHTTP(w, r)
	if w.Code != 200 || !strings.Contains(w.Body.String(), `"user":null`) || strings.Contains(w.Body.String(), `"all_features":true`) {
		t.Fatal("normal mode inherited local member access")
	}
}
