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
		"aw.status<>'archived'",
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
	if strings.Contains(museumDirectoryCTE, "status='published'") {
		t.Fatal("directory must include every active status")
	}
	if !strings.Contains(museumScopedCTE, museumMembershipAggregate) {
		t.Fatal("museum cards must retain deduplicated holdings/display counts")
	}
}

func TestMuseumDirectoryCardScopesIndexedReads(t *testing.T) {
	for _, fragment := range []string{
		"aw.current_institution_id=page.id",
		"current_institution_id IS DISTINCT FROM page.id",
		"d.institution_id=page.id AND d.state='on_view'",
		"SELECT DISTINCT aw.id,aw.title,aw.creation_year_start,aw.primary_media_id,aw.current_institution_id",
		"SELECT (SELECT count(*) FROM card_holdings) AS holdings",
	} {
		if !strings.Contains(museumDirectoryCardCTE, fragment) {
			t.Errorf("card scope changed: %s", fragment)
		}
	}
	if !strings.Contains(museumDirectoryCardCTE, "FROM selections s WHERE s.institution_id=page.id") ||
		!strings.Contains(museumDirectoryCardJSON, "FROM card_holdings aw WHERE aw.primary_media_id IS NOT NULL") {
		t.Fatal("highlight and cover lookup must start from indexed candidates")
	}
}

func TestMuseumDirectorySelectiveCandidates(t *testing.T) {
	for _, tc := range []struct {
		filter MuseumFilter
		source string
	}{
		{MuseumFilter{Selection: "museum"}, "FROM selections"},
		{MuseumFilter{Artist: "rembrandt"}, "a.slug=ANY($6::text[])"},
		{MuseumFilter{Artists: []string{"rembrandt"}}, "a.slug=ANY($6::text[])"},
		{MuseumFilter{Movement: "baroque"}, "m.slug=ANY($7::text[])"},
		{MuseumFilter{Movements: []string{"baroque"}}, "m.slug=ANY($7::text[])"},
	} {
		cte, relation := museumDirectoryFilterCTE(tc.filter)
		if relation != "directory_filtered_memberships" || !strings.Contains(cte, tc.source) ||
			!strings.Contains(cte, "WHERE artwork_id=candidate.artwork_id OFFSET 0") {
			t.Errorf("filter not scoped: %+v", tc.filter)
		}
	}
}
