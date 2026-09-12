package ingest

import (
	"context"
	"fmt"
	"net/url"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

type Work struct {
	SourceSnapshotAt                              time.Time
	FetchError                                    string
	ID, Source, Title, URL, APIURL, Accession     string
	ArtistQID, ArtistName                         string
	ArtistBirth, ArtistDeath                      *int
	First, Last                                   *int
	Date, Precision, Type, Medium, Dimensions     string
	Highlight                                     bool
	SelectionKind                                 string // museum designation or owner-selected museum holding
	SelectionURL, SelectionReason                 string
	ImageURL, Rights, Credit, Copyright           string
	ImageSourceURL, ImagePolicyURL, ImageProvider string
	Raw                                           map[string]any
}

func (w Work) Eligible() string {
	if w.FetchError != "" {
		return "metadata_fetch_failed"
	}
	if w.SelectionKind != "" && w.SelectionKind != "museum" && w.SelectionKind != "owner" {
		return "invalid_selection_kind"
	}
	if !w.Highlight && !(w.SelectionKind == "owner" && reviewedMuseumURL(w.Source, w.URL) && w.SelectionReason != "" && w.SelectionURL == w.URL) {
		return "not_museum_highlight"
	}
	if w.Type == "" {
		return "excluded_object_type"
	}
	if catalog.CreationScope(w.First, w.Last, w.Precision) != "eligible" {
		return "creation_" + catalog.CreationScope(w.First, w.Last, w.Precision)
	}
	if w.URL == "" || w.ID == "" || w.Title == "" {
		return "missing_identity"
	}
	idPattern := `^[0-9]{1,12}$`
	if w.Source == "prado" {
		idPattern = `^P[0-9]{6}$`
	} else if _, ok := reviewedMuseums[w.Source]; ok {
		idPattern = `^Q[1-9][0-9]*$`
	}
	if !regexp.MustCompile(idPattern).MatchString(w.ID) {
		return "invalid_source_identity"
	}
	u, err := url.Parse(w.URL)
	if err != nil || u.Scheme != "https" || u.User != nil || u.Port() != "" {
		return "invalid_official_link"
	}
	switch w.Source {
	case "uffizi", "mam":
		if !reviewedMuseumURL(w.Source, w.URL) || !reviewedMuseumSelectionURL(w.Source, w.SelectionURL) || w.SelectionReason == "" {
			return "invalid_official_link"
		}
	case "prado":
		if u.Hostname() != "www.museodelprado.es" || !strings.HasPrefix(u.Path, "/en/the-collection/art-work/") || w.SelectionReason == "" || !pradoSelectionURL(w.SelectionURL) {
			return "invalid_official_link"
		}
	case "met":
		if u.Hostname() != "www.metmuseum.org" || u.Path != "/art/collection/search/"+w.ID {
			return "invalid_official_link"
		}
	case "cleveland":
		if (u.Hostname() != "clevelandart.org" && u.Hostname() != "www.clevelandart.org") || !strings.HasPrefix(u.Path, "/art/") {
			return "invalid_official_link"
		}
	case "aic":
		if u.Hostname() != "www.artic.edu" || u.Path != "/artworks/"+w.ID {
			return "invalid_official_link"
		}
	default:
		return "unapproved_source"
	}
	return "eligible"
}
func (w Work) ImageAllowed() bool {
	if w.Eligible() != "eligible" || w.ImageURL == "" || strings.TrimSpace(w.Copyright) != "" {
		return false
	}
	if w.Source == "prado" {
		return pradoImageAllowed(w)
	}
	if w.Rights != "cc0" {
		return false
	}
	u, e := url.Parse(w.ImageURL)
	if e != nil {
		return false
	}
	switch w.Source {
	case "met":
		return u.Scheme == "https" && u.Hostname() == "images.metmuseum.org"
	case "cleveland":
		return u.Scheme == "https" && u.Hostname() == "openaccess-cdn.clevelandart.org"
	case "aic":
		return u.Scheme == "https" && u.Hostname() == "www.artic.edu" && strings.HasPrefix(u.Path, "/iiif/2/")
	}
	return false
}
func value(m map[string]any, k string) string { v, _ := m[k].(string); return v }
func yes(m map[string]any, k string) bool     { v, _ := m[k].(bool); return v }
func number(m map[string]any, k string) *int {
	if n, ok := m[k].(float64); ok {
		return integer(strconv.FormatFloat(n, 'f', -1, 64))
	}
	return integer(value(m, k))
}
func idOf(m map[string]any, k string) string {
	if n, ok := m[k].(float64); ok {
		return strconv.FormatFloat(n, 'f', 0, 64)
	}
	return value(m, k)
}
func workType(s string) string {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "painting", "paintings":
		return "painting"
	case "fresco":
		return "fresco"
	case "drawing", "drawings":
		return "drawing"
	case "watercolor", "watercolour", "watercolors":
		return "watercolor"
	case "print", "prints":
		return "print"
	case "manuscript illumination":
		return "manuscript_illumination"
	}
	return ""
}

func NormalizeMet(m map[string]any) Work {
	w := Work{Source: "met", ID: idOf(m, "objectID"), Title: value(m, "title"), URL: value(m, "objectURL"),
		Accession: value(m, "accessionNumber"), ArtistName: value(m, "artistDisplayName"), ArtistBirth: number(m, "artistBeginDate"), ArtistDeath: number(m, "artistEndDate"),
		First: number(m, "objectBeginDate"), Last: number(m, "objectEndDate"), Date: value(m, "objectDate"), Type: workType(value(m, "classification")),
		Medium: value(m, "medium"), Dimensions: value(m, "dimensions"), Highlight: yes(m, "isHighlight"),
		ImageURL: value(m, "primaryImageSmall"), Credit: value(m, "creditLine"), Copyright: value(m, "rightsAndReproduction"), Raw: m}
	if w.ImageURL == "" {
		w.ImageURL = value(m, "primaryImage")
	}
	if strings.TrimSpace(value(m, "artistPrefix")) != "" || strings.TrimSpace(value(m, "artistSuffix")) != "" {
		w.ArtistName = ""
		w.ArtistBirth = nil
	} else {
		u, e := url.Parse(value(m, "artistWikidata_URL"))
		if e == nil && u.Hostname() == "www.wikidata.org" {
			w.ArtistQID = strings.TrimPrefix(u.Path, "/wiki/")
		}
	}
	w.APIURL = "https://collectionapi.metmuseum.org/public/collection/v1/objects/" + w.ID
	w.SelectionURL = w.APIURL
	w.SelectionReason = "The Met designates this object isHighlight=true. This is not a current-display assertion."
	if yes(m, "isPublicDomain") {
		w.Rights = "cc0"
	}
	w.Precision = catalog.SourceDatePrecision(w.Date, w.First, w.Last)
	return w
}

func (c *Client) Met(ctx context.Context, progress func(string)) ([]Work, error) {
	seen := map[int]bool{}
	var ids []int
	for _, department := range []string{"11", "6", "21", "9", "1"} {
		for _, q := range []string{"painting", "print", "drawing"} {
			for offset := 0; offset < 2000; offset += 100 {
				u := "https://collectionapi.metmuseum.org/public/collection/v1.1/search?" + url.Values{"q": {q}, "isHighlight": {"true"}, "departmentId": {department}, "dateBegin": {"1100"}, "dateEnd": {"1970"}, "limit": {"100"}, "offset": {strconv.Itoa(offset)}}.Encode()
				var page struct {
					Total int   `json:"total"`
					IDs   []int `json:"objectIDs"`
				}
				if _, e := c.JSON(ctx, u, &page); e != nil {
					return nil, e
				}
				if page.Total > 2000 {
					return nil, fmt.Errorf("Met highlight result exceeded safety bound")
				}
				for _, id := range page.IDs {
					if !seen[id] {
						seen[id] = true
						ids = append(ids, id)
					}
				}
				if offset+len(page.IDs) >= page.Total {
					break
				}
				if len(page.IDs) == 0 {
					return nil, fmt.Errorf("Met pagination stopped early")
				}
			}
		}
	}
	if len(ids) == 0 || len(ids) > 2000 {
		return nil, fmt.Errorf("Met discovery returned unexpected count %d; inspect API filters", len(ids))
	}
	sort.Ints(ids)
	var out []Work
	consecutiveFailures := 0
	for i, id := range ids {
		var m map[string]any
		if _, e := c.JSON(ctx, fmt.Sprintf("https://collectionapi.metmuseum.org/public/collection/v1/objects/%d", id), &m); e != nil {
			out = append(out, Work{Source: "met", ID: strconv.Itoa(id), FetchError: e.Error(), Raw: map[string]any{"fetch_error": e.Error()}})
			consecutiveFailures++
			progress(fmt.Sprintf("Met object %d unavailable; recorded for retry", id))
			if consecutiveFailures >= 3 || ctx.Err() != nil {
				return out, fmt.Errorf("Met paused after consecutive request failures: %w", e)
			}
			continue
		}
		consecutiveFailures = 0
		work := NormalizeMet(m)
		work.SourceSnapshotAt = c.snapshotTime(work.APIURL)
		out = append(out, work)
		if i%25 == 0 {
			progress(fmt.Sprintf("Met highlight metadata: %d/%d", i+1, len(ids)))
		}
	}
	return out, nil
}

func NormalizeCleveland(m map[string]any) Work {
	w := Work{Source: "cleveland", ID: idOf(m, "id"), Title: value(m, "title"), URL: value(m, "url"), Accession: value(m, "accession_number"),
		First: number(m, "creation_date_earliest"), Last: number(m, "creation_date_latest"), Date: value(m, "creation_date"), Type: workType(value(m, "type")),
		Medium: value(m, "technique"), Dimensions: value(m, "measurements"), Highlight: yes(m, "is_highlight"), Credit: value(m, "creditline"), Copyright: value(m, "copyright"), Raw: m}
	creators, _ := m["creators"].([]any)
	if len(creators) == 1 {
		a, _ := creators[0].(map[string]any)
		if value(a, "qualifier") == "" && value(a, "extent") == "" && value(a, "role") == "artist" {
			w.ArtistName = strings.TrimSpace(strings.Split(value(a, "description"), " (")[0])
			w.ArtistBirth = number(a, "birth_year")
			w.ArtistDeath = number(a, "death_year")
		}
	}
	if images, ok := m["images"].(map[string]any); ok {
		if web, ok := images["web"].(map[string]any); ok {
			w.ImageURL = value(web, "url")
		}
	}
	if value(m, "share_license_status") == "CC0" {
		w.Rights = "cc0"
	}
	w.APIURL = "https://openaccess-api.clevelandart.org/api/artworks/" + w.ID
	w.SelectionURL = w.APIURL
	w.SelectionReason = "Cleveland Museum of Art designates this object is_highlight=true. This is not a current-display assertion."
	w.Precision = catalog.SourceDatePrecision(w.Date, w.First, w.Last)
	return w
}

func (c *Client) Cleveland(ctx context.Context, progress func(string)) ([]Work, error) {
	var out []Work
	fields := "id,title,url,accession_number,creation_date,creation_date_earliest,creation_date_latest,type,technique,measurements,is_highlight,creditline,copyright,creators,images,share_license_status"
	for skip := 0; skip < 2000; skip += 100 {
		u := "https://openaccess-api.clevelandart.org/api/artworks/?" + url.Values{"highlight": {"1"}, "limit": {"100"}, "skip": {strconv.Itoa(skip)}, "fields": {fields}}.Encode()
		var page struct {
			Info struct {
				Total int `json:"total"`
			} `json:"info"`
			Data []map[string]any `json:"data"`
		}
		if _, e := c.JSON(ctx, u, &page); e != nil {
			return nil, e
		}
		if page.Info.Total > 2000 {
			return nil, fmt.Errorf("Cleveland highlight result exceeded safety bound")
		}
		for _, m := range page.Data {
			work := NormalizeCleveland(m)
			work.SourceSnapshotAt = c.snapshotTime(u)
			out = append(out, work)
		}
		progress(fmt.Sprintf("Cleveland highlight metadata: %d/%d", len(out), page.Info.Total))
		if skip+len(page.Data) >= page.Info.Total {
			break
		}
		if len(page.Data) == 0 {
			return nil, fmt.Errorf("Cleveland pagination stopped early")
		}
	}
	return out, nil
}

func (c *Client) AIC(ctx context.Context, progress func(string)) ([]Work, error) {
	var out []Work
	artists := map[int]map[string]any{}
	fields := []string{"id", "title", "is_boosted", "artist_id", "artist_title", "artist_ids", "date_start", "date_end", "date_display", "artwork_type_title", "medium_display", "dimensions", "main_reference_number", "is_public_domain", "image_id", "credit_line", "copyright_notice"}
	for pageNum := 1; pageNum <= 20; pageNum++ {
		params := rawJSON(map[string]any{"query": map[string]any{"term": map[string]any{"is_boosted": true}}, "limit": 100, "page": pageNum, "fields": fields, "sort": []any{map[string]any{"id": "asc"}}})
		u := "https://api.artic.edu/api/v1/artworks/search?params=" + url.QueryEscape(string(params))
		var page struct {
			Pagination struct {
				Total int `json:"total"`
				Pages int `json:"total_pages"`
			} `json:"pagination"`
			Data []map[string]any `json:"data"`
		}
		if _, e := c.JSON(ctx, u, &page); e != nil {
			return nil, e
		}
		if page.Pagination.Total > 2000 {
			return nil, fmt.Errorf("AIC essentials exceeded safety bound")
		}
		for _, m := range page.Data {
			w := Work{Source: "aic", ID: idOf(m, "id"), Title: value(m, "title"), Accession: value(m, "main_reference_number"), ArtistName: value(m, "artist_title"), First: number(m, "date_start"), Last: number(m, "date_end"), Date: value(m, "date_display"), Type: workType(value(m, "artwork_type_title")), Medium: value(m, "medium_display"), Dimensions: value(m, "dimensions"), Highlight: yes(m, "is_boosted"), Credit: value(m, "credit_line"), Copyright: value(m, "copyright_notice"), Raw: m}
			w.URL = "https://www.artic.edu/artworks/" + w.ID
			w.APIURL = "https://api.artic.edu/api/v1/artworks/" + w.ID
			w.SelectionURL = w.APIURL
			w.SelectionReason = "Art Institute of Chicago essentials selection (is_boosted=true); API documentation explains essentials are boosted. Not a current-display assertion."
			w.Precision = catalog.SourceDatePrecision(w.Date, w.First, w.Last)
			if yes(m, "is_public_domain") {
				w.Rights = "cc0"
			}
			if imageID := value(m, "image_id"); imageID != "" {
				w.ImageURL = "https://www.artic.edu/iiif/2/" + url.PathEscape(imageID) + "/full/1686,/0/default.jpg"
			}
			artistIDs, _ := m["artist_ids"].([]any)
			artistID := number(m, "artist_id")
			// integer() above bounds years; museum IDs have no year limit.
			if v, ok := m["artist_id"].(float64); ok {
				x := int(v)
				artistID = &x
			}
			if len(artistIDs) == 1 && artistID != nil && w.Eligible() == "eligible" {
				a, ok := artists[*artistID]
				if !ok {
					var response struct {
						Data map[string]any `json:"data"`
					}
					if _, e := c.JSON(ctx, fmt.Sprintf("https://api.artic.edu/api/v1/artists/%d?fields=id,title,birth_date,death_date", *artistID), &response); e != nil {
						return nil, e
					}
					a = response.Data
					artists[*artistID] = a
				}
				w.ArtistBirth = number(a, "birth_date")
				w.ArtistDeath = number(a, "death_date")
				m["artline_artist_snapshot"] = a
			}
			w.SourceSnapshotAt = c.snapshotTime(u)
			out = append(out, w)
		}
		progress(fmt.Sprintf("AIC essentials metadata: %d/%d", len(out), page.Pagination.Total))
		if pageNum >= page.Pagination.Pages {
			break
		}
		if len(page.Data) == 0 {
			return nil, fmt.Errorf("AIC pagination stopped early")
		}
	}
	return out, nil
}
