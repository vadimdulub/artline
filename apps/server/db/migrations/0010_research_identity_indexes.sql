-- Exact source-identity reconciliation must not scan ten million artwork rows.
-- These are intentionally non-unique: ambiguous legacy records must be reported,
-- not hidden by an arbitrary LIMIT 1 or silently merged.
CREATE INDEX external_identifiers_url_idx ON external_identifiers(entity_type,canonical_url,entity_id)
  WHERE canonical_url IS NOT NULL;
CREATE INDEX citations_source_url_idx ON citations(entity_type,source_url,entity_id);
CREATE INDEX artworks_institution_accession_idx ON artworks(current_institution_id,accession_number,id)
  WHERE accession_number IS NOT NULL;
