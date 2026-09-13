-- Read-only receipt. Compare source/mapping digests, not generated UUIDs.
WITH linked AS MATERIALIZED (
 SELECT r.research_record_id,r.source_kind,r.source_object_id,r.artwork_id,r.artist_id,
 w.slug work_slug,w.status work_status,w.creation_year_start,w.creation_year_end,w.date_precision,
 w.title,w.work_type,w.medium_text,w.dimensions_text,w.current_location_text,a.slug artist_slug,a.display_name,
 a.birth_year,a.death_year,a.timeline_start_year,a.timeline_end_year,a.status artist_status
 FROM research_resolutions r JOIN artworks w ON w.id=r.artwork_id JOIN artists a ON a.id=r.artist_id
 WHERE r.state='catalogued'
), created_works AS MATERIALIZED (
 SELECT DISTINCT w.* FROM artworks w JOIN import_records i ON i.matched_entity_id=w.id
 JOIN import_jobs j ON j.id=i.import_job_id
 WHERE j.adapter_version='expanded-resolution-v1' AND i.matched_entity_type='artwork' AND i.outcome='created'
 AND w.status<>'archived'
)
SELECT jsonb_build_object(
 'database',current_database(),
 'artists_total',(SELECT count(*) FROM artists),
 'artworks_total',(SELECT count(*) FROM artworks),
 'research_records',(SELECT count(*) FROM research_records),
 'resolution_entries',(SELECT count(*) FROM research_resolutions),
 'source_digest',(SELECT md5(string_agg(research_record_id||':'||source_kind||':'||source_object_id||':'||facts_sha256,'|' ORDER BY research_record_id,source_kind,source_object_id)) FROM research_resolutions),
 'review_evidence_digest',(SELECT md5(string_agg(research_record_id||':'||review_evidence::text,'|' ORDER BY research_record_id)) FROM research_resolutions WHERE review_evidence<>'{}'),
 'disposition_digest',(SELECT md5(string_agg(research_record_id||':'||state||':'||note,'|' ORDER BY research_record_id,source_kind,source_object_id)) FROM research_resolutions),
 'catalogue_mapping_digest',(SELECT md5(string_agg((to_jsonb(l)-'artwork_id'-'artist_id')::text,'|' ORDER BY research_record_id)) FROM linked l),
 'source_states',(SELECT jsonb_agg(to_jsonb(s)) FROM (SELECT source_kind,state,count(*) entries FROM research_resolutions GROUP BY 1,2 ORDER BY 1,2) s),
 'catalogued_entries',(SELECT count(*) FROM linked),
 'catalogued_objects',(SELECT count(DISTINCT artwork_id) FROM linked),
 'created_active_artworks',(SELECT count(*) FROM created_works),
 'created_active_painters',(SELECT count(DISTINCT artist_id) FROM linked WHERE artist_slug LIKE '%-research-%'),
 'violations',jsonb_build_object(
  'ineligible_new_artworks',(SELECT count(*) FROM created_works WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)<>'eligible'),
  'unreviewed_status',(SELECT count(*) FROM created_works WHERE status<>'review'),
  'missing_artist',(SELECT count(*) FROM created_works w WHERE NOT EXISTS(SELECT 1 FROM artwork_artists a WHERE a.artwork_id=w.id)),
  'missing_holding',(SELECT count(*) FROM created_works WHERE current_institution_id IS NULL),
  'new_painter_without_artwork',(SELECT count(*) FROM artists a WHERE a.slug LIKE '%-research-%' AND a.status<>'archived' AND NOT EXISTS(SELECT 1 FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=a.id AND w.status<>'archived')),
  'missing_source',(SELECT count(*) FROM created_works w WHERE NOT EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=w.id AND c.source_url LIKE 'https://%')),
  'new_image_claim',(SELECT count(*) FROM created_works WHERE primary_media_id IS NOT NULL),
  'new_display_claim',(SELECT count(*) FROM created_works w JOIN artwork_location_assertions l ON l.artwork_id=w.id WHERE l.claim_type='display'),
  'hidden_catalogue_link',(SELECT count(*) FROM linked WHERE artist_status='archived' OR work_status='archived')
 ),
 'review_reasons',(SELECT jsonb_agg(to_jsonb(s)) FROM (SELECT note,count(*) entries FROM research_resolutions WHERE state='needs_review' GROUP BY 1 ORDER BY 2 DESC,1) s)
);
