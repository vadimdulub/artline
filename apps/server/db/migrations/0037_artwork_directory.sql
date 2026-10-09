-- Keyset browsing of every non-archived artwork, including undated research.
-- Build concurrently on an existing production catalogue via the release runbook.
CREATE INDEX IF NOT EXISTS artworks_directory_title_id_idx
ON artworks(normalized_title,id) WHERE status<>'archived';

CREATE INDEX IF NOT EXISTS artworks_directory_undated_idx
 ON artworks(normalized_title,id)
 WHERE status<>'archived' AND creation_year_start IS NULL AND creation_year_end IS NULL;

CREATE INDEX IF NOT EXISTS artworks_directory_media_idx
 ON artworks(primary_media_id) WHERE status<>'archived' AND primary_media_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS media_directory_local_idx ON media_assets(id)
 WHERE storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$';
