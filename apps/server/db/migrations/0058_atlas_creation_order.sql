-- Support creation-year-first keyset pages without sorting the whole gallery.
-- For a populated production catalogue, prebuild these indexes CONCURRENTLY
-- before applying this migration through the transactional runner.
CREATE INDEX IF NOT EXISTS artwork_atlas_creation_page_idx
 ON artwork_atlas_projection(start_year,gallery_priority,(id::text)) INCLUDE(id,end_year);
CREATE INDEX IF NOT EXISTS artwork_atlas_highlight_creation_page_idx
 ON artwork_atlas_projection(start_year,gallery_priority,(id::text)) INCLUDE(id,end_year)
 WHERE is_highlight;
