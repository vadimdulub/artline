WITH candidates AS MATERIALIZED (
 SELECT w.* FROM artworks w WHERE w.research_candidate
), links AS MATERIALIZED (
 SELECT l.*,w.slug FROM research_artwork_links l LEFT JOIN artworks w ON w.id=l.artwork_id
), bad AS (
 SELECT
 (SELECT count(*) FROM candidates WHERE status<>'review') AS nonreview_status,
 (SELECT count(*) FROM candidates WHERE unlinked_creator_label IS NULL) AS missing_creator_label,
 (SELECT count(*) FROM candidates WHERE current_institution_id IS NOT NULL OR location_checked_at IS NOT NULL) AS invented_holding,
 (SELECT count(*) FROM candidates WHERE primary_media_id IS NOT NULL) AS invented_primary_image,
 (SELECT count(*) FROM candidates w JOIN artwork_media m ON m.artwork_id=w.id) AS invented_image,
 (SELECT count(*) FROM candidates w JOIN artwork_location_assertions la ON la.artwork_id=w.id) AS invented_location_claim,
 (SELECT count(*) FROM candidates w JOIN artwork_artists aa ON aa.artwork_id=w.id) AS invented_artist_link,
 (SELECT count(*) FROM candidates WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='excluded') AS out_of_scope,
 (SELECT count(*) FROM candidates w WHERE NOT EXISTS(SELECT 1 FROM citations c JOIN sources s ON s.id=c.source_id
 WHERE c.entity_type='artwork' AND c.entity_id=w.id AND c.field_name='supplied_research' AND s.slug='expanded-csv-review-artworks')) AS missing_provenance,
 (SELECT count(*) FROM candidates w WHERE NOT EXISTS(SELECT 1 FROM research_artwork_links l WHERE l.artwork_id=w.id)) AS missing_research_link,
 (SELECT count(*) FROM research_records r WHERE r.source_key='supplied-registry' AND r.raw_json->>'input_sha256'='210a729ead48d12b0f228eb9e1fe0c5a6708750b196be38ddfbbb270aa1355c8'
 AND NOT EXISTS(SELECT 1 FROM research_resolutions x WHERE x.research_record_id=r.source_record_id AND x.state='catalogued')
 AND NOT EXISTS(SELECT 1 FROM research_artwork_links l WHERE l.source_key=r.source_key AND l.record_kind=r.record_kind AND l.research_record_id=r.source_record_id)) AS unhandled_entries
)
SELECT jsonb_build_object(
 'artworks_total',(SELECT count(*) FROM artworks),
 'artists_total',(SELECT count(*) FROM artists),
 'research_records',(SELECT count(*) FROM research_records),
 'new_review_artworks',(SELECT count(*) FROM candidates),
 'links',(SELECT count(*) FROM links),
 'dispositions',(SELECT jsonb_object_agg(disposition,n) FROM(SELECT disposition,count(*) n FROM links GROUP BY disposition) x),
 'work_types',(SELECT jsonb_object_agg(work_type,n) FROM(SELECT work_type,count(*) n FROM candidates GROUP BY work_type) x),
 'date_scopes',(SELECT jsonb_object_agg(scope,n) FROM(SELECT artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,count(*) n FROM candidates GROUP BY 1) x),
 'violations',(SELECT to_jsonb(bad) FROM bad),
 -- Hash each row before aggregation so the audit does not construct a
 -- hundreds-of-megabytes string on the small production database instance.
 'link_digest',(SELECT md5(string_agg(md5(research_record_id||':'||object_key||':'||disposition||':'||coalesce(slug,'')||':'||entry_sha256||':'||plan_sha256),'|' ORDER BY research_record_id)) FROM links),
 'artwork_digest',(SELECT md5(string_agg(md5((to_jsonb(candidates)-ARRAY['id','created_at','updated_at'])::text),'|' ORDER BY slug)) FROM candidates),
 'publication_guard',(SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='artworks'::regclass AND conname='artwork_candidate_publication')
);
