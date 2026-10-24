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

func TestConnectionChronologyPreservesUnknownBoundsAndStableKeys(t *testing.T) {
	y := func(value int) *int { return &value }
	connections := []Connection{
		{Place: "Unknown"},
		{Place: "Later", Start: y(1900), End: y(1901)},
		{Place: "End only", End: y(1800)},
		{Place: "Ancient", Start: y(-500)},
		{Place: "Earlier", Start: y(1880), End: y(1888)},
	}
	orderConnections(connections)
	want := []string{"Ancient", "End only", "Earlier", "Later", "Unknown"}
	keys := map[string]string{}
	for i, c := range connections {
		if c.Place != want[i] || c.Key == "" {
			t.Fatalf("bad chronology: %+v", connections)
		}
		keys[c.Place] = c.Key
	}
	if connections[0].End != nil || connections[1].Start != nil || connections[4].Start != nil {
		t.Fatal("invented dates")
	}
	subset := []Connection{connections[3], connections[2]}
	orderConnections(subset)
	for _, c := range subset {
		if c.Key != keys[c.Place] {
			t.Fatal("selection changed evidence identity")
		}
	}
}

func TestSamePlaceKeepsDistinctConnectionsAndDuplicateKeysUnique(t *testing.T) {
	y := 1888
	connections := []Connection{{Place: "Arles", Relation: "lived", Start: &y}, {Place: "Arles", Relation: "painted", Start: &y}, {Place: "Arles", Relation: "painted", Start: &y}}
	orderConnections(connections)
	keys := map[string]bool{}
	for _, c := range connections {
		if keys[c.Key] {
			t.Fatal("duplicate key")
		}
		keys[c.Key] = true
	}
	if len(connections) != 3 {
		t.Fatal("connections lost")
	}
}
