-- Additive: retain all existing review data. Eligibility is not publication.
CREATE FUNCTION artline_creation_scope(first_year integer,last_year integer,date_kind text)
RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
 SELECT CASE
 WHEN date_kind='unknown' OR (first_year IS NULL AND last_year IS NULL) THEN 'review'
 WHEN first_year IS NOT NULL AND last_year IS NOT NULL AND first_year>last_year THEN 'review'
 WHEN date_kind='after' THEN CASE WHEN first_year>=1970 THEN 'excluded' ELSE 'review' END
 WHEN date_kind='before' THEN CASE WHEN coalesce(last_year,first_year)<=1971 THEN 'eligible' ELSE 'review' END
 WHEN first_year>1970 THEN 'excluded'
 WHEN last_year>1970 THEN 'review'
 WHEN date_kind IN ('range','circa_range','decade','century') AND (first_year IS NULL OR last_year IS NULL) THEN 'review'
 WHEN date_kind IN ('circa','circa_range') AND coalesce(last_year,first_year)=1970 THEN 'review'
 WHEN date_kind NOT IN ('exact','circa','range','circa_range','decade','century') THEN 'review'
 ELSE 'eligible' END
$$;

CREATE INDEX artworks_institution_year_page_idx ON artworks(current_institution_id,creation_year_start,normalized_title,id)
 WHERE status<>'archived';
CREATE INDEX artwork_display_institution_idx ON artwork_location_assertions(institution_id,artwork_id)
 WHERE claim_type='display' AND review_state='accepted' AND superseded_by IS NULL;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX artist_display_search_idx ON artists USING gin(display_name gin_trgm_ops);
CREATE INDEX artist_sort_search_idx ON artists USING gin(sort_name gin_trgm_ops);
CREATE INDEX artist_alias_search_idx ON artist_aliases USING gin(alias gin_trgm_ops);
CREATE INDEX artwork_title_search_idx ON artworks USING gin(title gin_trgm_ops);

-- Payloads are kept outside the public asset directory, in auditable database rows.
ALTER TABLE import_records ADD COLUMN raw_json jsonb;
ALTER TABLE import_records ADD COLUMN normalized_json jsonb;
CREATE TABLE painter_import_cohort (
 import_job_id uuid NOT NULL REFERENCES import_jobs(id),
 artist_id uuid NOT NULL REFERENCES artists(id),
 authority_id text NOT NULL,
 rank integer NOT NULL CHECK(rank>0),
 popularity_score double precision NOT NULL,
 selection_note text NOT NULL,
 PRIMARY KEY(import_job_id,artist_id),
 UNIQUE(import_job_id,authority_id),
 UNIQUE(import_job_id,rank)
);
CREATE TABLE media_rights_evidence (
 media_id uuid PRIMARY KEY REFERENCES media_assets(id),
 source_id uuid NOT NULL REFERENCES sources(id),
 source_record_id text NOT NULL,
 source_checksum char(64) NOT NULL,
 source_image_url text NOT NULL CHECK(source_image_url ~ '^https://'),
 policy_url text NOT NULL CHECK(policy_url ~ '^https://'),
 rights_basis text NOT NULL,
 adapter_version text NOT NULL,
 checked_at timestamptz NOT NULL,
 evidence_json jsonb NOT NULL
);

CREATE FUNCTION artline_has_selection_evidence(work_id uuid) RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT EXISTS(SELECT 1 FROM artwork_location_assertions la JOIN sources s ON s.id=la.source_id
   JOIN institutions i ON i.id=la.institution_id
   WHERE la.artwork_id=work_id AND la.claim_type='holding' AND la.review_state='accepted'
   AND la.superseded_by IS NULL AND s.is_active AND i.status<>'archived'
   AND length(trim(la.evidence_note))>0 AND la.checked_at<=now())
 OR EXISTS(SELECT 1 FROM curated_collection_items ci JOIN curated_collections cc ON cc.id=ci.collection_id
   LEFT JOIN sources s ON s.id=ci.source_id
   WHERE ci.artwork_id=work_id AND cc.status<>'archived' AND length(trim(ci.reason))>0
   AND (cc.curator_kind='owner' OR (s.is_active AND ci.source_url IS NOT NULL AND ci.checked_at<=now())))
$$;
