-- Durable, versioned research projections. Documentary exhibition objects do
-- not expand the main artwork catalogue's creation-date eligibility.
CREATE TABLE exhibition_research_batches (
  id text PRIMARY KEY,
  corpus_sha256 text NOT NULL CHECK (corpus_sha256 ~ '^[0-9a-f]{64}$'),
  manifest jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE exhibition_research (
  exhibition_id uuid PRIMARY KEY REFERENCES exhibitions(id),
  batch_id text NOT NULL REFERENCES exhibition_research_batches(id),
  detail jsonb NOT NULL CHECK (jsonb_typeof(detail)='object' AND NOT detail ? 'entries'),
  summary jsonb NOT NULL CHECK (jsonb_typeof(summary)='object' AND NOT summary ? 'entries'),
  concepts text[] NOT NULL,
  featured boolean NOT NULL DEFAULT false,
  entry_count integer NOT NULL CHECK (entry_count >= 0),
  illustrated_count integer NOT NULL CHECK (illustrated_count BETWEEN 0 AND entry_count)
);
CREATE INDEX exhibition_research_concepts_idx ON exhibition_research USING gin(concepts);
CREATE TABLE exhibition_research_people (
  exhibition_id uuid NOT NULL REFERENCES exhibition_research(exhibition_id),
  person_id uuid NOT NULL,
  artist_id uuid REFERENCES artists(id),
  PRIMARY KEY(exhibition_id,person_id)
);
CREATE INDEX exhibition_research_people_person_idx ON exhibition_research_people(person_id,exhibition_id);
CREATE INDEX exhibition_research_people_artist_idx ON exhibition_research_people(artist_id,exhibition_id) WHERE artist_id IS NOT NULL;
CREATE TABLE exhibition_objects (
  id uuid PRIMARY KEY,
  provider text NOT NULL,
  source_object_id text NOT NULL,
  artwork_id uuid REFERENCES artworks(id),
  batch_id text NOT NULL REFERENCES exhibition_research_batches(id),
  detail jsonb NOT NULL CHECK (jsonb_typeof(detail)='object' AND NOT detail ? 'appearances'),
  UNIQUE(provider,source_object_id)
);
CREATE INDEX exhibition_objects_artwork_idx ON exhibition_objects(artwork_id,id) WHERE artwork_id IS NOT NULL;
CREATE TABLE exhibition_object_entries (
  id uuid PRIMARY KEY,
  exhibition_id uuid NOT NULL REFERENCES exhibition_research(exhibition_id),
  object_id uuid NOT NULL REFERENCES exhibition_objects(id),
  source_record_id uuid NOT NULL REFERENCES exhibition_source_records(id),
  participation text NOT NULL CHECK (participation IN ('exhibited','catalogued','illustrated_only','discussed_only','proposed','withdrawn','uncertain')),
  detail jsonb NOT NULL CHECK (jsonb_typeof(detail)='object'),
  appearance jsonb NOT NULL CHECK (jsonb_typeof(appearance)='object'),
  UNIQUE(exhibition_id,object_id)
);
CREATE INDEX exhibition_object_entries_exhibition_idx ON exhibition_object_entries(exhibition_id,id);
CREATE INDEX exhibition_object_entries_participation_idx ON exhibition_object_entries(exhibition_id,participation,id);
CREATE INDEX exhibition_object_entries_object_idx ON exhibition_object_entries(object_id,id);
-- A reviewed complete-list projection supersedes the earlier sampled response,
-- while original source records and sampled entries remain immutable evidence.
-- Corrections require a new batch manifest and atomic replacement of all affected
-- projections/relationships; no status transition controls catalogue visibility.
