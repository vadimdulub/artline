package member

import (
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
)

func beginPainter(t *testing.T, mux *http.ServeMux, destination string) (*http.Cookie, string) {
	t.Helper()
	w := request(mux, "POST", "/api/v1/auth/google/start?"+url.Values{"return_to": {destination}}.Encode(), "https://artlines.org")
	if w.Code != http.StatusSeeOther {
		t.Fatalf("start returned %d", w.Code)
	}
	u, _ := url.Parse(w.Header().Get("Location"))
	return w.Result().Cookies()[0], u.Query().Get("state")
}

func TestPainterLoginDestination(t *testing.T) {
	for _, destination := range []string{
		"/artists/claude-monet",
		"/museums",
		"/bookmarks?kind=artwork",
		"/all?itemType=artwork&item=11111111-1111-4111-8111-111111111111",
		"/museums/the-met?artist=monet&artist=giotto#collection",
		"/artists/artist_import?catalogue=all&art_q=Water+lilies&art_year=1900#works-painter",
		"/artists/giotto/works/11111111-1111-4111-8111-111111111111?art_images=false",
	} {
		t.Run(destination, func(t *testing.T) {
			_, store, _, mux := fixture()
			cookie, state := beginPainter(t, mux, destination)
			// The callback's query must not replace the signed destination.
			w := request(mux, "GET", "/api/v1/auth/google/callback?state="+state+"&code=valid&return_to=https://evil.example", "", cookie)
			if w.Code != 303 || w.Header().Get("Location") != "https://artlines.org"+destination || store.logins != 1 {
				t.Fatalf("did not return to painter: %d %s", w.Code, w.Header().Get("Location"))
			}
		})
	}
}

func TestPainterLoginRejectsUnsafeDestinations(t *testing.T) {
	for _, destination := range []string{
		"/museums/../account", "/museums/%2Fexample", "/museums/" + strings.Repeat("x", 101), "https://evil.example", "//evil.example/artists/monet", "/artists/../account",
		"/artists/%2e%2e/account", "/artists/monet/extra", "/artists/monet\\evil",
		"/artists/monet\n", "/artists/monet?x=\r\nLocation:evil", "/api/auth/logout",
		"/account?return_to=/artists/monet", "/artists/" + strings.Repeat("x", 101),
		"/artists/monet?q=" + strings.Repeat("x", 768),
	} {
		t.Run(destination, func(t *testing.T) {
			_, _, _, mux := fixture()
			cookie, state := beginPainter(t, mux, destination)
			w := request(mux, "GET", "/api/v1/auth/google/callback?state="+state+"&code=valid", "", cookie)
			if w.Code != 303 || w.Header().Get("Location") != "https://artlines.org/artists" {
				t.Fatal("unsafe destination accepted")
			}
		})
	}
}

func TestPainterLoginFailureKeepsDestinationForRetry(t *testing.T) {
	for _, failure := range []string{"cancelled", "provider", "database"} {
		t.Run(failure, func(t *testing.T) {
			_, store, google, mux := fixture()
			destination := "/artists/monet?art_year=1900&catalogue=all"
			cookie, state := beginPainter(t, mux, destination)
			extra := ""
			switch failure {
			case "cancelled":
				extra = "&error=access_denied"
			case "provider":
				google.fail = true
			case "database":
				store.fail = true
			}
			w := request(mux, "GET", "/api/v1/auth/google/callback?state="+state+"&code=valid"+extra, "", cookie)
			u, _ := url.Parse(w.Header().Get("Location"))
			if w.Code != 303 || u.Path != "/account" || u.Query().Get("error") != "google_signin" || u.Query().Get("return_to") != destination || store.logins != 0 {
				t.Fatal("failed login lost its painter destination")
			}
		})
	}
}

func TestPainterDestinationCannotBeChangedInFlowCookie(t *testing.T) {
	_, store, google, mux := fixture()
	cookie, state := beginPainter(t, mux, "/artists/monet")
	payload, signature, _ := strings.Cut(cookie.Value, ".")
	raw, _ := base64.RawURLEncoding.DecodeString(payload)
	var f flow
	if err := json.Unmarshal(raw, &f); err != nil {
		t.Fatal(err)
	}
	f.ReturnTo = "/artists/giotto"
	raw, _ = json.Marshal(f)
	cookie.Value = base64.RawURLEncoding.EncodeToString(raw) + "." + signature
	w := request(mux, "GET", "/api/v1/auth/google/callback?state="+state+"&code=valid", "", cookie)
	if w.Header().Get("Location") != "https://artlines.org/account?error=google_signin" || store.logins != 0 || google.calls != 0 {
		t.Fatal("tampered return destination was accepted")
	}
}

func TestOversizedEscapedDestinationDoesNotBreakLogin(t *testing.T) {
	_, _, _, mux := fixture()
	cookie, state := beginPainter(t, mux, "/artists/monet?q="+strings.Repeat("&", 700))
	if len(cookie.Value) > 2048 {
		t.Fatal("flow cookie cannot be read")
	}
	w := request(mux, "GET", "/api/v1/auth/google/callback?state="+state+"&code=valid", "", cookie)
	if w.Header().Get("Location") != "https://artlines.org/artists" {
		t.Fatal("oversized destination prevented login")
	}
}

func TestLocalDebugPainterDestination(t *testing.T) {
	h := New(Config{Origin: "http://localhost:3000", LocalDebug: true}, nil)
	h.google = nil
	mux := http.NewServeMux()
	h.Register(mux)
	for _, address := range []string{"127.0.0.1:1234", "203.0.113.10:1234"} {
		r := httptest.NewRequest("POST", "/api/v1/auth/google/start?return_to=%2Fartists%2Fmonet", nil)
		r.Header.Set("Origin", "http://localhost:3000")
		r.RemoteAddr = address
		w := httptest.NewRecorder()
		mux.ServeHTTP(w, r)
		if address == "127.0.0.1:1234" {
			if w.Code != 303 || w.Header().Get("Location") != "http://localhost:3000/artists/monet" || len(w.Result().Cookies()) != 0 {
				t.Fatal("local preview did not return to painter without a session write")
			}
		} else if w.Code != 403 {
			t.Fatal("remote request bypassed local-debug guard")
		}
	}
}
