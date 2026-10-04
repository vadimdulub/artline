package atlas

import (
	"cmp"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strings"
	"testing"
)

func compareGalleryItems(a, b Item) int {
	return cmp.Or(cmp.Compare(a.galleryPriority, b.galleryPriority), cmp.Compare(a.StartYear, b.StartYear), strings.Compare(a.ID, b.ID))
}

func TestGalleryCursor(t *testing.T) {
	f := Filter{Range: Bounds, Types: []string{"artwork"}, Limit: 3}
	for _, priority := range []int{0, 1, 2} {
		item := Item{ID: "00000000-0000-0000-0000-000000000001", StartYear: 1600, galleryPriority: priority}
		token := encodeCursor(item, f, "artwork")
		c, err := decodeCursor(token, f, "artwork")
		if err != nil || c.Priority != priority || c.Year != item.StartYear || c.ID != item.ID {
			t.Fatalf("cursor lost gallery position: %+v %v", c, err)
		}
		for _, invalid := range []int{-1, 3} {
			c.Priority = invalid
			raw, _ := json.Marshal(c)
			if _, err := decodeCursor(base64.RawURLEncoding.EncodeToString(raw), f, "artwork"); err == nil {
				t.Fatal("accepted an invalid priority")
			}
		}
		raw, _ := json.Marshal(item)
		if strings.Contains(string(raw), "riority") {
			t.Fatal("internal gallery priority leaked into public artwork metadata")
		}
	}
	// A chronological-only cursor must be rejected, rather than skip or repeat
	// records after changing sort order. Its old scope did not include a version.
	legacy := []any{f.Range, "", f.Types, false, false, "", f.Limit, "artwork", false, map[string][]string{}, f.Entities, f.Countries, f.Continents, f.CountryScope, f.Creators, "", presetFocus("")}
	raw, _ := json.Marshal(legacy)
	old := cursor{Year: 1600, ID: "00000000-0000-0000-0000-000000000001", Scope: fmt.Sprintf("%x", sha256.Sum256(raw))[:24]}
	raw, _ = json.Marshal(old)
	if _, err := decodeCursor(base64.RawURLEncoding.EncodeToString(raw), f, "artwork"); err == nil {
		t.Fatal("old gallery cursor was accepted")
	}
	book := Item{ID: "book-one", StartYear: 1600}
	c, _ := decodeCursor(encodeCursor(book, f, "book"), f, "book")
	c.Priority = 1
	raw, _ = json.Marshal(c)
	if _, err := decodeCursor(base64.RawURLEncoding.EncodeToString(raw), f, "book"); err == nil {
		t.Fatal("book cursor accepted artwork ordering")
	}
}
