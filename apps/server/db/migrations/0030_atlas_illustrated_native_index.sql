-- Keep native illustrated-window scans off the wide artwork heap. Membership,
-- source activity, publication and media delivery are still validated at read
-- time. PostgreSQL maintains this index when dates/images/status are edited.
CREATE INDEX artworks_atlas_illustrated_native_idx
ON artworks (coalesce(creation_year_start,creation_year_end),id)
INCLUDE (creation_year_start,creation_year_end,status,date_precision,
         primary_media_id,work_type,cultural_context)
WHERE status<>'archived' AND primary_media_id IS NOT NULL
 AND date_precision IN ('exact','circa','range','circa_range','decade','century')
 AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible'
 AND coalesce(creation_year_start,creation_year_end)<>0
 AND coalesce(creation_year_end,creation_year_start)<>0;
