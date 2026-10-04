package atlas

import (
	"net/url"
	"strconv"
)

// Missing filters in a shared preset URL receive its reviewed starting choices.
// An edited view is explicit, including deliberately empty creator/country lists.
func ApplyStartingFilters(q url.Values, p Preset) {
	if q.Get("preset_filters") == "custom" {
		return
	}
	if !q.Has("country") && !q.Has("continent") && !q.Has("region") && !q.Has("artwork_country") && !q.Has("artwork_region") && len(p.StartingCountries) > 0 {
		q["country"] = append([]string(nil), p.StartingCountries...)
		q.Set("country_scope", "artwork")
	}
	if !q.Has("creator") && !q.Has("artwork_painter") && !q.Has("book_author") && len(p.StartingCreators) > 0 {
		q["creator"] = append([]string(nil), p.StartingCreators...)
	}
	if !q.Has("highlights") {
		q.Set("highlights", strconv.FormatBool(p.StartingHighlights))
	}
}
