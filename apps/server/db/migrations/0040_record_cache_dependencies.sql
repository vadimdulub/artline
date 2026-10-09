-- Artist detail now shares the bounded revision-aware catalogue cache. A new
-- opening-work selection must invalidate it just like artwork/source edits.
CREATE TRIGGER catalogue_cache_changed
AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON artist_key_artworks
FOR EACH STATEMENT EXECUTE FUNCTION artline_invalidate_catalogue();
