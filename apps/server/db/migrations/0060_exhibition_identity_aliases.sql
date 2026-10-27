-- An archived duplicate remains addressable by its original public UUID.
-- Tours and programme sections keep their separate parent_exhibition_id meaning.
ALTER TABLE exhibitions
  ADD COLUMN canonical_exhibition_id uuid REFERENCES exhibitions(id),
  ADD CONSTRAINT exhibitions_canonical_identity_check
    CHECK (canonical_exhibition_id IS NULL OR
      (canonical_exhibition_id <> id AND status = 'archived'));
CREATE INDEX exhibitions_canonical_identity_idx ON exhibitions(canonical_exhibition_id)
  WHERE canonical_exhibition_id IS NOT NULL;
