#!/usr/bin/env python3
"""Independent production, attribution, audit, storage and public-byte verification."""
import base64,fcntl,gzip,hashlib,importlib.util,io,json
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-nsw-images-000043.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 images,audit,review=i.accepted(b.B);assert len(images)==2
 ids=[x['artwork_id'] for x in images];expected={x['artwork_id']:x for x in images};selection=i.selected(b.B);selected={r['artwork_id']:r for r in selection['rows']}
 pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
 bp=i.BACKUP/b.B/'before-000.json.gz';before=h.load(bp);assert all(before[aid]['artwork']['primary_media_id'] is None for aid in ids)
 files=[];sources=[]
 pre=h.load(b.E/'independent-prewrite-verification.json');assert pre['selection_sha256']==pin
 for im in images:
  aid=im['artwork_id'];r=selected[aid];rc=r['image']['receipt'];body=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(body)==rc['sha256'] and rc['status']==200
  assert any(d['artwork_id']==aid and d['viewed_individually'] and d['sha256']==im['sha256'] and d['decision']=='accept' for d in review['decisions'])
  raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(original)==im['source_sha256']
  with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
  with Image.open(io.BytesIO(original)) as pic:pic.load();assert abs(pic.width/pic.height-im['width']/im['height'])<.005
  files.append(dict(artwork_id=aid,path=im['path'],sha256=im['sha256'],bytes=im['bytes'],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,full_composition_proportions=True,actually_viewed=True))
  source=next(s for s in pre['sources'] if s['artwork_id']==aid);assert source['source_sha256']==rc['sha256']
  sources.append(source)
 b.save('independent-source-verification.json',dict(at=h.now(),selection_sha256=pin,records=sources,metadata_changes=0,actual_rights_label_preserved=True,user_approval_is_not_licence=True))
 b.save('independent-file-verification.json',dict(at=h.now(),files=files,originals_outside_documents=True))
 with b.connect() as db:
  after=h.snapshot(db,ids)
  rows=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.rights_status,ma.license_label,ma.source_page_url,ma.creator_credit,mre.adapter_version,mre.source_checksum,mre.source_image_url,mre.source_record_id,mre.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence mre ON mre.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(rows)==2
  for row in rows:
   aid=row['id'];im=expected[aid];r=selected[aid];ev=row['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert row['primary_media_id']==im['media_id'] and row['checksum_sha256']==im['sha256'] and row['storage_path']==im['storage_path'] and row['byte_size']==im['bytes']
   assert row['adapter_version']==i.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv and ev['original_catalogue_plan_sha256']==r['plan_sha256']
   assert row['source_checksum']==r['image']['receipt']['sha256'] and row['source_image_url']==im['source_image_url'] and row['source_page_url']==r['source_url'] and row['source_record_id']==r['current_source_id']
   assert row['rights_status']==r['rights_status']=='public_domain' and row['license_label']==r['rights_label']=='Public domain'
   assert ev['identity_confidence']>=.9 and ev['identity']==r['identity_basis'] and ev['user_approval']['copyright_holder_licence'] is False
   assert ev['visual_review']['viewed_individually'] and ev['visual_review']['decision']=='accept'
   assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
   assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings']
   assert len(after[aid]['attachments'])==len(before[aid]['attachments'])+1 and any(x['media_id']==im['media_id'] for x in after[aid]['attachments'])
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images]))]
  assert len(events)==2
  for ev in events:assert ev['before_json']==before[ev['entity_id']]['artwork'] and ev['before_json']['primary_media_id'] is None
  search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[]) AND primary_media_id=ANY(%s::uuid[])',(ids,[im['media_id'] for im in images])).fetchone()['n'];assert search==2
  old=h.load(b.E/'nsw-live-gap-reconciliation.json')['before'];unselected=[aid for aid in old if aid not in ids];unchanged=h.snapshot(db,unselected);assert all(unchanged[aid]==old[aid] for aid in unselected)
 b.save('independent-production-verification.json',dict(at=h.now(),rows=rows,after=after,verified_new_primary_images=2,transaction_preimage=str(bp),transaction_preimage_sha256=h.sha(bp.read_bytes()),selection_sha256=pin,visual_review_sha256=rv,metadata_creators_holdings_status_preserved=True,search_documents=search))
 b.save('independent-audit-history-verification.json',dict(at=h.now(),events=events,exact_locked_preimages_match=True,new_primary_from_null=2))
 b.save('independent-unselected-verification.json',dict(at=h.now(),ids=unselected,all_33_unchanged=True))
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);storage=[];public=[]
 for im in images:
  raw=Path(im['path']).read_bytes();blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload()
  assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==i.OP
  storage.append(dict(artwork_id=im['artwork_id'],storage_path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],md5_verified=True))
  url='https://artlines.org'+im['storage_path'];r=i.session().get(url,timeout=(15,60));r.raise_for_status();assert h.sha(r.content)==im['sha256']
  with Image.open(io.BytesIO(r.content)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
  api='https://artlines.org/api/backend/v1/atlas/artworks/'+im['artwork_id'];resp=i.session().get(api,timeout=(15,60));resp.raise_for_status();assert im['storage_path'] in resp.text and selected[im['artwork_id']]['source_url'] in resp.text
  b.save('public-api-'+im['artwork_id']+'.json',resp.json())
  public.append(dict(artwork_id=im['artwork_id'],image_url=url,sha256=im['sha256'],image_http_status=r.status_code,api_url=api,api_http_status=resp.status_code,source_link_present=True,anonymous_access=True))
 b.save('independent-storage-verification.json',dict(at=h.now(),rows=storage))
 b.save('independent-public-verification.json',dict(at=h.now(),rows=public))
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=2,alternate_images=0,museum_links=0)
 b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,selection_sha256=pin,visual_review_sha256=rv,production_target=b.target(),attribution='Exact null-primary locked transaction preimages and matching audit preimages; own persisted adapter, selection/source/visual checksums; storage operation and delivered hashes verified independently. Prior French/Warsaw campaign rows excluded.'))
 print(json.dumps(counts))
