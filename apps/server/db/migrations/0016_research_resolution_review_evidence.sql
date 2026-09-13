-- Supplemental source review does not rewrite the immutable matched facts.
ALTER TABLE research_resolutions ADD COLUMN review_evidence jsonb NOT NULL DEFAULT '{}'
 CHECK(jsonb_typeof(review_evidence)='object');
