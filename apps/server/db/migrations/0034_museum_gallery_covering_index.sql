-- Gallery pages select IDs before enriching their bounded cards. Cover the
-- default image/title order and date/type filters without reading every object
-- heap row in a large museum. Live installations use the accompanying operator
-- script to build this index concurrently before recording the migration.
CREATE INDEX artworks_museum_gallery_covering_idx
 ON artworks(current_institution_id,status,id)
 INCLUDE(normalized_title,creation_year_start,creation_year_end,
         primary_media_id,unlinked_creator_label,work_type)
 WHERE status<>'archived';
