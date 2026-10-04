package atlas

import "testing"

func TestPresetArtworkIdentityRetainsSelectionAndContextAcrossCatalogues(t *testing.T) {
	focus := &PresetFocus{
		Related:           map[string][]string{"artwork": {"local-selected", "shared"}, "book": {"book-one"}},
		Context:           map[string][]string{"artwork": {"local-context"}},
		ArtworkIdentities: map[string]string{"local-selected": "selected-work", "local-context": "context-work"},
	}
	resolved, err := resolvedArtworkFocus(focus, map[string]string{"selected-work": "production-selected", "context-work": "production-context"})
	if err != nil {
		t.Fatal(err)
	}
	if resolved.Related["artwork"][0] != "production-selected" || resolved.Context["artwork"][0] != "production-context" || resolved.Related["artwork"][1] != "shared" || resolved.Related["book"][0] != "book-one" {
		t.Fatal("selection, context or unrelated identity changed")
	}
	if focus.Related["artwork"][0] != "local-selected" || focus.Context["artwork"][0] != "local-context" {
		t.Fatal("canonical preset mutated")
	}
	if _, err := resolvedArtworkFocus(focus, map[string]string{"selected-work": "production-selected"}); err == nil {
		t.Fatal("missing identity silently reused an unrelated target UUID")
	}
}
