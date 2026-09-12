CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE editor_accounts (
  user_id text PRIMARY KEY,
  email text,
  display_name text,
  role text NOT NULL CHECK (role IN ('owner', 'editor', 'reviewer')),
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  name text NOT NULL,
  source_type text NOT NULL CHECK (source_type IN ('museum_api', 'authority_data', 'collection_page', 'book', 'article', 'manual')),
  base_url text,
  api_docs_url text,
  terms_url text,
  adapter_key text,
  priority integer NOT NULL DEFAULT 100,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE countries (
  code char(2) PRIMARY KEY,
  name text NOT NULL,
  region_code text NOT NULL,
  historical_note text
);

CREATE TABLE places (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  normalized_name text NOT NULL,
  country_code char(2) REFERENCES countries(code),
  latitude double precision,
  longitude double precision,
  wikidata_id text UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE institutions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  normalized_name text NOT NULL,
  place_id uuid REFERENCES places(id),
  website_url text,
  wikidata_id text UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE media_assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  storage_kind text NOT NULL CHECK (storage_kind IN ('local', 'remote', 'placeholder')),
  storage_path text UNIQUE,
  delivery_url text,
  source_page_url text,
  provider_name text,
  mime_type text,
  width integer CHECK (width IS NULL OR width > 0),
  height integer CHECK (height IS NULL OR height > 0),
  byte_size bigint CHECK (byte_size IS NULL OR byte_size >= 0),
  checksum_sha256 char(64),
  alt_text text,
  rights_status text NOT NULL CHECK (rights_status IN ('public_domain', 'cc0', 'cc_by', 'cc_by_sa', 'licensed', 'restricted', 'unknown')),
  license_label text,
  license_url text,
  creator_credit text,
  attribution_text text,
  retrieved_at timestamptz,
  verified_at timestamptz,
  verified_by text REFERENCES editor_accounts(user_id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (storage_kind <> 'local' OR storage_path IS NOT NULL),
  CHECK (storage_kind <> 'remote' OR delivery_url IS NOT NULL)
);

CREATE TABLE movements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  name text NOT NULL,
  start_year integer,
  end_year integer,
  color_hex char(7) NOT NULL CHECK (color_hex ~ '^#[0-9A-Fa-f]{6}$'),
  summary_md text,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'published', 'archived')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (start_year IS NULL OR end_year IS NULL OR start_year <= end_year)
);

CREATE TABLE artists (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  display_name text NOT NULL,
  sort_name text NOT NULL,
  normalized_name text NOT NULL,
  entity_type text NOT NULL DEFAULT 'person' CHECK (entity_type IN ('person', 'anonymous_master', 'workshop', 'collective')),
  birth_year integer,
  death_year integer,
  birth_display text,
  death_display text,
  birth_precision text,
  death_precision text,
  active_start_year integer,
  active_end_year integer,
  activity_display text,
  timeline_start_year integer NOT NULL,
  timeline_end_year integer NOT NULL,
  timeline_display text NOT NULL,
  timeline_basis text NOT NULL CHECK (timeline_basis IN ('life', 'activity', 'mixed', 'estimated')),
  biography_md text,
  portrait_media_id uuid REFERENCES media_assets(id),
  influence_review_state text NOT NULL DEFAULT 'not_reviewed' CHECK (influence_review_state IN ('not_reviewed', 'documented', 'none_found', 'contested')),
  movement_review_state text NOT NULL DEFAULT 'not_reviewed' CHECK (movement_review_state IN ('not_reviewed', 'classified', 'unclassified')),
  geography_review_state text NOT NULL DEFAULT 'not_reviewed' CHECK (geography_review_state IN ('not_reviewed', 'classified', 'unknown')),
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'published', 'archived')),
  revision integer NOT NULL DEFAULT 1 CHECK (revision > 0),
  created_by text REFERENCES editor_accounts(user_id),
  updated_by text REFERENCES editor_accounts(user_id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  CHECK (birth_year IS NULL OR death_year IS NULL OR birth_year <= death_year),
  CHECK (active_start_year IS NULL OR active_end_year IS NULL OR active_start_year <= active_end_year),
  CHECK (timeline_start_year <= timeline_end_year)
);

CREATE TABLE artist_aliases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  artist_id uuid NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  alias text NOT NULL,
  normalized_alias text NOT NULL,
  language_code text,
  alias_type text NOT NULL DEFAULT 'alternate' CHECK (alias_type IN ('alternate', 'birth_name', 'native_name', 'historical', 'transliteration')),
  UNIQUE NULLS NOT DISTINCT (artist_id, normalized_alias, language_code)
);

CREATE TABLE slug_redirects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type text NOT NULL CHECK (entity_type IN ('artist', 'artwork', 'movement')),
  entity_id uuid NOT NULL,
  old_slug text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (entity_type, old_slug)
);

CREATE TABLE artist_countries (
  artist_id uuid NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  country_code char(2) NOT NULL REFERENCES countries(code),
  relationship_type text NOT NULL CHECK (relationship_type IN ('birth', 'death', 'citizenship', 'active', 'cultural_affiliation', 'historical_region')),
  is_primary boolean NOT NULL DEFAULT false,
  note text,
  PRIMARY KEY (artist_id, country_code, relationship_type)
);

CREATE TABLE artist_places (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  artist_id uuid NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  place_id uuid NOT NULL REFERENCES places(id),
  relationship_type text NOT NULL CHECK (relationship_type IN ('birth', 'death', 'studio', 'active', 'education', 'travel')),
  start_year integer,
  end_year integer,
  note text,
  CHECK (start_year IS NULL OR end_year IS NULL OR start_year <= end_year)
);

CREATE TABLE artist_movements (
  artist_id uuid NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  movement_id uuid NOT NULL REFERENCES movements(id),
  role text NOT NULL DEFAULT 'associated' CHECK (role IN ('primary', 'associated', 'precursor', 'later_association')),
  sort_order integer NOT NULL DEFAULT 0,
  PRIMARY KEY (artist_id, movement_id)
);

CREATE TABLE artworks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  title text NOT NULL,
  alternate_title text,
  normalized_title text NOT NULL,
  date_display text NOT NULL,
  creation_year_start integer,
  creation_year_end integer,
  date_precision text NOT NULL CHECK (date_precision IN ('exact', 'circa', 'range', 'circa_range', 'before', 'after', 'decade', 'century', 'unknown')),
  work_type text NOT NULL CHECK (work_type IN ('painting', 'fresco', 'manuscript_illumination', 'drawing', 'watercolor', 'print')),
  medium_text text,
  dimensions_text text,
  description_md text,
  creation_place_display text,
  creation_place_unknown_reason text,
  current_institution_id uuid REFERENCES institutions(id),
  current_location_text text,
  current_location_unknown_reason text,
  location_checked_at timestamptz,
  accession_number text,
  primary_media_id uuid REFERENCES media_assets(id),
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'published', 'archived')),
  revision integer NOT NULL DEFAULT 1 CHECK (revision > 0),
  created_by text REFERENCES editor_accounts(user_id),
  updated_by text REFERENCES editor_accounts(user_id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  CHECK (creation_year_start IS NULL OR creation_year_end IS NULL OR creation_year_start <= creation_year_end)
);

CREATE TABLE artwork_artists (
  artwork_id uuid NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  artist_id uuid NOT NULL REFERENCES artists(id),
  attribution_role text NOT NULL CHECK (attribution_role IN ('primary', 'workshop', 'attributed_to', 'circle_of', 'follower_of', 'formerly_attributed_to')),
  representative_order integer,
  attribution_note text,
  PRIMARY KEY (artwork_id, artist_id, attribution_role),
  CHECK (representative_order IS NULL OR representative_order BETWEEN 1 AND 10)
);

CREATE TABLE artwork_places (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  artwork_id uuid NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  place_id uuid NOT NULL REFERENCES places(id),
  relationship_type text NOT NULL CHECK (relationship_type IN ('created', 'begun', 'continued', 'completed')),
  start_year integer,
  end_year integer,
  sort_order integer NOT NULL DEFAULT 0,
  note text,
  CHECK (start_year IS NULL OR end_year IS NULL OR start_year <= end_year)
);

CREATE TABLE artwork_media (
  artwork_id uuid NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  media_id uuid NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
  sort_order integer NOT NULL DEFAULT 0,
  view_label text,
  PRIMARY KEY (artwork_id, media_id)
);

CREATE TABLE influence_claims (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_artist_id uuid REFERENCES artists(id),
  source_label text NOT NULL,
  target_artist_id uuid NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  relationship_type text NOT NULL CHECK (relationship_type IN ('influenced', 'teacher_of', 'workshop_of', 'collaborated_with', 'documented_admiration', 'responded_to_work_of')),
  evidence_level text NOT NULL CHECK (evidence_level IN ('documented', 'scholarly_consensus', 'contested', 'editorial_inference')),
  confidence text NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
  evidence_note text NOT NULL,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'published', 'archived')),
  created_by text REFERENCES editor_accounts(user_id),
  updated_by text REFERENCES editor_accounts(user_id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (source_artist_id IS NOT NULL OR length(trim(source_label)) > 0),
  CHECK (source_artist_id IS NULL OR source_artist_id <> target_artist_id)
);

CREATE TABLE external_identifiers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type text NOT NULL CHECK (entity_type IN ('artist', 'artwork', 'movement', 'place', 'institution')),
  entity_id uuid NOT NULL,
  scheme text NOT NULL,
  external_id text NOT NULL,
  canonical_url text,
  source_id uuid REFERENCES sources(id),
  retrieved_at timestamptz,
  UNIQUE (scheme, external_id),
  UNIQUE (entity_type, entity_id, scheme)
);

CREATE TABLE citations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type text NOT NULL CHECK (entity_type IN ('artist', 'artwork', 'movement', 'influence', 'place', 'institution', 'media')),
  entity_id uuid NOT NULL,
  field_name text NOT NULL,
  source_id uuid NOT NULL REFERENCES sources(id),
  source_record_id text,
  source_url text NOT NULL,
  page_or_locator text,
  evidence_note text,
  retrieved_at timestamptz NOT NULL,
  created_by text REFERENCES editor_accounts(user_id),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE import_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL REFERENCES sources(id),
  requested_by text NOT NULL REFERENCES editor_accounts(user_id),
  adapter_version text NOT NULL,
  query_json jsonb NOT NULL,
  status text NOT NULL CHECK (status IN ('preview', 'running', 'needs_review', 'completed', 'failed', 'cancelled')),
  idempotency_key text NOT NULL UNIQUE,
  checkpoint_json jsonb,
  raw_manifest_path text,
  total_records integer NOT NULL DEFAULT 0,
  accepted_records integer NOT NULL DEFAULT 0,
  rejected_records integer NOT NULL DEFAULT 0,
  error_summary text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);

CREATE TABLE import_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  import_job_id uuid NOT NULL REFERENCES import_jobs(id) ON DELETE CASCADE,
  source_record_id text NOT NULL,
  source_checksum char(64) NOT NULL,
  raw_path text,
  outcome text NOT NULL CHECK (outcome IN ('pending', 'created', 'updated', 'skipped', 'rejected', 'conflict', 'failed')),
  matched_entity_type text,
  matched_entity_id uuid,
  warnings_json jsonb,
  error_text text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (import_job_id, source_record_id)
);

CREATE TABLE audit_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_user_id text REFERENCES editor_accounts(user_id),
  action text NOT NULL,
  entity_type text NOT NULL,
  entity_id uuid NOT NULL,
  request_id text,
  before_json jsonb,
  after_json jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_artists_status_timeline_start ON artists(status, timeline_start_year);
CREATE INDEX idx_artists_status_timeline_end ON artists(status, timeline_end_year);
CREATE INDEX idx_artists_normalized_name ON artists(normalized_name);
CREATE INDEX idx_artist_aliases_normalized_alias ON artist_aliases(normalized_alias);
CREATE INDEX idx_slug_redirects_entity ON slug_redirects(entity_type, entity_id);
CREATE INDEX idx_artist_countries_country_artist ON artist_countries(country_code, artist_id);
CREATE INDEX idx_artist_movements_movement_artist ON artist_movements(movement_id, artist_id);
CREATE UNIQUE INDEX idx_artist_movements_one_primary ON artist_movements(artist_id) WHERE role = 'primary';
CREATE INDEX idx_artwork_artists_artist_order ON artwork_artists(artist_id, representative_order);
CREATE INDEX idx_artwork_places_artwork_order ON artwork_places(artwork_id, sort_order);
CREATE INDEX idx_artworks_status_creation_year ON artworks(status, creation_year_start);
CREATE INDEX idx_influence_claims_target_status ON influence_claims(target_artist_id, status);
CREATE INDEX idx_influence_claims_source_status ON influence_claims(source_artist_id, status);
CREATE INDEX idx_citations_entity_field ON citations(entity_type, entity_id, field_name);
CREATE INDEX idx_import_records_job_outcome ON import_records(import_job_id, outcome);
CREATE INDEX idx_audit_log_entity_created ON audit_log(entity_type, entity_id, created_at DESC);

