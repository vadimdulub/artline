#!/usr/bin/env python3
"""Bounded metadata-only discovery and durable captures for batch 42."""
import csv, datetime, fcntl, gzip, hashlib, importlib.util, json, shutil
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000042'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000042'
C=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/batch-000042/captures'
for p in [E,R,C]:p.mkdir(parents=True,exist_ok=True)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,v):
 p=E/name;b=json.dumps(v,ensure_ascii=False,indent=2,default=str).encode()
 if p.exists():return json.loads(p.read_bytes())
 p.write_bytes(b);return v
def capture(name,url):
 p=E/(name+'.receipt.json')
 if p.exists():
  rc=json.loads(p.read_bytes());raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert sha(raw)==rc['sha256'];return rc,raw
 response=requests.get(url,timeout=(15,45),headers={'User-Agent':'ArtlineResearch/1.0 (bounded museum catalogue research)'})
 raw=response.content;body=C/(name+'.body.gz');body.write_bytes(gzip.compress(raw,mtime=0))
 rc=save(name+'.receipt.json',dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=now(),sha256=sha(raw),bytes=len(raw),body_path=str(body),retry_after=response.headers.get('Retry-After')))
 assert response.status_code==200,('Access hold; no retry',response.status_code,url)
 return rc,raw
def main():
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json','docs/research/continuous-production-20261011/batches/000041/CHECKPOINT.json','docs/research/continuous-production-20261011/batches/000041/source-access-holds.json','docs/research/continuous-production-20261011/batches/000040/source-access-holds.json']
  regpath=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(regpath.open()));assert len(reg)==111
  save('required-input-reconciliation.json',dict(at=now(),files=[dict(path=p,sha256=sha((ROOT/p).read_bytes()),bytes=(ROOT/p).stat().st_size) for p in required],registry=dict(path=str(regpath),sha256=sha(regpath.read_bytes()),rows=len(reg)),overrides='Original CSV retained in full; supplemental JSON is not its replacement. Local catalogue read-only. One bounded batch; external supervisor untouched.'))
  save('original-source-registry.json',reg)
  q=save('source-queue-before.json',json.loads((E.parents[1]/'source-queue.json').read_bytes()))
  save('source-access-holds.json',dict(at=now(),inherited_ledger='docs/research/continuous-production-20261011/batches/000041/source-access-holds.json',inherited_queue='source-queue-before.json',policy='No access-held provider retried; Warsaw public native object route available. Prior identity/date holds preserved.',new_holds=['discovery-route-verification.json']))
  save('discovery-route-verification.json',dict(at=now(),routes=[dict(source_id='national_gallery_prague',queries=['site.ngprague.cz sbirky ikona','site.sbirky.ngprague.cz ikona Detail'],checked_url='https://sbirky.ngprague.cz/katalog?search=ikona',result='Web tool reports URL not accessible; no HTTP status supplied. Collection-level long-term loan context does not establish individual artwork identities or ownership.',resume='Do not repeat unchanged searches. Require accessible exact catalogue inventories or a documented loan catalogue.',objects_selected=0),dict(source_id='lacma',queries=['site.collections.lacma.org icon Russian'],result='Search discovery only: official object 40124 Dancing Soldiers 1909–1910, Mikhail Larionov. Neo-primitivist painting, not an icon; no direct object capture or production selection in this batch.',url='https://collections.lacma.org/object/40124',resume='Potential separate Russian avant-garde metadata route; exact object and global creator reconciliation required. Restricted rights cannot borrow Russian-museum approval.',objects_selected=0)]))
  prior=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw')
  ids=prior['resume_cursor']['pending_native_ids_current_page'];assert len(ids)==17
  for oid in ids:
   rc,raw=capture('object-'+oid,'https://cyfrowe-api.mnw.art.pl/api/object/'+oid)
   obj=json.loads(raw);save('object-'+oid+'.json',obj)
   o=obj['data'];print(json.dumps({k:o.get(k) for k in ['id','title','noEvidence','createDates','authors','types','dimensionText','owner','copyrights']},ensure_ascii=False),flush=True)
  old=ROOT/'docs/research/continuous-production-20261011/batches/000040/policy-project.receipt.json'
  rc=json.loads(old.read_bytes());assert sha(gzip.decompress(Path(rc['body_path']).read_bytes()))==rc['sha256'];save('policy-project.receipt.json',rc)
if __name__=='__main__':main()
