#!/usr/bin/env python3
"""Independent source/file and scoped recovery verification, no catalogue writes."""
import fcntl,gzip,importlib.util,io,json,os,subprocess
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-basel-images-000104.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);assert len(images)==1 and not audit['identity_holds'];rows=i.selected(b.B)['rows'];pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());source=[];files=[]
for row in rows:
 im=next(x for x in images if x['artwork_id']==row['artwork_id']);rc=row['image']['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
 sp=BeautifulSoup(raw,'html.parser');text=sp.select_one('.mw-parser-output').get_text(' ',strip=True);assert text==row['image']['source']['metadata_text']
 assert sp.select_one('.fullImageLink > a')['href']==row['image']['image_url']==im['source_image_url']
 assert all(x in text for x in ['Gustave Courbet','Inv. 1428','46.6 x 61.5','1859','CC BY-SA 4.0','Public Domain Mark','Kunstmuseum Basel artwork ID : 1462','sammlungonline.kunstmuseumbasel.ch'])
 official=row['image']['source']['official_metadata'];rc2=official['receipt'];raw2=gzip.decompress(Path(rc2['body_path']).read_bytes());assert h.sha(raw2)==rc2['sha256'] and rc2['status']==200
 md=json.loads(BeautifulSoup(raw2,'html.parser').select_one('#__NEXT_DATA__').string)['props']['pageProps']['data']['item'];assert md==official['metadata']
 assert md['Id']==row['native_id']=='1462' and md['ObjListInvTxt']['LabelTxt']==row['accession_number']=='1428' and md['ObjDetailDateTxt']['LabelTxt']==str(row['first'])==str(row['last'])=='1859'
 assert md['ObjDetailRightsTxt']['LabelTxt']=='Bilddaten gemeinfrei - Kunstmuseum Basel' and 'Gustave Courbet' in md['ObjListArtistTxt']['LabelTxt']
 citation=row['image']['source']['identity_reconciliation']['source_citation'];note=json.loads(citation['evidence_note']);assert note['plan_sha256']==row['plan_sha256']
 original_plan=b.ROOT/'docs/research/switzerland-southern-cone-1000-20261011/CH-wave2/plan.json.gz';assert h.sha(original_plan.read_bytes())==row['plan_sha256'];historical=h.load(original_plan)
 assert row['identity_confidence']>=.9 and row['rights_status']=='cc_by_sa' and row['rights_label']=='CC BY-SA 4.0; PD-Art / Public Domain Mark'
 source.append(dict(artwork_id=row['artwork_id'],native_id=row['native_id'],accession=row['accession_number'],source_sha256=rc['sha256'],museum_sha256=rc2['sha256'],original_plan_sha256=row['plan_sha256'],source_citation_sha256=h.sha(json.dumps(citation,sort_keys=True,ensure_ascii=False).encode()),licence='CC BY-SA 4.0; PD-Art / Public Domain Mark',provenance='Explicit former native museum source URL; current official museum metadata and inventory exact match',native_image_requests=0))
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(original)==im['source_sha256']
 assert Path(im['path']).resolve().is_relative_to((b.ROOT/'apps/web/public/assets/artworks/imported'/i.OP).resolve())
 assert Path(im['original_path']).resolve().is_relative_to(i.ORIG.resolve()) and not Path(im['original_path']).resolve().is_relative_to(Path.home()/'Documents')
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height']) and pic.format=='JPEG'
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.003
 ratio=61.5/46.6;diff=abs(ratio-im['width']/im['height'])/ratio;assert diff<.01
 decision=next(d for d in review['decisions'] if d['artwork_id']==row['artwork_id']);assert decision['viewed_individually'] and decision['original_viewed'] and decision['decision']=='accept' and decision['sha256']==im['sha256']
 files.append(dict(artwork_id=im['artwork_id'],path=im['path'],bytes=len(raw),sha256=im['sha256'],dimensions=[im['width'],im['height']],original_path=im['original_path'],original_sha256=im['source_sha256'],original_bytes=len(original),complete_decode=True,full_source_frame=True,actual_visual_review=True,physical_ratio_difference=diff))
with b.connect() as db:
 for row in rows:
  aid=row['artwork_id'];live=h.snapshot(db,[aid]);assert live[aid]==b.load(b.E/'gap-input.json.gz')['before'][aid] and live[aid]['artwork']['primary_media_id'] is None
  citation=row['image']['source']['identity_reconciliation']['source_citation'];fresh=[dict(r) for r in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name=%s",(aid,citation['field_name']))];assert citation in fresh
 assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in images],)).fetchall()
b.save('independent-source-verification.json',dict(at=h.now(),records=source));b.save('independent-file-verification.json',dict(at=h.now(),files=files))
b.save('production-target-before-scoped-recovery.json',b.target())
if not (b.E/'local-recovery-verification.json').exists():
 i.BACKUP.chmod(0o700)
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
 kw=h.psycopg.conninfo.conninfo_to_dict(secret);env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
 path=i.BACKUP/'production-schema-before.pgdump';result=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180);assert result.returncode==0,'Schema export failed';path.chmod(0o600)
 result=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True);toc=i.BACKUP/'production-schema-before.toc';toc.write_bytes(result.stdout);toc.chmod(0o600)
 with open(os.devnull,'wb') as sink:subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
 with b.connect() as db:
  before=h.snapshot(db,[r['artwork_id'] for r in rows]);assert all(v==b.load(b.E/'gap-input.json.gz')['before'][aid] and v['artwork']['primary_media_id'] is None for aid,v in before.items())
  h.save(i.BACKUP/'affected-row-recovery-before.json.gz',dict(at=h.now(),before=before,selection_sha256=pin))
 h.save(i.BACKUP/'image-selection.json.gz',i.selected(b.B))
 paths=[path,toc,i.BACKUP/'affected-row-recovery-before.json.gz',i.BACKUP/'image-selection.json.gz'];[h.load(p) for p in paths if p.suffix=='.gz']
 b.save('local-recovery-verification.json',dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',path=str(i.BACKUP),files=[dict(path=str(p),bytes=p.stat().st_size,sha256=h.sha(p.read_bytes())) for p in paths],selected_images=len(images),schema_archive_fully_decoded=True,all_json_exports_fully_decoded=True,full_database_backup=False,cloud_backups_created=0,additional_locked_preimages_required=True,local_catalogue_connections=0,recovery='Reconcile pinned source/selection/rights checksums with before-000 locked transaction backup and audit event before corrective work; no recovery mutations performed.'))
b.save('independent-prewrite-verification.json',dict(at=h.now(),selection_sha256=pin,visual_review_sha256=h.sha((i.folder(b.B)/'visual-review.json').read_bytes()),source_records=len(rows),files_verified=len(images),passed=True,shared_ingestion_lock='artline-curated-ingestion'))
print('Source, full-file, actual visual review and scoped recovery checks passed.')
