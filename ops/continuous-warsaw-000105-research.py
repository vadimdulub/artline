#!/usr/bin/env python3
"""Bounded page-thirteen native icon research; external supervisor unchanged."""
import csv, fcntl, gzip, importlib.util, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=mod('base105','continuous-image-batch-000002.py');h=base.h;i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000105'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000105'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/batches/000105'
for p in [E,R,S,E/'warsaw']:p.mkdir(parents=True,exist_ok=True)
def save(n,v):
 p=E/n
 if not p.exists():h.save(p,v)
 return h.load(p)
def preflight():
 q=h.load(E.parents[1]/'source-queue.json');save('source-queue-before.json',q)
 paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000104/CHECKPOINT.json',E.parent/'000104/source-access-holds.json',E.parent/'000100/research-holds.json',ROOT/'ops/india-300-delivery-20261011.py']
 reg=list(csv.DictReader(paths[1].open()));assert len(reg)==111 and {x['source_id'] for x in reg}=={x['source_id'] for x in q['sources']}
 save('required-input-reconciliation.json',dict(started_at=h.now(),inputs=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in paths],complete_original_registry=reg,precedence='Current user and source approvals; real local catalogue read-only. External supervisor owns continuation.'))
 target=base.target();actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres';save('production-target-reconciliation.json',dict(target,connection_name=actual,helper='ops/india-300-delivery-20261011.py'))
 prev=h.load(E.parent/'000104/independent-production-verification.json');receipt=h.load(E.parent/'000104/batch-verification-receipt.json')
 with h.connect() as db:
  ids=receipt['production_ids'];live=h.snapshot(db,ids);assert live==prev['after']
  own=[dict(x) for x in db.execute("SELECT id::text FROM artworks WHERE slug LIKE 'continuous-warsaw-20261011-b000105-%%'")];assert not own,'Reconcile interrupted writes first'
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),prior_batch=104,ids=ids,exact_snapshot_equal=True,current_batch_existing_writes=own,new_increments=0))
 checkpoint=h.load(E.parents[1]/'CHECKPOINT.json');pid=checkpoint['supervisor_pid']
 proc=subprocess.run(['ps','-p',str(pid),'-o','pid=,etime=,comm='],capture_output=True,text=True)
 save('external-continuation-observation.json',dict(at=h.now(),supervisor_pid=pid,process_present=proc.returncode==0,process=proc.stdout.strip(),checkpoint_inflight=checkpoint.get('inflight'),prior_completed_batches=[103,104],new_supervisors_started=0,supervisor_modified=False))
 inherited=E.parent/'000104/source-access-holds.json';save('source-access-holds.json',dict(at=h.now(),inherited_ledger=str(inherited),inherited_sha256=h.sha(inherited.read_bytes()),holds=h.load(inherited),provider_holds_preserved=True,held_provider_requests=0))
 policy=h.load(E.parent/'000057/policy-project.receipt.json');assert h.sha(gzip.decompress(Path(policy['body_path']).read_bytes()))==policy['sha256'];save('warsaw/policy-project.receipt.json',policy)
 print('Production target verified; prior delivery unchanged; no previous batch-105 writes.')
def get(key,url):
 ep=E/'warsaw'/(key+'.receipt.json')
 if ep.exists():
  rc=h.load(ep);raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256'];return json.loads(raw)
 assert not (E/'warsaw/warsaw-access-hold.json').exists()
 i.provider_slot('cyfrowe-api.mnw.art.pl');resp=i.session().get(url,timeout=(15,45));raw=resp.content;path=S/(key+'.body.gz');path.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,final_url=resp.url,status=resp.status_code,retrieved_at=h.now(),sha256=h.sha(raw),bytes=len(raw),body_path=str(path),retry_after=resp.headers.get('Retry-After'));save('warsaw/'+key+'.receipt.json',rc)
 if resp.status_code in [401,403,429]:save('warsaw/warsaw-access-hold.json',rc)
 assert resp.status_code==200
 obj=resp.json();save('warsaw/'+key+'.json',obj);return obj
def discover():
 q=h.load(E/'source-queue-before.json');route=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw');assert route['resume_cursor']['next_page_after_pending']==13
 url='https://cyfrowe-api.mnw.art.pl/api/search/Object/page/13?filter%5Bdepartment%5D%5B%5D=97306&filter%5Bphrase%5D=Ikona&maxPerPage=24'
 page=get('warsaw-icons-page13',url)['data'];assert page['paginatorDetails']['currentPage']==13;print('PAGINATOR',page['paginatorDetails'],flush=True)
 prior=set(route['resume_cursor']['processed_native_ids'])
 for item in page['items']:
  oid=str(item['id'])
  if oid in prior:print('SKIP',oid,flush=True);continue
  o=get('object-'+oid,'https://cyfrowe-api.mnw.art.pl/api/object/'+oid)['data'];print(oid,o['title'],o['noEvidence'],o['createDates'],o['authors'],o['dimensionText'],[x['name'] for x in o['techniques']],flush=True)
if __name__=='__main__':
 import sys
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
