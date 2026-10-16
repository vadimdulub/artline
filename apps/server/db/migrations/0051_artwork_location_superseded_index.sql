-- Index the self-referencing FK so deleting reviewed location assertions does
-- not scan the complete assertion history for each removed row.
CREATE INDEX IF NOT EXISTS artwork_location_superseded_idx
  ON artwork_location_assertions(superseded_by)
  WHERE superseded_by IS NOT NULL;
