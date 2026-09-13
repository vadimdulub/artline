-- Format source measurements for display, retaining the exact original facts
-- and citations. Only newly created artworks from this import are eligible.
BEGIN;
SELECT pg_advisory_xact_lock(2026090959);
WITH candidates AS MATERIALIZED (
 SELECT DISTINCT ON (w.id) w.id,w.dimensions_text,w.current_location_text,
 r.source_kind,r.facts_json->>'dimensions' raw_dimensions,
 r.facts_json->'institution'->>'Name' institution_name,
 r.facts_json->'institution'->>'City' city
 FROM artworks w JOIN research_resolutions r ON r.artwork_id=w.id AND r.state='catalogued'
 WHERE w.status='review' AND EXISTS (
  SELECT 1 FROM import_records i JOIN import_jobs j ON j.id=i.import_job_id
  WHERE i.matched_entity_type='artwork' AND i.matched_entity_id=w.id
  AND i.outcome='created' AND j.adapter_version='expanded-resolution-v1'
 ) ORDER BY w.id,r.research_record_id
), formatted AS (
 SELECT c.id,
 CASE WHEN source_kind='smk' AND dimensions_text=raw_dimensions THEN (
  SELECT string_agg(CASE WHEN label<>'' THEN label||': ' ELSE '' END||value,'; ' ORDER BY ord)
  FROM (
   SELECT ord,btrim(concat(e->>'part',' ',e->>'type')) label,
    btrim(concat(e->>'value',' ',e->>'unit',CASE WHEN coalesce(e->>'notes','')<>'' THEN ' ('||(e->>'notes')||')' ELSE '' END)) value
   FROM jsonb_array_elements(raw_dimensions::jsonb) WITH ORDINALITY d(e,ord)
  ) measurements WHERE value<>''
 ) ELSE dimensions_text END dimensions_text,
 CASE WHEN source_kind='joconde' AND current_location_text=institution_name||', '||city
  THEN institution_name ELSE current_location_text END current_location_text
 FROM candidates c
), changed AS (
 UPDATE artworks w SET dimensions_text=f.dimensions_text,current_location_text=f.current_location_text,
 revision=revision+1,updated_at=now(),updated_by='local-european-research'
 FROM formatted f WHERE w.id=f.id AND (w.dimensions_text IS DISTINCT FROM f.dimensions_text
 OR w.current_location_text IS DISTINCT FROM f.current_location_text)
 RETURNING w.id
)
SELECT json_build_object('formatted_artworks',count(*)) FROM changed;
COMMIT;
