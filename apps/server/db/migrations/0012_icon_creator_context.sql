-- Object-level catalogue attribution is not a fabricated artist authority.
-- NULL preserves the existing linked-artist visibility policy for all old rows.
ALTER TABLE artworks
  ADD COLUMN unlinked_creator_label text,
  ADD COLUMN cultural_context text,
  ADD COLUMN object_form text,
  ADD CONSTRAINT artwork_unlinked_creator_label CHECK
    (unlinked_creator_label IS NULL OR length(trim(unlinked_creator_label)) BETWEEN 1 AND 500),
  ADD CONSTRAINT artwork_cultural_context CHECK
    (cultural_context IS NULL OR length(trim(cultural_context)) BETWEEN 1 AND 500),
  ADD CONSTRAINT artwork_object_form CHECK (object_form IS NULL OR object_form='icon');

COMMENT ON COLUMN artworks.unlinked_creator_label IS
  'Reviewed source-level creator wording when no authority is linked; never a substitute for a hidden/archived linked artist. May identify an unresolved named creator or an unidentified workshop.';
COMMENT ON COLUMN artworks.cultural_context IS
  'Source-backed tradition/school context, not nationality inferred from the holding museum or an artist biography.';
COMMENT ON COLUMN artworks.object_form IS
  'Object form independent of medium/work_type: a painted icon remains a painting.';
