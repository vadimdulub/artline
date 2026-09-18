#!/usr/bin/env python3
"""Prepare and apply only pinned, rights-reviewed Russian artwork images."""
import argparse,importlib.util,json,time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
from psycopg.types.json import Jsonb
spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-russian-deep-images.py'));r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
core=r.core;RUN=r.RUN;IMAGES=RUN/'images';PROVIDER='russian-deep-commons'
core.PROVIDERS.update({PROVIDER:'Wikimedia Commons','russian-deep-met':'The Metropolitan Museum of Art','russian-deep-nga':'National Gallery of Art','russian-deep-cleveland':'The Cleveland Museum of Art','russian-deep-chicago':'Art Institute of Chicago'});core.VERSION='russian-deep-exact-images-v1'
UA='Artline/1.0 (https://github.com/vadimdulub/artline; selected public-domain artwork research)'

def candidate(i):return {k:i[k] for k in ('artwork_id','slug','title','artist','provider','scheme','external_id')}
def seed():
 d,gaps=r.gaps();wanted={w['id'] for w in gaps};prior=json.loads((r.PREVIOUS/'final-verification.json').read_bytes())['pending_preparation'];out=[]
 for c in prior:
  if c['artwork_id'] not in wanted:continue
  p=r.PREVIOUS/'images/selected'/c['provider']/(c['artwork_id']+'.json');old=json.loads(p.read_bytes());assert old['countries']==['RU']
  i={**old,'provider':PROVIDER,'raw':{'previous_verified_selection':old,'selection_file':str(p.relative_to(r.ROOT)),'selection_sha256':core.sha(p.read_bytes())}}
  core.save_new(IMAGES/'selected'/PROVIDER/(i['artwork_id']+'.json'),i);out.append(candidate(i))
 core.save_new(RUN/'queued-selection.json',{'candidates':out,'selection':'Previously researched missing Russian images, re-scoped to the current catalogue audit.'});print('Selected pending Russian images',len(out),flush=True)

def evidence():
 assert (RUN/'backups.json').exists();inputs=[]
 for p in (IMAGES/'selected').glob('*/*.json'):
  s=json.loads(p.read_bytes());inputs.append({'scheme':s['scheme'],'oid':s['external_id'],'url':s['page'],'note':json.dumps({'state':'Rights-reviewed image candidate; attachment recorded separately in media evidence and receipts.','identity_basis':s['identity_basis'],'source_image_url':s['source_image_url'],'license':s['license_label'],'license_url':s['policy_url'],'creator_credit':s.get('creator_credit',s['artist']),'research_evidence_sha256':core.sha(core.encode(s['raw'])),'checked_at':s['checked_at']},ensure_ascii=False)})
 results={}
 for target,dsn in [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]:
  with r.psycopg.connect(dsn,row_factory=r.dict_row) as db:
   db.execute('SELECT pg_advisory_xact_lock(2026091330)');db.execute("SET LOCAL statement_timeout='30s'")
   db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES('russian-deep-image-research','Russian artwork image research — exact museum and Commons evidence','authority_data','https://commons.wikimedia.org') ON CONFLICT DO NOTHING")
   sid=db.execute("SELECT id FROM sources WHERE slug='russian-deep-image-research'").fetchone()['id']
   n=db.execute("WITH input AS(SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(scheme text,oid text,url text,note text)) SELECT count(*) n FROM input i JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=i.scheme AND e.external_id=i.oid",(Jsonb(inputs),)).fetchone()['n'];assert n==len(inputs)
   cursor=db.execute("""WITH input AS(SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(scheme text,oid text,url text,note text))
    INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
    SELECT 'artwork',e.entity_id,'image_candidate',%s,i.scheme||':'||i.oid,i.url,i.note,now(),%s FROM input i JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=i.scheme AND e.external_id=i.oid
    WHERE NOT EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=e.entity_id AND c.field_name='image_candidate' AND c.source_id=%s AND c.source_url=i.url)""",(Jsonb(inputs),sid,core.ACTOR,sid))
   results[target]={'rights_reviewed_candidates':n,'inserted_citations':cursor.rowcount}
 core.save_new(RUN/'commons-research-database-receipt.json',results);print(results,flush=True)

class ProviderPaused(BaseException):pass
class Fetcher(core.Fetcher):
 def __init__(self,cache):
  super().__init__(cache);self.session.headers['User-Agent']=UA
 def get(self,url,limit=8_000_000):
  host=urlparse(url).hostname
  approved={'upload.wikimedia.org','thumb.wikimedia.org','images.metmuseum.org','www.artic.edu','openaccess-cdn.clevelandart.org','api.nga.gov','api.smk.dk','iip.smk.dk'}
  if urlparse(url).scheme!='https' or host not in approved:raise ValueError('Unapproved image source host')
  for log in [r.PREVIOUS/'images/events.jsonl',IMAGES/'events.jsonl']:
   if not log.exists():continue
   for line in log.read_text().splitlines():
    e=json.loads(line);other=urlparse(e.get('source_url','')).hostname or ''
    if e.get('outcome')!='provider_paused_http' or not (host==other or host.endswith('wikimedia.org') and other.endswith('wikimedia.org')):continue
    retry=e.get('retry_after') or '600';delay=int(retry) if retry.isdigit() else 600
    if datetime.fromisoformat(e['at'].replace('Z','+00:00')).timestamp()+delay>time.time():raise ProviderPaused('Recorded provider cooldown active; no image request sent')
  time.sleep(max(0,(8 if host.endswith('wikimedia.org') else 1.4)-(time.monotonic()-self.last)));self.last=time.monotonic()
  with self.session.get(url,timeout=(15,45),stream=True,allow_redirects=False) as response:
   if response.status_code in (429,502,503,504):
    core.event(IMAGES,{'provider':PROVIDER if host.endswith('wikimedia.org') else 'russian-deep-museum','outcome':'provider_paused_http','status':response.status_code,'retry_after':response.headers.get('Retry-After'),'source_url':url});raise ProviderPaused('Provider paused; Retry-After saved without an early retry')
   response.raise_for_status();assert response.status_code==200;data=bytearray()
   for chunk in response.iter_content(65536):
    data.extend(chunk)
    if len(data)>limit:raise ValueError('Selected source exceeds image byte budget')
   return bytes(data),{k:response.headers.get(k) for k in ('Content-Type','ETag','Last-Modified')}
core.Fetcher=Fetcher
original_attach=core.attach
def attach(db,image,target):
 with db.transaction():
  result=original_attach(db,image,target)
  if result=='attached' and image.get('creator_credit'):
   db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(image['creator_credit'],image['attribution_text'],image['media_id']))
   db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',(image['identity_basis']+'; explicit per-file reusable image rights.',image['media_id']))
  return result
core.attach=attach
old_event=core.event
def event(run,value):
 old_event(run,value)
 if sum(core.COUNTS.values())%5==0 or value['outcome'] not in ('prepared','complete'):print(core.now(),dict(core.COUNTS),value.get('error',''),flush=True)
core.event=event

def run(phase,provider,limit):
 selected=[json.loads(p.read_bytes()) for p in (IMAGES/'selected'/provider).glob('*.json')];selected.sort(key=lambda s:(s.get('priority',1),s['artist']!='Ilya Repin',s['external_id']))
 latest={}
 if (IMAGES/'events.jsonl').exists():
  for line in (IMAGES/'events.jsonl').read_text().splitlines():
   e=json.loads(line)
   if e.get('artwork_id'):latest[e['artwork_id']]=e
 if phase=='prepare':selected=[s for s in selected if not (IMAGES/'images'/provider/(s['artwork_id']+'.json')).exists()]
 else:
  assert (RUN/'backups.json').exists(),'Recovery backup verification required'
  selected=[s for s in selected if (IMAGES/'images'/provider/(s['artwork_id']+'.json')).exists() and latest.get(s['artwork_id'],{}).get('outcome')!='complete']
 if limit:selected=selected[:limit]
 print(phase,provider,len(selected),flush=True)
 core.PROVIDERS.setdefault(provider,'Museum open-access programme')
 try:core.worker(provider,[candidate(s) for s in selected],SimpleNamespace(run=IMAGES,prepare_only=phase=='prepare',upload_prepared_only=phase=='apply'),'' if phase=='prepare' else core.cloud_dsn())
 except ProviderPaused as error:print(str(error),flush=True)
 print('Current pass finished',dict(core.COUNTS),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['seed','prepare','apply','evidence']);p.add_argument('--provider',default=PROVIDER);p.add_argument('--limit',type=int,default=0);a=p.parse_args()
 if a.phase=='seed':seed()
 elif a.phase=='evidence':evidence()
 else:run(a.phase,a.provider,a.limit)
