-- Preserve imported institution identities while consolidating reviewed aliases.
-- No institution is merged or published by this schema migration.
ALTER TABLE institutions ADD COLUMN canonical_institution_id uuid REFERENCES institutions(id);
ALTER TABLE institutions ADD CONSTRAINT institution_alias_not_self
 CHECK(canonical_institution_id IS NULL OR canonical_institution_id<>id);
CREATE INDEX institutions_canonical_idx ON institutions(canonical_institution_id)
 WHERE canonical_institution_id IS NOT NULL;

CREATE FUNCTION artline_validate_institution_alias() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 PERFORM pg_advisory_xact_lock(202610053);
 IF NEW.canonical_institution_id IS NOT NULL THEN
  IF EXISTS(SELECT 1 FROM institutions WHERE id=NEW.canonical_institution_id AND canonical_institution_id IS NOT NULL)
     OR EXISTS(SELECT 1 FROM institutions WHERE canonical_institution_id=NEW.id) THEN
   RAISE EXCEPTION 'institution aliases must point directly to a canonical institution';
  END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER institution_alias_identity BEFORE INSERT OR UPDATE OF canonical_institution_id ON institutions
 FOR EACH ROW EXECUTE FUNCTION artline_validate_institution_alias();

-- Normalizing new imports prevents source-specific museum identifiers from
-- splitting the collection again. Locks serialize a concurrent reconciliation.
CREATE FUNCTION artline_normalize_artwork_institution() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE canonical uuid;
BEGIN
 IF NEW.current_institution_id IS NOT NULL THEN
  SELECT canonical_institution_id INTO canonical FROM institutions
   WHERE id=NEW.current_institution_id FOR SHARE;
  NEW.current_institution_id:=coalesce(canonical,NEW.current_institution_id);
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER artwork_canonical_institution BEFORE INSERT OR UPDATE OF current_institution_id ON artworks
 FOR EACH ROW EXECUTE FUNCTION artline_normalize_artwork_institution();

CREATE FUNCTION artline_normalize_assertion_institution() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE canonical uuid;
BEGIN
 SELECT canonical_institution_id INTO canonical FROM institutions WHERE id=NEW.institution_id FOR SHARE;
 NEW.institution_id:=coalesce(canonical,NEW.institution_id);
 RETURN NEW;
END $$;
CREATE TRIGGER assertion_canonical_institution BEFORE INSERT OR UPDATE OF institution_id ON artwork_location_assertions
 FOR EACH ROW EXECUTE FUNCTION artline_normalize_assertion_institution();

-- A reviewed reconciliation can move a venue and its assertions together.
ALTER TABLE artwork_location_assertions
 ALTER CONSTRAINT artwork_location_assertions_venue_id_institution_id_fkey DEFERRABLE INITIALLY IMMEDIATE;
