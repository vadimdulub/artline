#!/usr/bin/env python3
"""One bounded reserve audit and page-eight discovery. Never starts a worker."""
import csv, fcntl, gzip, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=mod('base82','continuous-image-batch-000002.py');h=b.h;i=b.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000082'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000082'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000082'
for p in [E,R,S]:p.mkdir(parents=True,exist_ok=True)
def save(n,v):
 p=E/n
 if not p.exists():h.save(p,v)
 return h.load(p)
def run():
 q=h.load(E.parents[1]/'source-queue.json');save('source-queue-before.json',q)
 paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000081/CHECKPOINT.json',E.parent/'000081/source-access-holds.json',ROOT/'ops/india-300-delivery-20261011.py',ROOT/'docs/research/printmaking-continuation-20261011/README.md']
 reg=list(csv.DictReader(paths[1].open()));assert len(reg)==111
 save('required-input-reconciliation.json',dict(at=h.now(),inputs=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in paths],registry=reg,registry_rows=111,precedence='Current source-specific approvals; production authorized, real local catalogue read-only; one bounded batch, external supervisor unmodified.'))
 save('production-target-reconciliation.json',b.target())
 prior=h.load(E.parent/'000081/independent-production-verification.json');receipt=h.load(E.parent/'000081/batch-verification-receipt.json')
 with h.connect() as db:
  live=h.snapshot(db,receipt['production_ids']);expected=prior.get('after',prior.get('rows'));assert live==expected
  notes=list(db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='continuous_pola_object_evidence_b000081'",(receipt['production_ids'],)))
  assert len(notes)==9 and all(x['pin']==receipt['metadata_plan_sha256'] for x in notes)
  own=list(db.execute("SELECT entity_id::text FROM citations WHERE field_name='continuous_warsaw_object_evidence_20261011_b000082'"))
  assert not own or (E/'warsaw-icons/plan-pin.json').exists(),'Own prior write requires pinned-plan recovery'
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch_verified=True,batch=81,verified_rows=9,persisted_plan_checksum_verified=True,live_matches_previous=True,current_batch_existing_citations=own,increment=0))
 reserve=mod('reserve82','continuous-reserve-warsaw-000052-research.py');reserve.E=E;reserve.reserve()
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=h.load(pp);pin=h.sha(pp.read_bytes());ids=[r['artwork_id'] for r in p['rows']]
 save('production-target-before-reserve-read.json',b.target())
 with h.connect() as db:
  live=h.snapshot(db,ids)
  cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
  assert len(live)==len(cit)==188 and all(x['plan_sha256']==pin for x in cit)
  for row in p['rows']:
   a=live[row['artwork_id']]['artwork'];im=p['images'][row['artwork_id']]
   assert a['accession_number']==row['accession_number'] and a['primary_media_id']==im['media_id'] and a['status']!='archived'
   assert all(a[k]==v for k,v in row['date'].items())
 save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,new_programme_increments=0,plan_sha256=pin,source_citations=cit,live_rows=live,selected=0,physical_date_holds_preserved=['80082','80437','81054'],next_action='Warsaw page eight; reserve exhausted; no replay or historical plan mutation.'))
 print('Reserve: all 188 already delivered; zero new candidates.',flush=True)
 hold=E.parent/'000081/source-access-holds.json';save('source-access-holds.json',dict(at=h.now(),inherited_ledger=str(hold.relative_to(ROOT)),inherited_sha256=h.sha(hold.read_bytes()),provider_holds_preserved=True,warsaw_previous_held_ids=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor']['held_native_ids'],new_holds=[],held_provider_requests=0))
 policy=h.load(E.parent/'000057/policy-project.receipt.json');assert h.sha(gzip.decompress(Path(policy['body_path']).read_bytes()))==policy['sha256'];save('policy-project.receipt.json',policy)
 def get(key,url):
  p=E/(key+'.receipt.json')
  if p.exists():
   rc=h.load(p);assert rc['status']==200;raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'];return json.loads(raw)
  assert not (E/'warsaw-access-hold.json').exists()
  i.provider_slot('cyfrowe-api.mnw.art.pl');resp=i.session().get(url,timeout=(15,45));raw=resp.content;path=S/(key+'.body.gz');assert not path.exists();path.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,final_url=resp.url,status=resp.status_code,retrieved_at=h.now(),sha256=h.sha(raw),bytes=len(raw),body_path=str(path),retry_after=resp.headers.get('Retry-After'));save(key+'.receipt.json',rc)
  if resp.status_code in [401,403,429]:save('warsaw-access-hold.json',rc)
  assert resp.status_code==200
  obj=resp.json();save(key+'.json',obj);return obj
 cursor=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor'];assert cursor['next_discovery_page']==8
 url='https://cyfrowe-api.mnw.art.pl/api/search/Object/page/8?filter%5Bdepartment%5D%5B%5D=97306&filter%5Bphrase%5D=Ikona&maxPerPage=24'
 page=get('warsaw-icons-page8',url)['data'];print('PAGINATOR',page['paginatorDetails'],flush=True)
 for item in page['items']:
  oid=str(item['id'])
  if oid in cursor['processed_native_ids']:print('SKIP',oid);continue
  o=get('object-'+oid,'https://cyfrowe-api.mnw.art.pl/api/object/'+oid)['data']
  print(json.dumps(dict(id=oid,title=o['title'],acc=o['noEvidence'],dates=o['createDates'],authors=o['authors'],dimensions=o['dimensionText'],types=o['types'],techniques=o['techniques'],materials=o['materials']),ensure_ascii=False),flush=True)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);run()
