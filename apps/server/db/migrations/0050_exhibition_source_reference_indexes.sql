-- Source-record deletion/reconciliation must not rescan all child rows for each
-- source. These also support exact source-scoped evidence maintenance.
CREATE INDEX IF NOT EXISTS exhibition_entries_source_idx ON exhibition_entries(source_record_id);
CREATE INDEX IF NOT EXISTS exhibition_occurrences_source_idx ON exhibition_occurrences(source_record_id);
CREATE INDEX IF NOT EXISTS exhibition_participants_source_idx ON exhibition_participants(source_record_id);
CREATE INDEX IF NOT EXISTS exhibition_publications_source_idx ON exhibition_publications(source_record_id);
