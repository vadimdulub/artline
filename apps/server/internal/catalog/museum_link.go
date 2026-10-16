package catalog

// MuseumLinkSlugSQL is a bounded, correlated link check for an institution
// aliased as i. It follows museumCTE's active holding / fresh accepted display
// membership without materializing a museum's whole collection for a link.
// Empty institutions remain useful research records and retain their labels.
const MuseumLinkSlugSQL = `CASE WHEN i.status<>'archived' AND (
 EXISTS(SELECT 1 FROM artworks link_work WHERE link_work.current_institution_id=i.id AND link_work.status<>'archived')
 OR EXISTS(SELECT 1 FROM artwork_location_assertions la
   JOIN artworks link_work ON link_work.id=la.artwork_id AND link_work.status<>'archived'
   JOIN sources source ON source.id=la.source_id AND source.is_active
   LEFT JOIN institution_venues venue ON venue.id=la.venue_id
   WHERE la.institution_id=i.id AND la.claim_type='display' AND la.review_state='accepted'
    AND la.superseded_by IS NULL AND la.display_state='on_view'
    AND la.checked_at BETWEEN now()-interval '30 days' AND now()
    AND (la.effective_from IS NULL OR la.effective_from<=now())
    AND (la.effective_to IS NULL OR la.effective_to>=now())
    AND (venue.id IS NULL OR venue.status<>'archived')
    AND NOT EXISTS(SELECT 1 FROM artwork_location_assertions conflict WHERE conflict.artwork_id=la.artwork_id
      AND conflict.claim_type='display' AND conflict.review_state='conflict' AND conflict.superseded_by IS NULL))
 ) THEN i.slug ELSE NULL END`
