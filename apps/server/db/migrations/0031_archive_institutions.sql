-- Archival photographs can be explicitly selected without calling their
-- repository a museum or asserting physical custody of the depicted object.
ALTER TABLE institutions DROP CONSTRAINT institutions_kind_check;
ALTER TABLE institutions ADD CONSTRAINT institutions_kind_check
  CHECK(kind IN ('museum','historic_site','foundation','archive'));
