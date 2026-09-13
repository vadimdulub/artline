#!/usr/bin/env python3
"""Apply a pinned enrichment plan to existing review artworks, in guarded batches."""
import argparse,hashlib,importlib.util,json,os,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('common',ROOT/'ops/reconcile-artwork-creators.py');common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)
q=common.literal

def load(directory):
 raw=(directory/'plan.json').read_bytes();manifest=json.loads((directory/'manifest.json').read_text())
 if hashlib.sha256(raw).hexdigest()!=manifest['sha256']:raise ValueError('Plan checksum changed')
 rows=json.loads(raw)
 if len(rows)!=manifest['links'] or len({r['rid'] for r in rows})!=len(rows):raise ValueError('Plan count/identity mismatch')
 for r in rows:
  a=r['artist'];p=r['painter']
  if common.QUALIFIED.search(p['name']) or a['entity_type']!='person':raise ValueError('Unresolved creator')
  if a['new'] and (a['birth_year'] is None or a['death_year'] is None or not 0<=a['death_year']-a['birth_year']<=125):raise ValueError('Invalid new biography')
  if r['patch'] and r['patch']['type'] not in ('painting','drawing','watercolor','print','fresco','manuscript_illumination'):raise ValueError('Unsupported known artwork type')
  r['entry_hash']=hashlib.sha256(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  # Same alphabetic/numeric token normalization as the ingestion backend.
  import unicodedata
  name=''.join(c for c in unicodedata.normalize('NFD',a['display_name'].lower()) if not unicodedata.combining(c))
  r['artist']['normalized_name']=' '.join(re.findall(r'[^\W_]+',name))
 return manifest,rows

def sql_for(rows,sha):
 return """BEGIN;
SET LOCAL TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SET LOCAL statement_timeout='300s';
DO $$ BEGIN
 IF current_database()<>'artline' THEN RAISE EXCEPTION 'Wrong database'; END IF;
 PERFORM pg_advisory_xact_lock(2026090959);
END $$;
CREATE TEMP TABLE r2_input ON COMMIT DROP AS SELECT value p FROM jsonb_array_elements("""+q(json.dumps(rows,ensure_ascii=False))+"""::jsonb);
ANALYZE r2_input;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM r2_input i JOIN research_artwork_enrichments e
 ON e.plan_sha256="""+q(sha)+""" AND e.research_record_id=i.p->>'rid' WHERE e.entry_sha256<>i.p->>'entry_hash')
 THEN RAISE EXCEPTION 'Applied entry changed'; END IF;
END $$;
DELETE FROM r2_input i WHERE EXISTS(SELECT 1 FROM research_artwork_enrichments e
 WHERE e.plan_sha256="""+q(sha)+""" AND e.research_record_id=i.p->>'rid');
ANALYZE r2_input;
CREATE TEMP TABLE r2_checked ON COMMIT DROP AS
SELECT i.p,w.id work_id,l.snapshot_id FROM r2_input i
JOIN research_artwork_links l ON l.research_record_id=i.p->>'rid' AND l.source_key='supplied-registry' AND l.record_kind='catalogue_object'
JOIN artworks w ON w.id=l.artwork_id AND w.slug=i.p->>'slug'
JOIN research_records rr ON rr.snapshot_id=l.snapshot_id AND rr.source_key=l.source_key AND rr.record_kind=l.record_kind AND rr.source_record_id=l.research_record_id
WHERE l.disposition='created' AND l.entry_sha256=i.p->>'entry_sha' AND rr.raw_json#>'{csv,cells}'=i.p->'cells'
AND w.status='review' AND w.research_candidate AND w.unlinked_creator_label=i.p->>'label'
AND w.title=i.p#>>'{before,title}' AND w.work_type=i.p#>>'{before,type}' AND w.date_precision=i.p#>>'{before,precision}'
AND w.creation_year_start IS NOT DISTINCT FROM (i.p#>>'{before,first}')::int
AND w.creation_year_end IS NOT DISTINCT FROM (i.p#>>'{before,last}')::int
AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id)
AND ((i.p->'patch'='null'::jsonb AND EXISTS(SELECT 1 FROM research_resolutions r
 WHERE r.research_record_id=l.research_record_id AND r.facts_sha256=i.p#>>'{evidence,original_facts_sha}'
 AND r.state=i.p#>>'{evidence,original_state}' AND r.note=i.p#>>'{evidence,original_note}'
 AND r.review_evidence=i.p#>'{evidence,original_review}' AND r.state='needs_review'))
 OR (i.p->'patch'<>'null'::jsonb AND w.work_type='unknown' AND coalesce(w.medium_text,'')='' AND coalesce(w.dimensions_text,'')='' AND coalesce(w.accession_number,'')=''
 AND artline_creation_scope((i.p#>>'{patch,date,first}')::int,(i.p#>>'{patch,date,last}')::int,i.p#>>'{patch,date,precision}')<>'excluded'));
ANALYZE r2_checked;
DO $$ BEGIN
 IF (SELECT count(*) FROM r2_checked)<>(SELECT count(*) FROM r2_input) THEN RAISE EXCEPTION 'Artwork/source evidence changed'; END IF;
 PERFORM 1 FROM artworks WHERE id IN(SELECT work_id FROM r2_checked) FOR UPDATE;
END $$;
CREATE TEMP TABLE r2_people ON COMMIT DROP AS
 SELECT DISTINCT ON(p#>>'{artist,slug}') p->'artist' a FROM r2_checked ORDER BY p#>>'{artist,slug}';
ANALYZE r2_people;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM r2_people p LEFT JOIN artists a ON a.slug=p.a->>'slug'
 WHERE ((p.a->>'new')::boolean=false AND a.id IS NULL)
 OR (a.id IS NOT NULL AND (a.status<>p.a->>'status' OR a.entity_type<>'person'
 OR a.birth_year IS DISTINCT FROM (p.a->>'birth_year')::int OR a.death_year IS DISTINCT FROM (p.a->>'death_year')::int))
 OR ((p.a->>'new')::boolean AND a.id IS NOT NULL AND a.created_by<>'local-european-research'))
 THEN RAISE EXCEPTION 'Painter identity changed'; END IF;
END $$;
WITH added AS (
 INSERT INTO artists(slug,display_name,sort_name,normalized_name,birth_year,death_year,birth_display,death_display,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status,created_by,updated_by)
 SELECT a->>'slug',a->>'display_name',a->>'sort_name',a->>'normalized_name',(a->>'birth_year')::int,(a->>'death_year')::int,
 a->>'birth_year',a->>'death_year',(a->>'birth_year')::int,(a->>'death_year')::int,
 (a->>'birth_year')||'–'||(a->>'death_year'),'life','review','local-european-research','local-european-research'
 FROM r2_people WHERE (a->>'new')::boolean ON CONFLICT(slug) DO NOTHING RETURNING id
) SELECT json_build_object('created_artists',count(*)) FROM added;
INSERT INTO sources(slug,name,source_type) VALUES('expanded-round2-research','Expanded artwork research — official museum evidence','manual') ON CONFLICT DO NOTHING;
CREATE TEMP TABLE r2_ready ON COMMIT DROP AS SELECT c.*,a.id artist_id FROM r2_checked c JOIN artists a ON a.slug=c.p#>>'{artist,slug}';
ANALYZE r2_ready;
-- Source person IDs may have duplicate museum authority records. Preserve every
-- ID in evidence, while respecting the catalogue's one-ID-per-scheme constraint.
INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,source_id,canonical_url,retrieved_at)
 SELECT DISTINCT ON(v.artist_id,v.p->>'source') 'artist',v.artist_id,(v.p->>'source')||'-person',v.p#>>'{painter,source_id}',s.id,v.p#>>'{evidence,object_url}',now()
 FROM r2_ready v CROSS JOIN sources s WHERE s.slug='expanded-round2-research' AND coalesce(v.p#>>'{painter,source_id}','')<>''
 AND NOT EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=v.artist_id AND e.scheme=(v.p->>'source')||'-person')
 ORDER BY v.artist_id,v.p->>'source',v.p#>>'{painter,source_id}' ON CONFLICT DO NOTHING;
WITH linked AS (
 INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note)
 SELECT work_id,artist_id,'primary','Official museum creator: '||(p#>>'{painter,name}')||'; identity basis: '||(p#>>'{artist,basis}')||'; '||(p#>>'{evidence,object_url}')||'. Review status retained.' FROM r2_ready RETURNING artwork_id
) SELECT json_build_object('linked_artworks',count(*)) FROM linked;
WITH changed AS (
 UPDATE artworks w SET unlinked_creator_label=NULL,
 work_type=CASE WHEN v.p->'patch'='null'::jsonb THEN w.work_type ELSE v.p#>>'{patch,type}' END,
 date_display=CASE WHEN v.p->'patch'='null'::jsonb THEN w.date_display ELSE v.p#>>'{patch,date,display}' END,
 creation_year_start=CASE WHEN v.p->'patch'='null'::jsonb THEN w.creation_year_start ELSE (v.p#>>'{patch,date,first}')::int END,
 creation_year_end=CASE WHEN v.p->'patch'='null'::jsonb THEN w.creation_year_end ELSE (v.p#>>'{patch,date,last}')::int END,
 date_precision=CASE WHEN v.p->'patch'='null'::jsonb THEN w.date_precision ELSE v.p#>>'{patch,date,precision}' END,
 medium_text=CASE WHEN v.p->'patch'='null'::jsonb THEN w.medium_text ELSE nullif(v.p#>>'{patch,medium}','') END,
 dimensions_text=CASE WHEN v.p->'patch'='null'::jsonb THEN w.dimensions_text ELSE nullif(v.p#>>'{patch,dimensions}','') END,
 accession_number=CASE WHEN v.p->'patch'='null'::jsonb THEN w.accession_number ELSE nullif(v.p#>>'{patch,accession}','') END,
 revision=revision+1,updated_at=now(),updated_by='local-european-research'
 FROM r2_ready v WHERE w.id=v.work_id RETURNING w.id
) SELECT json_build_object('updated_artworks',count(*)) FROM changed;
INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,source_id,canonical_url,retrieved_at)
 SELECT 'artwork',work_id,(p->>'source')||'-object',p#>>'{evidence,object_id}',s.id,p#>>'{evidence,object_url}',now()
 FROM r2_ready CROSS JOIN sources s WHERE s.slug='expanded-round2-research' AND p->'patch'<>'null'::jsonb ON CONFLICT DO NOTHING;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM r2_ready v WHERE v.p->'patch'<>'null'::jsonb AND NOT EXISTS(SELECT 1 FROM external_identifiers e
 WHERE e.entity_type='artwork' AND e.entity_id=v.work_id AND e.scheme=(v.p->>'source')||'-object' AND e.external_id=v.p#>>'{evidence,object_id}'))
 THEN RAISE EXCEPTION 'Existing museum object identity conflict'; END IF;
END $$;
INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
 SELECT 'artwork',work_id,'round2_museum_research',s.id,p->>'rid',p#>>'{evidence,object_url}',
 'Exact museum object/creator evidence. Identity basis: '||(p#>>'{artist,basis}')||'; plan SHA256: '||"""+q(sha)+"""||'. Original CSV preserved; review status retained. No current display or image claim.',now(),'local-european-research'
 FROM r2_ready CROSS JOIN sources s WHERE s.slug='expanded-round2-research';
INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
 SELECT DISTINCT ON(r2_ready.artist_id) 'artist',r2_ready.artist_id,'round2_creator_authority',s.id,artist_id::text,p#>>'{evidence,object_url}',
 'Museum creator: '||(p#>>'{painter,name}')||'; source biography: '||coalesce(p#>>'{painter,birth}','unknown')||'–'||coalesce(p#>>'{painter,death}','unknown')||'; identity basis: '||(p#>>'{artist,basis}')||'; source facts preserved in research_artwork_enrichments.',now(),'local-european-research'
 FROM r2_ready CROSS JOIN sources s WHERE s.slug='expanded-round2-research'
 AND NOT EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artist' AND c.entity_id=r2_ready.artist_id AND c.field_name='round2_creator_authority') ORDER BY r2_ready.artist_id,p->>'rid';
INSERT INTO research_artwork_enrichments(plan_sha256,research_record_id,entry_sha256,artwork_id,artist_id,museum_source,source_object_id,source_url,evidence_json,metadata_enriched)
 SELECT """+q(sha)+""",p->>'rid',p->>'entry_hash',work_id,artist_id,p->>'source',p#>>'{evidence,object_id}',p#>>'{evidence,object_url}',p,p->'patch'<>'null'::jsonb FROM r2_ready;
COMMIT;
"""

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--dir',type=Path,required=True);ap.add_argument('--label',required=True);ap.add_argument('--start',type=int,default=0);ap.add_argument('--end',type=int,default=1000000);ap.add_argument('--batch-size',type=int,default=250);args=ap.parse_args()
 if not 1<=args.batch_size<=250:raise ValueError('Batch size must be between 1 and 250')
 manifest,rows=load(args.dir);started=time.monotonic()
 with (args.dir/(args.label+'-apply.jsonl')).open('a') as log:
  for start in range(args.start,min(args.end,len(rows)),args.batch_size):
   subset=rows[start:min(start+args.batch_size,args.end)]
   result=common.query(sql_for(subset,manifest['sha256']),write=True)
   receipt={'start':start,'records':len(subset),'result':result,'elapsed_seconds':round(time.monotonic()-started,1)}
   log.write(json.dumps(receipt)+'\n');log.flush();print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
