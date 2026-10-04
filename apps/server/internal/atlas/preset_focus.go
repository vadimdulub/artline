package atlas

import (
	"fmt"
	"slices"
	"strings"
)

func presetFocus(id string) *PresetFocus {
	p, ok := FindPreset(id)
	if !ok {
		return nil
	}
	return p.Focus
}

func focusPredicate(kind string, focus *PresetFocus, args *[]any) string {
	if focus == nil {
		return "true"
	}
	clauses := []string{"false"}
	selected := kind == "event" && focus.SelectedEvents || kind == "book" && focus.SelectedBooks
	bind := func(value any) string { p := fmt.Sprintf("$%d", len(*args)); *args = append(*args, value); return p }
	if focus.Global && !selected {
		clauses = append(clauses, "true")
	}
	if len(focus.Countries) > 0 && !selected {
		clauses = append(clauses, geographyPredicate(kind, Filter{Countries: focus.Countries}, args))
	}
	if len(focus.Regions) > 0 && !selected {
		p := bind(focus.Regions)
		switch kind {
		case "artwork":
			clauses = append(clauses, artworkGeographyMatch(`c.region_code=ANY(`+p+`::text[])`))
		case "book":
			clauses = append(clauses, `d.regions && `+p+`::text[]`)
		case "event":
			clauses = append(clauses, `EXISTS(SELECT 1 FROM unnest(e.regions) region WHERE replace(lower(region),' ','-')=ANY(`+p+`::text[]))`)
		}
	}
	if kind == "artwork" && len(focus.ArtworkTraditions) > 0 {
		// Match the recorded object tradition, irrespective of creator or current
		// custody. Exact reviewed values avoid inventing geographic provenance.
		clauses = append(clauses, `a.cultural_context=ANY(`+bind(focus.ArtworkTraditions)+`::text[])`)
	}
	geographic := "(" + strings.Join(clauses, " OR ") + ")"
	ids := append(slices.Clone(focus.Related[kind]), focus.Context[kind]...)
	if len(ids) == 0 {
		return geographic
	}
	parameter := fmt.Sprintf("$%d", len(*args))
	*args = append(*args, ids)
	key, cast := "b.id", "::text[]"
	if kind == "event" {
		key = "e.id"
	}
	if kind == "artwork" {
		key, cast = "a.id", "::text[]::uuid[]"
	}
	return "((" + geographic + ") OR " + key + "=ANY(" + parameter + cast + "))"
}

// A reviewed preset's explicitly selected books/events are local highlights.
// This does not mutate global highlight membership or bypass visibility/dates.
func presetHighlightPredicate(kind string, focus *PresetFocus, args *[]any) string {
	column, key := "d.top100", "b.id"
	if kind == "event" {
		column, key = "e.top100", "e.id"
	}
	if focus == nil || len(focus.Related[kind]) == 0 {
		return column
	}
	p := fmt.Sprintf("$%d", len(*args))
	*args = append(*args, focus.Related[kind])
	return "(" + column + " OR " + key + "=ANY(" + p + "::text[]))"
}
