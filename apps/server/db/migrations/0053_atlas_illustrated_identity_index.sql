-- Selected creators yield UUIDs, not years. The existing year-first covering
-- index serves broad windows; this companion avoids random wide artwork-row
-- reads for a few thousand selected IDs. Source and image evidence remain live.
-- Production may prebuild this exact index CONCURRENTLY before this migration.
CREATE INDEX IF NOT EXISTS artworks_atlas_illustrated_identity_idx
ON artworks (id)
INCLUDE (creation_year_start,creation_year_end,primary_media_id,work_type,cultural_context)
WHERE status<>'archived' AND primary_media_id IS NOT NULL
 AND date_precision IN ('exact','circa','range','circa_range','decade','century')
 AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible'
 AND coalesce(creation_year_start,creation_year_end)<>0
 AND coalesce(creation_year_end,creation_year_start)<>0;
