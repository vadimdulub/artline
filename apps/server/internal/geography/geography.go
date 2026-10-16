// Package geography projects bounded, already selected catalogue records onto
// a map. It never infers creation from holdings, nationality or depicted places.
package geography

import (
	"context"
	_ "embed"
	"encoding/json"
	"fmt"
	"math"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
)

const MaxIDs = 80
const MaxConnections = 32

//go:embed countries.json
var countryData []byte

//go:embed evidence.json
var evidenceData []byte

type Country struct {
	Code string  `json:"code"`
	QID  string  `json:"qid"`
	Name string  `json:"name"`
	Lat  float64 `json:"lat"`
	Lon  float64 `json:"lon"`
}
type Connection struct {
	Place       string   `json:"place"`
	Relation    string   `json:"relation"`
	Precision   string   `json:"precision"`
	Lat         *float64 `json:"lat"`
	Lon         *float64 `json:"lon"`
	Start       *int     `json:"start"`
	End         *int     `json:"end"`
	Note        string   `json:"note"`
	SourceURL   string   `json:"sourceUrl,omitempty"`
	SourceLabel string   `json:"sourceLabel"`
}
type Record struct {
	ID          string       `json:"id"`
	Connections []Connection `json:"connections"`
	Truncated   bool         `json:"truncated"`
}
type Response struct {
	Records []Record `json:"records"`
}
type Evidence struct {
	Kind       string     `json:"kind"`
	Scheme     string     `json:"scheme"`
	ExternalID string     `json:"externalId"`
	Connection Connection `json:"connection"`
}
type rawPlace struct {
	Place     string   `json:"place"`
	Code      string   `json:"code"`
	Country   string   `json:"country"`
	QID       string   `json:"qid"`
	Relation  string   `json:"relation"`
	Lat       *float64 `json:"lat"`
	Lon       *float64 `json:"lon"`
	Start     *int     `json:"start"`
	End       *int     `json:"end"`
	Note      string   `json:"note"`
	SourceURL string   `json:"sourceUrl"`
}

var countries []Country
var evidence []Evidence

func init() {
	if err := json.Unmarshal(countryData, &countries); err != nil {
		panic(err)
	}
	if err := json.Unmarshal(evidenceData, &evidence); err != nil {
		panic(err)
	}
}

// resolveCountry uses stable identifiers only. Historical states are not
// silently replaced by their modern successors. A country label is not a site.
func resolveCountry(code, qid string) *Country {
	for i := range countries {
		c := &countries[i]
		if (code != "" && c.Code == code) || (qid != "" && c.QID == qid) {
			return c
		}
	}
	return nil
}
func project(p rawPlace) Connection {
	c := Connection{Place: p.Place, Relation: p.Relation, Start: p.Start, End: p.End, Note: p.Note, SourceURL: p.SourceURL, SourceLabel: "Catalogue association · see record sources", Precision: "unlocated"}
	// Only use a country's label point if the source identifies the country itself.
	country := resolveCountry("", p.QID)
	if country == nil && p.Code != "" && p.Country != "" && strings.EqualFold(p.Place, p.Country) {
		country = resolveCountry(p.Code, "")
	}
	if country != nil {
		c.Lat = &country.Lat
		c.Lon = &country.Lon
		c.Precision = "country"
	} else if p.Lat != nil && p.Lon != nil && validCoordinate(*p.Lat, *p.Lon) {
		c.Lat = p.Lat
		c.Lon = p.Lon
		c.Precision = "recorded point"
		c.Note = strings.TrimSpace(c.Note + " Coordinate precision has not been established.")
	}
	return c
}
func validCoordinate(lat, lon float64) bool {
	return !math.IsNaN(lat) && !math.IsNaN(lon) && math.Abs(lat) <= 90 && math.Abs(lon) <= 180
}
func inRange(c Connection, start, end int) bool {
	// A single documented bound is not an inferred point date.
	return (c.Start == nil || *c.Start <= end) && (c.End == nil || *c.End >= start)
}
func assemble(kind, id string, identities map[string]string, raw []rawPlace, start, end int) Record {
	out := Record{ID: id, Connections: []Connection{}}
	for _, e := range evidence {
		if e.Kind == kind && identities[e.Scheme] == e.ExternalID && inRange(e.Connection, start, end) {
			out.Connections = append(out.Connections, e.Connection)
		}
	}
	for _, p := range raw {
		c := project(p)
		if inRange(c, start, end) {
			out.Connections = append(out.Connections, c)
		}
	}
	if len(out.Connections) > MaxConnections {
		out.Truncated = true
		out.Connections = out.Connections[:MaxConnections]
	}
	return out
}

// Lookup performs indexed identity lookups, never a worldwide catalogue scan.
// The caller supplies at most 80 IDs from a native, server-filtered result page.
func Lookup(ctx context.Context, db *pgxpool.Pool, kind string, ids []string, start, end int) (Response, error) {
	out := Response{Records: []Record{}}
	if len(ids) == 0 || len(ids) > MaxIDs {
		return out, fmt.Errorf("use 1–%d record IDs", MaxIDs)
	}
	if db == nil {
		return out, fmt.Errorf("database unavailable")
	}
	var query string
	args := []any{ids, kind}
	switch kind {
	case "artwork", "artist":
		args = append(args, start, end)
		table, relations, fk := "artworks", "artwork_places", "artwork_id"
		if kind == "artist" {
			table, relations, fk = "artists", "artist_places", "artist_id"
		}
		places := `SELECT p.name AS place,p.country_code AS code,coalesce(c.name,'') AS country,coalesce(p.wikidata_id,'') AS qid,ap.relationship_type AS relation,p.latitude AS lat,p.longitude AS lon,ap.start_year AS start,ap.end_year AS end,coalesce(ap.note,'') AS note FROM ` + relations + ` ap JOIN places p ON p.id=ap.place_id LEFT JOIN countries c ON c.code=p.country_code WHERE ap.` + fk + `=w.id AND (ap.start_year IS NULL OR ap.start_year<=$4) AND (ap.end_year IS NULL OR ap.end_year>=$3)`
		if kind == "artist" {
			places += ` UNION ALL SELECT c.name,c.code,c.name,'',ac.relationship_type,NULL::double precision,NULL::double precision,NULL::integer,NULL::integer,coalesce(ac.note,'') FROM artist_countries ac JOIN countries c ON c.code=ac.country_code WHERE ac.artist_id=w.id`
		}
		query = `SELECT w.id::text,coalesce((SELECT jsonb_object_agg(x.scheme,x.external_id) FROM external_identifiers x WHERE x.entity_type=$2 AND x.entity_id=w.id),'{}'),coalesce((SELECT jsonb_agg(to_jsonb(p)) FROM (` + places + ` ORDER BY relation,place,start NULLS LAST LIMIT 33) p),'[]') FROM ` + table + ` w WHERE w.id=ANY($1::uuid[]) AND w.status<>'archived' ORDER BY w.id`
	case "book":
		query = `SELECT b.id,jsonb_build_object('sourceId',b.source_id),coalesce((SELECT jsonb_agg(jsonb_build_object('place',coalesce(t.name,k.qid),'qid',k.qid,'relation',CASE WHEN d.evidence#>>'{work,countryProperty}'='P495' THEN 'country of origin' ELSE 'recorded country association' END,'sourceUrl',b.record->>'sourceUrl','note','Country metadata is not evidence of where the book was written or published.')) FROM (SELECT unnest(d.countries) qid LIMIT 33) k LEFT JOIN book_discovery_terms t ON t.kind='country' AND t.key=k.qid),'[]') FROM book_records b LEFT JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum WHERE b.id=ANY($1::text[]) AND b.status<>'archived' AND (b.end_year<=2000 OR b.start_year IS NULL) AND $2='book' ORDER BY b.id`
	case "event":
		query = `SELECT e.id,jsonb_build_object('sourceId',e.source_id),coalesce((SELECT jsonb_agg(jsonb_build_object('place',p.v->>'name','qid',CASE WHEN p.v->>'url' ~ '^https://www.wikidata.org/wiki/Q[0-9]+$' THEN regexp_replace(p.v->>'url','^.*/','') ELSE '' END,'relation','recorded event location','sourceUrl',e.record->>'sourceUrl','note','A recorded location association; not an exact venue or historical boundary.')) FROM (SELECT v FROM jsonb_array_elements(coalesce(e.record->'locations','[]')) v LIMIT 33) p),'[]') FROM event_records e WHERE e.id=ANY($1::text[]) AND e.status<>'archived' AND $2='event' ORDER BY e.id`
	default:
		return out, fmt.Errorf("unknown record type")
	}
	rows, err := db.Query(ctx, query, args...)
	if err != nil {
		return out, err
	}
	defer rows.Close()
	for rows.Next() {
		var id string
		var identitiesJSON, placesJSON []byte
		if err = rows.Scan(&id, &identitiesJSON, &placesJSON); err != nil {
			return out, err
		}
		var identities map[string]string
		var places []rawPlace
		if err = json.Unmarshal(identitiesJSON, &identities); err != nil {
			return out, err
		}
		if err = json.Unmarshal(placesJSON, &places); err != nil {
			return out, err
		}
		out.Records = append(out.Records, assemble(kind, id, identities, places, start, end))
	}
	return out, rows.Err()
}
