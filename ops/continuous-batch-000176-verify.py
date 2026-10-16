#!/usr/bin/env python3
"""Fresh source-attributed read-only production/storage/public verification."""
import base64,fcntl,gzip,hashlib,importlib.util,io,json
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b176',Path(__file__).with_name('continuous-batch-000176.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 images,audit,review=i.accepted(b.B);assert len(images)==3
 ids=[im['artwork_id'] for im in images];expected={im['artwork_id']:im for im in images};selected={r['artwork_id']:r for r in i.selected(b.B)['rows']}
 pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
 path=i.BACKUP/b.B/'before-000.json.gz';before=h.load(path);assert set(before)==set(ids) and all(before[aid]['artwork']['primary_media_id'] is None for aid in ids)
 b.target('verification')
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids)
  media=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.width,ma.height,ma.rights_status,ma.license_label,ma.creator_credit,ma.source_page_url,e.adapter_version,e.source_record_id,e.source_checksum,e.source_image_url,e.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(media)==len(ids)
  for r in media:
   aid=r['id'];im=expected[aid];row=selected[aid];ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert r['primary_media_id']==im['media_id'] and r['checksum_sha256']==im['sha256'] and r['storage_path']==im['storage_path'] and r['byte_size']==im['bytes']<=100000
   assert r['adapter_version']==b.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv
   assert r['source_checksum']==row['image']['receipt']['sha256'] and r['source_record_id']==row['current_source_id'] and r['source_image_url']==im['source_image_url']
   assert ev['identity_confidence']>=.9 and ev['identity']==row['identity_basis'] and ev['original_catalogue_plan_sha256']==row['plan_sha256']
   assert ev['visual_review']['viewed_individually'] and ev['visual_review']['original_individually_viewed'] and ev['visual_review']['decision']=='accept'
   assert ev['native_source']['original_museum_capture']==row['image']['source']['original_museum_capture'] and ev['user_approval']==h.load(b.E/'authorization.json')
   assert r['rights_status']==row['rights_status']=='public_domain' and r['license_label']==row['rights_label']=='Public domain'
   assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
   assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings']
   assert len(after[aid]['attachments'])==len(before[aid]['attachments'])+1 and any(x['media_id']==im['media_id'] for x in after[aid]['attachments'])
   prior=row['image']['source']['original_museum_capture'];assert h.sha((b.ROOT/prior['path']).read_bytes())==prior['sha256'];rc=prior['object']['capture'];assert h.sha(gzip.decompress((b.ROOT/rc['body_path']).read_bytes()))==rc['receipt']['sha256']
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images]))];assert len(events)==len(ids)
  for event in events:
   aid=event['entity_id'];assert event['before_json']==before[aid]['artwork'] and event['after_json']==after[aid]['artwork']
  search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[]) AND primary_media_id=ANY(%s::uuid[])',(ids,[im['media_id'] for im in images])).fetchone()['n'];assert search==len(ids)
  initial=h.load(b.E/'gap-input.json.gz')['before'];heldids=[aid for aid in initial if aid not in ids];held=h.snapshot(db,heldids);assert all(held[aid]==initial[aid] for aid in heldids)
  current_plan_citations=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,source_url,source_record_id,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  for aid in ids:assert next(x for x in current_plan_citations if x['entity_id']==aid)==next(x for x in h.load(b.E/'gap-input.json.gz')['citations'] if x['entity_id']==aid)
 b.save('independent-production-verification.json',dict(at=h.now(),rows=after,media=media,source_citations=current_plan_citations,search_documents=search,selection_sha256=pin,visual_review_sha256=rv,locked_preimage_path=str(path),locked_preimage_sha256=h.sha(path.read_bytes()),verified_new_primary_images=len(ids),metadata_status_creators_and_holdings_preserved=True,local_catalogue_connections=0))
 b.save('independent-audit-history-verification.json',dict(at=h.now(),events=events,locked_preimages_equal_audit_before=True,newly_illustrated=len(ids)))
 b.save('independent-other-gaps-verification.json',dict(at=h.now(),ids=heldids,unchanged=True,viewed_ratio_hold_not_uploaded=True))
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);stored=[];public=[];files=[]
 for im in images:
  blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();raw=blob.download_as_bytes();assert blob.size==im['bytes'] and h.sha(raw)==im['sha256'] and blob.metadata['operation']==b.OP and blob.metadata['sha256']==im['sha256'];assert blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
  stored.append(dict(artwork_id=im['artwork_id'],object_key=blob.name,generation=blob.generation,bytes=blob.size,sha256=h.sha(raw),metadata=blob.metadata,md5_verified=True))
  response=i.session().get('https://artlines.org'+im['storage_path'],timeout=(15,60));response.raise_for_status();assert h.sha(response.content)==im['sha256']
  with Image.open(io.BytesIO(response.content)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
  api='https://artlines.org/api/backend/v1/atlas/artworks/'+im['artwork_id'];r=i.session().get(api,timeout=(15,60));r.raise_for_status();assert im['storage_path'] in r.text;b.save('public-api-'+im['artwork_id']+'.json',r.json())
  public.append(dict(artwork_id=im['artwork_id'],image_url='https://artlines.org'+im['storage_path'],image_status=response.status_code,image_sha256=h.sha(response.content),bytes=len(response.content),api_url=api,api_status=r.status_code,api_body_sha256=h.sha(r.content),complete_decoding=True))
  assert h.sha(Path(im['path']).read_bytes())==im['sha256'] and h.sha(Path(im['original_path']).read_bytes())==im['source_sha256'];assert Path(im['original_path']).is_relative_to(Path.home()/'Library/Application Support/Artline')
  files.append(dict(artwork_id=im['artwork_id'],path=im['path'],original_path=im['original_path'],sha256=im['sha256'],original_sha256=im['source_sha256'],bytes=im['bytes'],actually_viewed_individually=True))
 held_image=next(x for x in audit['prepared_images'] if x['artwork_id']=='12829a02-5075-55e7-b9ff-f94815c48c4f');assert not bucket.blob(held_image['storage_path'].lstrip('/')).exists() and not (i.folder(b.B)/'uploads'/(held_image['artwork_id']+'.json')).exists()
 b.save('independent-storage-verification.json',dict(at=h.now(),rows=stored,held_image_not_uploaded=True));b.save('independent-public-verification.json',dict(at=h.now(),rows=public));b.save('independent-file-verification.json',dict(at=h.now(),rows=files,originals_outside_documents=True))
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
 b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,selection_sha256=pin,visual_review_sha256=rv,locked_preimage_sha256=h.sha(path.read_bytes()),production_target=b.TARGET,shared_ingestion_lock='artline-curated-ingestion',attribution='Each exact existing active artwork had null primary media in this transaction preimage, equal to its image-update audit before-row. Persisted rights carry own operation, selection, source-capture, original catalogue plan and actual visual-review checksums. Fresh production, Storage and public byte checks confirm3 distinct newly illustrated objects; previous programmes excluded.',limitations=['NGA native403; no current native object/image checks. Archived museum-published metadata hashed and reviewed locally, no Google Arts & Culture calls.','Legacy museum dimension units uncertain; no correction invented. Shearing shed held for source ratio mismatch.','WikiArt does not specify holding or dimensions on these pages; only image attachments changed.','All4 originals and4 derivatives actually viewed;3 accepted and1 held. Source originals are600–750pixels on long edge.']))
 stop=h.load(b.E/'campaign-stop-preservation.json');assert h.sha((b.ROOT/stop['path']).read_bytes())==stop['sha256']
 b.save('independent-campaign-stop-verification.json',dict(at=h.now(),stop_unchanged=True,original_campaign_restarted=False,separate_campaign=b.OP))
 # Read-only reconciliation proves a resumed worker can skip completed writes.
 with h.connect() as db:
  resumed=h.snapshot(db,ids);assert resumed==after
  rights=[dict(x) for x in db.execute('SELECT media_id::text,adapter_version,evidence_json FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([im['media_id'] for im in images],))];assert len(rights)==len(ids)
  for row in rights:
   ev=row['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev;assert row['adapter_version']==b.OP and ev['selection_sha256']==pin
 b.save('independent-read-only-resume-verification.json',dict(at=h.now(),production_rows_equal=True,persisted_operation_selection_and_source_attribution_verified=True,receipt_sha256=h.sha((b.E/'batch-verification-receipt.json').read_bytes()),replay_required=False,new_production_writes=0,replay_increments={k:0 for k in counts},local_catalogue_connections=0))
 print(json.dumps(counts))
