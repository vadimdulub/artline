#!/usr/bin/env python3
"""Independent source/file/review checks and scoped recovery before batch 86."""
import fcntl,gzip,html,importlib.util,io,json,os,re,subprocess
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-canada-images-000086.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);assert len(images)==1 and not audit['identity_holds']
pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rows=i.selected(b.B)['rows'];source=[];files=[]
for row in rows:
 im=next(x for x in images if x['artwork_id']==row['artwork_id']);rc=row['image']['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
 sp=BeautifulSoup(raw,'html.parser');tag=sp.select_one('.wiki-layout-painting-info-bottom[ng-init]');md=json.loads(tag['ng-init'].split('=',1)[1].strip())
 assert md['_id']==row['current_source_id'] and h.norm(html.unescape(md['title']))==h.norm(row['title']) and md['artistName']==row['creator_label'] and int(md['year'])==row['first']==row['last']==1884
 assert sp.select_one('img[itemprop=image]')['src']==im['source_image_url']==row['image']['image_url']
 assert sp.select_one('.copyright-wrapper .copyright').get_text(' ',strip=True)==row['rights_label']=='Public domain' and row['rights_status']=='public_domain'
 secondary=row['image']['source']['independent_object_metadata'];rc2=secondary['receipt'];raw2=gzip.decompress(Path(rc2['body_path']).read_bytes());assert h.sha(raw2)==rc2['sha256'] and rc2['status']==200
 text=BeautifulSoup(raw2,'html.parser').get_text(' ',strip=True);assert text==secondary['text'] and all(v in text for v in ['1884','122.5','142.7','National Gallery of Canada','William Brymner'])
 original=row['image']['source']['original_catalogue_source_receipt'];prior=b.ROOT/original['body_path'];priorraw=gzip.decompress(prior.read_bytes());assert h.sha(priorraw)==original['sha256']
 ent=json.loads(priorraw)['entities'][row['native_id']];claims=ent['claims'];assert claims['P217'][0]['mainsnak']['datavalue']['value']=='19'
 assert float(claims['P2048'][0]['mainsnak']['datavalue']['value']['amount'])==122.5 and float(claims['P2049'][0]['mainsnak']['datavalue']['value']['amount'])==142.7
 assert row['identity_confidence']>=.9 and row['accession_number'] is None
 recon=b.load(b.E/'extended-identity-reconciliation.json');assert recon['original_plan_sha256']==row['plan_sha256'] and recon['original_capture_hash_verified']
 source.append(dict(artwork_id=row['artwork_id'],source_id=row['current_source_id'],native_id=row['native_id'],source_sha256=rc['sha256'],independent_object_url=rc2['url'],independent_object_sha256=rc2['sha256'],preserved_original_source_sha256=original['sha256'],source_inventory='19',catalogue_null_accession_preserved=True,source_dimensions='122.5 x 142.7 cm',date_scope_evidence='1884 on WikiArt and Art Canada Institute',actual_rights_label=row['rights_label'],rights_status=row['rights_status'],selection_sha256=pin,editorial_confidence=row['identity_confidence'],native_image_downloaded=False))
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(original)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert pic.size==tuple(im['original_dimensions']) and abs(pic.width/pic.height-im['width']/im['height'])<.03
 difference=abs(142.7/122.5-im['width']/im['height']);assert difference<.03
 decision=next(d for d in review['decisions'] if d['artwork_id']==row['artwork_id']);assert decision['viewed_individually'] and decision['sha256']==im['sha256'] and decision['decision']=='accept'
 files.append(dict(artwork_id=im['artwork_id'],path=im['path'],bytes=len(raw),sha256=im['sha256'],width=im['width'],height=im['height'],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,full_source_frame=True,actually_viewed=True,museum_referenced_aspect_ratio_difference=difference))
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
