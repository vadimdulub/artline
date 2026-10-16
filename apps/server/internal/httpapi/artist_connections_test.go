package httpapi

import (
	"net/http/httptest"
	"testing"
)

func TestArtistConnectionsRejectsInvalidFiltersBeforeRead(t *testing.T) {
	api := &API{}
	for _, query := range []string{"", "direction=both", "direction=incoming&direction=outgoing", "direction=incoming&cursor=a&cursor=b"} {
		w := httptest.NewRecorder()
		r := httptest.NewRequest("GET", "/api/v1/artists/artist/connections?"+query, nil)
		r.SetPathValue("slug", "artist")
		api.artistConnections(w, r)
		if w.Code != 400 {
			t.Fatalf("%s: %d", query, w.Code)
		}
	}
	if !cacheableCataloguePath("/api/v1/artists/artist/connections") {
		t.Fatal("connections must use the revision-keyed catalogue read cache and budget")
	}
}
