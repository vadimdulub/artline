package atlas

import (
	"context"
	"fmt"
	"slices"
	"strings"
)

var Continents = []Region{{"africa", "Africa"}, {"asia", "Asia"}, {"europe", "Europe"}, {"north-america", "North America"}, {"south-america", "South America"}, {"oceania", "Oceania"}, {"antarctica", "Antarctica"}}
var continentRegions = map[string][]string{
	"africa":        {"northern-africa", "western-africa", "eastern-africa", "middle-africa", "southern-africa"},
	"asia":          {"central-asia", "eastern-asia", "southern-asia", "south-eastern-asia", "western-asia"},
	"europe":        {"eastern-europe", "northern-europe", "southern-europe", "western-europe"},
	"north-america": {"northern-america", "central-america", "caribbean"}, "south-america": {"south-america"},
	"oceania": {"australia-and-new-zealand", "melanesia", "micronesia", "polynesia", "oceania"}, "antarctica": {"antarctica"},
}

func (f Filter) validateGeography() error {
	if len(f.Countries) > 32 || len(f.Continents) > 7 {
		return ErrFilter
	}
	for _, country := range f.Countries {
		if strings.TrimSpace(country) == "" || len(country) > 250 {
			return ErrFilter
		}
	}
	for _, continent := range f.Continents {
		if _, ok := continentRegions[continent]; !ok {
			return ErrFilter
		}
	}
	return nil
}

// Country names retain historical states separately. Shared keys match recorded
// labels case-insensitively; no modern-country attribution is inferred.
func (r *Repository) Countries(ctx context.Context, preview bool) ([]Region, error) {
	out := []Region{}
	if r.db == nil {
		return out, fmt.Errorf("atlas unavailable")
	}
	rows, err := r.db.Query(ctx, `WITH names AS (
 SELECT name FROM countries
 UNION SELECT t.name FROM book_discovery_terms t WHERE t.kind='country' AND EXISTS(
  SELECT 1 FROM book_records b JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum
  WHERE b.status<>'archived' AND ($1 OR b.status='published') AND (b.end_year<=2000 OR b.start_year IS NULL) AND t.key=ANY(d.countries))
 UNION SELECT unnest(countries) FROM event_records WHERE status<>'archived' AND ($1 OR status='published')
 ) SELECT lower(trim(name)),min(trim(name)) FROM names WHERE trim(name)<>'' GROUP BY lower(trim(name)) ORDER BY min(trim(name)) LIMIT 1000`, preview)
	if err != nil {
		return out, err
	}
	defer rows.Close()
	for rows.Next() {
		var v Region
		if err = rows.Scan(&v.Key, &v.Name); err != nil {
			return out, err
		}
		out = append(out, v)
	}
	return out, rows.Err()
}
func geographyPredicate(kind string, f Filter, args *[]any) string {
	clauses := []string{"true"}
	bind := func(v any) string { p := fmt.Sprintf("$%d", len(*args)); *args = append(*args, v); return p }
	if len(f.Countries) > 0 {
		names := slices.Clone(f.Countries)
		for i, v := range names {
			names[i] = strings.ToLower(strings.TrimSpace(v))
		}
		p := bind(names)
		switch kind {
		case "artwork":
			clauses = append(clauses, `EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id JOIN artist_countries ac ON ac.artist_id=ar.id JOIN countries c ON c.code=ac.country_code WHERE aa.artwork_id=a.id AND ar.status<>'archived' AND ($3 OR ar.status='published') AND lower(c.name)=ANY(`+p+`::text[]))`)
		case "book":
			clauses = append(clauses, `d.countries && ARRAY(SELECT key FROM book_discovery_terms WHERE kind='country' AND lower(name)=ANY(`+p+`::text[]))`)
		case "event":
			clauses = append(clauses, `EXISTS(SELECT 1 FROM unnest(e.countries) country WHERE lower(country)=ANY(`+p+`::text[]))`)
		}
	}
	if len(f.Continents) > 0 {
		regions := []string{}
		for _, c := range f.Continents {
			regions = append(regions, continentRegions[c]...)
		}
		p := bind(regions)
		switch kind {
		case "artwork":
			clauses = append(clauses, `EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id JOIN artist_countries ac ON ac.artist_id=ar.id JOIN countries c ON c.code=ac.country_code WHERE aa.artwork_id=a.id AND ar.status<>'archived' AND ($3 OR ar.status='published') AND c.region_code=ANY(`+p+`::text[]))`)
		case "book":
			clauses = append(clauses, `d.regions && `+p+`::text[]`)
		case "event":
			clauses = append(clauses, `EXISTS(SELECT 1 FROM unnest(e.regions) region WHERE replace(lower(region),' ','-')=ANY(`+p+`::text[]))`)
		}
	}
	return strings.Join(clauses, " AND ")
}
