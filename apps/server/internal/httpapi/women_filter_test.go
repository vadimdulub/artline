package httpapi

import (
	"net/http/httptest"
	"testing"

	"github.com/vadimdulub/artline/apps/server/internal/config"
)

func TestWomenFilterValidation(t *testing.T) {
	for _, tc := range []struct {
		values []string
		want   bool
		valid  bool
	}{
		{nil, false, true}, {[]string{"true"}, true, true}, {[]string{"false"}, false, true},
		{[]string{""}, false, false}, {[]string{"yes"}, false, false}, {[]string{"true,false"}, false, false}, {[]string{"true", "true"}, false, false},
	} {
		got, err := parseWomen(tc.values)
		if got != tc.want || (err == nil) != tc.valid {
			t.Fatalf("parseWomen(%v) = %v, %v", tc.values, got, err)
		}
	}
	handler := New(config.Config{}, nil)
	for _, route := range []string{"timeline", "timeline/facets", "painters/options"} {
		response := httptest.NewRecorder()
		handler.ServeHTTP(response, httptest.NewRequest("GET", "/api/v1/"+route+"?women=true&women=false", nil))
		if response.Code != 400 {
			t.Fatalf("%s did not reject duplicate gender filter before database access: %d", route, response.Code)
		}
	}
}
