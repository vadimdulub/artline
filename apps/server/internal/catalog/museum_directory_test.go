package catalog

import (
	"strings"
	"testing"
)

func TestMuseumDirectoryKeepsEvidencePolicy(t *testing.T) {
	for _, policy := range []string{
		"la.claim_type='display' AND la.review_state='accepted' AND la.superseded_by IS NULL",
		"la.checked_at<now()-interval '30 days'",
		"conflict.review_state='conflict'",
		"JOIN sources s ON s.id=la.source_id AND s.is_active",
		"aw.unlinked_creator_label IS NOT NULL",
		"a.status<>'archived' AND ($1 OR a.status='published')",
		"WHERE d.state='on_view'",
	} {
		if !strings.Contains(museumDirectoryCTE, policy) {
			t.Errorf("directory lost policy: %s", policy)
		}
	}
	if strings.Contains(museumDirectoryCTE, "GROUP BY artwork_id,institution_id") ||
		!strings.Contains(museumDirectoryCTE, "museum_memberships AS NOT MATERIALIZED (") {
		t.Fatal("directory existence checks must not aggregate global membership")
	}
	if strings.Count(museumDirectoryCTE, " OFFSET 0") != 2 {
		t.Fatal("creator visibility checks must remain correlated with the candidate artwork")
	}
	if !strings.Contains(museumScopedCTE, museumMembershipAggregate) {
		t.Fatal("museum cards must retain deduplicated holdings/display counts")
	}
}

func TestMuseumDirectoryCardScopesAndReusesNarrowWorks(t *testing.T) {
	for _, fragment := range []string{
		"aw.current_institution_id=page.id",
		"aw.current_institution_id IS DISTINCT FROM page.id",
		"la.institution_id=page.id",
		"visible_works AS MATERIALIZED (",
		"SELECT aw.id,aw.current_institution_id,aw.primary_media_id,aw.title,aw.creation_year_start",
		"JOIN artworks aw ON aw.id=visible.id",
		museumMembershipAggregate,
	} {
		if !strings.Contains(museumDirectoryCardCTE, fragment) {
			t.Errorf("card scope changed: %s", fragment)
		}
	}
	if !strings.Contains(museumDirectoryCardJSON, "museum_memberships member JOIN visible_works aw") {
		t.Fatal("cover selection should reuse the bounded narrow relation")
	}
}

func TestMuseumDirectorySelectiveCandidates(t *testing.T) {
	for _, tc := range []struct {
		filter MuseumFilter
		source string
	}{
		{MuseumFilter{Selection: "museum"}, "FROM selections"},
		{MuseumFilter{Artist: "rembrandt"}, "a.slug=ANY($7::text[])"},
		{MuseumFilter{Artists: []string{"rembrandt"}}, "a.slug=ANY($7::text[])"},
		{MuseumFilter{Movement: "baroque"}, "m.slug=ANY($8::text[])"},
		{MuseumFilter{Movements: []string{"baroque"}}, "m.slug=ANY($8::text[])"},
	} {
		cte, relation := museumDirectoryFilterCTE(tc.filter)
		if relation != "directory_filtered_memberships" || !strings.Contains(cte, tc.source) ||
			!strings.Contains(cte, "WHERE artwork_id=candidate.artwork_id OFFSET 0") {
			t.Errorf("filter not scoped: %+v", tc.filter)
		}
	}
}
