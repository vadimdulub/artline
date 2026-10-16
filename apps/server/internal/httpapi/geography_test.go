package httpapi

import (
	"net/http/httptest"
	"strings"
	"testing"
)

func TestMapInputBounds(t *testing.T) {
	for _, q := range []string{"kind=invalid&id=abc", "kind=artist&id=bad", "kind=book&id=x&id=x", "kind=book&id=x&start=1900&end=1800", "kind=book&id=x&end=oops", "kind=book" + strings.Repeat("&id=x", 81)} {
		w := httptest.NewRecorder()
		(&API{}).mapLocations(w, httptest.NewRequest("GET", "/api/v1/map/locations?"+q, nil))
		if w.Code != 400 {
			t.Fatalf("%q: %d", q, w.Code)
		}
	}
}
func TestMapDatabaseFailureIsNotAnEmptyMap(t *testing.T) {
	w := httptest.NewRecorder()
	(&API{}).mapLocations(w, httptest.NewRequest("GET", "/api/v1/map/locations?kind=book&id=wd-q150827", nil))
	if w.Code != 500 {
		t.Fatal(w.Code)
	}
}
