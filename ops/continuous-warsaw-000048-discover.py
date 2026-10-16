import csv,gzip,json,hashlib,importlib.util
from pathlib import Path
ROOT=Path.cwd(); E=ROOT/'docs/research/continuous-production-20261011/batches/000048'; E.mkdir(parents=True,exist_ok=True)
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/batch-000048'; S.mkdir(parents=True,exist_ok=True)
s=importlib.util.spec_from_file_location('base','ops/continuous-image-batch-000002.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
def save(n,v):
 p=E/n
 if p.exists():return h.load(p)
 h.save(p,v);return v
q=h.load(E.parents[1]/'source-queue.json');save('source-queue-before.json',q)
paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',E.parent/'000047/CHECKPOINT.json',E.parent/'000047/source-access-holds.json',ROOT/'docs/research/germany-deep-20261011/image-failures.json',E.parent/'000042/research-holds.json']
registry=list(csv.DictReader(paths[1].open())); assert len(registry)==111
save('required-input-reconciliation.json',dict(at=h.now(),inputs=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in paths],registry_rows=111,registry=registry,precedence='Current production authorization; real local database remains read-only; one bounded batch and existing external supervisor untouched.'))
save('production-target-reconciliation.json',b.target())
prior=h.load(E.parent/'000047/batch-verification-receipt.json');ids=prior['production_ids']
with h.connect() as db:
 expected=h.load(E.parent/'000047/independent-production-verification.json')['after'];live=h.snapshot(db,ids);assert live==expected
 evs=[dict(x) for x in db.execute('SELECT a.id::text,e.adapter_version,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
 for x in evs:
  ev=json.loads(x['evidence_json']) if isinstance(x['evidence_json'],str) else x['evidence_json'];assert ev['selection_sha256']==prior['selection_sha256'] and x['adapter_version']=='continuous-primary-images-20261011-b000047'
 assert len(evs)==18
save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch_verified=True,batch=47,rows=18,own_persisted_selection_checksums_verified=True,live_matches_previous=True,uncertain_writes=0,increment=0))
holds=h.load(ROOT/'docs/research/germany-deep-20261011/image-failures.json');skd=[x for x in holds if 'skd-online' in str(x)]
save('skd-route-verification.json',dict(at=h.now(),registry=next(x for x in registry if x['source_id']=='skd_dresden'),historical_holds=skd,historical_hold_path=str(paths[-2]),hold_sha256=h.sha(paths[-2].read_bytes()),web_probe=dict(terms_url='https://www.skd.museum/en/terms-of-use/',terms_result='web tool internal error; no HTTP code available',sample_url='https://skd-online-collection.skd.museum/Details/Index/372144',sample_result='web tool rendered navigation without object metadata before historical hold located'),decision='Preserve historical host access denial; no direct provider or image request. Rotate to Warsaw page 2.',retry_held_image=False))
save('source-access-holds.json',dict(at=h.now(),inherited_ledger=str(paths[8]),inherited_sha256=h.sha(paths[8].read_bytes()),skd_hold=skd,warsaw_prior_holds=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor']['held_native_ids'],requests_to_held_image_endpoints=0))
policy=h.load(E.parent/'000042/policy-project.receipt.json');assert h.sha(gzip.decompress(Path(policy['body_path']).read_bytes()))==policy['sha256'];save('policy-project.receipt.json',policy)
def get(key,url):
 p=E/(key+'.receipt.json')
 if p.exists():rc=h.load(p);return json.loads(gzip.decompress(Path(rc['body_path']).read_bytes()))
 i.provider_slot('cyfrowe-api.mnw.art.pl');resp=i.session().get(url,timeout=(15,45));data=resp.content;path=S/(key+'.body.gz');path.write_bytes(gzip.compress(data,mtime=0));rc=dict(url=url,final_url=resp.url,status=resp.status_code,retrieved_at=h.now(),sha256=h.sha(data),bytes=len(data),body_path=str(path),retry_after=resp.headers.get('Retry-After'));save(key+'.receipt.json',rc)
 assert resp.status_code==200,rc
 obj=resp.json();save(key+'.json',obj);return obj
url='https://cyfrowe-api.mnw.art.pl/api/search/Object/page/2?filter%5Bdepartment%5D%5B%5D=97306&filter%5Bphrase%5D=Ikona&maxPerPage=24'
page=get('warsaw-icons-page2',url)['data'];print('PAGINATOR',page['paginatorDetails']);priorids=set(next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor']['processed_native_ids'])
for r in page['items']:
 oid=str(r['id'])
 if oid in priorids:print('SKIP',oid);continue
 o=get('object-'+oid,'https://cyfrowe-api.mnw.art.pl/api/object/'+oid)['data'];print(oid,o['title'],o['noEvidence'],o['createDates'],o['authors'],o['dimensionText'],o['types'],flush=True)
