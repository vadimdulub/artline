-- Discovery membership is sourced independently of publication and popularity.
-- Missing evidence means unknown, not an inferred gender.
CREATE TABLE artist_gender_evidence (
 artist_id uuid PRIMARY KEY REFERENCES artists(id),
 is_woman boolean NOT NULL,
 basis text NOT NULL CHECK (length(trim(basis)) > 0),
 source_url text NOT NULL CHECK (source_url LIKE 'https://%'),
 source_record_id text NOT NULL CHECK (length(trim(source_record_id)) > 0),
 source_checksum text NOT NULL CHECK (source_checksum ~ '^[a-f0-9]{64}$'),
 evidence_json jsonb NOT NULL CHECK (jsonb_typeof(evidence_json) = 'object'),
 checked_at timestamptz NOT NULL,
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX artist_gender_women_idx ON artist_gender_evidence(artist_id) WHERE is_woman;
