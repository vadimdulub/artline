package catalog

import "strings"

const ArtworkCreationCutoff = 1970

// CreationScope mirrors artline_creation_scope; a database parity test guards it.
// "before" is exclusive; "after" is unbounded, not an invented completion date.
func CreationScope(first, last *int, precision string) string {
	if precision == "unknown" || (first == nil && last == nil) {
		return "review"
	}
	if first != nil && last != nil && *first > *last {
		return "review"
	}
	if precision == "after" {
		if first != nil && *first >= ArtworkCreationCutoff {
			return "excluded"
		}
		return "review"
	}
	bound := first
	if last != nil {
		bound = last
	}
	if precision == "before" {
		if *bound <= ArtworkCreationCutoff+1 {
			return "eligible"
		}
		return "review"
	}
	if first != nil && *first > ArtworkCreationCutoff {
		return "excluded"
	}
	if last != nil && *last > ArtworkCreationCutoff {
		return "review"
	}
	switch precision {
	case "range", "circa_range", "decade", "century":
		if first == nil || last == nil {
			return "review"
		}
	case "exact", "circa":
	default:
		return "review"
	}
	if (precision == "circa" || precision == "circa_range") && *bound == ArtworkCreationCutoff {
		return "review"
	}
	return "eligible"
}

// Preserve the source display string; this classifies it without manufacturing years.
func SourceDatePrecision(display string, first, last *int) string {
	s := strings.ToLower(strings.TrimSpace(display))
	if s == "" || strings.Contains(s, "undated") || strings.Contains(s, "unknown") || (first == nil && last == nil) {
		return "unknown"
	}
	if strings.Contains(s, "before") {
		return "before"
	}
	if strings.Contains(s, "after") {
		return "after"
	}
	if strings.Contains(s, "century") {
		return "century"
	}
	approx := strings.Contains(s, "circa") || strings.HasPrefix(s, "ca.") || strings.HasPrefix(s, "c.") || strings.Contains(s, "about")
	if first != nil && last != nil && *first != *last {
		if approx {
			return "circa_range"
		}
		return "range"
	}
	if approx {
		return "circa"
	}
	return "exact"
}
