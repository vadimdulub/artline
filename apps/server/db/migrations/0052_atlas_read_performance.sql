-- Teach the planner the actual distributions behind the illustrated-window
-- index. Without expression statistics it estimated 155 rows for 302,090
-- candidates, choosing hundreds of thousands of nested-loop probes.
CREATE STATISTICS artworks_atlas_scope_stats ON
 (artline_creation_scope(creation_year_start,creation_year_end,date_precision)),
 (coalesce(creation_year_start,creation_year_end)),
 (coalesce(creation_year_end,creation_year_start))
FROM artworks;

-- Title search already has a narrow indexed projection. Preserve unresolved
-- creator labels as an independent search branch without scanning the heap.
-- Production may prebuild this exact index CONCURRENTLY before this migration.
CREATE INDEX IF NOT EXISTS artworks_unlinked_creator_search_idx
ON artworks USING gin (unlinked_creator_label gin_trgm_ops)
WHERE status<>'archived' AND unlinked_creator_label IS NOT NULL;

ANALYZE artworks;
