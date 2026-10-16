#!/usr/bin/env python3
import importlib.util,json,gzip,sys,fcntl,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('base',ROOT/'ops/continuous-image-batch-000002.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
i=base.i;h=base.h;connect=base.connect;target=base.target;load=base.load;original_save=base.save
def save(path,value):
 if path.exists():return load(path)
 return original_save(path,value)
E=ROOT/'docs/research/continuous-production-20261011/batches/000017';RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000017';B='mia-000'
i.OP='continuous-primary-images-20261011-b000017';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
MID='9d7ff4ab-bbef-5ecc-836c-f7ed18b6bda9';SCHEME='mia-object'
helper=base.mod('mia_helpers','overnight-mia-images.py')
i.CFG['mia']=dict(mid=MID,scheme=SCHEME,name='Minneapolis Institute of Art',rights='public_domain',license='Public Domain Mark 1.0',policy='https://creativecommons.org/publicdomain/mark/1.0/',host='img.artsmia.org')
old_uid=i.m.uid
i.m.uid=lambda k:'fb892ae1-7ed8-4643-bc35-8950da2861e2' if k=='source/mia' else old_uid(k)
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def prepare():
 if (i.folder(B)/'selection.json.gz').exists():
  assert h.sha((i.folder(B)/'selection.json.gz').read_bytes())==load(i.folder(B)/'pin.json')['sha256']
  return finish_preparation(i.selected(B)['rows'])
 
 if not (E/'production-target-reconciliation.json').exists():save(E/'production-target-reconciliation.json',target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rs=list(csv.DictReader(registry.open()));assert len(rs)==111
 if not (E/'source-register.json').exists():save(E/'source-register.json',dict(at=h.now(),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,source=[r for r in rs if r['source_id']=='minneapolis_institute_art'],policy='docs/ARTLINE_IMAGE_USE.md',retained_holds={str(p.relative_to(ROOT)):load(p) for p in (base.OLD/'access-holds').glob('*.json')}))
 with connect() as db:
  rows=[dict(x) for x in db.execute(helper.QUERY+" AND a.current_institution_id=%s AND a.primary_media_id IS NULL AND a.creation_year_end<=1955 AND a.id>%s::uuid ORDER BY a.id LIMIT 60",(MID,"4eec4ea7-e092-4cac-9be9-32a3d0ba0a31"))]
 chosen=[];checks=[]
 for a in rows:
  native=a['external_id'];url='https://search.artsmia.org/id/'+native;receiptpath=E/'source-captures'/(native+'.receipt.json')
  if receiptpath.exists():
   rc=load(receiptpath);raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200;d=json.loads(raw);body=ROOT/rc['body_path']
  else:
   i.provider_slot('search.artsmia.org');r=i.session().get(url,timeout=(15,40));raw=r.content
   body=E/'source-captures'/(native+'.body.gz');body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(raw,mtime=0));rc=dict(at=h.now(),url=url,status=r.status_code,sha256=h.sha(raw),body_path=str(body.relative_to(ROOT)))
   save(receiptpath,rc)
   if r.status_code in [401,403,429]:save(E/'source-access-holds.json',dict(rc,retry_after=r.headers.get('Retry-After')));break
   r.raise_for_status();d=r.json()
  reason='eligible'
  try:
   if not a['artist']:raise ValueError('Unresolved object-level creator requires anonymous/workshop identity workflow')
   image,facts=helper.source_match(a,d)
  except ValueError as exc:reason=str(exc)
  checks.append(dict(artwork_id=a['artwork_id'],native_id=native,reason=reason))
  if reason=='eligible':
   chosen.append(dict(artwork_id=a['artwork_id'],native_id=native,title=a['title'],creator_label=d['artist'],source_url='https://collections.artsmia.org/art/'+native,accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='mia',image=dict(native_url=image,image_url=image,source=d,receipt=rc),plan_sha256=h.sha(body.read_bytes()),plan_path=str(body),rights_basis='Fresh museum object API explicitly states Public Domain, unrestricted Full image display and exact primary rendition. '+d.get('creditline','')))
  if len(chosen)==12:break
 save(E/'gap-reconciliation.json',dict(at=h.now(),rows=checks,selected=len(chosen),resume_after_artwork_id=checks[-1]['artwork_id'] if checks else None))
 assert chosen,'No eligible bounded gaps'
 save(i.folder(B)/'selection.json.gz',dict(provider='mia',batch=B,rows=chosen,selection_basis='Existing exact native accession/title/date gaps; fresh CC0 API image evidence.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 finish_preparation(chosen)
def finish_preparation(chosen):
 for row in chosen:i.prepare_one(row,B)
 (i.ORIG/B).mkdir(parents=True,exist_ok=True)
 if not (E/'cloud-backup.json').exists():save(E/'cloud-backup.json',load(base.OLD/'cloud-backup.json'))
 i.audit(B)
 print(load(i.folder(B)/'sheets/000.json')['path'])

def deliver():
 checked=target(True)
 if not (E/'production-target-before-write.json').exists():save(E/'production-target-before-write.json',checked)
 i.upload(B);target(True);i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
