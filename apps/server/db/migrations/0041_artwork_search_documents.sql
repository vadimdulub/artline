-- Narrow, synchronously maintained search rows avoid random reads from wide
-- artwork records. Source records, statuses and evidence remain untouched.
CREATE TABLE artwork_search_documents (
 id uuid PRIMARY KEY,
 title text NOT NULL,
 normalized_title text NOT NULL,
 status text NOT NULL,
 undated boolean NOT NULL,
 primary_media_id uuid
) WITH (fillfactor=90);

CREATE FUNCTION artline_refresh_artwork_search() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
BEGIN
 INSERT INTO public.artwork_search_documents(id,title,normalized_title,status,undated,primary_media_id)
 VALUES(NEW.id,NEW.title,NEW.normalized_title,NEW.status,
 NEW.creation_year_start IS NULL AND NEW.creation_year_end IS NULL,NEW.primary_media_id)
 ON CONFLICT(id) DO UPDATE SET title=excluded.title,
 normalized_title=excluded.normalized_title,status=excluded.status,
 undated=excluded.undated,primary_media_id=excluded.primary_media_id;
 RETURN NULL;
END;
$$;

CREATE TRIGGER artwork_search_changed
AFTER INSERT OR UPDATE OF title,normalized_title,status,creation_year_start,creation_year_end,primary_media_id
ON artworks FOR EACH ROW EXECUTE FUNCTION artline_refresh_artwork_search();

-- Installation and the copy share one transaction. Source writes wait for
-- trigger installation; catalogue reads remain available. Add the foreign key
-- after the copy so initial validation scans once instead of random row probes.
INSERT INTO artwork_search_documents(id,title,normalized_title,status,undated,primary_media_id)
SELECT id,title,normalized_title,status,
 creation_year_start IS NULL AND creation_year_end IS NULL,primary_media_id
FROM artworks ORDER BY normalized_title,id;
ALTER TABLE artwork_search_documents ADD CONSTRAINT artwork_search_documents_artwork_fk
 FOREIGN KEY(id) REFERENCES artworks(id) ON DELETE CASCADE;

CREATE INDEX artwork_search_documents_title_trgm_idx
ON artwork_search_documents USING gin(title gin_trgm_ops) WHERE status<>'archived';
CREATE INDEX artwork_search_documents_page_idx
ON artwork_search_documents(normalized_title,id) WHERE status<>'archived';
-- Image eligibility stays in the media table, avoiding a cross-table derived
-- boolean that can become stale during concurrent media and artwork updates.
CREATE INDEX media_assets_local_image_id_idx ON media_assets(id)
WHERE storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$';
CREATE TRIGGER catalogue_cache_changed
AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON artwork_search_documents
FOR EACH STATEMENT EXECUTE FUNCTION artline_invalidate_catalogue();
ANALYZE artwork_search_documents;
ANALYZE media_assets;
