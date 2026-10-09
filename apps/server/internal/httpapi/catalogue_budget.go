package httpapi

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"
)

func catalogueReadPath(path string) bool {
	if !strings.HasPrefix(path, "/api/v1/") {
		return false
	}
	section, _, _ := strings.Cut(strings.TrimPrefix(path, "/api/v1/"), "/")
	switch section {
	case "artists", "artworks", "museums", "timeline", "painters", "catalogue", "seo", "atlas", "books", "events":
		return true
	}
	return false
}

func catalogueReadBudget(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet || !catalogueReadPath(r.URL.Path) {
			next.ServeHTTP(w, r)
			return
		}
		budget := 8 * time.Second
		if r.URL.Path == "/api/v1/atlas" {
			budget = 25 * time.Second
		}
		ctx, cancel := context.WithTimeout(r.Context(), budget)
		defer cancel()
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func catalogueBusy(w http.ResponseWriter) {
	w.Header().Set("Retry-After", "1")
	writeError(w, http.StatusServiceUnavailable, "CATALOGUE_BUSY", "The catalogue is busy. Please try again shortly.")
}

// Keep a bounded number of cache misses in flight. Hits bypass this gate, while
// four of the eight pool connections remain available to snapshots/member reads.
// Neither a crawler's identity nor publication status changes admission.
func catalogueAdmission(next http.Handler, activeLimit, waitingLimit int, maxWait time.Duration) http.Handler {
	active, waiting := make(chan struct{}, activeLimit), make(chan struct{}, waitingLimit)
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet || !catalogueReadPath(r.URL.Path) {
			next.ServeHTTP(w, r)
			return
		}
		start := time.Now()
		select {
		case active <- struct{}{}:
		default:
			select {
			case waiting <- struct{}{}:
			default:
				catalogueBusy(w)
				return
			}
			timer := time.NewTimer(maxWait)
			acquired := false
			select {
			case active <- struct{}{}:
				acquired = true
			case <-timer.C:
			case <-r.Context().Done():
			}
			timer.Stop()
			<-waiting
			if !acquired {
				catalogueBusy(w)
				return
			}
		}
		defer func() { <-active }()
		w.Header().Add("Server-Timing", fmt.Sprintf("catalogue_queue;dur=%.2f", float64(time.Since(start).Microseconds())/1000))
		if r.Context().Err() != nil {
			catalogueBusy(w)
			return
		}
		next.ServeHTTP(w, r)
	})
}
