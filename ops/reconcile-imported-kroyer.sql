-- One-off repair of an import-created duplicate; preserve the original seed.
-- Explicit authority: Pantheon Q365068, Peder Severin Krøyer, 1851–1909.
-- The imported record is archived, never deleted; its old URL redirects.
BEGIN;
SELECT pg_advisory_xact_lock(hashtext('artline-curated-import'));
DO $$
DECLARE original_id uuid; duplicate_id uuid; duplicate_slug text;
BEGIN
 SELECT id INTO STRICT original_id FROM artists WHERE slug='p-s-kroyer'
 AND birth_year=1851 AND death_year=1909 AND created_by IS NULL;
 SELECT a.id,a.slug INTO duplicate_id,duplicate_slug FROM artists a
 JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id
 WHERE e.scheme='wikidata' AND e.external_id='Q365068'
 AND a.created_by='local-curated-import' AND a.status='review' AND a.id<>original_id;
 IF duplicate_id IS NULL THEN RETURN; END IF;
 IF EXISTS(SELECT 1 FROM artwork_artists WHERE artist_id=duplicate_id)
 OR EXISTS(SELECT 1 FROM artist_movements WHERE artist_id=duplicate_id) THEN
   RAISE EXCEPTION 'duplicate has new relationships; manual merge required';
 END IF;
 UPDATE external_identifiers SET entity_id=original_id WHERE entity_type='artist' AND entity_id=duplicate_id;
 UPDATE painter_import_cohort SET artist_id=original_id WHERE artist_id=duplicate_id;
 UPDATE citations SET entity_id=original_id WHERE entity_type='artist' AND entity_id=duplicate_id;
 UPDATE import_records SET matched_entity_id=original_id WHERE matched_entity_type='artist' AND matched_entity_id=duplicate_id;
 INSERT INTO slug_redirects(entity_type,entity_id,old_slug) VALUES('artist',original_id,duplicate_slug) ON CONFLICT DO NOTHING;
 INSERT INTO audit_log(action,entity_type,entity_id,before_json,after_json,actor_user_id)
 VALUES('reconcile_imported_alias','artist',original_id,jsonb_build_object('duplicate_id',duplicate_id),jsonb_build_object('authority','Q365068','preserved_seed',original_id),'local-curated-import');
 UPDATE artists SET status='archived',revision=revision+1,updated_at=now() WHERE id=duplicate_id;
END $$;
COMMIT;
