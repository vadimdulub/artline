#!/usr/bin/env python3
import importlib.util,json,gzip,sys,fcntl,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('base',ROOT/'ops/continuous-image-batch-000002.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
i=base.i;h=base.h;connect=base.connect;target=base.target;load=base.load;save=base.save
E=ROOT/'docs/research/continuous-production-20261011/batches/000005';RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000005';B='cleveland-000'
i.OP='continuous-primary-images-20261011-b000005';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
MID='729385eb-92b0-4cc8-9229-1ac3a46aee1f';SCHEME='european-cleveland-cleveland-museum-of-art-object'
i.CFG['cleveland']=dict(mid=MID,scheme=SCHEME,name='Cleveland Museum of Art',rights='cc0',license='CC0 1.0',policy='https://www.clevelandart.org/open-access',host='openaccess-cdn.clevelandart.org')
old_uid=i.m.uid
i.m.uid=lambda k:'d63cee47-716a-45ba-9e88-b552ff5b59c0' if k=='source/cleveland' else old_uid(k)
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return
 
 if not (E/'production-target-reconciliation.json').exists():save(E/'production-target-reconciliation.json',target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rs=list(csv.DictReader(registry.open()));assert len(rs)==111
 if not (E/'source-register.json').exists():save(E/'source-register.json',dict(at=h.now(),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,source=[r for r in rs if r['source_id']=='cleveland_museum'],policy='docs/ARTLINE_IMAGE_USE.md',retained_holds={str(p.relative_to(ROOT)):load(p) for p in (base.OLD/'access-holds').glob('*.json')}))
 with connect() as db:
  rows=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_precision,e.external_id,(SELECT string_agg(ar.display_name,'; ' ORDER BY ar.display_name) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creator FROM artworks a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artwork' AND e.scheme=%s WHERE a.current_institution_id=%s AND a.primary_media_id IS NULL AND a.status<>'archived' AND a.creation_year_end<=1955 ORDER BY a.id LIMIT 80",(SCHEME,MID))]
 chosen=[];checks=[]
 for a in rows:
  native=a['external_id'];url='https://openaccess-api.clevelandart.org/api/artworks/'+native;i.provider_slot('openaccess-api.clevelandart.org');r=i.session().get(url,timeout=(15,40));raw=r.content
  body=E/'source-captures'/(native+'.body.gz');body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(raw,mtime=0));rc=dict(at=h.now(),url=url,status=r.status_code,sha256=h.sha(raw),body_path=str(body.relative_to(ROOT)))
  save(E/'source-captures'/(native+'.receipt.json'),rc)
  if r.status_code in [401,403,429]:save(E/'source-access-holds.json',dict(rc,retry_after=r.headers.get('Retry-After')));break
  r.raise_for_status();d=r.json()['data'];reason='eligible';image=d.get('images',{}).get('web',{}).get('url')
  if d['share_license_status']!='CC0' or not image:reason='no_explicit_cc0_primary_image'
  elif (str(d['id']),d['title'],d['accession_number'],d['creation_date_earliest'],d['creation_date_latest'])!=(native,a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end']):reason='identity_or_date_mismatch'
  elif not image.startswith('https://openaccess-cdn.clevelandart.org/'):reason='unverified_image_host'
  checks.append(dict(artwork_id=a['id'],native_id=native,reason=reason))
  if reason=='eligible':
   source=dict(d,assistivetext=d.get('description') or '')
   chosen.append(dict(artwork_id=a['id'],native_id=native,title=a['title'],creator_label=a['creator'] or '; '.join(c['description'] for c in d.get('creators',[])),source_url=d['url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=d['type'].lower(),provider='cleveland',image=dict(native_url=image,image_url=image,source=source,receipt=rc),plan_sha256=rc['sha256'],plan_path=str(body),rights_basis='Native object API explicitly marks CC0 and supplies this exact object web reproduction. '+d.get('creditline','')))
  if len(chosen)==12:break
 save(E/'gap-reconciliation.json',dict(at=h.now(),rows=checks,selected=len(chosen),resume_after_artwork_id=checks[-1]['artwork_id']))
 assert chosen,'No eligible bounded gaps'
 save(i.folder(B)/'selection.json.gz',dict(provider='cleveland',batch=B,rows=chosen,selection_basis='Existing exact native accession/title/date gaps; fresh CC0 API image evidence.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for row in chosen:i.prepare_one(row,B)
 save(E/'cloud-backup.json',load(base.OLD/'cloud-backup.json'));i.audit(B)
 print(load(i.folder(B)/'sheets/000.json')['path'])
def deliver():
 save(E/'production-target-before-write.json',target(True));i.upload(B);target(True);i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
