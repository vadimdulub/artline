-- Broad illustrated filters validate thousands of native IDs. Keep these
-- existence/evidence checks off the large media and assertion heap rows.
-- Membership follows edits immediately; source/institution visibility is still
-- checked by the query. This does not publish records or assert display status.
CREATE INDEX media_assets_atlas_deliverable_idx
ON media_assets (id)
WHERE storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$';

CREATE INDEX artwork_atlas_holding_evidence_idx
ON artwork_location_assertions (artwork_id)
INCLUDE (source_id,institution_id)
WHERE claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL;
