-- Cache invalidation follows committed catalogue writes, not cluster-wide XIDs
-- (Cloud SQL heartbeats and member sessions must not evict catalogue responses).
-- Fixed shards avoid making every importer contend on one global revision row.
-- A transaction increments its shard once; rollback rolls the increment back.
-- Readers SUM every shard, so out-of-order commits cannot hide invalidations.
CREATE TABLE catalogue_cache_revisions (
 shard smallint PRIMARY KEY CHECK (shard >= 0 AND shard < 64),
 revision bigint NOT NULL DEFAULT 0 CHECK (revision >= 0),
 transaction_id xid8
);
INSERT INTO catalogue_cache_revisions(shard) SELECT generate_series(0,63);

CREATE FUNCTION artline_invalidate_catalogue() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE
 xid xid8 := pg_current_xact_id();
BEGIN
 UPDATE public.catalogue_cache_revisions
 SET revision=revision+1,transaction_id=xid
 WHERE shard=(xid::text::numeric % 64)::smallint
   AND transaction_id IS DISTINCT FROM xid;
 RETURN NULL;
END;
$$;

-- Register new catalogue dependencies here (or in a later migration) when
-- adding cached queries. Operational audit/import/account tables are excluded.
DO $$
DECLARE relation text;
BEGIN
 FOREACH relation IN ARRAY ARRAY[
  'artists','artist_aliases','artist_countries','artist_places','artist_movements',
  'artist_discovery_selection','artist_gender_evidence','movements','countries','places',
  'artworks','artwork_artists','artwork_places','artwork_media','media_assets',
  'media_rights_evidence','institutions','institution_venues','artwork_location_assertions',
  'curated_collections','curated_collection_items','sources','source_institutions',
  'source_connector_config','citations','external_identifiers','influence_claims',
  'slug_redirects','painter_import_cohort','research_records','research_resolutions',
  'research_artwork_links','research_artwork_enrichments','research_snapshots',
  'book_records','book_creators','book_creator_links','book_discovery','book_discovery_terms',
  'event_records'
 ] LOOP
  EXECUTE format('CREATE TRIGGER catalogue_cache_changed AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.artline_invalidate_catalogue()',relation);
 END LOOP;
END;
$$;
