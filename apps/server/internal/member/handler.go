package member

import (
	"context"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"net"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"
)

type Config struct {
	ClientID, ClientSecret, CookieKey, Origin string
	LocalDebug                                bool
}
type Handler struct {
	config Config
	store  Store
	google Google
	now    func() time.Time
}
type flow struct {
	State, Nonce, Verifier string
	Expires                int64
	ReturnTo               string `json:",omitempty"`
}

var museumRecordPath = regexp.MustCompile(`^/museums(?:/([a-z0-9]+(?:[-_][a-z0-9]+)*))?$`)

var painterRecordPath = regexp.MustCompile(`^/artists/([a-z0-9]+(?:[-_][a-z0-9]+)*)(?:/works/[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12})?$`)

func memberReturnTo(value string) string {
	if len(value) > 768 {
		return ""
	}
	for _, c := range value {
		if c < '!' || c > '~' || c == '\\' {
			return ""
		}
	}
	path, _, _ := strings.Cut(value, "?")
	path, _, _ = strings.Cut(path, "#")
	switch path {
	case "/", "/artists", "/artworks", "/all", "/bookmarks", "/books", "/events":
		return value
	}
	match := painterRecordPath.FindStringSubmatch(path)
	if match == nil {
		match = museumRecordPath.FindStringSubmatch(path)
	}
	if match == nil || len(match[1]) > 100 {
		return ""
	}
	return value
}

func New(cfg Config, store Store) *Handler {
	return &Handler{config: cfg, store: store, google: newGoogle(cfg.ClientID, cfg.ClientSecret, cfg.Origin), now: time.Now}
}

func (h *Handler) Register(mux *http.ServeMux) {
	mux.HandleFunc("POST /api/v1/auth/google/start", h.wrap(h.start))
	mux.HandleFunc("GET /api/v1/auth/google/callback", h.wrap(h.callback))
	mux.HandleFunc("GET /api/v1/auth/session", h.wrap(h.session))
	mux.HandleFunc("POST /api/v1/auth/logout", h.wrap(h.logout))
}

func (h *Handler) enabled() bool {
	return h.config.ClientID != "" && h.config.ClientSecret != "" && len(h.config.CookieKey) >= 32 && h.config.Origin != ""
}
func (h *Handler) secure() bool { return strings.HasPrefix(h.config.Origin, "https://") }
func (h *Handler) cookieName(kind string) string {
	if h.secure() {
		return "__Host-artline_" + kind
	}
	return "artline_" + kind
}
func (h *Handler) cookie(w http.ResponseWriter, kind, value string, age int) {
	expires := h.now().Add(time.Duration(age) * time.Second)
	if age < 0 {
		expires = time.Unix(1, 0)
	}
	http.SetCookie(w, &http.Cookie{Name: h.cookieName(kind), Value: value, Path: "/", MaxAge: age, Expires: expires, HttpOnly: true, Secure: h.secure(), SameSite: http.SameSiteLaxMode})
}
func (h *Handler) wrap(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "private, no-store")
		w.Header().Set("Referrer-Policy", "no-referrer")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		if r.Method == http.MethodHead {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		if h.config.LocalDebug {
			host, _, err := net.SplitHostPort(r.RemoteAddr)
			if err != nil || !net.ParseIP(host).IsLoopback() {
				http.Error(w, "Local debug is only available on loopback.", http.StatusForbidden)
				return
			}
		}
		if r.Method == http.MethodPost && (r.Header.Get("Origin") != h.config.Origin || r.Header.Get("Sec-Fetch-Site") == "cross-site") {
			http.Error(w, "This request must come from Artline.", http.StatusForbidden)
			return
		}
		if h.config.LocalDebug {
			if r.URL.Path == "/api/v1/auth/session" {
				w.Header().Set("Content-Type", "application/json")
				json.NewEncoder(w).Encode(struct {
					Enabled     bool `json:"enabled"`
					LocalDebug  bool `json:"local_debug"`
					AllFeatures bool `json:"all_features"`
					User        User `json:"user"`
				}{false, true, true, User{ID: "local-debug", Name: "Local explorer", Email: ""}})
			} else {
				destination := "/artists"
				if target := memberReturnTo(r.URL.Query().Get("return_to")); target != "" {
					destination = target
				}
				if r.URL.Path == "/api/v1/auth/logout" {
					destination = "/account"
				}
				http.Redirect(w, r, h.config.Origin+destination, http.StatusSeeOther)
			}
			return // No Google call, cookie, or database account/session writes.
		}
		if !h.enabled() && r.URL.Path != "/api/v1/auth/session" {
			http.Error(w, "Google sign-in is unavailable.", http.StatusServiceUnavailable)
			return
		}
		ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		defer cancel()
		next(w, r.WithContext(ctx))
	}
}
func randomToken() string {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	return base64.RawURLEncoding.EncodeToString(b)
}
func hashToken(token string) string {
	sum := sha256.Sum256([]byte(token))
	return hex.EncodeToString(sum[:])
}
func (h *Handler) sessionHash(r *http.Request) string {
	c, err := r.Cookie(h.cookieName("session"))
	if err != nil || len(c.Value) != 43 {
		return ""
	}
	return hashToken(c.Value)
}
func (h *Handler) sign(payload string) string {
	mac := hmac.New(sha256.New, []byte(h.config.CookieKey))
	mac.Write([]byte(payload))
	return base64.RawURLEncoding.EncodeToString(mac.Sum(nil))
}
func (h *Handler) start(w http.ResponseWriter, r *http.Request) {
	f := flow{State: randomToken(), Nonce: randomToken(), Verifier: randomToken(), Expires: h.now().Add(10 * time.Minute).Unix(), ReturnTo: memberReturnTo(r.URL.Query().Get("return_to"))}
	raw, _ := json.Marshal(f)
	payload := base64.RawURLEncoding.EncodeToString(raw)
	if len(payload)+44 > 2048 {
		// Unusually escaped query strings must not create an unreadable flow cookie.
		f.ReturnTo = ""
		raw, _ = json.Marshal(f)
		payload = base64.RawURLEncoding.EncodeToString(raw)
	}
	h.cookie(w, "oauth", payload+"."+h.sign(payload), 600)
	http.Redirect(w, r, h.google.AuthURL(f.State, f.Nonce, f.Verifier), http.StatusSeeOther)
}
func (h *Handler) readFlow(r *http.Request) (flow, error) {
	var f flow
	c, err := r.Cookie(h.cookieName("oauth"))
	if err != nil {
		return f, err
	}
	payload, sig, ok := strings.Cut(c.Value, ".")
	if !ok || len(c.Value) > 2048 || !hmac.Equal([]byte(sig), []byte(h.sign(payload))) {
		return f, errors.New("invalid flow")
	}
	raw, err := base64.RawURLEncoding.DecodeString(payload)
	if err != nil {
		return f, err
	}
	if err = json.Unmarshal(raw, &f); err != nil {
		return f, err
	}
	if f.Expires <= h.now().Unix() || len(f.State) != 43 || len(f.Nonce) != 43 || len(f.Verifier) != 43 || subtle.ConstantTimeCompare([]byte(f.State), []byte(r.URL.Query().Get("state"))) != 1 {
		return f, errors.New("expired or mismatched flow")
	}
	return f, nil
}
func (h *Handler) callback(w http.ResponseWriter, r *http.Request) {
	f, err := h.readFlow(r)
	h.cookie(w, "oauth", "", -1)
	if err != nil {
		h.failed(w, r, "")
		return
	}
	if r.URL.Query().Get("error") != "" || r.URL.Query().Get("code") == "" {
		h.failed(w, r, f.ReturnTo)
		return
	}
	identity, err := h.google.Exchange(r.Context(), r.URL.Query().Get("code"), f.Verifier, f.Nonce)
	if err != nil {
		h.failed(w, r, f.ReturnTo)
		return
	}
	token := randomToken()
	if err = h.store.Login(r.Context(), identity, hashToken(token), h.sessionHash(r), h.now().Add(30*24*time.Hour)); err != nil {
		h.failed(w, r, f.ReturnTo)
		return
	}
	h.cookie(w, "session", token, 30*24*60*60)
	destination := memberReturnTo(f.ReturnTo)
	if destination == "" {
		destination = "/artists"
	}
	http.Redirect(w, r, h.config.Origin+destination, http.StatusSeeOther)
}
func (h *Handler) failed(w http.ResponseWriter, r *http.Request, returnTo string) {
	query := url.Values{"error": {"google_signin"}}
	if destination := memberReturnTo(returnTo); destination != "" {
		query.Set("return_to", destination)
	}
	http.Redirect(w, r, h.config.Origin+"/account?"+query.Encode(), http.StatusSeeOther)
}
func (h *Handler) session(w http.ResponseWriter, r *http.Request) {
	var user *User
	if h.enabled() && h.sessionHash(r) != "" {
		found, err := h.store.Session(r.Context(), h.sessionHash(r))
		if err == nil {
			user = &found
		} else if errors.Is(err, ErrNoSession) {
			h.cookie(w, "session", "", -1)
		} else {
			http.Error(w, "Account is temporarily unavailable.", http.StatusServiceUnavailable)
			return
		}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(struct {
		Enabled bool  `json:"enabled"`
		User    *User `json:"user"`
	}{h.enabled(), user})
}
func (h *Handler) logout(w http.ResponseWriter, r *http.Request) {
	if hash := h.sessionHash(r); hash != "" {
		if err := h.store.Logout(r.Context(), hash); err != nil {
			http.Error(w, "Sign-out failed. Please retry.", http.StatusServiceUnavailable)
			return
		}
	}
	h.cookie(w, "session", "", -1)
	h.cookie(w, "oauth", "", -1)
	http.Redirect(w, r, h.config.Origin+"/account", http.StatusSeeOther)
}
