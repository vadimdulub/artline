#!/usr/bin/env python3
"""Fresh independent production, audit, storage and delivery verification."""
import importlib.util,fcntl,copy,json,datetime,gzip,io,requests,os
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location("b","ops/continuous-batch-000284.py");b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h,i,E,R,B,OP,TARGET,ROOT=b.h,b.i,b.E,b.R,b.B,b.OP,b.TARGET,b.ROOT
save,rel=b.save,b.rel
def verify_delivery():
    reconciliation_count=h.load(E/'identity-reconciliation.json')['captured_records']
    images,audit,review=i.accepted(B);rows=i.selected(B)['rows'];ids=[x['artwork_id'] for x in images];expected={x['artwork_id']:x for x in images}
    assert len(ids)==len(rows)==len(review['decisions'])
    selection=h.sha((i.folder(B)/'selection.json.gz').read_bytes());preimage_path=i.BACKUP/B/'before-000.json.gz';before=h.load(preimage_path)
    assert all(before[x]['artwork']['primary_media_id'] is None for x in ids)
    with h.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids)
        media=[dict(x) for x in db.execute("SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.width,ma.height,ma.rights_status,ma.creator_credit,ma.source_page_url,e.adapter_version,e.source_record_id,e.source_checksum,e.source_image_url,e.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=ma.id WHERE a.id=ANY(%s::uuid[])",(ids,))]
        search=[dict(x) for x in db.execute('SELECT a.id::text,s.primary_media_id::text,s.status,s.title FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.primary_media_id=a.primary_media_id AND s.status=a.status AND s.title=a.title',(ids,))]
    assert len(after)==len(media)==len(search)==len(ids)
    for aid in ids:
        assert after[aid]['artwork']['primary_media_id']==expected[aid]['media_id']
        assert after[aid]['holdings']==before[aid]['holdings'] and after[aid]['creators']==before[aid]['creators']
        assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
        assert any(x['media_id']==expected[aid]['media_id'] for x in after[aid]['attachments'])
    for row in media:
        im=expected[row['id']];evidence=row['evidence_json'] if isinstance(row['evidence_json'],dict) else json.loads(row['evidence_json'])
        assert (row['checksum_sha256'],row['byte_size'],row['rights_status'],row['adapter_version'])==(im['sha256'],im['bytes'],'cc0',OP)
        assert evidence['native_identity_review']==h.load(E/'identity-review-supplement.json') and evidence['identity_review_supplement_sha256']==h.sha((E/'identity-review-supplement.json').read_bytes())
        assert evidence['selection_sha256']==selection and evidence['visual_review']['viewed_individually'] and evidence['visual_review']['sha256']==im['sha256']
        assert row['source_checksum']==rows[0]['image']['receipt']['sha256']
        assert im['bytes']<=100000 and Path(im['original_path']).is_relative_to(Path.home()/'Library/Application Support/Artline')
        with Image.open(im['path']) as decoded:decoded.load();assert list(decoded.size)==[im['width'],im['height']]
    counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
    with h.connect() as db:
        events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images]))]
    assert len(events)==len(ids) and {x['entity_id'] for x in events}==set(ids)
    for event in events:
        aid=event['entity_id'];assert event['before_json']==before[aid]['artwork'] and event['after_json']==after[aid]['artwork']
    save('independent-audit-history-verification.json',dict(at=h.now(),events=events,passed=True,new_programme_primary_images=len(ids),preimage_sha256=h.sha(preimage_path.read_bytes()),selection_sha256=selection))
    save('independent-production-verification.json',dict(at=h.now(),rows=after,media=media,search_documents=search,transaction_preimage_path=str(preimage_path),preimage_sha256=h.sha(preimage_path.read_bytes()),selection_sha256=selection,verified_counts=counts,metadata_creators_holdings_and_status_unchanged=True,local_catalogue_connections=0))
    public=[]
    for aid in ids:
        im=expected[aid];url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;response=requests.get(url,timeout=(15,45));response.raise_for_status()
        picture=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,45));picture.raise_for_status()
        assert im['storage_path'] in response.text and h.sha(picture.content)==im['sha256']
        with Image.open(io.BytesIO(picture.content)) as decoded:decoded.load();assert list(decoded.size)==[im['width'],im['height']]
        public.append(dict(artwork_id=aid,api_url=url,api_status=response.status_code,api_body_sha256=h.sha(response.content),image_status=picture.status_code,storage_path=im['storage_path'],image_sha256=h.sha(picture.content),bytes=len(picture.content),complete_decoding=True))
    save('independent-public-verification.json',dict(at=h.now(),rows=public,all_selected_images_delivered=True))
    import base64,hashlib
    from google.cloud import storage
    credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);stored=[]
    for aid in ids:
        im=expected[aid];blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();payload=blob.download_as_bytes()
        assert h.sha(payload)==im['sha256'] and blob.size==im['bytes'] and blob.metadata['operation']==OP and blob.metadata['sha256']==im['sha256']
        assert blob.md5_hash==base64.b64encode(hashlib.md5(payload).digest()).decode()
        stored.append(dict(artwork_id=aid,object_key=blob.name,generation=blob.generation,bytes=blob.size,sha256=h.sha(payload),metadata=blob.metadata))
    save('independent-storage-verification.json',dict(at=h.now(),rows=stored,verified=True))
    save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,production_writes=len(ids),selection_sha256=selection,transaction_preimage_sha256=h.sha(preimage_path.read_bytes()),production_target=TARGET,shared_ingestion_lock='artline-curated-ingestion',attribution='Each exact existing work had null primary media in this transaction preimage; persisted media-rights evidence carries this unique operation, selection and original-source checksums and actual visual decisions. Fresh database, search-document, storage-byte and public-byte reads verify the additions; no French reserve or previous programme changes counted.'))
    return counts

def finalize():
 counts=verify_delivery();rec=h.load(E/'identity-reconciliation.json');images,_,review=i.accepted(B);rows=i.selected(B)['rows'];pin=h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 assert rec['captured_records']==72 and rec['windows'][0]['start']==50 and rec['windows'][1]['end_exclusive']==50
 nxt='Review the three saved Berlin icon notices 1787183, 1792924 and 1792913 from page2, preserving all nine object holds, then page3. Smithsonian SAAM resumes at shard46 offset50; Athens paintings at page5. Do not replay completed shards or the delivered French reserve.'
 last=rec['windows'][-1];cursor=dict(unit='saam',completed_shard='45',next_shard='46',next_record_offset=50,total_records_in_shard=last['total_records'],remaining_records_in_shard=last['total_records']-50,source_sha256=last['source_sha256'],classification_windows=rec['windows'],records_classified_this_batch=72,existing_primary_gaps_delivered=len(images),newly_illustrated_native_ids=[x['native_id'] for x in rows],held_native_ids=['27371','7739'],scope='Bounded existing-image-gap scan only: shard45 offsets50–71 and shard46 offsets0–49. No new metadata records selected.',next_route=nxt)
 gaps=['SAAM shard46 from offset50 remains unresearched; no full museum coverage claim.','Earlier same-title impression holds27371/7739 and source access holds remain.','Other new-object leads and unknown/crossing dates were not selected by this image-only pass.','Historical source creator spelling, titles, dates, accession fields, holdings and status were preserved; no current-display claims.']
 access=dict(public_bulk_metadata='Reused checksum-verified shard45; HTTP200 shard46',selected_native_pages='HTTP200 two exact objects, original and current captures verified',selected_ids_images='HTTP200 two exact CC0 images',web_search='Existing403 hold preserved; not requested',rest_api='API key required; not used')
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);q=h.load(qp);before=copy.deepcopy(q);source=next(x for x in q['sources'] if x['source_id']=='smithsonian_open_access')
  if source.get('last_batch')!=284:
   assert source['resume_cursor']['next_shard']=='45' and source['resume_cursor']['next_record_offset']==50
   source.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(source['resume_cursor']))
   source.update(status='two_exact_existing_cc0_primary_images_verified_batch284',last_batch=284,last_checked_at=h.now(),checkpoint=rel(E/'CHECKPOINT.json'),resume_cursor=cursor,latest_batch_verified_counts=counts,access_status=access,remaining_gaps=gaps)
   source.setdefault('batch_history',[]).append(dict(batch=284,verified_counts=counts,selection_sha256=pin,verification_receipt=rel(E/'batch-verification-receipt.json')))
   source.setdefault('evidence_paths',[]).extend(rel(E/x) for x in ['identity-reconciliation.json','exact-identity-decisions.json','identity-review-supplement.json','independent-production-verification.json','independent-audit-history-verification.json','independent-public-verification.json','independent-storage-verification.json','batch-verification-receipt.json','CHECKPOINT.json'])
   b.atomic(qp,q)
  else:assert source['resume_cursor']==cursor and source['latest_batch_verified_counts']==counts
  assert [x for x in q['sources'] if x['source_id']!='smithsonian_open_access']==[x for x in before['sources'] if x['source_id']!='smithsonian_open_access']
  assert q['supplementary_image_routes']==before['supplementary_image_routes']
 save('source-queue-update-verification.json',dict(at=h.now(),updated_source='smithsonian_open_access',unrelated_entries_preserved=True,queue_sha256=h.sha(qp.read_bytes()),resume_cursor=cursor))
 save('source-register-final.json',dict(at=h.now(),provider='smithsonian_open_access',policy_reference='Original111-source CSV Smithsonian CC0 row and docs/ARTLINE_IMAGE_USE.md; actual CC0 rights preserved separately from user approval.',access_status=access,directory_coverage_increment=0,records_classified=72,selected=2,prepared=2,imported=2,verified=2,remaining_gaps=gaps,resume_cursor=cursor))
 save('failures-and-holds.json',dict(at=h.now(),provider_failures=[],production_write_failures=0,prior_provider_and_object_holds_preserved=True,local_diagnostics=['System Python lacked psycopg; older research environment lacked google.cloud.storage. Reused established b266 environment without installing dependencies.'],visual_review=dict(derivatives=2,originals=2,contact_sheets=0),new_paid_services=0,spending_limits_changed=False,translation_calls=0,local_catalogue_connections=0,real_local_database_untouched=True))
 evidence=['required-input-verification.json','source-register.json','production-target-reconciliation.json','batch107-live-reconciliation.json','attempt-reconciliation.json','inherited-holds-verification.json','identity-reconciliation.json','exact-identity-decisions.json','identity-review-supplement.json','actual-visual-review.json','independent-prewrite-verification.json','local-recovery-verification.json','production-target-before-storage-write.json','production-target-before-database-write.json','independent-production-verification.json','independent-audit-history-verification.json','independent-public-verification.json','independent-storage-verification.json','batch-verification-receipt.json','source-queue-update-verification.json','source-register-final.json','failures-and-holds.json']
 start=h.load(E/'required-input-verification.json')['at'];end=h.now();elapsed=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
 cp=dict(at=end,batch=284,stage='independently_verified_complete',started_at=start,finished_at=end,measured_runtime_seconds=elapsed,records_classified=72,selected=2,prepared=2,imported=2,verified=2,verified_counts=counts,production_ids=[x['artwork_id'] for x in images],selection_sha256=pin,resume_cursor=cursor,next_task=nxt,blocker='',external_supervisor_unmodified=True,local_catalogue_connections=0,translation_calls=0,evidence=[rel(E/x) for x in evidence])
 b.atomic(E/'CHECKPOINT.json',cp);b.atomic(R/'CHECKPOINT.json',cp)
 checked=[]
 for name in evidence+['CHECKPOINT.json']:
  p=E/name;h.load(p);checked.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
 save('independent-final-artifact-verification.json',dict(at=h.now(),artifacts=checked,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,passed=True))
 result=dict(outcome='progress',summary='Verified two new CC0 primary images on existing Smithsonian paintings after72 metadata records were classified. Both originals and derivatives were visually reviewed. Production, audit history, storage and public delivery passed; metadata and local catalogue were preserved.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in ['CHECKPOINT.json','batch-verification-receipt.json','independent-production-verification.json','independent-audit-history-verification.json','independent-public-verification.json','independent-storage-verification.json','actual-visual-review.json','source-queue-update-verification.json','independent-final-artifact-verification.json']])
 save('verified-batch-result.json',result);h.save(R/'verified-batch-result.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);finalize()
