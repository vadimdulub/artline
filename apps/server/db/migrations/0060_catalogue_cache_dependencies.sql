-- New cached resources must invalidate the same transactional catalogue revision.
-- Statement triggers change no catalogue records and roll back with the writer.
DO $$
DECLARE relation text;
BEGIN
 FOREACH relation IN ARRAY ARRAY[
  'artist_key_artworks','exhibitions','exhibition_source_records',
  'exhibition_occurrences','exhibition_participants','exhibition_entries',
  'exhibition_publications','exhibition_research','exhibition_research_people',
  'exhibition_objects','exhibition_object_entries'
 ] LOOP
  IF NOT EXISTS(SELECT 1 FROM pg_trigger
    WHERE tgrelid=format('public.%I',relation)::regclass
      AND tgname='catalogue_cache_changed' AND NOT tgisinternal) THEN
   EXECUTE format('CREATE TRIGGER catalogue_cache_changed AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.artline_invalidate_catalogue()',relation);
  END IF;
 END LOOP;
END;
$$;
