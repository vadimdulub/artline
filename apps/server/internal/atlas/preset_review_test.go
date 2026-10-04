package atlas

import (
	"fmt"
	"reflect"
	"regexp"
	"slices"
	"strings"
	"testing"
)

func TestEveryPresetHasReviewedFocus(t *testing.T) {
	regions := map[string]bool{}
	for _, values := range continentRegions {
		for _, value := range values {
			regions[value] = true
		}
	}
	for _, p := range Presets() {
		t.Run(p.ID, func(t *testing.T) {
			f := p.Focus
			if f == nil || f.Label == "" {
				t.Fatal("missing reviewed focus")
			}
			if !f.Global && len(f.Countries)+len(f.Regions)+len(f.Related["artwork"])+len(f.Context["artwork"]) == 0 {
				t.Fatal("missing regional or explicitly selected artwork scope")
			}
			if f.Global && len(f.Countries)+len(f.Regions) > 0 {
				t.Fatal("ambiguous global scope")
			}
			for _, region := range f.Regions {
				if !regions[region] {
					t.Fatalf("unknown region %q", region)
				}
			}
			for _, labels := range [][]string{f.Countries, f.Regions, f.ArtworkTraditions} {
				seen := map[string]bool{}
				for _, label := range labels {
					key := strings.ToLower(strings.TrimSpace(label))
					if key == "" || seen[key] {
						t.Fatalf("empty/duplicate label %q", label)
					}
					seen[key] = true
				}
			}
			for _, kind := range []string{"artwork", "book", "event"} {
				if kind != "artwork" && len(f.Context[kind]) > 3 {
					t.Fatal("too many contextual entries")
				}
				ids := append(slices.Clone(f.Related[kind]), f.Context[kind]...)
				if kind == "artwork" {
					// Editorial selections can span a full gallery; the separate
					// public Picks filter keeps its 60-ID interaction bound.
					seen := map[string]bool{}
					for _, id := range ids {
						if !regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`).MatchString(id) || seen[id] {
							t.Fatalf("invalid or duplicate artwork selection: %s", id)
						}
						seen[id] = true
					}
					continue
				}
				if len(ids) > 0 {
					filter := Filter{Range: p.Context, Limit: 60, Selection: true, Picks: map[string][]string{kind: ids}}
					if err := filter.Validate(); err != nil {
						t.Fatalf("invalid or overlapping %s links: %v", kind, err)
					}
				}
			}
			for _, links := range []map[string][]string{f.Related, f.Context} {
				for kind := range links {
					if !slices.Contains([]string{"artwork", "book", "event"}, kind) {
						t.Fatalf("unknown kind %s", kind)
					}
				}
			}
			if f.SelectedEvents && len(f.Related["event"]) == 0 {
				t.Fatal("event selection without core events")
			}
			for _, kind := range []string{"artwork", "book", "event"} {
				args := []any{nil, 1, 2000, true}
				sql := focusPredicate(kind, f, &args)
				for i := 4; i < len(args); i++ {
					if !regexp.MustCompile(fmt.Sprintf(`\$%d\b`, i)).MatchString(sql) {
						t.Fatalf("unused parameter %d in %s", i, sql)
					}
				}
				if kind == "event" && f.SelectedEvents && (strings.Contains(sql, "e.countries") || strings.Contains(sql, "e.regions")) {
					t.Fatal("unrelated regional events enter curated sequence")
				}
			}
		})
	}
}

func TestPresetFocusParametersAndLocalHighlights(t *testing.T) {
	f := &PresetFocus{Countries: []string{"value'--"}, Regions: []string{"western-asia"}, ArtworkTraditions: []string{"Byzantine"}, Related: map[string][]string{"book": {"book-core"}, "event": {"event-core"}}, Context: map[string][]string{"book": {"book-context"}, "event": {"event-context"}}}
	for _, kind := range []string{"artwork", "book", "event"} {
		args := []any{nil, 1, 2000, true}
		sql := focusPredicate(kind, f, &args)
		if strings.Contains(sql, "value'") || strings.Contains(sql, "Byzantine") {
			t.Fatal("unbound value")
		}
		if kind == "artwork" && (!strings.Contains(sql, "a.cultural_context") || strings.Contains(sql, "institution")) {
			t.Fatal("tradition must be independent of present custody")
		}
		if kind != "artwork" {
			args = []any{nil}
			sql = presetHighlightPredicate(kind, f, &args)
			if !strings.Contains(sql, "top100 OR") || !reflect.DeepEqual(args[1], f.Related[kind]) {
				t.Fatal("only reviewed core entries are preset highlights")
			}
		}
	}
	args := []any{nil}
	if focusPredicate("book", nil, &args) != "true" || len(args) != 1 {
		t.Fatal("default discovery changed")
	}
	if presetHighlightPredicate("book", nil, &args) != "d.top100" || len(args) != 1 {
		t.Fatal("global highlights changed")
	}
}
