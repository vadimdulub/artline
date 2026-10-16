#!/usr/bin/env python3
import base64,fcntl,gzip,hashlib,importlib.util,io,json
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('n','ops/continuous-nationalmuseum-images-000030.py');n=importlib.util.module_from_spec(s);s.loader.exec_module(n);b=n.b;h=n.h;i=n.i;E=n.E
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 images,audit,review=i.accepted(n.B);assert len(images)==1;im=images[0];aid=im['artwork_id'];row=i.selected(n.B)['rows'][0]
 pin=h.sha((i.folder(n.B)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(n.B)/'visual-review.json').read_bytes());before=h.load(i.BACKUP/n.B/'before-000.json.gz');assert before[aid]['artwork']['primary_media_id'] is None
 obj,rc=n.capture('media-102922');assert obj==row['image']['source'];p=obj['properties']
 assert p['inventarienummer']['value']==[row['accession_number']]==['NMI 148'] and p['titel_en']['value']==[row['title']] and p['konstnar']['value']==['Okänd'] and p['licens']['value']=='Public Domain'
 assert row['source_credit']==p['photocreditline']['value']=='Foto: Heiko Arens / Nationalmuseum'
 fm=next(x for x in obj['downloadables'] if x['templateName']=='Full JPEG');assert 'https://media.nationalmuseum.se'+fm['url']==im['source_image_url']
 native=h.load(E/'objects/26466.json');assert native['ObjTitleMainTxt_sv']==p['titel']['value'][0] and native['ObjPersonRefTxt']=='Unknown'
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert len(raw)==im['bytes']<=100000 and h.sha(raw)==im['sha256'] and h.sha(original)==im['source_sha256']
 assert str(Path(im['original_path'])).startswith(str(Path.home()/'Library/Application Support/Artline/source-images'))
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert pic.size==(1644,2513) and abs(pic.width/pic.height-im['width']/im['height'])<.003
 h.save(E/'independent-image-source-verification.json',dict(at=h.now(),artwork_id=aid,native_id='26466',inventory='NMI 148',media_portal_id=102922,media_source_sha256=rc['sha256'],both_titles_and_unknown_maker_verified=True,actual_rights_label='Public Domain',exact_credit=row['source_credit'],direct_collection_image_hold_preserved=True))
 h.save(E/'independent-file-verification.json',dict(at=h.now(),artwork_id=aid,bytes=len(raw),sha256=im['sha256'],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decoding=True,proportions_preserved=True,actually_viewed=True))
 with h.connect() as db:
  after=h.snapshot(db,[aid]);rs=db.execute('SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.rights_status,ma.creator_credit,ma.license_label,ma.license_url,mre.adapter_version,mre.source_checksum,mre.source_image_url,mre.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence mre ON mre.media_id=ma.id WHERE a.id=%s',(aid,)).fetchone();ev=rs['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
  assert rs['primary_media_id']==im['media_id'] and rs['checksum_sha256']==im['sha256'] and rs['byte_size']==im['bytes'] and rs['storage_path']==im['storage_path']
  assert rs['adapter_version']==i.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv and ev['original_catalogue_plan_sha256']==h.pinned(b.PHASE)[1]
  assert rs['source_checksum']==rc['sha256'] and rs['source_image_url']==im['source_image_url'] and rs['rights_status']=='public_domain' and rs['license_label']=='Public Domain' and row['source_credit'] in rs['creator_credit']
  assert ev['visual_review']['viewed_individually'] and ev['visual_review']['decision']=='accept'
  assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE);assert after[aid]['holdings']==before[aid]['holdings'] and after[aid]['creators']==before[aid]['creators'];assert len(after[aid]['attachments'])==1
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=%s AND action='update' AND after_json->>'primary_media_id'=%s",(aid,im['media_id']))];assert len(events)==1 and events[0]['before_json']==before[aid]['artwork']
  sd=db.execute('SELECT primary_media_id::text FROM artwork_search_documents WHERE id=%s',(aid,)).fetchone();assert sd['primary_media_id']==im['media_id']
  metadata=h.load(E/'independent-production-verification.json')['rows'];final=h.snapshot(db,list(metadata));assert len(final)==10
  for id_,state in final.items():
   if id_==aid:assert all(state['artwork'][k]==v for k,v in metadata[id_]['artwork'].items() if k not in i.IGNORE);assert state['holdings']==metadata[id_]['holdings'] and state['creators']==metadata[id_]['creators']
   else:assert state==metadata[id_]
 h.save(E/'independent-image-production-verification.json',dict(at=h.now(),row=rs,selection_sha256=pin,visual_review_sha256=rv,transaction_preimages=str(i.BACKUP/n.B/'before-000.json.gz'),preimage_sha256=h.sha((i.BACKUP/n.B/'before-000.json.gz').read_bytes()),verified_newly_illustrated=1,metadata_and_holdings_preserved=True,other_nine_rows_unchanged=True,search_document_verified=True,final_rows=final))
 h.save(E/'independent-image-audit-verification.json',dict(at=h.now(),events=events,locked_preimages_equal_audit_preimages=True))
 creds=i.d.core.GcloudCredentials();creds.refresh(None);client=i.storage.Client(project='artline-508319',credentials=creds);blob=client.bucket(i.d.core.BUCKET).blob(im['storage_path'].lstrip('/'));blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==i.OP
 h.save(E/'independent-storage-verification.json',dict(at=h.now(),artwork_id=aid,storage_path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],md5_verified=True))
 u='https://artlines.org'+im['storage_path'];resp=i.session().get(u,timeout=(15,45));resp.raise_for_status();assert h.sha(resp.content)==im['sha256']
 au='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;r=i.session().get(au,timeout=(15,45));r.raise_for_status();assert im['storage_path'] in r.text
 h.save(E/'independent-image-public-verification.json',dict(at=h.now(),artwork_id=aid,image_url=u,image_status=resp.status_code,sha256=im['sha256'],api_url=au,api_status=r.status_code))
 meta=h.load(E/'batch-verification-receipt.json');counts=dict(meta['verified_counts'],newly_illustrated=1)
 h.save(E/'combined-batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=meta['production_ids'],newly_illustrated_ids=[aid],metadata_plan_sha256=meta['plan_sha256'],image_selection_sha256=pin,visual_review_sha256=rv,production_target=b.base.target(),attribution='10 absent metadata transaction preimages plus unique programme checksum-bound citations and insert audits; one absent primary-media image preimage plus exact programme/source/review rights checksums and update audit. All 10 live rows rechecked after image write. Previous campaigns excluded.'))
 print(json.dumps(counts))
