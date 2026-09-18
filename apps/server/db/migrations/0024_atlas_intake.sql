-- A review inbox, not a publication or catalogue import. No content is inserted.
CREATE TABLE atlas_drafts (
 id uuid PRIMARY KEY,
 kind text NOT NULL CHECK(kind IN ('artwork','book','event')),
 record jsonb NOT NULL CHECK(jsonb_typeof(record)='object'),
 status text NOT NULL DEFAULT 'review' CHECK(status IN ('review','archived')),
 revision integer NOT NULL DEFAULT 1 CHECK(revision>0),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(record->>'type'=kind AND length(trim(record->>'title'))>0)
);
CREATE INDEX atlas_drafts_page_idx ON atlas_drafts(status,created_at DESC,id DESC);
