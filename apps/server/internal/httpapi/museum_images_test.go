package httpapi

import (
	"net/http/httptest"
	"testing"
)

func TestMuseumGalleryFilters(t *testing.T) {
	for _, query := range []string{"", "sort=images", "sort=year", "sort=title", "selection=museum&sort=curated", "image_only=1&limit=60", "image_only=0&limit=1", "start=1800&end=1900", "unknown_date=1"} {
		t.Run("valid-"+query, func(t *testing.T) {
			if _, e := museumFilter(httptest.NewRequest("GET", "/api/v1/museums/musee-du-louvre/works?"+query, nil)); e != nil {
				t.Fatal(e)
			}
		})
	}
	for _, query := range []string{"sort=anything", "image_only=true", "image_only=-1", "limit=0", "limit=61", "limit=all", "start=1900&end=1800", "unknown_date=1&start=1800", "start=unknown", "display=holding", "selection=top100"} {
		t.Run("invalid-"+query, func(t *testing.T) {
			if _, e := museumFilter(httptest.NewRequest("GET", "/api/v1/museums/musee-du-louvre/works?"+query, nil)); e == nil {
				t.Fatal("invalid filter accepted")
			}
		})
	}
}
