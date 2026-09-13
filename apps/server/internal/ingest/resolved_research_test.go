package ingest

import (
	"encoding/json"
	"testing"

	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

func TestResolvedCreationEvidence(t *testing.T) {
	for _, tc := range []struct{ display, scope string }{
		{"1969", "eligible"}, {"1970", "eligible"}, {"c.1970", "review"},
		{"1960–1980", "review"}, {"1971", "excluded"}, {"unknown", "review"},
		{"1899-02", "review"}, {"1864/65", "eligible"}, {"acquired 1900", "review"},
	} {
		d := resolvedDate(ResolvedFact{Source: "tate", DateDisplay: tc.display})
		if got := catalog.CreationScope(d.First, d.Last, d.Precision); got != tc.scope {
			t.Errorf("%q: got %s want %s", tc.display, got, tc.scope)
		}
	}
	f := ResolvedFact{Source: "smk", DateDisplay: "1900", DateFields: map[string]json.RawMessage{
		"start": json.RawMessage(`"1900-01-01T00:00:00Z"`), "end": json.RawMessage(`"1900-12-31T00:00:00Z"`),
		"notes": json.RawMessage(`["Ud ateret"]`),
	}}
	if resolvedDate(f).Precision != "exact" {
		t.Fatal("literal documented artwork year")
	}
	f.DateFields["notes"] = json.RawMessage(`["Udateret; baseret på kunstnerens årstal"]`)
	if resolvedDate(f).First != nil {
		t.Fatal("lifetime fallback became artwork date")
	}
	f.DateFields["notes"] = json.RawMessage(`[]`)
	f.DateFields["end"] = json.RawMessage(`"1901-01-01"`)
	if resolvedDate(f).First != nil {
		t.Fatal("conflicting source bounds accepted")
	}
	f = ResolvedFact{Source: "joconde", DateDisplay: "1950", DateFields: map[string]json.RawMessage{
		"millesime_de_creation": json.RawMessage(`"1950"`), "periode_de_creation": json.RawMessage(`"19e siècle"`),
	}}
	if resolvedDate(f).First != nil {
		t.Fatal("inconsistent museum date fields accepted")
	}
}

func TestResolvedCreatorAliasCollision(t *testing.T) {
	b := 1833
	p := ResolvedPainter{Name: "C. F. Aagaard", Birth: &b}
	a := resolvedAuthor{Name: "Carl Frederik Aagaard", Birth: &b}
	if !possibleResolvedAlias(p, a) {
		t.Fatal("shortened creator name could create duplicate")
	}
	a.Birth = nil
	if possibleResolvedAlias(p, a) {
		t.Fatal("name alone treated as biography collision")
	}
	if resolutionNameKey("Monet, Claude") != resolutionNameKey("Claude Monet") {
		t.Fatal("source name order")
	}
}

func TestResolvedAccessionPlaceholders(t *testing.T) {
	for _, value := range []string{"SN", "S.N.", "sans numéro", "sans numéro d’inventaire"} {
		if resolvedAccession(value) != "" {
			t.Fatalf("placeholder became an object identity: %s", value)
		}
	}
	if resolvedAccession("INV 1234") != "INV 1234" {
		t.Fatal("real inventory identifier lost")
	}
}

func TestResolvedDanishAnonymousAttributions(t *testing.T) {
	for _, name := range []string{"Rembrandts skole", "Mesteren fra Citta di Castello", "Mesteren fra det hell. blods broderskab", "Ukendt kunstner"} {
		if !qualifiedCreator.MatchString(name) {
			t.Errorf("unidentified attribution accepted: %s", name)
		}
	}
	for _, name := range []string{"Johannes Hofmeister", "Anshelm Schultzberg"} {
		if qualifiedCreator.MatchString(name) {
			t.Errorf("real surname rejected: %s", name)
		}
	}
	d := closedResolvedDate(1650, 1650, "exact")
	f := ResolvedFact{Source: "smk", WorkType: "painting", ObjectContext: map[string]string{"creator_notes": "Jesper Svenningsen: kopi efter Furini"}}
	if resolvedIssue(f, d) != "creator_attribution_review" {
		t.Fatal("copy caveat in separate source notes ignored")
	}
	f.ObjectContext = map[string]string{"creator_qualifier": "Andet"}
	if resolvedIssue(f, d) != "creator_attribution_review" {
		t.Fatal("source qualifier ignored")
	}
}

func TestResolvedDimensionsPreserveSourceMeasurements(t *testing.T) {
	raw := `[{"part":"Netto","type":"højde","value":"41","unit":"centimeter","notes":"410 x 575 mm"},{"part":"Netto","type":"bredde","value":"57.5","unit":"centimeter"}]`
	want := "Netto højde: 41 centimeter (410 x 575 mm); Netto bredde: 57.5 centimeter"
	if got := resolvedDimensions("smk", raw); got != want {
		t.Fatalf("%q", got)
	}
	if resolvedDimensions("joconde", "H. 23 cm") != "H. 23 cm" {
		t.Fatal("unstructured source changed")
	}
	if resolvedDimensions("smk", "[]") != "" {
		t.Fatal("empty measurements displayed as code")
	}
}
