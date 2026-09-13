-- Incomplete supplied records can be real review artworks without fabricated
-- types, artist authorities, accepted holdings or publication eligibility.
ALTER TABLE artworks DROP CONSTRAINT artworks_work_type_check;
ALTER TABLE artworks ADD CONSTRAINT artworks_work_type_check CHECK
 (work_type IN ('painting','fresco','manuscript_illumination','drawing','watercolor','print','unknown'));
ALTER TABLE artworks ADD COLUMN research_candidate boolean NOT NULL DEFAULT false;
ALTER TABLE artworks ADD CONSTRAINT artwork_candidate_publication CHECK
 (status<>'published' OR (NOT research_candidate AND work_type<>'unknown'));
COMMENT ON COLUMN artworks.research_candidate IS
 'Incomplete supplied artwork. Explicit identity, content-scope and evidence review must clear this flag before publication. This flag is not a museum holding or artist attribution.';

CREATE TABLE research_artwork_links (
 snapshot_id uuid NOT NULL,
 source_key text NOT NULL DEFAULT 'supplied-registry',
 record_kind text NOT NULL DEFAULT 'catalogue_object',
 research_record_id text NOT NULL,
 artwork_id uuid REFERENCES artworks(id),
 object_key text NOT NULL,
 disposition text NOT NULL CHECK(disposition IN ('created','existing','existing_conflict','excluded')),
 possible_artwork_ids uuid[] NOT NULL DEFAULT '{}',
 review_note text NOT NULL,
 plan_sha256 text NOT NULL CHECK(plan_sha256 ~ '^[a-f0-9]{64}$'),
 entry_sha256 text NOT NULL CHECK(entry_sha256 ~ '^[a-f0-9]{64}$'),
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(snapshot_id,source_key,record_kind,research_record_id),
 UNIQUE(source_key,record_kind,research_record_id),
 FOREIGN KEY(snapshot_id,source_key,record_kind,research_record_id)
 REFERENCES research_records(snapshot_id,source_key,record_kind,source_record_id),
 CHECK ((disposition IN ('created','existing'))=(artwork_id IS NOT NULL)),
 CHECK (disposition<>'existing_conflict' OR cardinality(possible_artwork_ids)>1)
);
CREATE INDEX research_artwork_links_object_idx ON research_artwork_links(object_key,artwork_id);
CREATE INDEX research_artwork_links_work_idx ON research_artwork_links(artwork_id) WHERE artwork_id IS NOT NULL;
CREATE INDEX research_artwork_links_plan_idx ON research_artwork_links(plan_sha256);
CREATE INDEX artwork_research_review_page_idx ON artworks(normalized_title,id) WHERE research_candidate AND status='review';
