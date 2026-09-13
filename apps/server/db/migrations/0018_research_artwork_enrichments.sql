-- Supplemental researched facts never replace the immutable supplied CSV.
CREATE TABLE research_artwork_enrichments (
 plan_sha256 text NOT NULL CHECK(plan_sha256 ~ '^[a-f0-9]{64}$'),
 research_record_id text NOT NULL,
 research_source_key text NOT NULL DEFAULT 'supplied-registry',
 research_record_kind text NOT NULL DEFAULT 'catalogue_object',
 entry_sha256 text NOT NULL CHECK(entry_sha256 ~ '^[a-f0-9]{64}$'),
 artwork_id uuid NOT NULL REFERENCES artworks(id),
 artist_id uuid NOT NULL REFERENCES artists(id),
 museum_source text NOT NULL,
 source_object_id text NOT NULL,
 source_url text NOT NULL CHECK(source_url LIKE 'https://%'),
 evidence_json jsonb NOT NULL CHECK(jsonb_typeof(evidence_json)='object'),
 metadata_enriched boolean NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(plan_sha256,research_record_id),
 FOREIGN KEY(research_source_key,research_record_kind,research_record_id)
 REFERENCES research_artwork_links(source_key,record_kind,research_record_id)
);
CREATE INDEX research_artwork_enrichments_work_idx ON research_artwork_enrichments(artwork_id);
CREATE INDEX research_artwork_enrichments_source_idx ON research_artwork_enrichments(museum_source,source_object_id);
