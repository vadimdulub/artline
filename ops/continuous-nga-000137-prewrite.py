#!/usr/bin/env python3
"""Verify selected NGA source identities and scoped recovery; no catalogue mutations."""
import csv,fcntl,gzip,importlib.util,io,json,os,subprocess
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-nga-images-000137.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);assert 1<=len(images)<=100
pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rows=i.selected(b.B)['rows'];source=[];files=[]
source_records={};captured=[]
for name in ['objects.csv','published_images.csv']:
 rc=b.load(i.m.RUN/'sources/nga'/(name+'.receipt.json'));path=Path(rc['path']);assert h.sha(path.read_bytes())==rc['sha256'];captured.append(rc)
 with path.open(encoding='utf-8-sig',newline='') as file:
  key='objectid' if name=='objects.csv' else 'uuid';wanted={row['native_id'] if key=='objectid' else row['image']['source']['uuid'] for row in rows};source_records[name]={r[key]:r for r in csv.DictReader(file) if r[key] in wanted}
for row in rows:
 rc=b.load(b.E/'source-captures'/(row['native_id']+'.info.receipt.json'));body=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(body)==rc['sha256'] and rc['status']==200
 info=json.loads(body);assert info.get('@id',info.get('id'))==row['image']['native_url'];src=row['image']['source'];assert src['openaccess']=='1' and src['viewtype']=='primary' and src['depictstmsobjectid']==row['native_id']
 assert source_records['published_images.csv'][src['uuid']]==src
 obj=source_records['objects.csv'][row['native_id']];assert obj['title']==row['title'] and obj['accessionnum']==row['accession_number'] and obj['isvirtual']=='0' and obj['accessioned']=='1'
 planpath=Path(row['plan_path']);assert h.sha(planpath.read_bytes())==row['plan_sha256']
 orig=next(x for x in b.load(planpath)['new_artworks'] if x['artwork_id']==row['artwork_id']);assert all(obj[k]==v for k,v in orig['raw'].items());assert set(obj)-set(orig['raw'])=={'markings','inscription','provenancetext'}
 assert row['creator_label']==obj['attribution']
 assert (row['first'],row['last'])==(orig['first'],orig['last']) and row['last']<=1955
 source.append(dict(artwork_id=row['artwork_id'],native_id=row['native_id'],source_object=obj,primary_image=src,info_receipt=rc,source_csv_receipt=row['image']['receipt'],original_catalogue_plan_sha256=row['plan_sha256'],qualified_creator=row['creator_label'],date_range=[row['first'],row['last']],rights='NGA openaccess=1; CC0'))
for im in images:
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(original)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert pic.size==tuple(im['original_dimensions']) and abs(pic.width/pic.height-im['width']/im['height'])<.03
 decision=next(d for d in review['decisions'] if d['artwork_id']==im['artwork_id']);assert decision['sha256']==im['sha256'] and decision['decision']=='accept' and decision['actually_viewed'] is True
 files.append(dict(artwork_id=im['artwork_id'],path=im['path'],bytes=len(raw),sha256=im['sha256'],width=im['width'],height=im['height'],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,full_source_frame=True,actual_visual_method=decision['visual_method']))
with b.connect() as db:
 ids=[r['artwork_id'] for r in rows];initial=b.load(b.E/'preparation-production-snapshot.json.gz')['before'];live=h.snapshot(db,ids);assert initial==live
 native=[dict(x) for x in db.execute("SELECT entity_id::text,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=ANY(%s)",(i.CFG['nga']['scheme'],[r['native_id'] for r in rows]))]
 citations=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
 artists=[dict(x) for x in db.execute("SELECT aa.artwork_id::text,aa.attribution_role,ar.id::text,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])",(ids,))]
 for row in rows:
  assert [x['entity_id'] for x in native if x['external_id']==row['native_id']]==[row['artwork_id']]
  assert live[row['artwork_id']]['artwork']['primary_media_id'] is None
  assert live[row['artwork_id']]['artwork']['unlinked_creator_label']==row['creator_label']
b.save(b.E/'independent-source-verification.json',dict(at=h.now(),records=source,csv_receipts=captured))
b.save(b.E/'independent-file-verification.json',dict(at=h.now(),files=files))
b.save(b.E/'independent-identity-verification.json',dict(at=h.now(),native_identifiers=native,citations=citations,artists=artists,all_selected_preimages_unchanged=True,global_native_id_unique=True))
b.save(b.E/'production-target-before-scoped-recovery.json',b.target())
if not (b.E/'local-recovery-verification.json').exists():
 i.BACKUP.chmod(0o700)
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
 kw=h.psycopg.conninfo.conninfo_to_dict(secret);env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
 path=i.BACKUP/'production-schema-before.pgdump';result=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180);assert result.returncode==0,'Schema export failed';path.chmod(0o600)
 result=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True);toc=i.BACKUP/'production-schema-before.toc';toc.write_bytes(result.stdout);toc.chmod(0o600)
 with open(os.devnull,'wb') as sink:subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
 with b.connect() as db:
  before=h.snapshot(db,[r['artwork_id'] for r in rows]);assert all(v==b.load(b.E/'preparation-production-snapshot.json.gz')['before'][aid] and v['artwork']['primary_media_id'] is None for aid,v in before.items())
  h.save(i.BACKUP/'affected-row-recovery-before.json.gz',dict(at=h.now(),before=before,selection_sha256=pin))
 h.save(i.BACKUP/'image-selection.json.gz',i.selected(b.B))
 paths=[path,toc,i.BACKUP/'affected-row-recovery-before.json.gz',i.BACKUP/'image-selection.json.gz'];[h.load(p) for p in paths if p.suffix=='.gz']
 b.save(b.E/'local-recovery-verification.json',dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',path=str(i.BACKUP),files=[dict(path=str(p),bytes=p.stat().st_size,sha256=h.sha(p.read_bytes())) for p in paths],selected_images=len(images),schema_archive_fully_decoded=True,all_json_exports_fully_decoded=True,full_database_backup=False,cloud_backups_created=0,additional_locked_preimages_required=True,local_catalogue_connections=0,recovery='Reconcile pinned source/selection/rights checksums with before-000 locked transaction backup and audit event before corrective work; no recovery mutations performed.'))
b.save(b.E/'independent-prewrite-verification.json',dict(at=h.now(),selection_sha256=pin,visual_review_sha256=h.sha((i.folder(b.B)/'visual-review.json').read_bytes()),source_records=len(rows),files_verified=len(images),passed=True,shared_ingestion_lock='artline-curated-ingestion'))
print('Source, full-file, actual visual review and scoped recovery checks passed.')
