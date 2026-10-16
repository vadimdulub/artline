package geography

import "testing"

func TestCountryPrecisionAndHistoricalStates(t *testing.T) {
	c := project(rawPlace{Place: "France", QID: "Q142", Relation: "country of origin"})
	if c.Precision != "country" || c.Relation != "country of origin" || c.Lat == nil || c.CountryCode != "FR" {
		t.Fatalf("lost country precision: %+v", c)
	}
	c = project(rawPlace{Place: "United Kingdom of Great Britain and Ireland", QID: "Q174193", Relation: "country of origin"})
	if c.Lat != nil || c.Precision != "unlocated" || c.CountryCode != "" {
		t.Fatal("historical state incorrectly assigned modern geometry")
	}
	c = project(rawPlace{Place: "An unknown studio", Code: "FR", Country: "France", Relation: "created"})
	if c.Lat != nil || c.CountryCode != "" {
		t.Fatal("country must not invent a studio coordinate")
	}
}
func TestExactObjectIdentityAndDateScope(t *testing.T) {
	found := assemble("artwork", "local", map[string]string{"european-ng-object": "NG3863"}, nil, 1888, 1888)
	if len(found.Connections) != 1 || found.Connections[0].Place != "Arles" {
		t.Fatalf("missing exact object: %+v", found)
	}
	wrong := assemble("artwork", "different-sunflowers", map[string]string{"european-met-the-met-object": "436524"}, nil, 1888, 1888)
	if len(wrong.Connections) != 0 {
		t.Fatal("same title / different version must not match")
	}
	outside := assemble("artwork", "local", map[string]string{"european-ng-object": "NG3863"}, nil, 1889, 1889)
	if len(outside.Connections) != 0 {
		t.Fatal("connection outside selected years")
	}
}
func TestWritingAndPublicationRemainSeparate(t *testing.T) {
	r := assemble("book", "local", map[string]string{"sourceId": "Q150827"}, nil, 1800, 1900)
	if len(r.Connections) != 2 || r.Connections[0].Place != "Lake Geneva" || r.Connections[1].Place != "London" || r.Connections[0].Relation == r.Connections[1].Relation {
		t.Fatalf("conflated writing and publication: %+v", r)
	}
}
func TestBoundedConnectionsAndUnknownDates(t *testing.T) {
	raw := make([]rawPlace, 33)
	for i := range raw {
		raw[i] = rawPlace{Place: "Unlocated", Relation: "created"}
	}
	r := assemble("artwork", "x", nil, raw, 1800, 1900)
	if !r.Truncated || len(r.Connections) != 32 {
		t.Fatal("unbounded connections")
	}
	if r.Connections[0].Start != nil || r.Connections[0].Lat != nil {
		t.Fatal("unknown facts fabricated")
	}
}
func TestEmbeddedEvidence(t *testing.T) {
	for _, e := range evidence {
		c := e.Connection
		if e.Scheme == "" || e.ExternalID == "" || c.SourceURL == "" || c.Lat == nil || c.Lon == nil || !validCoordinate(*c.Lat, *c.Lon) || c.Start == nil || c.End == nil || *c.Start > *c.End {
			t.Fatalf("incomplete evidence: %+v", e)
		}
	}
}

func TestSelectedRelationsKeepLifeAndWorkSeparate(t *testing.T) {
	born := assemble("artist", "vincent", map[string]string{"wikidata": "Q5582"}, []rawPlace{{Place: "Netherlands", Code: "NL", Country: "Netherlands", Relation: "citizenship"}}, 1800, 1900, "birth")
	if len(born.Connections) != 1 || born.Connections[0].Place != "Zundert" {
		t.Fatalf("birth filter leaked other relationships: %+v", born)
	}
	for _, filter := range []string{"education", "residence"} {
		r := assemble("artist", "vincent", map[string]string{"wikidata": "Q5582"}, nil, 1885, 1886, filter)
		found := false
		for _, c := range r.Connections {
			if c.Place == "Antwerp" {
				found = true
			}
		}
		if !found {
			t.Fatalf("Antwerp's documented residence and study must match %s", filter)
		}
	}
	r := assemble("artist", "vincent", map[string]string{"wikidata": "Q5582"}, nil, 1800, 1900, "creation")
	if len(r.Connections) != 0 {
		t.Fatal("artist residence was presented as painting creation")
	}
}
func TestRelationFilteringBeforeConnectionCap(t *testing.T) {
	raw := make([]rawPlace, 40)
	for i := range raw {
		raw[i] = rawPlace{Place: "France", QID: "Q142", Relation: "cultural_affiliation"}
	}
	raw = append(raw, rawPlace{Place: "Netherlands", QID: "Q55", Relation: "birth"})
	r := assemble("artist", "x", nil, raw, 1800, 1900, "birth")
	if r.Truncated || len(r.Connections) != 1 || r.Connections[0].CountryCode != "NL" {
		t.Fatalf("birthplace hidden by affiliations: %+v", r)
	}
}
