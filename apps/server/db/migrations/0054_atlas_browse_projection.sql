-- A narrow browse projection, with a transactional dirty overlay. Source writes
-- mark affected IDs; readers evaluate those IDs live until a worker refreshes
-- them. No eligibility decision can become stale while refresh is delayed.
-- No FK on these derived tables: deletion markers must survive source deletion,
-- and a refresher must never wait on a source row locked by an invalidating writer.
CREATE TABLE artwork_atlas_projection (
 id uuid PRIMARY KEY,
 start_year integer NOT NULL,
 end_year integer NOT NULL,
 gallery_priority smallint NOT NULL,
 primary_media_id uuid NOT NULL,
 work_type text,
 cultural_context text,
 is_highlight boolean NOT NULL
);
CREATE TABLE artwork_atlas_dirty (artwork_id uuid PRIMARY KEY);

CREATE INDEX artwork_atlas_page_idx
 ON artwork_atlas_projection(gallery_priority,start_year,(id::text)) INCLUDE(id,end_year);
CREATE INDEX artwork_atlas_highlight_page_idx
 ON artwork_atlas_projection(gallery_priority,start_year,(id::text)) INCLUDE(id,end_year)
 WHERE is_highlight;
-- Reverse invalidation starts at changed media IDs, never the entire catalogue.
-- Production can prebuild this index concurrently before installing the migration.
CREATE INDEX IF NOT EXISTS artworks_primary_media_lookup_idx
 ON artworks(primary_media_id,id) WHERE primary_media_id IS NOT NULL;

-- This is the canonical projection definition for refresh AND pending reads.
-- The IDs are mandatory and bound before enrichment. Status remains audit data:
-- only archives are excluded. Holdings never assert current display.
CREATE FUNCTION artline_atlas_browse_rows(ids uuid[])
RETURNS SETOF artwork_atlas_projection LANGUAGE sql STABLE
AS $$
 SELECT a.id,coalesce(a.creation_year_start,a.creation_year_end),
 coalesce(a.creation_year_end,a.creation_year_start),
 (CASE WHEN a.work_type IN ('painting','fresco','watercolor','manuscript_illumination') THEN 0
       WHEN a.work_type IN ('drawing','print','calligraphy') THEN 2 ELSE 1 END)::smallint,
 a.primary_media_id,a.work_type,a.cultural_context,
 EXISTS(SELECT 1 FROM curated_collection_items ci JOIN curated_collections cc ON cc.id=ci.collection_id
        WHERE ci.artwork_id=a.id AND cc.status<>'archived'
        AND (cc.curator_kind='owner' OR (ci.source_url IS NOT NULL
             AND EXISTS(SELECT 1 FROM sources s WHERE s.id=ci.source_id AND s.is_active)))) AS is_highlight
 FROM artworks a JOIN media_assets image ON image.id=a.primary_media_id
 WHERE a.id=ANY(ids) AND a.status<>'archived'
 AND image.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$'
 AND a.date_precision IN ('exact','circa','range','circa_range','decade','century')
 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
 AND coalesce(a.creation_year_start,a.creation_year_end)<>0
 AND coalesce(a.creation_year_end,a.creation_year_start)<>0
 AND (NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id)
      OR EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id
                WHERE aa.artwork_id=a.id AND ar.status<>'archived'))
 AND (EXISTS(SELECT 1 FROM curated_collection_items ci JOIN curated_collections cc ON cc.id=ci.collection_id
             WHERE ci.artwork_id=a.id AND cc.status<>'archived'
             AND (cc.curator_kind='owner' OR (ci.source_url IS NOT NULL
                  AND EXISTS(SELECT 1 FROM sources s WHERE s.id=ci.source_id AND s.is_active))))
      OR EXISTS(SELECT 1 FROM artwork_location_assertions h
                 JOIN sources s ON s.id=h.source_id AND s.is_active
                 JOIN institutions i ON i.id=h.institution_id AND i.status<>'archived'
                 WHERE h.artwork_id=a.id AND h.claim_type='holding'
                 AND h.review_state='accepted' AND h.superseded_by IS NULL))
$$;

CREATE VIEW artwork_atlas_browse AS
 SELECT p.* FROM artwork_atlas_projection p
 WHERE NOT EXISTS(SELECT 1 FROM artwork_atlas_dirty d WHERE d.artwork_id=p.id)
 UNION ALL
 SELECT * FROM artline_atlas_browse_rows(ARRAY(SELECT artwork_id FROM artwork_atlas_dirty));

-- Transition tables batch invalidation for imports. ON CONFLICT must UPDATE:
-- DO NOTHING could lose a change when a concurrent refresher removes the marker.
-- The worker locks markers, reads sources in a subsequent READ COMMITTED
-- statement, refreshes, then deletes its locked markers in the same transaction.
CREATE FUNCTION artline_dirty_atlas_browse() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE changed text; affected text; cols text;
BEGIN
 IF TG_OP='INSERT' AND TG_TABLE_NAME IN ('media_assets','artists','institutions','sources','curated_collections') THEN
  -- Immediate source FKs prevent pre-existing dependants. Their own insertion
  -- triggers mark artworks after the new parent is available.
  RETURN NULL;
 END IF;
 IF TG_OP='TRUNCATE' THEN
  INSERT INTO public.artwork_atlas_dirty
   SELECT id FROM public.artwork_atlas_projection
   UNION SELECT id FROM public.artworks WHERE primary_media_id IS NOT NULL
   ORDER BY 1
   ON CONFLICT(artwork_id) DO UPDATE SET artwork_id=excluded.artwork_id;
  RETURN NULL;
 END IF;

 IF TG_TABLE_NAME IN ('artwork_artists','artwork_location_assertions','curated_collection_items') THEN
  IF TG_OP='INSERT' THEN changed:='SELECT artwork_id AS id FROM new_rows';
  ELSIF TG_OP='DELETE' THEN changed:='SELECT artwork_id AS id FROM old_rows';
  ELSE changed:='SELECT artwork_id AS id FROM new_rows UNION SELECT artwork_id FROM old_rows'; END IF;
  affected:=changed;
 ELSE
  IF TG_OP='INSERT' THEN changed:='SELECT id FROM new_rows';
  ELSIF TG_OP='DELETE' THEN changed:='SELECT id FROM old_rows';
  ELSE
   -- Ignore unrelated edits (credits, titles, biography, revision timestamps).
   CASE TG_TABLE_NAME
    WHEN 'artworks' THEN cols:='status,creation_year_start,creation_year_end,date_precision,primary_media_id,work_type,cultural_context';
    WHEN 'media_assets' THEN cols:='storage_path';
    WHEN 'artists' THEN cols:='status';
    WHEN 'institutions' THEN cols:='status';
    WHEN 'sources' THEN cols:='is_active';
    WHEN 'curated_collections' THEN cols:='status,curator_kind';
   END CASE;
   changed:=format('SELECT id FROM (SELECT id,%1$s FROM new_rows EXCEPT SELECT id,%1$s FROM old_rows) n
                   UNION SELECT id FROM (SELECT id,%1$s FROM old_rows EXCEPT SELECT id,%1$s FROM new_rows) o',cols);
  END IF;
  CASE TG_TABLE_NAME
   WHEN 'artworks' THEN affected:=changed;
   WHEN 'media_assets' THEN affected:='SELECT a.id FROM public.artworks a JOIN ('||changed||') c ON c.id=a.primary_media_id';
   WHEN 'artists' THEN affected:='SELECT aa.artwork_id AS id FROM public.artwork_artists aa JOIN ('||changed||') c ON c.id=aa.artist_id';
   WHEN 'institutions' THEN affected:='SELECT h.artwork_id AS id FROM public.artwork_location_assertions h JOIN ('||changed||') c ON c.id=h.institution_id
                                      WHERE h.claim_type=''holding'' AND h.review_state=''accepted'' AND h.superseded_by IS NULL';
   WHEN 'sources' THEN affected:='SELECT h.artwork_id AS id FROM public.artwork_location_assertions h JOIN ('||changed||') c ON c.id=h.source_id
                                 WHERE h.claim_type=''holding'' AND h.review_state=''accepted'' AND h.superseded_by IS NULL
                                 UNION SELECT ci.artwork_id FROM public.curated_collection_items ci JOIN ('||changed||') c ON c.id=ci.source_id';
   WHEN 'curated_collections' THEN affected:='SELECT ci.artwork_id AS id FROM public.curated_collection_items ci JOIN ('||changed||') c ON c.id=ci.collection_id';
  END CASE;
 END IF;
 EXECUTE 'INSERT INTO public.artwork_atlas_dirty(artwork_id) SELECT DISTINCT id FROM ('||affected||') affected ORDER BY id
          ON CONFLICT(artwork_id) DO UPDATE SET artwork_id=excluded.artwork_id';
 RETURN NULL;
END;
$$;

DO $$
DECLARE relation text;
BEGIN
 FOREACH relation IN ARRAY ARRAY['artworks','artwork_artists','artwork_location_assertions',
 'curated_collection_items','media_assets','artists','institutions','sources','curated_collections'] LOOP
  EXECUTE format('CREATE TRIGGER atlas_browse_insert AFTER INSERT ON %I REFERENCING NEW TABLE AS new_rows FOR EACH STATEMENT EXECUTE FUNCTION artline_dirty_atlas_browse()',relation);
  EXECUTE format('CREATE TRIGGER atlas_browse_update AFTER UPDATE ON %I REFERENCING OLD TABLE AS old_rows NEW TABLE AS new_rows FOR EACH STATEMENT EXECUTE FUNCTION artline_dirty_atlas_browse()',relation);
  EXECUTE format('CREATE TRIGGER atlas_browse_delete AFTER DELETE ON %I REFERENCING OLD TABLE AS old_rows FOR EACH STATEMENT EXECUTE FUNCTION artline_dirty_atlas_browse()',relation);
  EXECUTE format('CREATE TRIGGER atlas_browse_truncate AFTER TRUNCATE ON %I FOR EACH STATEMENT EXECUTE FUNCTION artline_dirty_atlas_browse()',relation);
 END LOOP;
END;
$$;

-- Seed pending work, not a stale snapshot. Until drained, the view reads these
-- candidates live. New/changed records are marked by the installed triggers.
INSERT INTO artwork_atlas_dirty(artwork_id)
SELECT id FROM artworks WHERE status<>'archived' AND primary_media_id IS NOT NULL
 AND date_precision IN ('exact','circa','range','circa_range','decade','century')
 AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible'
 AND coalesce(creation_year_start,creation_year_end)<>0
 AND coalesce(creation_year_end,creation_year_start)<>0
ORDER BY id ON CONFLICT DO NOTHING;
ANALYZE artwork_atlas_dirty;
ANALYZE artwork_atlas_projection;
