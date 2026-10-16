package httpapi

import (
	"github.com/vadimdulub/artline/apps/server/internal/guides"
	"net/http"
)

func (api *API) guides(w http.ResponseWriter, r *http.Request) {
	page, err := guides.Default.Search(r.URL.Query())
	if err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_GUIDE_FILTERS", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, page)
}
