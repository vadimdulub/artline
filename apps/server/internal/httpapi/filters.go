package httpapi

import (
	"fmt"
	"regexp"
	"sort"
	"strings"
)

var regionSlug = regexp.MustCompile(`^[a-z]+(?:-[a-z]+)*$`)

// Multi-value query parameters share one bounded, canonical representation.
// Bound raw tokens as well as unique values so duplicates cannot bypass limits.
func parseChoices(values []string, valid func(string) bool, upper bool) ([]string, error) {
	result := []string{}
	seen := map[string]bool{}
	count := 0
	for _, raw := range values {
		if len(raw) > 4096 {
			return nil, fmt.Errorf("Filter selection is too long.")
		}
		for _, value := range strings.Split(raw, ",") {
			count++
			if count > 32 {
				return nil, fmt.Errorf("Choose at most 32 values per filter.")
			}
			value = strings.ToLower(strings.TrimSpace(value))
			if upper {
				value = strings.ToUpper(value)
			}
			if value == "" {
				continue
			}
			if len(value) > 100 || !valid(value) {
				return nil, fmt.Errorf("Invalid filter value.")
			}
			if !seen[value] {
				result = append(result, value)
				seen[value] = true
			}
		}
	}
	sort.Strings(result)
	return result, nil
}

var countryPattern = regexp.MustCompile(`^[A-Z]{2}$`)

func validWorkType(value string) bool {
	return allowed(value, "painting", "fresco", "manuscript_illumination", "drawing", "watercolor", "print")
}

func parsePopular(values []string) (bool, error) {
	if len(values) == 0 {
		return true, nil
	}
	if len(values) != 1 {
		return false, fmt.Errorf("Use popular=true or popular=false once.")
	}
	switch values[0] {
	case "true":
		return true, nil
	case "false":
		return false, nil
	default:
		return false, fmt.Errorf("Use popular=true or popular=false.")
	}
}

// Accept old single-region bookmarks, repeated parameters, and comma-separated
// clients. Values are bounded and passed as a parameterized PostgreSQL array.
func parseRegions(values []string) ([]string, error) {
	regions := []string{}
	seen := map[string]bool{}
	count := 0
	for _, raw := range values {
		if len(raw) > 2048 {
			return nil, fmt.Errorf("Region selection is too long.")
		}
		for _, value := range strings.Split(raw, ",") {
			count++
			if count > 32 {
				return nil, fmt.Errorf("Choose at most 32 regions.")
			}
			value = strings.ToLower(strings.TrimSpace(value))
			if value == "" {
				continue
			}
			if len(value) > 64 || !regionSlug.MatchString(value) {
				return nil, fmt.Errorf("Use region codes such as northern-europe.")
			}
			if !seen[value] {
				regions = append(regions, value)
				seen[value] = true
			}
		}
	}
	sort.Strings(regions)
	return regions, nil
}
