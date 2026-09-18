-- Rebuildable research projections. Membership never changes publication status.
CREATE TABLE book_discovery_terms (
 kind text NOT NULL CHECK (kind IN ('language','country','region')),
 key text NOT NULL,
 name text NOT NULL CHECK (length(trim(name)) > 0),
 evidence jsonb NOT NULL CHECK (jsonb_typeof(evidence) = 'object'),
 PRIMARY KEY(kind,key)
);
CREATE TABLE book_discovery (
 book_id text PRIMARY KEY REFERENCES book_records(id),
 book_checksum text NOT NULL CHECK (book_checksum ~ '^[a-f0-9]{64}$'),
 woman_author_ids text[] NOT NULL DEFAULT '{}',
 top100 boolean NOT NULL DEFAULT false,
 languages text[] NOT NULL DEFAULT '{}',
 countries text[] NOT NULL DEFAULT '{}',
 regions text[] NOT NULL DEFAULT '{}',
 evidence jsonb NOT NULL CHECK (jsonb_typeof(evidence) = 'object'),
 checked_at timestamptz NOT NULL,
 projection_checksum text NOT NULL CHECK (projection_checksum ~ '^[a-f0-9]{64}$')
);
CREATE INDEX book_discovery_women_idx ON book_discovery(book_id) WHERE cardinality(woman_author_ids)>0;
CREATE INDEX book_discovery_top100_idx ON book_discovery(book_id) WHERE top100;
CREATE INDEX book_discovery_languages_idx ON book_discovery USING gin(languages);
CREATE INDEX book_discovery_countries_idx ON book_discovery USING gin(countries);
CREATE INDEX book_discovery_regions_idx ON book_discovery USING gin(regions);

-- Source changes invalidate derived membership until research is rebuilt.
CREATE FUNCTION invalidate_book_discovery() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_TABLE_NAME='book_creators' THEN
  DELETE FROM book_discovery WHERE book_id IN (SELECT book_id FROM book_creator_links WHERE creator_id=NEW.id);
 ELSE
  DELETE FROM book_discovery WHERE book_id=NEW.id;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER book_discovery_record_changed AFTER UPDATE OF source_checksum ON book_records
 FOR EACH ROW WHEN (OLD.source_checksum IS DISTINCT FROM NEW.source_checksum) EXECUTE FUNCTION invalidate_book_discovery();
CREATE TRIGGER book_discovery_creator_changed AFTER UPDATE OF source_checksum ON book_creators
 FOR EACH ROW WHEN (OLD.source_checksum IS DISTINCT FROM NEW.source_checksum) EXECUTE FUNCTION invalidate_book_discovery();
