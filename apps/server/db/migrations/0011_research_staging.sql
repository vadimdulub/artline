-- Discovery and source catalogue evidence are not published institutions/artworks.
-- Immutable, checksum-addressed snapshots allow replay and later reconciliation.
CREATE TABLE research_snapshots (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 sha256 text NOT NULL UNIQUE CHECK(sha256 ~ '^[a-f0-9]{64}$'),
 snapshot_name text NOT NULL CHECK(length(snapshot_name) BETWEEN 1 AND 160),
 record_count integer NOT NULL CHECK(record_count BETWEEN 0 AND 100000),
 imported_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE research_records (
 snapshot_id uuid NOT NULL REFERENCES research_snapshots(id),
 source_key text NOT NULL,
 record_kind text NOT NULL CHECK(record_kind IN ('museum_candidate','museum_directory','catalogue_source','catalogue_object')),
 source_record_id text NOT NULL,
 country_code text NOT NULL,
 display_name text NOT NULL,
 source_url text NOT NULL CHECK(source_url ~ '^https://'),
 decision text NOT NULL,
 raw_json jsonb NOT NULL,
 PRIMARY KEY(snapshot_id,source_key,record_kind,source_record_id)
);
CREATE INDEX research_country_page_idx ON research_records(country_code,record_kind,source_key,source_record_id,snapshot_id);
CREATE INDEX research_review_page_idx ON research_records(source_key,record_kind,decision,source_record_id,snapshot_id);
-- Source rows may describe the same institution across sources; do not merge on
-- names, websites, co-location or Wikipedia text. No automatic public API route.
