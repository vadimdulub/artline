-- A card needs one illustrated cover, ordered by source year/title/identity.
-- Build CONCURRENTLY outside a transaction on production, verify indisvalid,
-- then record this migration. The transactional form is for fresh installs.
CREATE INDEX IF NOT EXISTS artworks_museum_illustrated_cover_idx
 ON artworks(current_institution_id,creation_year_start,title,id)
 INCLUDE(primary_media_id)
 WHERE status<>'archived' AND primary_media_id IS NOT NULL;
