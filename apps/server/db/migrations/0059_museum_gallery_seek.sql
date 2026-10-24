-- Bound gallery/title and illustrated-prefix reads before card enrichment.
-- Existing installations should build these indexes CONCURRENTLY through the
-- operator workflow before recording this migration; fresh installs are atomic.
CREATE INDEX IF NOT EXISTS artworks_museum_title_seek_idx
 ON artworks(current_institution_id,normalized_title,id)
 INCLUDE(primary_media_id,creation_year_start,creation_year_end,work_type)
 WHERE status<>'archived';
CREATE INDEX IF NOT EXISTS artworks_museum_image_title_seek_idx
 ON artworks(current_institution_id,normalized_title,id)
 INCLUDE(primary_media_id)
 WHERE status<>'archived' AND primary_media_id IS NOT NULL;

-- The standalone Artworks directory shares the paintings-only browsing policy.
CREATE INDEX IF NOT EXISTS artworks_painting_directory_seek_idx
 ON artworks(normalized_title,id) INCLUDE(primary_media_id,creation_year_start,creation_year_end)
 WHERE status<>'archived' AND work_type='painting';
