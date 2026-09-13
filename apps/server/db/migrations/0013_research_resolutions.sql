-- Museum evidence supplements immutable supplied CSV snapshots. No public
-- visibility follows from a source match; promotion is a separate reviewed step.
CREATE TABLE research_resolutions (
 snapshot_id uuid NOT NULL,
 research_source_key text NOT NULL DEFAULT 'supplied-registry',
 research_record_kind text NOT NULL DEFAULT 'catalogue_object',
 research_record_id text NOT NULL,
 source_kind text NOT NULL CHECK(source_kind IN ('smk','tate','joconde')),
 source_object_id text NOT NULL,
 object_url text NOT NULL CHECK(object_url ~ '^https://'),
 facts_sha256 text NOT NULL CHECK(facts_sha256 ~ '^[a-f0-9]{64}$'),
 facts_json jsonb NOT NULL,
 date_scope text NOT NULL CHECK(date_scope IN ('eligible','review','excluded')),
 state text NOT NULL CHECK(state IN ('needs_review','ready','catalogued','conflict')),
 note text NOT NULL DEFAULT '',
 artist_id uuid REFERENCES artists(id),
 artwork_id uuid REFERENCES artworks(id),
 resolved_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(snapshot_id,research_source_key,research_record_kind,research_record_id,source_kind,source_object_id),
 FOREIGN KEY(snapshot_id,research_source_key,research_record_kind,research_record_id)
 REFERENCES research_records(snapshot_id,source_key,record_kind,source_record_id)
);
CREATE INDEX research_resolutions_work_idx ON research_resolutions(artwork_id) WHERE artwork_id IS NOT NULL;
CREATE INDEX research_resolutions_queue_idx ON research_resolutions(state,source_kind,research_record_id);
