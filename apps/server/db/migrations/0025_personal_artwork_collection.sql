-- An owner's collection may include works with no known holding institution.
-- This selection does not create a museum, holding, display claim or publication.
ALTER TABLE curated_collections ALTER COLUMN institution_id DROP NOT NULL;
ALTER TABLE curated_collections ADD CONSTRAINT museum_collection_requires_institution
  CHECK(curator_kind='owner' OR institution_id IS NOT NULL);
CREATE UNIQUE INDEX curated_global_owner_collection
  ON curated_collections(curator_kind) WHERE institution_id IS NULL;
COMMENT ON INDEX curated_global_owner_collection IS
  'One personal owner collection independent of museum holdings; institution-scoped owner lists retain their existing uniqueness.';
