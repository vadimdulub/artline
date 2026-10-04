package httpapi

import (
	"net/http/httptest"
	"testing"
)

func TestArtistDirectoryFilters(t *testing.T) {
	for _, query := range []string{"q=Rembrandt&country=NL&sort=name", "popular=true&women=true&limit=60", "movement=post-impressionism", ""} {
		if _, err := artistDirectoryFilter(httptest.NewRequest("GET", "/api/v1/artists?"+query, nil)); err != nil {
			t.Errorf("valid filter %q: %v", query, err)
		}
	}
	for _, query := range []string{"q=a&q=b", "country=Netherlands", "sort=random", "popular=1", "women=yes", "limit=61", "movement=bad%20slug"} {
		if _, err := artistDirectoryFilter(httptest.NewRequest("GET", "/api/v1/artists?"+query, nil)); err == nil {
			t.Errorf("invalid filter accepted: %q", query)
		}
	}
}
func TestArtistCatalogueFilters(t *testing.T) {
	f, err := artistWorksFilter(httptest.NewRequest("GET", "/api/v1/artists/rembrandt/works?q=self&museum=the-met&work_type=painting", nil))
	if err != nil || f.Query != "self" || f.Museum != "the-met" || f.WorkType != "painting" {
		t.Fatalf("filters lost: %+v %v", f, err)
	}
	for _, query := range []string{"q=a&q=b", "museum=bad%20slug", "work_type=painting%27", "work_type=painting&work_type=print"} {
		if _, err := artistWorksFilter(httptest.NewRequest("GET", "/api/v1/artists/rembrandt/works?"+query, nil)); err == nil {
			t.Errorf("invalid filter accepted: %q", query)
		}
	}
}
