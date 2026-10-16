#!/usr/bin/env python3
import importlib.util,json,gzip,sys,fcntl,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('base',ROOT/'ops/continuous-image-batch-000002.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
i=base.i;h=base.h;connect=base.connect;target=base.target;load=base.load;save=base.save
E=ROOT/'docs/research/continuous-production-20261011/batches/000008';RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000008';B='aic-000'
i.OP='continuous-primary-images-20261011-b000008';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
MID='9e75033c-8e6b-464b-974b-d94fcc91c6a3';SCHEME='aic-object'
i.CFG['aic']=dict(mid=MID,scheme=SCHEME,name='Art Institute of Chicago',rights='cc0',license='CC0 1.0',policy='https://www.artic.edu/open-access/open-access-images',host='www.artic.edu')
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return
 
 if not (E/'production-target-reconciliation.json').exists():save(E/'production-target-reconciliation.json',target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rs=list(csv.DictReader(registry.open()));assert len(rs)==111
 if not (E/'source-register.json').exists():save(E/'source-register.json',dict(at=h.now(),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,source=[r for r in rs if r['source_id']=='artic'],policy='docs/ARTLINE_IMAGE_USE.md',retained_holds={str(p.relative_to(ROOT)):load(p) for p in (base.OLD/'access-holds').glob('*.json')}))
 with connect() as db:
  rows=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_precision,e.external_id,(SELECT string_agg(ar.display_name,'; ' ORDER BY ar.display_name) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creator FROM artworks a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artwork' AND e.scheme=%s WHERE a.current_institution_id=%s AND a.primary_media_id IS NULL AND a.status<>'archived' AND a.creation_year_end<=1955 ORDER BY a.id LIMIT 80",(SCHEME,MID))]
 chosen=[];checks=[]
 for a in rows:
  native=a['external_id'];url='https://api.artic.edu/api/v1/artworks/'+native;i.provider_slot('api.artic.edu');r=i.session().get(url,timeout=(15,40));raw=r.content
  body=E/'source-captures'/(native+'.body.gz');body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(raw,mtime=0));rc=dict(at=h.now(),url=url,status=r.status_code,sha256=h.sha(raw),body_path=str(body.relative_to(ROOT)))
  save(E/'source-captures'/(native+'.receipt.json'),rc)
  if r.status_code in [401,403,429]:save(E/'source-access-holds.json',dict(rc,retry_after=r.headers.get('Retry-After')));break
  r.raise_for_status();d=r.json()['data'];reason='eligible';image_id=d.get('image_id')
  spec=importlib.util.spec_from_file_location('aicdates',ROOT/'ops/million-aic-20261011.py');am=importlib.util.module_from_spec(spec);spec.loader.exec_module(am);dates=am.creation(d)
  if not d.get('is_public_domain') or not image_id:reason='no_explicit_public_domain_primary_image'
  elif (str(d['id']),d['title'],d['main_reference_number'])!=(native,a['title'],a['accession_number']):reason='identity_mismatch'
  elif not dates or dates[:2]!=(a['creation_year_start'],a['creation_year_end']):reason='creation_date_mismatch'
  checks.append(dict(artwork_id=a['id'],native_id=native,reason=reason))
  if reason=='eligible':
   image='https://www.artic.edu/iiif/2/'+image_id+'/full/843,/0/default.jpg'
   source=dict(d,assistivetext=(d.get('thumbnail') or {}).get('alt_text',''))
   chosen.append(dict(artwork_id=a['id'],native_id=native,title=a['title'],creator_label=d.get('artist_display') or a['creator'] or '',source_url='https://www.artic.edu/artworks/'+native,accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=d['artwork_type_title'].lower(),provider='aic',image=dict(native_url=image,image_url=image,source=source,receipt=rc),plan_sha256=h.sha(body.read_bytes()),plan_path=str(body),rights_basis='Native object API is_public_domain true; Art Institute open-access images CC0. '+(d.get('credit_line') or '')))
  if len(chosen)==12:break
 save(E/'gap-reconciliation.json',dict(at=h.now(),rows=checks,selected=len(chosen),resume_after_artwork_id=checks[-1]['artwork_id']))
 assert chosen,'No eligible bounded gaps'
 save(i.folder(B)/'selection.json.gz',dict(provider='cleveland',batch=B,rows=chosen,selection_basis='Existing exact native accession/title/date gaps; fresh CC0 API image evidence.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for row in chosen:i.prepare_one(row,B)
 (i.ORIG/B).mkdir(parents=True,exist_ok=True)
 save(E/'cloud-backup.json',load(base.OLD/'cloud-backup.json'));i.audit(B)
 print(load(i.folder(B)/'sheets/000.json')['path'])
def deliver():
 
 if not (E/'production-target-before-write.json').exists():save(E/'production-target-before-write.json',target(True))
 i.upload(B);target(True);i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
