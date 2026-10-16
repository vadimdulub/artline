#!/usr/bin/env python3
"""Fresh read-only attribution, file, storage and public verification."""
import datetime,fcntl,importlib.util,io,json
from pathlib import Path
s=importlib.util.spec_from_file_location('batch',Path(__file__).with_name('continuous-icon-batch-000003.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h,i,E=b.h,b.i,b.E
def verify():
 plan,pin=h.pinned(b.PHASE);images,audit,review=i.accepted(b.B);ids=[r['artwork_id'] for r in plan['records']];expected={im['artwork_id']:im for im in images};assert set(ids)==set(expected)
 image_pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());review_pin=h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
 metadata_before=h.load(b.BACKUP/b.PHASE/'locked-before.json.gz');assert metadata_before['plan_sha256']==pin and metadata_before['artworks']=={}
 image_before=h.load(b.BACKUP/b.B/'before-000.json.gz');assert all(image_before[x]['artwork']['primary_media_id'] is None for x in ids)
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  after=h.snapshot(db,ids)
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb note,source_url,source_record_id FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='continuous_museum_batch_000003'",(ids,))];assert len(citations)==2
  media=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.mime_type,mre.adapter_version,mre.evidence_json,mre.source_image_url FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence mre ON mre.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(media)==2
  for r in plan['records']:
   aid=r['artwork_id'];state=after[aid];a=state['artwork'];note=next(x['note'] for x in citations if x['entity_id']==aid)
   assert note['plan_sha256']==pin and note['evidence']['sha256']==r['evidence']['sha256'] and note['source_id']==r['source_id']
   assert (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])==(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],b.IID)
   assert a['status']=='review' and a['published_at'] is None and a['unlinked_creator_label'] is None and state['creators']==[]
   assert db.execute('SELECT artline_creation_scope(%s,%s,%s) scope',(r['first'],r['last'],r['precision'])).fetchone()['scope']=='eligible'
   holding=[x for x in state['holdings'] if x['claim_type']=='holding' and x['review_state']=='accepted' and not x['superseded_by']];assert len(holding)==1 and holding[0]['institution_id']==b.IID
   ev=json.loads(holding[0]['evidence_note']);assert ev['confidence']>=.8 and ev['source_sha256']==r['evidence']['sha256']
   assert all(a[k]==v for k,v in image_before[aid]['artwork'].items() if k not in i.IGNORE)
   assert state['holdings']==image_before[aid]['holdings'] and state['creators']==image_before[aid]['creators']
   assert any(x['media_id']==expected[aid]['media_id'] for x in state['attachments'])
   acc=db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(b.IID,r['accession_number'])).fetchall();assert acc==[dict(id=aid)]
  for row in media:
   im=expected[row['id']];ev=row['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert row['adapter_version']==b.OP and ev['selection_sha256']==image_pin and ev['original_catalogue_plan_sha256']==pin and ev['batch_visual_review_sha256']==review_pin
   assert row['primary_media_id']==im['media_id'] and row['checksum_sha256']==im['sha256'] and row['storage_path']==im['storage_path'] and row['byte_size']==im['bytes']<=100000 and ev['visual_review']['decision']=='accept'
  search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[]) AND primary_media_id=ANY(%s::uuid[])',(ids,[im['media_id'] for im in images])).fetchone()['n'];assert search==2
  audits=[x['table_name'] for x in db.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name ILIKE '%%audit%%'")]
  h.save(E/'independent-production-verification.json',dict(at=h.now(),metadata_plan_sha256=pin,image_plan_sha256=image_pin,visual_review_sha256=review_pin,metadata_preimage_file=str(b.BACKUP/b.PHASE/'locked-before.json.gz'),image_preimage_file=str(b.BACKUP/b.B/'before-000.json.gz'),citations=citations,media=media,after=after,verified_new_artworks=2,verified_new_primary_images=2,verified_holdings=2,search_documents=search,audit_tables=audits,attribution='Empty locked metadata preimages; exact own-plan checksums in persisted object citations and media rights plans. Both image preimages lacked primary media. Other campaign records excluded.'))
 files=[];public=[]
 for im in images:
  raw=Path(im['path']).read_bytes();assert len(raw)==im['bytes']<=100000 and h.sha(raw)==im['sha256']
  orig=Path(im['original_path']).read_bytes();assert h.sha(orig)==im['source_sha256']
  with i.Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height']) and pic.format=='JPEG'
  with i.Image.open(io.BytesIO(orig)) as pic:pic.load();assert abs(pic.width/pic.height-im['width']/im['height'])<.03
  files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],bytes=len(raw),original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True))
  url='https://artlines.org'+im['storage_path'];r=i.session().get(url,timeout=(15,60));r.raise_for_status();assert h.sha(r.content)==im['sha256']
  api='https://artlines.org/api/backend/v1/atlas/artworks/'+im['artwork_id'];r2=i.session().get(api,timeout=(15,60));r2.raise_for_status();assert im['storage_path'] in r2.text
  public.append(dict(artwork_id=im['artwork_id'],image_url=url,image_status=r.status_code,api_url=api,api_status=r2.status_code,sha256=im['sha256']))
 h.save(E/'independent-file-verification.json',dict(at=h.now(),files=files));h.save(E/'independent-public-verification.json',dict(at=h.now(),rows=public))
 b.backup();counts=dict(new_painters=0,new_artworks=2,newly_illustrated=2,alternate_images=0,museum_links=2)
 h.save(E/'batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,production_target=b.target(),metadata_plan_sha256=pin,image_plan_sha256=image_pin,attribution='Only this programme: both records absent from locked transaction preimages and own checksums verified in production citations and rights evidence.',new_artworks_review=True,no_current_display_claims=True,local_database_connections=0))
 next_task='Rotate to a bounded NGA primary-image gap batch with current production reconciliation, preserving Rijksmuseum 044 cursor 25. Later resume Cleveland religious objects from saved 20-result discovery, excluding the pendant/triptych components and already illustrated objects; retain Walters direct HTTP 403 hold.'
 cp=dict(at=h.now(),stage='independently_verified_complete',verified_counts=counts,production_ids=ids,next_task=next_task,remaining_source_cases='Greek: 11 existing Kontoglou objects, six image gaps constrained by dates/detail identity. Walters: first object page 403, no retry. Cleveland: remaining discovery objects unselected; component identities excluded.',evidence=['independent-production-verification.json','independent-file-verification.json','independent-public-verification.json','batch-verification-receipt.json'])
 tmp=E/'CHECKPOINT.tmp';tmp.write_text(json.dumps(cp,indent=2));tmp.replace(E/'CHECKPOINT.json')
 qp=E.parents[1]/'source-queue.json';queue=json.loads(qp.read_text())
 for route in queue['sources']:
  sid=route['source_id']
  if sid not in ['national_gallery_athens','walters_art_museum','cleveland_museum']:continue
  route.update(last_checked_at=h.now(),checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)))
  paths=['source-register.json']
  if sid=='national_gallery_athens':route.update(status='kontoglou_existing_objects_reconciled_date_and_detail_image_holds',resume_cursor=dict(creator='kontoglou-fotis',objects_checked=11,creator_complete=True,next_creator='doxaras-nikolaos'));paths+=['kontoglou-reconciliation.json']
  elif sid=='walters_art_museum':route.update(status='direct_object_http_403_access_hold',resume_cursor=dict(object_accession='57.1818',surface='direct HTTPS art.thewalters.org/object/',retry_allowed=False));paths+=['walters/57.1818.receipt.json']
  else:route.update(status='bounded_religious_objects_delivered_verified',resume_cursor=dict(discovery_query='icon',limit=20,selected_native_ids=[129825,149363],delivered_native_ids=[129825,149363],excluded_component_ids=[128825,128826,136863,136864,136865],next_task='Rotate source before returning to these saved discovery objects'),verified_counts=counts);paths+=cp['evidence']
  route.setdefault('evidence_paths',[]).extend(str((E/p).relative_to(b.ROOT)) for p in paths if str((E/p).relative_to(b.ROOT)) not in route.get('evidence_paths',[]))
 tmp=qp.with_suffix('.tmp');tmp.write_text(json.dumps(queue,indent=2));tmp.replace(qp)
 print(json.dumps(counts))
if __name__=='__main__':
 with (b.RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);verify()
