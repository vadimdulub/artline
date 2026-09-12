-- Discovery is an editorial selection, independent of media coverage or status.
CREATE TABLE artist_discovery_selection (
 artist_id uuid PRIMARY KEY REFERENCES artists(id),
 is_popular boolean NOT NULL,
 popularity_rank integer CHECK (popularity_rank > 0),
 basis text NOT NULL CHECK (length(trim(basis)) > 0),
 source_url text NOT NULL CHECK (source_url LIKE 'https://%'),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX artist_discovery_popular_idx ON artist_discovery_selection(artist_id) WHERE is_popular;

INSERT INTO artist_discovery_selection(artist_id,is_popular,popularity_rank,basis,source_url)
SELECT artist_id,true,min(rank),'Pantheon 2025 imported painter cohort: top 100 by HPI. A popularity proxy, not an artistic-quality ranking.',
 'https://pantheon.world/data/datasets'
FROM painter_import_cohort WHERE rank<=100 GROUP BY artist_id;

INSERT INTO artist_discovery_selection(artist_id,is_popular,basis,source_url)
SELECT id,true,'Editorial inclusion: Hokusai is a major painter and printmaker, omitted by the source cohort occupation label.',
 'https://www.metmuseum.org/art/collection/search/45434'
FROM artists WHERE slug='katsushika-hokusai'
ON CONFLICT(artist_id) DO NOTHING;

-- Preserve the source record; the painting atlas is not a general sculptor index.
INSERT INTO artist_discovery_selection(artist_id,is_popular,basis,source_url)
SELECT id,false,'Editorial exclusion from the popular painting selection: primarily a sculptor. Original source record retained.',
 'https://www.vam.ac.uk/articles/donatello-a-master-at-work'
FROM artists WHERE slug='donatello-q37562'
ON CONFLICT(artist_id) DO UPDATE SET is_popular=false,basis=EXCLUDED.basis,source_url=EXCLUDED.source_url;
