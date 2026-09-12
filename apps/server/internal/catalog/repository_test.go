package catalog

import "testing"

func TestNormalizeSlug(t *testing.T) {
	t.Parallel()
	if got := NormalizeSlug("  Hilma-af-Klint-- "); got != "hilma-af-klint" {
		t.Fatalf("NormalizeSlug() = %q", got)
	}
}
