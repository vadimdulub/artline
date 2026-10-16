#!/usr/bin/env python3
"""One bounded read-only reserve audit and Warsaw page eleven discovery."""
import csv,fcntl,gzip,importlib.util,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=mod('base97','continuous-image-batch-000002.py');h=base.h;i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000097'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000097'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/batches/000097'
for p in [E,R,S,E/'warsaw']:p.mkdir(parents=True,exist_ok=True)
def save(n,v):
 p=E/n
 if not p.exists():h.save(p,v)
 return h.load(p)
def preflight():
 q=h.load(E.parents[1]/'source-queue.json');save('source-queue-before.json',q)
 paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000096/CHECKPOINT.json',E.parent/'000096/research-holds.json',E.parent/'000094/source-access-holds.json',E.parent/'000092/source-access-holds.json',ROOT/'ops/india-300-delivery-20261011.py']
 reg=list(csv.DictReader(paths[1].open()));assert len(reg)==111 and {x['source_id'] for x in reg}=={x['source_id'] for x in q['sources']}
 save('required-input-reconciliation.json',dict(at=h.now(),inputs=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in paths],complete_original_registry=reg,precedence='Current user and latest source-specific policy; local catalogue read-only. External supervisor owns continuation; no supervisor modifications.'))
 target=base.target();actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres';save('production-target-reconciliation.json',dict(target,connection_name=actual,helper='ops/india-300-delivery-20261011.py'))
 prev=h.load(E.parent/'000096/independent-production-verification.json');receipt=h.load(E.parent/'000096/batch-verification-receipt.json')
 with h.connect() as db:
  ids=receipt['production_ids'];assert h.snapshot(db,ids)==prev['after']
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name='continuous_greek_object_evidence_b000096' AND entity_id=ANY(%s::uuid[])",(ids,))]
  assert len(notes)==len(ids) and all(x['pin']==receipt['metadata_plan_sha256'] for x in notes)
  own=[dict(x) for x in db.execute("SELECT id::text FROM artworks WHERE slug LIKE 'continuous-warsaw-20261011-b000097-%%'")];assert not own,'In-flight writes require recovery before selecting'
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),prior_batch=96,ids=ids,exact_snapshot_equal=True,persisted_plan_checksums_verified=True,current_batch_existing_writes=own,new_increments=0))
 reserve=mod('reserve97','continuous-reserve-warsaw-000052-research.py');reserve.E=E;reserve.PREVIOUS=E.parent/'000094';reserve.reserve()
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=h.load(pp);pin=h.sha(pp.read_bytes());ids=[r['artwork_id'] for r in p['rows']]
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  live=h.snapshot(db,ids);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
  assert len(live)==len(cit)==188 and all(x['plan_sha256']==pin for x in cit)
  for r in p['rows']:
   a=live[r['artwork_id']]['artwork'];im=p['images'][r['artwork_id']];assert a['accession_number']==r['accession_number'] and a['primary_media_id']==im['media_id'] and a['status']!='archived' and all(a[k]==v for k,v in r['date'].items())
 save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,plan_sha256=pin,source_citations=cit,live_rows=live,physical_date_holds_preserved=['80082','80437','81054']))
 inherited=E.parent/'000094/source-access-holds.json';save('source-access-holds.json',dict(at=h.now(),inherited_ledger=str(inherited),inherited_sha256=h.sha(inherited.read_bytes()),provider_holds_preserved=True,held_provider_requests=0))
 policy=h.load(E.parent/'000057/policy-project.receipt.json');assert h.sha(gzip.decompress(Path(policy['body_path']).read_bytes()))==policy['sha256'];save('warsaw/policy-project.receipt.json',policy)
 print('Live French reserve: all 188 already delivered. Prior batch reconciled; zero reserve additions.')
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
 q=h.load(E/'source-queue-before.json');route=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw');assert route['resume_cursor']['next_page_after_pending']==11
 url='https://cyfrowe-api.mnw.art.pl/api/search/Object/page/11?filter%5Bdepartment%5D%5B%5D=97306&filter%5Bphrase%5D=Ikona&maxPerPage=24'
 page=get('warsaw-icons-page11',url)['data'];assert page['paginatorDetails']['currentPage']==11;print('PAGINATOR',page['paginatorDetails'],flush=True)
 prior=set(route['resume_cursor']['processed_native_ids'])
 for item in page['items']:
  oid=str(item['id'])
  if oid in prior:print('SKIP',oid,flush=True);continue
  o=get('object-'+oid,'https://cyfrowe-api.mnw.art.pl/api/object/'+oid)['data'];print(oid,o['title'],o['noEvidence'],o['createDates'],o['authors'],o['dimensionText'],o['types'],[x['name'] for x in o['techniques']],flush=True)
if __name__=='__main__':
 import sys
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
