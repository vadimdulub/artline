import importlib.util,json,concurrent.futures,subprocess,io
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-image-batch-000010.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
import fcntl
worker_lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(worker_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
original_save=b.save
def persisted_receipt(path,value):
 if path.exists():
  def stable(v):
   if isinstance(v,dict):return {k:stable(x) for k,x in v.items() if k!='at'}
   if isinstance(v,list):return [stable(x) for x in v]
   return v
  assert stable(b.h.safe(value))==stable(b.load(path)),'Existing immutable verification payload differs: '+str(path)
  return b.load(path)
 return original_save(path,value)
b.save=persisted_receipt
def extra_verification():
 import base64,hashlib,gzip,csv
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);checks=[]
 for im in images:
  blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();raw=Path(im['path']).read_bytes();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode();assert blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==i.OP
  checks.append(dict(artwork_id=im['artwork_id'],storage_path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],md5_verified=True))
 b.save(b.E/'independent-storage-verification.json',dict(at=i.m.now(),checks=checks))
 with b.connect() as db:
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images]))]
  for aid in ids:
   matches=[x for x in events if x['entity_id']==aid and x['before_json']['primary_media_id'] is None and x['after_json']['primary_media_id']==expected[aid]['media_id']];assert len(matches)==1
  b.save(b.E/'independent-audit-history-verification.json',dict(at=i.m.now(),events=events,locked_preimage_match=True))
 records=[]
 source_records={}
 for name in ['objects.csv','published_images.csv']:
  rc=b.load(i.m.RUN/'sources/nga'/(name+'.receipt.json'));path=Path(rc['path']);assert i.m.sha(path.read_bytes())==rc['sha256']
  with path.open(encoding='utf-8-sig',newline='') as file:
   key='objectid' if name=='objects.csv' else 'uuid';wanted={row['native_id'] if key=='objectid' else row['image']['source']['uuid'] for row in i.selected(b.B)['rows']};source_records[name]={r[key]:r for r in csv.DictReader(file) if r[key] in wanted}
 for row in i.selected(b.B)['rows']:
  rc=b.load(b.E/'source-captures'/(row['native_id']+'.info.receipt.json'));body=gzip.decompress((b.ROOT/rc['body_path']).read_bytes());assert i.m.sha(body)==rc['sha256'] and rc['status']==200
  obj=json.loads(body);assert obj.get('@id',obj.get('id'))==row['image']['native_url'];source=row['image']['source'];assert source['openaccess']=='1' and source['viewtype']=='primary' and source['depictstmsobjectid']==row['native_id']
  source_rc=row['image']['receipt'];assert source_records['published_images.csv'][source['uuid']]==source
  objrow=source_records['objects.csv'][row['native_id']];assert objrow['title']==row['title'] and objrow['accessionnum']==row['accession_number'] and objrow['isvirtual']=='0' and objrow['accessioned']=='1'
  planpath=Path(row['plan_path']);assert i.m.sha(planpath.read_bytes())==row['plan_sha256']
  records.append(dict(artwork_id=row['artwork_id'],native_id=row['native_id'],primary_image_uuid=source['uuid'],info_receipt_sha256=rc['sha256'],source_csv_sha256=source_rc['sha256'],openaccess=True,original_catalogue_plan_sha256=row['plan_sha256']))
 b.save(b.E/'independent-source-verification.json',dict(at=i.m.now(),records=records))
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
 search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[]) AND primary_media_id=ANY(%s::uuid[])',(ids,[im['media_id'] for im in images])).fetchone()['n'];assert search==len(ids)
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
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
extra_verification()
b.save(b.E/'batch-verification-receipt.json',dict(at=i.m.now(),verified_counts=counts,attribution='Locked transaction preimages lacked primary media; current assets carry this separate campaign adapter plus exact selection and visual-review checksums. Existing campaign increments excluded. French 188 already-delivered reserves excluded.',production_ids=ids,production_target=b.target(),verified_public_images=len(ids),verified_api_rows=len(ids)))
checkpoint=dict(at=i.m.now(),stage='verified_complete',verified_counts=counts,resume=b.load(b.E/'nga-gap-reconciliation.json')['resume_position'],next_task='Rotate to an undercovered registry institution, prioritizing Greek/Byzantine object evidence; retain NGA position 920 and existing Chicago, Walters and other holds. French reserve exhausted.',evidence=['independent-production-verification.json','independent-file-verification.json','independent-public-verification.json','independent-source-verification.json','independent-storage-verification.json','independent-audit-history-verification.json','batch-verification-receipt.json'])
# Batch checkpoint advances atomically; supervisor-owned root state remains untouched.
temp=b.E/'CHECKPOINT.tmp';temp.write_text(json.dumps(checkpoint,indent=2));temp.replace(b.E/'CHECKPOINT.json')
qpath=b.E.parents[1]/'source-queue.json';queue=json.loads(qpath.read_text())
for r in queue['sources'] if 'sources' in queue else queue['routes']:
 if r['source_id']=='yale_lux':
  r.update(status='french_reserve_exhausted_live_verified_188_already_delivered',checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),last_checked_at=i.m.now(),resume_cursor=dict(french_reserve_remaining=0,next_topic='american_printmaking_separate_reconciliation'))
  ev=str((b.E/'french-reserve-production-reconciliation.json').relative_to(b.ROOT))
  if ev not in r.setdefault('evidence_paths',[]):r['evidence_paths'].append(ev)
 if r['source_id']=='nga_washington':
  r.update(status='bounded_primary_image_continuation_verified',checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),last_checked_at=i.m.now(),resume_cursor=dict(reserve_batch='nga-native-unselected',position=checkpoint['resume']),verified_counts=counts)
  r.setdefault('evidence_paths',[]).extend(str((b.E/name).relative_to(b.ROOT)) for name in checkpoint['evidence'])
qtemp=qpath.with_suffix('.tmp');qtemp.write_text(json.dumps(queue,indent=2));qtemp.replace(qpath)
print(json.dumps(counts))
