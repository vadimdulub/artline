package atlas

import (
	"fmt"
	"net/url"
	"slices"
	"strings"
)

// Names mirror the native catalogues. Prefixes keep the three layer scopes independent.
var EntityFields = map[string][]string{
	"book":    {"q", "author", "language", "country", "region", "women", "top100"},
	"artwork": {"q", "painter", "movement", "country", "region", "work_type", "women", "popular", "image_only"},
	"event":   {"q", "topic", "kind", "country", "region", "top100"},
}

func (f Filter) validateEntities() error {
	for kind, values := range f.Entities {
		if !ValidType(kind) {
			return ErrFilter
		}
		for key, choices := range values {
			if !slices.Contains(EntityFields[kind], key) || len(choices) == 0 || len(choices) > 32 {
				return ErrFilter
			}
			if key == "q" || key == "women" || key == "popular" || key == "top100" || key == "image_only" {
				if len(choices) != 1 {
					return ErrFilter
				}
			}
			for _, value := range choices {
				if len(value) > 250 || strings.TrimSpace(value) == "" {
					return ErrFilter
				}
				if key == "q" && len(value) > 200 {
					return ErrFilter
				}
				if (key == "women" || key == "popular" || key == "top100" || key == "image_only") && value != "true" && value != "false" {
					return ErrFilter
				}
			}
		}
	}
	return nil
}

// Append only active predicates. Values are always bound, including array choices.
// Creator filters share one EXISTS so all requested attributes belong to the same painter.
func entityPredicate(kind string, values url.Values, args *[]any) string {
	conditions := []string{"true"}
	bind := func(value any) string { n := len(*args); *args = append(*args, value); return fmt.Sprintf("$%d", n) } // args[0] is pgx mode
	add := func(key, sql string) {
		if v := values[key]; len(v) > 0 {
			conditions = append(conditions, fmt.Sprintf(sql, bind(v)))
		}
	}
	if q := values.Get("q"); q != "" {
		p := bind(q)
		switch kind {
		case "book":
			conditions = append(conditions, "strpos(b.search_text,lower("+p+"))>0")
		case "event":
			conditions = append(conditions, "strpos(e.search_text,lower("+p+"))>0")
		case "artwork":
			conditions = append(conditions, artworkSearchPredicate(p))
		}
	}
	switch kind {
	case "book":
		if authors := values["author"]; len(authors) > 0 {
			p := bind(authors)
			conditions = append(conditions, "(b.author_label=ANY("+p+"::text[]) OR EXISTS(SELECT 1 FROM book_creator_links l JOIN book_creators c ON c.id=l.creator_id WHERE l.book_id=b.id AND c.name=ANY("+p+"::text[])))")
		}
		add("language", "d.languages && %s::text[]")
		add("country", "d.countries && %s::text[]")
		add("region", "d.regions && %s::text[]")
		if values.Get("women") == "true" {
			conditions = append(conditions, "cardinality(d.woman_author_ids)>0")
		}
		if values.Get("top100") == "true" {
			conditions = append(conditions, "d.top100")
		}
	case "event":
		add("topic", "e.topics && %s::text[]")
		add("country", "e.countries && %s::text[]")
		add("region", "e.regions && %s::text[]")
		add("kind", "e.kind=ANY(%s::text[])")
		if values.Get("top100") == "true" {
			conditions = append(conditions, "e.top100")
		}
	case "artwork":
		add("work_type", "a.work_type=ANY(%s::text[])")
		// image_only is accepted for old/shared URLs. All applies its mandatory
		// image predicate once in Repository.List, including when this is false.
		// A geographic discovery filter also includes documented production
		// places. Once a creator facet is selected, its predicates must still
		// belong to that same creator (including country and region).
		geographyOnly := len(values["painter"]) == 0 && len(values["movement"]) == 0 && values.Get("women") != "true" && values.Get("popular") != "true"
		if geographyOnly {
			if countries := values["country"]; len(countries) > 0 {
				conditions = append(conditions, artworkGeographyMatch("c.code::text=ANY("+bind(countries)+"::text[])"))
			}
			if regions := values["region"]; len(regions) > 0 {
				conditions = append(conditions, artworkGeographyMatch("c.region_code=ANY("+bind(regions)+"::text[])"))
			}
		}
		outer := conditions
		conditions = []string{}
		add("painter", "ar.slug=ANY(%s::text[])")
		if !geographyOnly {
			add("country", "EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=ar.id AND ac.country_code::text=ANY(%s::text[]))")
			add("region", "EXISTS(SELECT 1 FROM artist_countries ac JOIN countries c ON c.code=ac.country_code WHERE ac.artist_id=ar.id AND c.region_code=ANY(%s::text[]))")
		}
		add("movement", "EXISTS(SELECT 1 FROM artist_movements am JOIN movements m ON m.id=am.movement_id WHERE am.artist_id=ar.id AND m.status<>'archived' AND ($3 OR m.status='published') AND m.slug=ANY(%s::text[]))")
		if values.Get("women") == "true" {
			conditions = append(conditions, "EXISTS(SELECT 1 FROM artist_gender_evidence ge WHERE ge.artist_id=ar.id AND ge.is_woman)")
		}
		if values.Get("popular") == "true" {
			conditions = append(conditions, "EXISTS(SELECT 1 FROM artist_discovery_selection ds WHERE ds.artist_id=ar.id AND ds.is_popular)")
		}
		if len(conditions) > 0 {
			outer = append(outer, "EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id AND ar.status<>'archived' AND ($3 OR ar.status='published') AND "+strings.Join(conditions, " AND ")+")")
		}
		conditions = outer
	}
	return strings.Join(conditions, " AND ")
}

// Search narrow title/label and creator-ID projections before native eligibility.
// UNION lets the existing covering and creator-link indexes avoid fetching the
// wide artwork heap for every illustrated record. All values remain bound.
func artworkSearchPredicate(parameter string) string {
	return strings.ReplaceAll(`a.id IN (
 SELECT search.id FROM artworks search WHERE search.status<>'archived'
 AND (strpos(lower(search.title),lower($query))>0 OR strpos(lower(coalesce(search.unlinked_creator_label,'')),lower($query))>0)
 UNION SELECT aa.artwork_id FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id
 WHERE ar.status<>'archived' AND ($3 OR ar.status='published') AND (
 strpos(lower(ar.display_name),lower($query))>0 OR strpos(lower(ar.sort_name),lower($query))>0
 OR ar.id IN(SELECT x.artist_id FROM artist_aliases x WHERE strpos(lower(x.alias),lower($query))>0)
 OR ar.id IN(SELECT x.artist_id FROM artist_movements x JOIN movements m ON m.id=x.movement_id WHERE m.status<>'archived' AND ($3 OR m.status='published') AND strpos(lower(m.name),lower($query))>0)
 OR ar.id IN(SELECT x.artist_id FROM artist_countries x JOIN countries c ON c.code=x.country_code WHERE strpos(lower(c.name),lower($query))>0)
 OR ar.id IN(SELECT x.artist_id FROM artist_places x JOIN places pl ON pl.id=x.place_id WHERE strpos(lower(pl.name),lower($query))>0)
 ))`, "$query", parameter)
}
