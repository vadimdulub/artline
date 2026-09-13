-- Bulk reconciliation is scoped by the selected source-record IDs. Without
-- this index each small batch reads the entire immutable research collection.
CREATE INDEX research_records_identity_lookup_idx
 ON research_records(source_record_id,source_key,record_kind);
