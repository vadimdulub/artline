package guides

import (
	"encoding/json"
	"net/url"
	"strings"
	"testing"
)

func TestSearchEditorialGuides(t *testing.T) {
	for _, tc := range []struct{ query, slug string }{
		{"FRIDA kahlo", "frida-kahlo"}, {"Velazquez", "prado"}, {"Louvre Paris", "louvre"}, {"art history through time", "art-history-timeline"},
	} {
		t.Run(tc.query, func(t *testing.T) {
			page, err := Default.Search(url.Values{"q": {tc.query}})
			if err != nil {
				t.Fatal(err)
			}
			found := false
			for _, item := range page.Items {
				if item.Slug == tc.slug {
					found = true
				}
			}
			if !found {
				t.Fatalf("missing %s in %+v", tc.slug, page)
			}
		})
	}
	a, _ := Default.Search(url.Values{"q": {"Velázquez"}})
	b, _ := Default.Search(url.Values{"q": {"velazquez"}})
	if a.Matched == 0 || a.Matched != b.Matched {
		t.Fatal("accent normalization mismatch")
	}
	a, _ = Default.Search(url.Values{"q": {"nothingwillmatchthisguide"}})
	if a.Matched != 0 || a.Items == nil || a.NextCursor != "" {
		t.Fatal("invalid empty result")
	}
	raw, _ := json.Marshal(b)
	if strings.Contains(string(raw), `"search"`) || strings.Contains(string(raw), `"sources"`) {
		t.Fatal("internal projection exposed")
	}
}

func TestSearchTranslatedTitle(t *testing.T) {
	// The published Russian edition is searchable without transliteration.
	var doc struct {
		Entries []document `json:"entries"`
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		t.Fatal(err)
	}
	page, err := Default.Search(url.Values{"q": {"Фрида"}, "kind": {"artist"}})
	if err != nil || page.Matched < 1 || page.Items[0].Slug != "frida-kahlo" {
		t.Fatalf("translated query: %+v %v", page, err)
	}
}

func TestPaginationAndScopes(t *testing.T) {
	seen := map[string]bool{}
	q := url.Values{}
	count := 0
	for {
		page, err := Default.Search(q)
		if err != nil {
			t.Fatal(err)
		}
		if len(page.Items) > PageSize {
			t.Fatal("unbounded results")
		}
		count = page.Total
		for _, item := range page.Items {
			if seen[item.Slug] {
				t.Fatalf("duplicate %s", item.Slug)
			}
			seen[item.Slug] = true
		}
		if page.NextCursor == "" {
			break
		}
		q.Set("cursor", page.NextCursor)
	}
	if len(seen) != count {
		t.Fatalf("missing results %d/%d", len(seen), count)
	}
	first, _ := Default.Search(url.Values{})
	for _, q := range []url.Values{
		{"cursor": {first.NextCursor}, "q": {"Paris"}}, {"cursor": {first.NextCursor}, "kind": {"museum"}},
		{"cursor": {"invalid"}}, {"q": {strings.Repeat("é", 201)}}, {"q": {"a", "b"}}, {"kind": {"bad"}},
	} {
		if _, err := Default.Search(q); err == nil {
			t.Fatalf("accepted invalid filters %v", q)
		}
	}
	updated := *Default
	updated.version = "new-editions"
	if _, err := updated.Search(url.Values{"cursor": {first.NextCursor}}); err == nil {
		t.Fatal("accepted old edition cursor")
	}
	artists, err := Default.Search(url.Values{"kind": {"artist"}})
	if err != nil || artists.Matched != artists.Counts["artist"] || artists.Counts["museum"] == 0 {
		t.Fatal("incorrect facets")
	}
	for _, item := range artists.Items {
		if item.Kind != "artist" {
			t.Fatal("wrong kind")
		}
	}
}

func TestMuseumGuideIdentityAndReadOnlyProjection(t *testing.T) {
	for _, tc := range []struct{ institution, guide string }{
		{"national-gallery-london", "national-gallery-london"}, {"musee-du-louvre", "louvre"},
		{"wikimedia-museum-q705551", "art-gallery-new-south-wales"},
		{"alte-pinakothek", "munich-museums"}, {"neue-pinakothek", "munich-museums"}, {"lenbachhaus-munich", "munich-museums"},
	} {
		page, err := Default.Search(url.Values{"institution": {tc.institution}})
		if err != nil || page.Total != 1 || page.Matched != 1 || len(page.Items) != 1 || page.Items[0].Slug != tc.guide || page.Items[0].Href != "/guides/"+tc.guide {
			t.Fatalf("museum %s: %+v %v", tc.institution, page, err)
		}
	}
	for _, q := range []url.Values{{"institution": {"unmatched-museum"}}, {"institution": {"musee-du-louvre"}, "q": {"Monet"}}, {"institution": {"musee-du-louvre"}, "kind": {"artist"}}} {
		page, err := Default.Search(q)
		if err != nil || page.Matched != 0 || len(page.Items) != 0 {
			t.Fatalf("leaked unrelated guide: %+v %v", page, err)
		}
	}
	page, _ := Default.Search(url.Values{"institution": {"musee-du-louvre"}, "q": {"Leonardo"}})
	if page.Matched != 1 {
		t.Fatal("museum-scoped title search failed")
	}
	first, _ := Default.Search(url.Values{})
	for _, q := range []url.Values{{"institution": {"../louvre"}}, {"institution": {"louvre", "prado"}}, {"institution": {"musee-du-louvre"}, "cursor": {first.NextCursor}}} {
		if _, err := Default.Search(q); err == nil {
			t.Fatal("invalid museum scope accepted", q)
		}
	}
	// All prepared museum guides are associated explicitly, including guides whose
	// public slug differs from the catalogue's institution slug. Never name-match.
	for _, d := range Default.entries {
		if d.Kind == "museum" && len(d.Institutions) == 0 {
			t.Fatal("unmapped museum guide", d.Slug)
		}
	}
}
