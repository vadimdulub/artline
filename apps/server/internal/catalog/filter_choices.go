package catalog

import "slices"

// Keep repository callers using the former scalar fields compatible.
func filterChoices(values []string, legacy string) []string {
	result := append([]string{}, values...)
	if legacy != "" {
		result = append(result, legacy)
	}
	slices.Sort(result)
	return slices.Compact(result)
}
