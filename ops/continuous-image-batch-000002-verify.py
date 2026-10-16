import importlib.util,json,concurrent.futures,subprocess,io
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-image-batch-000002.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
images,audit,review=i.accepted(b.B);pin=i.m.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rv=i.m.sha((i.folder(b.B)/'visual-review.json').read_bytes());ids=[im['artwork_id'] for im in images];expected={im['artwork_id']:im for im in images}
before=i.m.load(i.BACKUP/b.B/'before-000.json.gz');assert all(before[aid]['artwork']['primary_media_id'] is None for aid in ids)
with b.connect() as db:
 after=i.d.snapshot(db,ids)
 rows=db.execute('SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.mime_type,mre.adapter_version,mre.evidence_json,mre.source_image_url FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence mre ON mre.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',(ids,)).fetchall()
 assert len(rows)==len(ids)
 for r in rows:
  aid=r['id'];im=expected[aid];ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
  assert r['primary_media_id']==im['media_id'] and r['checksum_sha256']==im['sha256'] and r['storage_path']==im['storage_path'] and r['byte_size']==im['bytes']<=100000
  assert r['adapter_version']==i.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv
  assert ev['visual_review']['decision']=='accept' and r['source_image_url']==im['source_image_url']
  assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
  assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings']
  assert any(x['media_id']==im['media_id'] for x in after[aid]['attachments'])
 search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[]) AND primary_media_id=ANY(%s::uuid[])',(ids,[im['media_id'] for im in images])).fetchone()['n'];assert search==25
 b.save(b.E/'independent-production-verification.json',dict(at=i.m.now(),rows=rows,verified_new_primary_images=len(rows),transaction_preimages=str(i.BACKUP/b.B/'before-000.json.gz'),selection_sha256=pin,visual_review_sha256=rv,metadata_creators_holdings_and_status_preserved=True,search_documents=search,after=after))
files=[]
for im in images:
 raw=Path(im['path']).read_bytes();assert i.m.sha(raw)==im['sha256'] and len(raw)<=100000
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height']) and pic.format=='JPEG'
 orig=Path(im['original_path']).read_bytes();assert i.m.sha(orig)==im['source_sha256']
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert abs(pic.width/pic.height-im['width']/im['height'])<.03
 files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],bytes=len(raw),complete_decode=True,original_sha256=im['source_sha256']))
b.save(b.E/'independent-file-verification.json',dict(at=i.m.now(),files=files))
def public(im):
 url='https://artlines.org'+im['storage_path'];r=i.session().get(url,timeout=(15,60));r.raise_for_status();assert i.m.sha(r.content)==im['sha256']
 api='https://artlines.org/api/backend/v1/atlas/artworks/'+im['artwork_id'];a=i.session().get(api,timeout=(15,60));a.raise_for_status();assert im['storage_path'] in a.text
 return dict(artwork_id=im['artwork_id'],image_url=url,sha256=im['sha256'],api_url=api,image_status=r.status_code,api_status=a.status_code)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:publics=list(pool.map(public,images))
b.save(b.E/'independent-public-verification.json',dict(at=i.m.now(),rows=publics))
backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791718979252','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';b.save(b.E/'backup-reverification.json',backup)
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=25,alternate_images=0,museum_links=0)
b.save(b.E/'batch-verification-receipt.json',dict(at=i.m.now(),verified_counts=counts,attribution='25 locked transaction preimages lacked primary media; 25 current assets carry this separate campaign adapter plus exact selection and visual-review checksums. Existing campaign increments excluded.',production_ids=ids,production_target=b.target(),verified_public_images=25,verified_api_rows=25))
checkpoint=dict(at=i.m.now(),stage='verified_complete',verified_counts=counts,resume=b.load(b.E/'reserve-reconciliation.json')['resume_position'],next_task='Select a bounded undercovered NGA or WikiArt primary-image gap route; retain Rijks 044 cursor for later varied-source rotation.',evidence=['independent-production-verification.json','independent-file-verification.json','independent-public-verification.json','batch-verification-receipt.json'])
# Batch checkpoint advances atomically; supervisor-owned root state remains untouched.
temp=b.E/'CHECKPOINT.tmp';temp.write_text(json.dumps(checkpoint,indent=2));temp.replace(b.E/'CHECKPOINT.json')
qpath=b.E.parents[1]/'source-queue.json';queue=json.loads(qpath.read_text())
for r in queue['sources'] if 'sources' in queue else queue['routes']:
 if r['source_id']=='rijksmuseum':
  r.update(status='bounded_primary_image_continuation_verified',checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),last_checked_at=i.m.now(),resume_cursor=dict(reserve_batch='rijks-044',position=checkpoint['resume']),verified_counts=counts)
  r.setdefault('evidence_paths',[]).extend(str((b.E/name).relative_to(b.ROOT)) for name in checkpoint['evidence'])
qtemp=qpath.with_suffix('.tmp');qtemp.write_text(json.dumps(queue,indent=2));qtemp.replace(qpath)
print(json.dumps(counts))
