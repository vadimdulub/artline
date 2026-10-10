package member

import (
	"context"
	"encoding/json"
	"errors"
	"net"
	"net/http"
	"strings"
	"time"
)

func protectedCataloguePath(path string) bool {
	return path == "/api/v1/museums" || strings.HasPrefix(path, "/api/v1/museums/")
}

// CatalogueAccess must run BEFORE the shared catalogue cache and admission queue.
// Artist pages, timeline previews and individual artworks remain public.
func (h *Handler) CatalogueAccess(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !protectedCataloguePath(r.URL.Path) || (r.Method != http.MethodGet && r.Method != http.MethodHead) {
			next.ServeHTTP(w, r)
			return
		}
		if _, ok := h.authorize(w, r); ok {
			next.ServeHTTP(w, r)
		}

	})
}

func (h *Handler) authorize(w http.ResponseWriter, r *http.Request) (User, bool) {
	w.Header().Set("Cache-Control", "private, no-store")
	if h.config.LocalDebug {
		host, _, err := net.SplitHostPort(r.RemoteAddr)
		if err != nil || !net.ParseIP(host).IsLoopback() {
			accessError(w, 403, "LOCAL_ONLY", "Local debug is only available on loopback.")
			return User{}, false
		}
		return User{ID: "local-debug", Name: "Local explorer"}, true
	}
	if h.enabled() {
		if hash := h.sessionHash(r); hash != "" {
			ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
			user, err := h.store.Session(ctx, hash)
			cancel()
			if err == nil && user.ID != "" {
				return user, true
			}
			if err != nil && !errors.Is(err, ErrNoSession) {
				accessError(w, 503, "SESSION_UNAVAILABLE", "Sign-in is temporarily unavailable.")
				return User{}, false
			}
		}
	}
	accessError(w, 401, "AUTH_REQUIRED", "Sign in to use this feature.")
	return User{}, false
}

func accessError(w http.ResponseWriter, status int, code, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]any{"error": map[string]string{"code": code, "message": message}})
}
