-- Artist summaries and museum evidence checks read these fields for a scoped
-- set of artwork IDs. Covering indexes avoid random reads of wide source rows.
CREATE INDEX artworks_active_summary_idx ON artworks(id)
INCLUDE(current_institution_id,work_type) WHERE status<>'archived';
CREATE INDEX artwork_holding_evidence_cover_idx
ON artwork_location_assertions(artwork_id,institution_id)
INCLUDE(source_id,checked_at,effective_from,effective_to)
WHERE claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL;
CREATE INDEX artwork_holding_conflict_idx ON artwork_location_assertions(artwork_id)
WHERE claim_type='holding' AND review_state='conflict' AND superseded_by IS NULL;
