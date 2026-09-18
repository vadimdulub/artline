-- Historical events are separate review records; this migration publishes none.
CREATE TABLE event_records (
    id text PRIMARY KEY,
    source_id text NOT NULL UNIQUE,
    status text NOT NULL DEFAULT 'review' CHECK (status IN ('review','published','archived')),
    record jsonb NOT NULL CHECK (jsonb_typeof(record)='object'),
    source_checksum text NOT NULL CHECK (source_checksum ~ '^[0-9a-f]{64}$'),
    imported_at timestamptz NOT NULL DEFAULT now(),
    title text GENERATED ALWAYS AS (record->>'title') STORED NOT NULL,
    start_year integer GENERATED ALWAYS AS ((record->>'startYear')::integer) STORED,
    end_year integer GENERATED ALWAYS AS ((record->>'endYear')::integer) STORED,
    kind text GENERATED ALWAYS AS (record->>'kind') STORED NOT NULL,
    top100 boolean GENERATED ALWAYS AS ((record->>'top100')::boolean) STORED NOT NULL,
    search_text text GENERATED ALWAYS AS (lower((record->>'title') || ' ' || coalesce(record->>'description','') || ' ' || coalesce(record->>'significance','') || ' ' || coalesce(record->>'searchTerms',''))) STORED,
    topics text[] NOT NULL,
    countries text[] NOT NULL,
    regions text[] NOT NULL,
    CHECK ((start_year IS NULL AND end_year IS NULL) OR
       (start_year IS NOT NULL AND end_year IS NOT NULL AND start_year BETWEEN -12000 AND 2000
        AND end_year BETWEEN start_year AND 2000 AND start_year<>0 AND end_year<>0)),
    CHECK (kind IN ('Event','Period','Movement')),
    CHECK (cardinality(topics)>0)
);
CREATE INDEX event_chronology_idx ON event_records (coalesce(start_year,2147483647),id) WHERE status<>'archived';
CREATE INDEX event_top100_idx ON event_records (top100,start_year) WHERE status<>'archived';
CREATE INDEX event_topics_idx ON event_records USING gin(topics);
CREATE INDEX event_countries_idx ON event_records USING gin(countries);
CREATE INDEX event_regions_idx ON event_records USING gin(regions);
CREATE INDEX event_dates_idx ON event_records (start_year,end_year);
