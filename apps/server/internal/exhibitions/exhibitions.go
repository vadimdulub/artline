package exhibitions

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
)

var ErrNotFound = errors.New("exhibition not found")
var ErrUnavailable = errors.New("exhibitions unavailable")
var uuidPattern = regexp.MustCompile(`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`)

func ValidID(id string) bool { return uuidPattern.MatchString(id) }

type Filter struct {
	Query, Institution, Artist, Artwork, Source, Format, State, After string
	Collection, Theme, Person                                         string
	Start, End                                                        *int
	Limit                                                             int
}

type Cursor struct {
	Year int    `json:"year"`
	ID   string `json:"id"`
}

func DecodeCursor(raw string) (Cursor, error) {
	c := Cursor{}
	if raw == "" {
		return c, nil
	}
	if len(raw) > 256 {
		return c, fmt.Errorf("invalid exhibition cursor")
	}
	b, err := base64.RawURLEncoding.DecodeString(raw)
	if err != nil || json.Unmarshal(b, &c) != nil || !ValidID(c.ID) || (c.Year != -2147483648 && (c.Year < -12000 || c.Year > 9999 || c.Year == 0)) {
		return Cursor{}, fmt.Errorf("invalid exhibition cursor")
	}
	return c, nil
}

func (f Filter) Validate() error {
	if f.Collection != "" && f.Collection != "archive" && f.Collection != "expanded" {
		return fmt.Errorf("invalid exhibition collection")
	}
	if len(f.Theme) > 80 || (f.Person != "" && !ValidID(f.Person)) {
		return fmt.Errorf("invalid exhibition topic or person")
	}
	if len(f.Query) > 200 || len(f.Source) > 80 || f.Limit < 1 || f.Limit > 100 {
		return fmt.Errorf("use a search up to 200 characters and a limit from 1 to 100")
	}
	for _, id := range []string{f.Institution, f.Artist, f.Artwork} {
		if id != "" && !ValidID(id) {
			return fmt.Errorf("invalid catalogue record identifier")
		}
	}
	for _, year := range []*int{f.Start, f.End} {
		if year != nil && (*year < -12000 || *year > 9999 || *year == 0) {
			return fmt.Errorf("invalid exhibition year")
		}
	}
	if f.Start != nil && f.End != nil && *f.Start > *f.End {
		return fmt.Errorf("start year must not follow end year")
	}
	if f.Format != "" && f.Format != "physical" && f.Format != "online" && f.Format != "hybrid" && f.Format != "unknown" {
		return fmt.Errorf("invalid exhibition format")
	}
	if f.State != "" && f.State != "held" && f.State != "announced" && f.State != "cancelled" && f.State != "uncertain" {
		return fmt.Errorf("invalid exhibition state")
	}
	_, err := DecodeCursor(f.After)
	return err
}

type Response struct {
	ExpandedStudyCount int               `json:"expandedStudyCount"`
	Featured           []json.RawMessage `json:"featured"`
	Items              []json.RawMessage `json:"items"`
	Total              int               `json:"total"`
	HeldTotal          int               `json:"heldTotal"`
	HasMore            bool              `json:"hasMore"`
	NextCursor         string            `json:"nextCursor"`
}

type EntriesResponse struct {
	Items      []json.RawMessage `json:"items"`
	Total      int               `json:"total"`
	HasMore    bool              `json:"hasMore"`
	NextCursor string            `json:"nextCursor"`
}
