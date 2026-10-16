-- Historical exhibitions have independent identities and no artwork-year cutoff.
-- Review status is audit data; active rows form one catalogue.
CREATE TABLE exhibitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL CHECK (btrim(title) <> ''),
  normalized_title text NOT NULL CHECK (btrim(normalized_title) <> ''),
  alternate_titles jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(alternate_titles) = 'array'),
  start_date date,
  end_date date,
  start_year integer,
  end_year integer,
  date_display text,
  date_precision text NOT NULL DEFAULT 'unknown' CHECK (date_precision IN ('day', 'month', 'year', 'mixed', 'unknown')),
  event_state text NOT NULL DEFAULT 'uncertain' CHECK (event_state IN ('held', 'announced', 'cancelled', 'uncertain')),
  state_basis text NOT NULL,
  format text NOT NULL DEFAULT 'unknown' CHECK (format IN ('physical', 'online', 'hybrid', 'unknown')),
  checklist_state text NOT NULL DEFAULT 'unknown' CHECK (checklist_state IN ('complete', 'partial', 'unavailable', 'unknown')),
  parent_exhibition_id uuid REFERENCES exhibitions(id),
  series_label text,
  status text NOT NULL DEFAULT 'review' CHECK (status IN ('draft', 'review', 'published', 'archived')),
  import_batch text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),
  CHECK (start_year IS NULL OR end_year IS NULL OR start_year <= end_year),
  CHECK (parent_exhibition_id IS NULL OR parent_exhibition_id <> id)
);
CREATE INDEX exhibitions_active_chronology_idx ON exhibitions (start_year, id) WHERE status <> 'archived';
CREATE INDEX exhibitions_active_title_idx ON exhibitions (normalized_title, id) WHERE status <> 'archived';
CREATE INDEX exhibitions_import_batch_idx ON exhibitions (import_batch, id);
CREATE INDEX exhibitions_parent_idx ON exhibitions (parent_exhibition_id) WHERE parent_exhibition_id IS NOT NULL;

CREATE TABLE exhibition_source_records (
  id uuid PRIMARY KEY,
  exhibition_id uuid NOT NULL REFERENCES exhibitions(id),
  source_key text NOT NULL CHECK (btrim(source_key) <> ''),
  source_record_id text NOT NULL CHECK (btrim(source_record_id) <> ''),
  source_url text NOT NULL CHECK (source_url ~ '^https?://'),
  retrieved_at timestamptz NOT NULL,
  capture_url text NOT NULL,
  capture_sha256 text NOT NULL CHECK (capture_sha256 ~ '^[0-9a-f]{64}$'),
  source_payload jsonb NOT NULL CHECK (jsonb_typeof(source_payload) = 'object'),
  interpretation jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (source_key, source_record_id)
);
CREATE INDEX exhibition_source_records_exhibition_idx ON exhibition_source_records (exhibition_id, id);

CREATE TABLE exhibition_occurrences (
  id uuid PRIMARY KEY,
  exhibition_id uuid NOT NULL REFERENCES exhibitions(id),
  source_record_id uuid NOT NULL REFERENCES exhibition_source_records(id),
  institution_id uuid REFERENCES institutions(id),
  source_venue_id text,
  venue_label text,
  city_label text,
  country_label text,
  country_code text,
  start_date date,
  end_date date,
  date_display text,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date)
);
CREATE INDEX exhibition_occurrences_exhibition_idx ON exhibition_occurrences (exhibition_id, id);
CREATE INDEX exhibition_occurrences_institution_idx ON exhibition_occurrences (institution_id, exhibition_id, id) WHERE institution_id IS NOT NULL;

CREATE TABLE exhibition_participants (
  id uuid PRIMARY KEY,
  exhibition_id uuid NOT NULL REFERENCES exhibitions(id),
  source_record_id uuid NOT NULL REFERENCES exhibition_source_records(id),
  artist_id uuid REFERENCES artists(id),
  institution_id uuid REFERENCES institutions(id),
  name_label text NOT NULL,
  role text NOT NULL,
  source_person_id text,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX exhibition_participants_exhibition_idx ON exhibition_participants (exhibition_id, id);
CREATE INDEX exhibition_participants_artist_idx ON exhibition_participants (artist_id, exhibition_id, id) WHERE artist_id IS NOT NULL;

CREATE TABLE exhibition_entries (
  id uuid PRIMARY KEY,
  exhibition_id uuid NOT NULL REFERENCES exhibitions(id),
  source_record_id uuid NOT NULL REFERENCES exhibition_source_records(id),
  occurrence_id uuid REFERENCES exhibition_occurrences(id),
  artwork_id uuid REFERENCES artworks(id),
  source_artwork_id text,
  catalogue_number text,
  title_label text,
  creator_label text,
  date_label text,
  medium_label text,
  dimensions_label text,
  lender_label text,
  participation text NOT NULL CHECK (participation IN ('exhibited', 'catalogued', 'illustrated_only', 'discussed_only', 'proposed', 'withdrawn', 'uncertain')),
  source_page text,
  evidence jsonb NOT NULL,
  match_basis text
);
CREATE INDEX exhibition_entries_exhibition_idx ON exhibition_entries (exhibition_id, id);
CREATE INDEX exhibition_entries_artwork_idx ON exhibition_entries (artwork_id, exhibition_id, id) WHERE artwork_id IS NOT NULL;
CREATE INDEX exhibition_entries_occurrence_idx ON exhibition_entries (occurrence_id) WHERE occurrence_id IS NOT NULL;

CREATE TABLE exhibition_publications (
  id uuid PRIMARY KEY,
  exhibition_id uuid NOT NULL REFERENCES exhibitions(id),
  source_record_id uuid NOT NULL REFERENCES exhibition_source_records(id),
  publication_type text NOT NULL CHECK (publication_type IN ('catalogue', 'checklist', 'review', 'press_release', 'installation', 'other')),
  title_label text,
  author_label text,
  publication_date_label text,
  url text,
  source_identifier text,
  page_label text,
  evidence jsonb NOT NULL
);
CREATE INDEX exhibition_publications_exhibition_idx ON exhibition_publications (exhibition_id, id);

CREATE TABLE exhibition_source_coverage (
  id uuid PRIMARY KEY,
  institution_id uuid REFERENCES institutions(id),
  source_key text,
  source_url text,
  claimed_start_year integer,
  claimed_end_year integer,
  inspected_start_year integer,
  inspected_end_year integer,
  research_state text NOT NULL CHECK (research_state IN ('not_started', 'discovered', 'partial', 'source_exhausted', 'access_held', 'no_source_found')),
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  checked_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX exhibition_source_coverage_institution_idx ON exhibition_source_coverage (institution_id, source_key);
