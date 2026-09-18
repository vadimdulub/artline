-- Work identities are independent of editions and of the artwork catalogue.
-- Imports remain in review. Publication is a separate editorial action.
CREATE TABLE book_records (
 id text PRIMARY KEY,
 source_id text NOT NULL UNIQUE,
 status text NOT NULL DEFAULT 'review' CHECK (status IN ('review','published','archived')),
 record jsonb NOT NULL CHECK (jsonb_typeof(record)='object' AND record->>'id'=id AND record->>'sourceId'=source_id),
 title text GENERATED ALWAYS AS (record->>'title') STORED NOT NULL,
 author_label text GENERATED ALWAYS AS (record->>'author') STORED NOT NULL,
 start_year integer GENERATED ALWAYS AS ((record->>'startYear')::integer) STORED,
 end_year integer GENERATED ALWAYS AS ((record->>'endYear')::integer) STORED,
 era text GENERATED ALWAYS AS (record->>'era') STORED NOT NULL,
 search_text text GENERATED ALWAYS AS (lower(coalesce(record->>'title','') || ' ' || coalesce(record->>'author','') || ' ' || coalesce(record->>'theme',''))) STORED,
 source_checksum text NOT NULL CHECK (source_checksum ~ '^[a-f0-9]{64}$'),
 imported_at timestamptz NOT NULL DEFAULT now(),
 CHECK ((start_year IS NULL AND end_year IS NULL) OR (start_year IS NOT NULL AND end_year IS NOT NULL AND start_year <> 0 AND end_year <> 0 AND start_year <= end_year)),
 CHECK (record->>'sourceUrl' LIKE 'https://www.wikidata.org/wiki/Q%')
);
CREATE INDEX book_chronology_idx ON book_records ((coalesce(start_year,2147483647)),id) WHERE status <> 'archived';
CREATE INDEX book_era_idx ON book_records(era) WHERE status <> 'archived';
CREATE INDEX book_status_idx ON book_records(status);
CREATE TABLE book_creators (
 id text PRIMARY KEY,
 name text NOT NULL,
 record jsonb NOT NULL CHECK (jsonb_typeof(record)='object' AND record->>'id'=id),
 source_checksum text NOT NULL CHECK (source_checksum ~ '^[a-f0-9]{64}$')
);
CREATE INDEX book_creator_name_idx ON book_creators(lower(name),id);
CREATE TABLE book_creator_links (
 book_id text NOT NULL REFERENCES book_records(id),
 creator_id text NOT NULL REFERENCES book_creators(id),
 position integer NOT NULL CHECK (position >= 0),
 credit text NOT NULL DEFAULT 'Author',
 PRIMARY KEY (book_id,creator_id)
);
CREATE INDEX book_creator_reverse_idx ON book_creator_links(creator_id,book_id);
