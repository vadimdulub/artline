package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/config"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestPreparedGuidesArePublicAndReadOnly(t *testing.T) {
	handler := New(config.Config{}, nil)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, httptest.NewRequest("GET", "/api/v1/guides?institution=musee-du-louvre", nil))
	if w.Code != 200 || !strings.Contains(w.Body.String(), `"href":"/guides/louvre"`) {
		t.Fatal("public guide missing", w.Code, w.Body.String())
	}
	for _, method := range []string{"POST", "PUT", "PATCH", "DELETE"} {
		w = httptest.NewRecorder()
		handler.ServeHTTP(w, httptest.NewRequest(method, "/api/v1/guides?institution=musee-du-louvre", strings.NewReader(`{"title":"Changed"}`)))
		if w.Code != 405 {
			t.Fatalf("%s accepted: %d", method, w.Code)
		}
	}
}
