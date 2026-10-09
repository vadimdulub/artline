-- The catalogue has one visibility scope: all non-archived records. Keep old
-- status values and publication audit history; add indexes for the new reads.
CREATE INDEX artists_active_seo_id_idx ON artists(id) WHERE status<>'archived';
CREATE INDEX artworks_active_seo_id_idx ON artworks(id) WHERE status<>'archived';
CREATE INDEX institutions_active_seo_id_idx ON institutions(id) WHERE status<>'archived';
CREATE INDEX artists_active_seo_slug_idx ON artists(slug) INCLUDE(display_name) WHERE status<>'archived';
