import csv,gzip,importlib.util,json,fcntl
from pathlib import Path
ROOT=Path.cwd();E=ROOT/'docs/research/continuous-production-20261011/batches/000090';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000090';S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000090'
for p in [E,R,S]:p.mkdir(parents=True,exist_ok=True)
lock=(R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
s=importlib.util.spec_from_file_location('b','ops/continuous-image-batch-000002.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
def save(n,v):
 p=E/n
 if not p.exists():h.save(p,v)
 return h.load(p)
q=h.load(E.parents[1]/'source-queue.json');save('source-queue-before.json',q)
paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000089/CHECKPOINT.json',E.parent/'000089/source-access-holds.json',E.parent/'000082/page-eight-editorial-dispositions.json']
reg=list(csv.DictReader(paths[1].open()));assert len(reg)==111
save('required-input-reconciliation.json',dict(at=h.now(),inputs=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in paths],registry_rows=111,registry=reg,precedence='User production authorization and source-specific approvals; local database read-only; external supervisor untouched.'))
save('production-target-reconciliation.json',b.target())
prior=h.load(E.parent/'000089/independent-production-verification.json'); receipt=h.load(E.parent/'000089/batch-verification-receipt.json')
with h.connect() as db:
 ids=receipt['production_ids'];live=h.snapshot(db,ids)
 expected=prior.get('after',prior.get('rows'));assert live==expected
 evs=list(db.execute('SELECT a.id::text,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,)))
 for x in evs:
  ev=x['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
  assert ev['selection_sha256']==receipt['selection_sha256']
 assert len(evs)==1
save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch_verified=True,batch=89,verified_rows=1,own_persisted_selection_checksum_verified=True,live_matches_previous=True,uncertain_writes=0,increment=0))
hold=E.parent/'000089/source-access-holds.json';save('source-access-holds.json',dict(at=h.now(),inherited_ledger=str(hold.relative_to(ROOT)),inherited_sha256=h.sha(hold.read_bytes()),provider_holds_preserved=True,warsaw_previous_held_ids=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor']['held_native_ids'],new_holds=[],held_provider_requests=0))
policy=h.load(E.parent/'000057/policy-project.receipt.json');assert h.sha(gzip.decompress(Path(policy['body_path']).read_bytes()))==policy['sha256'];save('policy-project.receipt.json',policy)
def get(key,url):
 p=E/(key+'.receipt.json')
 if p.exists():rc=h.load(p);assert rc['status']==200;raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'];return json.loads(raw)
 assert not (E/'warsaw-access-hold.json').exists()
 i.provider_slot('cyfrowe-api.mnw.art.pl');resp=i.session().get(url,timeout=(15,45));raw=resp.content;path=S/(key+'.body.gz');path.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,final_url=resp.url,status=resp.status_code,retrieved_at=h.now(),sha256=h.sha(raw),bytes=len(raw),body_path=str(path),retry_after=resp.headers.get('Retry-After'));save(key+'.receipt.json',rc)
 if resp.status_code in [401,403,429]:save('warsaw-access-hold.json',rc)
 assert resp.status_code==200
 obj=resp.json();save(key+'.json',obj);return obj
url='https://cyfrowe-api.mnw.art.pl/api/search/Object/page/9?filter%5Bdepartment%5D%5B%5D=97306&filter%5Bphrase%5D=Ikona&maxPerPage=24'
page=get('warsaw-icons-page9',url)['data'];print('PAGINATOR',page['paginatorDetails'])
priorids=set(next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor']['processed_native_ids'])
for item in page['items']:
 oid=str(item['id'])
 if oid in priorids:print('SKIP',oid);continue
 o=get('object-'+oid,'https://cyfrowe-api.mnw.art.pl/api/object/'+oid)['data'];print(oid,o['title'],o['noEvidence'],o['createDates'],o['authors'],o['dimensionText'],o['types'],[x['name'] for x in o['techniques']],flush=True)
