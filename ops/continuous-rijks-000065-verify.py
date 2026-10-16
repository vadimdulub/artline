import importlib.util,json,concurrent.futures,subprocess,io
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-rijks-images-000065.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
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
   assert matches[0]['before_json']==before[aid]['artwork']
  b.save(b.E/'independent-audit-history-verification.json',dict(at=i.m.now(),events=events,locked_preimage_match=True))
 records=[]
 import xml.etree.ElementTree as ET
 for row in i.selected(b.B)['rows']:
  rc=row['image']['receipt'];raw=Path(rc['path']).read_bytes();assert i.m.sha(raw)==rc['sha256'] and rc['status']==200
  source=row['image']['source'];assert source['rights']==['http://creativecommons.org/publicdomain/mark/1.0/'] and source['source_images']==[row['image']['native_url']]
  assert source['native_id']==row['native_id'] and source['accession']==row['accession_number'] and source['title']==row['title']
  records_xml=ET.fromstring(raw).findall('.//{http://www.openarchives.org/OAI/2.0/}record')
  assert any(i.m.sha(ET.tostring(x))==source['record_xml_sha256'] for x in records_xml)
  assert i.m.sha(Path(row['plan_path']).read_bytes())==row['plan_sha256']
  records.append(dict(artwork_id=row['artwork_id'],native_id=row['native_id'],source_checksum=rc['sha256'],record_xml_sha256=source['record_xml_sha256'],explicit_public_domain_mark=True,exact_image_url_verified=True))
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
  assert ev['visual_review']['decision']=='accept' and ev['visual_review']['viewed_individually'] is True and r['source_image_url']==im['source_image_url']
  selected=next(x for x in i.selected(b.B)['rows'] if x['artwork_id']==aid)
  assert ev['original_catalogue_plan_sha256']==selected['plan_sha256'] and ev['native_source']==selected['image']['source']
  assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
  assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings']
  assert any(x['media_id']==im['media_id'] for x in after[aid]['attachments'])
  assert len(after[aid]['attachments'])==len(before[aid]['attachments'])+1
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

extra_verification()
for entry in b.load(b.E/'local-recovery-verification.json')['files']:assert b.h.sha(Path(entry['path']).read_bytes())==entry['sha256']
for entry in b.load(b.E/'completed-campaign-stop-preservation.json')['files']:assert b.h.sha(Path(entry['path']).read_bytes())==entry['sha256']
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
b.save(b.E/'batch-verification-receipt.json',dict(at=i.m.now(),verified_counts=counts,production_ids=ids,selection_sha256=pin,visual_review_sha256=rv,attribution='Locked transaction preimages lacked primary media; current assets carry this separate campaign adapter plus exact selection, source and visual-review checksums. Existing campaign increments excluded.',production_target=b.target(),verified_public_images=len(ids),verified_api_rows=len(ids)))
print(json.dumps(counts))
