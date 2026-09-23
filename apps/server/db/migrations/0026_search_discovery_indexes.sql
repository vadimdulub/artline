-- Publication remains an explicit editorial operation. These projections of
-- published IDs support bounded sitemap range scans and keyset discovery.
CREATE INDEX artists_published_seo_id_idx ON artists(id) WHERE status='published';
CREATE INDEX artworks_published_seo_id_idx ON artworks(id) WHERE status='published';
CREATE INDEX institutions_published_seo_id_idx ON institutions(id) WHERE status='published';
CREATE INDEX artists_published_seo_slug_idx ON artists(slug) INCLUDE(display_name) WHERE status='published';
