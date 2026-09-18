#!/usr/bin/env python3
"""Read-only verification of selected image attachments and delivered bytes."""
import argparse,base64,collections,hashlib,importlib.util,json,re,subprocess
from pathlib import Path
import psycopg,requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from PIL import Image
from google.cloud import storage
spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('resolve-danish-russian-images.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
core=r.core;ROOT=r.ROOT;RUN=r.RUN

def main(label):
 events={}
 for line in (RUN/'images/events.jsonl').read_text().splitlines():
  e=json.loads(line)
  if e.get('artwork_id') and e['outcome']=='complete':events[e['artwork_id']]=e
 selected=[json.loads(p.read_bytes()) for p in (RUN/'images/selected').glob('*/*.json')]
 excluded={e['artwork_id'] for e in json.loads((RUN/'nationality-exclusions.json').read_bytes())}
 selected=[s for s in selected if s['artwork_id'] not in excluded]
 receipts=[json.loads(p.read_bytes()) for p in (RUN/'images/images').glob('*/*.json')]
 prepared={s['artwork_id']:s for s in receipts};completed=[s for s in receipts if s['artwork_id'] in events]
 assert all(events[s['artwork_id']]['local']=='attached' and events[s['artwork_id']]['cloud']=='attached' for s in completed)
 assert not (set(events)&excluded)
 client=storage.Client(project='artline-508319',credentials=core.GcloudCredentials());blobs={}
 for provider in {s['provider'] for s in completed}:
  if provider=='dk-local-sync':continue
  blobs.update({b.name:b for b in client.list_blobs(core.BUCKET,prefix='assets/artworks/open-museums/'+provider+'/')})
 for s in completed:
  path=ROOT/'apps/web/public'/s['path'].lstrip('/');data=path.read_bytes();assert core.sha(data)==s['sha256'] and len(data)==s['bytes']<=100000
  with Image.open(path) as im:assert im.size==(s['width'],s['height']);im.verify()
  b=blobs.get(s['path'].lstrip('/'))
  if b is None:b=client.bucket(core.BUCKET).get_blob(s['path'].lstrip('/'))
  assert b and b.size==len(data) and b.md5_hash==base64.b64encode(hashlib.md5(data).digest()).decode()
 reports={};queryplans={}
 for target,dsn in [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]:
  before=json.loads((RUN/(target+'-before.json')).read_bytes());bi={(e['scheme'],e['id']):w for w in before['works'] for e in w['identifiers'] or []}
  inputs=[{'scheme':s['scheme'],'external_id':s['external_id']} for s in completed]
  with psycopg.connect(dsn,row_factory=dict_row) as db:
   db.execute('SET TRANSACTION READ ONLY')
   rows=db.execute("""WITH input AS(SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(scheme text,external_id text))
    SELECT e.scheme,e.external_id,a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.accession_number,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.status,a.primary_media_id::text,i.slug institution,
     (SELECT jsonb_agg(jsonb_build_object('id',aa.artist_id::text,'role',aa.attribution_role)) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creators,
     to_jsonb(m) media,to_jsonb(r) evidence
    FROM input x JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=x.scheme AND e.external_id=x.external_id
    JOIN artworks a ON a.id=e.entity_id LEFT JOIN institutions i ON i.id=a.current_institution_id
    LEFT JOIN media_assets m ON m.id=a.primary_media_id LEFT JOIN media_rights_evidence r ON r.media_id=m.id""",(Jsonb(inputs),)).fetchall()
   assert len(rows)==len(completed);bykey={(x['scheme'],x['external_id']):x for x in rows}
   for s in completed:
    x=bykey[(s['scheme'],s['external_id'])];b=bi[(s['scheme'],s['external_id'])];m=x['media'];ev=x['evidence']
    for key in ('slug','title','alternate_title','accession_number','date_display','creation_year_start','creation_year_end','date_precision','work_type','status','institution'):assert x[key]==b[key],(target,s['external_id'],key)
    assert sorted(x['creators'],key=lambda a:(a['id'],a['role']))==sorted(b['creators'],key=lambda a:(a['id'],a['role']))
    assert x['primary_media_id']==s['media_id'] and m['storage_path']==s['path']
    assert (m['checksum_sha256'],m['byte_size'],m['rights_status'],m['license_url'])==(s['sha256'],s['bytes'],s['rights_status'],s['policy_url'])
    assert m['creator_credit']==s.get('creator_credit',s['artist'])
    assert ev['source_image_url']==s['source_image_url']
    expected=s['original_local_evidence']['source_checksum'] if s['provider']=='dk-local-sync' and target=='local' else core.sha(core.encode(s['raw']))
   assert ev['source_checksum']==expected
   candidate_evidence=None
   if (RUN/'commons-research-database-receipt.json').exists():
    candidate_evidence=db.execute("SELECT count(*) n FROM citations c JOIN sources s ON s.id=c.source_id WHERE s.slug='danish-russian-commons-gap-research' AND c.field_name='image_candidate'").fetchone()['n']
    assert candidate_evidence==sum(s['provider']=='dk-ru-commons' for s in selected)
   cohort=[{'id':w['id'],'countries':w['countries']} for w in before['works']]
   coverage=db.execute("""WITH cohort AS(SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(id uuid,countries jsonb))
    SELECT c.value country,count(*) works,count(*) FILTER(WHERE a.primary_media_id IS NOT NULL) with_images,
    count(*) FILTER(WHERE a.primary_media_id IS NULL AND a.status<>'archived' AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id)) eligible_gaps,
    count(*) FILTER(WHERE a.primary_media_id IS NULL AND a.work_type='painting' AND a.status<>'archived' AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id)) painting_gaps
    FROM cohort x JOIN artworks a ON a.id=x.id CROSS JOIN LATERAL jsonb_array_elements_text(x.countries) c GROUP BY c.value""",(Jsonb(cohort),)).fetchall()
   sample=rows[0]
   queryplans[target]=db.execute('EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON) SELECT a.id,a.primary_media_id FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type=\'artwork\' AND e.scheme=%s AND e.external_id=%s',(sample['scheme'],sample['external_id'])).fetchone()
  if target=='local':
   token=re.search(r'^ARTLINE_EDITOR_TOKEN=(.*)$',(ROOT/'apps/server/.env').read_text(),re.M)[1].strip().strip('\"\'');api='http://127.0.0.1:8080';web='http://localhost:3000'
  else:
   token=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-editor-token','--project=artline-508319'],text=True).strip();api='https://artline-api-lpuqqlugnq-ew.a.run.app';web='https://artline-web-lpuqqlugnq-ew.a.run.app'
  api_checks=[]
  for provider in sorted({s['provider'] for s in completed}):
   s=next(s for s in completed if s['provider']==provider);x=bykey[(s['scheme'],s['external_id'])]
   response=requests.get(api+'/api/v1/museums/'+x['institution']+'/works/'+x['artwork_id']+'?preview=1',headers={'Authorization':'Bearer '+token},timeout=30);assert response.status_code==200
   detail=response.json();assert detail['title']==x['title'] and detail['status']==x['status'] and detail['media_url']
   response=requests.get(web+s['path'],timeout=30);assert response.status_code==200 and core.sha(response.content)==s['sha256']
   api_checks.append({'provider':provider,'artwork_id':x['artwork_id'],'status':200,'image_sha256_matched':True})
  additions=collections.Counter(c for s in completed if not bi[(s['scheme'],s['external_id'])]['primary_media_id'] for c in s['countries'])
  reports[target]={'verified_attachments':len(completed),'new_image_attachments_by_country':dict(additions),'fixed_cohort_coverage':coverage,'api_checks':api_checks,'artwork_metadata_unchanged':True,'commons_candidate_citations':candidate_evidence}
 report={'at':core.now(),'selected_after_scope_exclusions':len(selected),'prepared':len(receipts),'complete_in_both':len(completed),'pending_preparation':[candidate_summary(s) for s in selected if s['artwork_id'] not in prepared],'pending_attachment':[candidate_summary(s) for s in receipts if s['artwork_id'] not in events],'completed_by_provider':dict(collections.Counter(s['provider'] for s in completed)),'completed_by_country':dict(collections.Counter(c for s in completed for c in s['countries'])),'largest_image_bytes':max(s['bytes'] for s in completed),'total_bytes':sum(s['bytes'] for s in completed),'targets':reports,'errors':[]}
 core.save_new(RUN/(label+'-verification.json'),report);core.save_new(RUN/(label+'-query-plans.json'),queryplans)
 print(json.dumps({k:v for k,v in report.items() if k not in ('pending_preparation','pending_attachment','targets')},ensure_ascii=False),flush=True)
def candidate_summary(s):return {k:s[k] for k in ('artwork_id','provider','external_id','artist','title')}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args();main(a.label)
