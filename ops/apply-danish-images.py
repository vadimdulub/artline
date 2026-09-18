#!/usr/bin/env python3
"""A bounded 500-image selection from the pinned Danish metadata batch."""
import argparse,collections,importlib.util,json,re,time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/danish-painters-20260913'
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
PROVIDER='smk-danish';SCHEME='european-smk-statens-museum-for-kunst-object';POLICY='https://creativecommons.org/publicdomain/mark/1.0/'
core.PROVIDERS[PROVIDER]='Statens Museum for Kunst';core.VERSION='danish-selected-smk-images-v1'

class ProviderPaused(BaseException):pass
class SelectedFetcher(core.Fetcher):
 def get(self,url,limit=8_000_000):
  if urlparse(url).scheme!='https' or urlparse(url).hostname not in ('iip.smk.dk','api.smk.dk'):raise ValueError('Unapproved Danish image source')
  time.sleep(max(0,1.2-(time.monotonic()-self.last)));self.last=time.monotonic()
  with self.session.get(url,timeout=(15,45),stream=True,allow_redirects=False) as r:
   if r.status_code in (429,502,503,504):
    core.event(RUN/'images',{'provider':PROVIDER,'outcome':'provider_paused_http','status':r.status_code,'retry_after':r.headers.get('Retry-After'),'source_url':url})
    raise ProviderPaused('Provider paused. Preserve receipts and respect Retry-After before resuming.')
   r.raise_for_status()
   if r.status_code!=200:raise ValueError('Unexpected image status')
   data=bytearray()
   for chunk in r.iter_content(65536):
    data.extend(chunk)
    if len(data)>limit:raise ValueError('Selected image exceeds source size cap')
   return bytes(data),{k:r.headers.get(k) for k in ('Content-Type','ETag','Last-Modified')}
core.Fetcher=SelectedFetcher

def eligible():
 m=json.loads((RUN/'batch/manifest.json').read_bytes());result=[]
 for chunk in m['chunks']:
  for w in json.loads((RUN/'batch'/chunk['file']).read_bytes())['works']:
   r=w['raw']
   if w['creation_date']['precision']=='unknown' or not r.get('has_image') or r.get('public_domain') is not True or r.get('rights')!=POLICY:continue
   base=r.get('image_iiif_id','');url=''
   if re.fullmatch(r'https://iip\.smk\.dk/iiif/jp2/[A-Za-z0-9_.-]+',base):url=base+'/full/!1000,1000/0/default.jpg'
   else:
    fallback=r.get('image_native') or r.get('image_thumbnail') or ''
    if re.fullmatch(r'https://api\.smk\.dk/api/v1/thumbnail/[a-f0-9-]{36}\.jpg',fallback):url=fallback
   result.append({'work':w,'source_image_url':url})
 return result

def selection():
 p=RUN/'images/candidates.json'
 if p.exists():return json.loads(p.read_bytes())['candidates']
 groups=collections.defaultdict(list)
 for c in eligible():
  if c['source_image_url']:groups[c['work']['painter']].append(c)
 for g in groups.values():g.sort(key=lambda c:(c['work']['work_type']!='painting',c['work']['source_object_id']))
 chosen=[];depth=0
 while len(chosen)<500:
  added=0
  for pid in sorted(groups):
   if depth<len(groups[pid]):chosen.append(groups[pid][depth]);added+=1
   if len(chosen)==500:break
  if not added:break
  depth+=1
 authors=json.loads((RUN/'selected-authors.json').read_bytes());candidates=[]
 with psycopg.connect('postgres://127.0.0.1/artline',row_factory=dict_row) as db:
  db.execute('SET TRANSACTION READ ONLY')
  for c in chosen:
   w=c['work'];row=db.execute("SELECT a.id::text artwork_id,a.slug,a.title FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme=%s AND e.external_id=%s AND a.status='review' AND a.primary_media_id IS NULL AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'",(SCHEME,w['source_object_id'])).fetchone()
   if not row:raise ValueError('Image target not ready: '+w['source_object_id'])
   image={**row,'provider':PROVIDER,'scheme':SCHEME,'external_id':w['source_object_id'],'artist':authors[w['painter']]['name'],'page':w['url'],'source_image_url':c['source_image_url'],'policy_url':POLICY,'rights_status':'public_domain','license_label':'Public Domain Mark 1.0','checked_at':core.now(),'raw':w['raw'],'identity_basis':'Exact SMK object number and named Danish painter person ID from pinned official collection metadata; explicit public_domain=true and Public Domain Mark.'}
   core.save_new(RUN/'images/selected'/PROVIDER/(row['artwork_id']+'.json'),image)
   candidates.append({k:image[k] for k in ('artwork_id','slug','title','provider','scheme','external_id','artist')})
 core.save_new(p,{'candidates':candidates,'limit':500,'selection':'Round-robin by source painter; dated public-domain images only, paintings preferred within painter.'});print('Selected images',len(candidates),flush=True)
 return candidates

def evidence():
 candidates=eligible();inputs=[{'oid':c['work']['source_object_id'],'url':c['work']['url'],'note':json.dumps({'state':'SMK rights-reviewed image candidate; attachment is a separate recorded action','public_domain':True,'rights':POLICY,'source_image_url':c['source_image_url'] or None,'source_image_iiif':c['work']['raw'].get('image_iiif_id'),'source_modified':c['work']['raw'].get('modified'),'person_id':c['work']['painter']},ensure_ascii=False)} for c in candidates]
 results={}
 for target,dsn in [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]:
  with psycopg.connect(dsn,row_factory=dict_row) as db:
   db.execute("SET LOCAL statement_timeout='30s'");db.execute('SELECT pg_advisory_xact_lock(2026091316)')
   sid=db.execute("SELECT id FROM sources WHERE slug='danish-painters-20260913'").fetchone()['id']
   n=db.execute("WITH input AS(SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(oid text,url text,note text)) SELECT count(*) n FROM input i JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=%s AND e.external_id=i.oid",(Jsonb(inputs),SCHEME)).fetchone()['n'];assert n==len(inputs)
   cursor=db.execute("""WITH input AS(SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(oid text,url text,note text))
    INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
    SELECT 'artwork',e.entity_id,'image_candidate',%s,i.oid,i.url,i.note,now(),%s FROM input i JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=%s AND e.external_id=i.oid
    WHERE NOT EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=e.entity_id AND c.field_name='image_candidate' AND c.source_id=%s)""",(Jsonb(inputs),sid,core.ACTOR,SCHEME,sid))
   results[target]={'candidates':n,'inserted_citations':cursor.rowcount}
 core.save_new(RUN/'image-candidate-database-receipt.json',results);print(results,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['select','prepare','apply','evidence']);a=p.parse_args()
 if a.phase=='evidence':evidence();raise SystemExit(0)
 candidates=selection()
 if a.phase=='select':raise SystemExit(0)
 if a.phase=='apply':
  latest={}
  for line in (RUN/'images/events.jsonl').read_text().splitlines():
   e=json.loads(line)
   if e.get('artwork_id'):latest[e['artwork_id']]=e
  candidates=[c for c in candidates if (RUN/'images/images'/PROVIDER/(c['artwork_id']+'.json')).exists() and latest.get(c['artwork_id'],{}).get('outcome')!='complete']
  # The metadata importer commits independently in bounded chunks. Attach only
  # targets already committed in production; later passes pick up the remainder.
  with psycopg.connect(core.cloud_dsn(),row_factory=dict_row) as db:
   db.execute('SET TRANSACTION READ ONLY')
   ready={r['external_id'] for r in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=ANY(%s)",(SCHEME,[c['external_id'] for c in candidates])).fetchall()}
  candidates=[c for c in candidates if c['external_id'] in ready]
  print('Prepared images pending attachment',len(candidates),flush=True)
 try:core.worker(PROVIDER,candidates,SimpleNamespace(run=RUN/'images',prepare_only=a.phase=='prepare',upload_prepared_only=a.phase=='apply'),'' if a.phase=='prepare' else core.cloud_dsn())
 except ProviderPaused as error:print(str(error),flush=True)
