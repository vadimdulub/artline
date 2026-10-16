#!/usr/bin/env python3
"""Independent read-only production attribution, source, file and delivery checks."""
import importlib.util,json,gzip,io,fcntl,datetime
from pathlib import Path
s=importlib.util.spec_from_file_location('batch',Path(__file__).with_name('continuous-greek-images-000015.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h,i,E=b.h,b.i,b.E
original_save=h.save
def stable_save(path,value):
 if path.exists():
  def strip(v):
   if isinstance(v,dict):return {k:strip(x) for k,x in v.items() if k!='at'}
   if isinstance(v,list):return [strip(x) for x in v]
   return v
  assert strip(h.load(path))==strip(h.safe(value)),str(path);return
 original_save(path,value)
h.save=stable_save

def verify():
 plan,pin=h.pinned(b.b.PHASE);ids=[r['artwork_id'] for r in plan['records']];images,audit,review=i.accepted(b.B);ims={x['artwork_id']:x for x in images};assert len(ids)==4 and len(ims)==3
 meta_before=h.load(h.BACKUP/b.b.PHASE/'locked-before.json.gz');assert meta_before['plan_sha256']==pin and meta_before['artworks']=={}
 pre=h.load(h.BACKUP/b.B/'before-000.json.gz');assert all(x['artwork']['primary_media_id'] is None for x in pre.values())
 image_pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());visual_pin=h.sha((i.folder(b.B)/'visual-review.json').read_bytes());sources=[]
 for r in plan['records']:
  rc=r['evidence'];raw=(b.ROOT/r['evidence_file']).read_bytes();assert h.sha(raw)==rc['sha256']
  soup=__import__('bs4').BeautifulSoup(raw,'html.parser');assert r['accession_number'] in soup.select_one('.artwork-no').get_text(' ',strip=True)
  assert r['raw']['image_url']==soup.select_one('img[src*="/wp-content/uploads/"]')['src']
  assert 'Koutouzis Nikolaos' in soup.get_text(' ',strip=True)
  sources.append(dict(artwork_id=r['artwork_id'],source_url=r['source_url'],sha256=rc['sha256'],accession=r['accession_number'],date_decision=r['date_decision'],original_date=r['date_display'],native_image_url=r['raw']['image_url']))
 h.save(E/'independent-source-verification.json',dict(at=h.now(),rows=sources,selected=4,creation_eligible=3,unknown_date_review=1,artist_authority='No unique existing painter found; original creator label retained object-level',date_exception='Undated named-creator museum object retained as explicit unknown review under AGENTS incomplete-data policy; excluded from definite creation-date eligible count and image selection'))
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids)
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb note FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(b.b.FIELD,ids))];assert len(citations)==4
  media=[dict(x) for x in db.execute('SELECT a.id::text,ma.id::text media_id,ma.storage_path,ma.checksum_sha256::text,ma.byte_size,ma.rights_status,mre.adapter_version,mre.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence mre ON mre.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(media)==3
  for r in plan['records']:
   aid=r['artwork_id'];state=after[aid];a=state['artwork'];note=next(x['note'] for x in citations if x['entity_id']==aid)
   assert note['plan_sha256']==pin and note['evidence']['sha256']==r['evidence']['sha256']
   assert (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])==(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],b.IID)
   assert a['status']=='review' and a['published_at'] is None
   assert state['creators']==[] and a['unlinked_creator_label']==r['creator_label']
   holds=[x for x in state['holdings'] if x['claim_type']=='holding' and x['review_state']=='accepted' and not x['superseded_by']];assert len(holds)==1 and holds[0]['institution_id']==b.IID
   ev=json.loads(holds[0]['evidence_note']);assert ev['confidence']>=.8 and ev['source_sha256']==r['evidence']['sha256']
   assert db.execute('SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(b.IID,r['accession_number'])).fetchone()['n']==1
   if aid in ims:
    im=ims[aid];assert a['primary_media_id']==im['media_id'];assert any(x['media_id']==im['media_id'] for x in state['attachments']);assert state['creators']==pre[aid]['creators'] and state['holdings']==pre[aid]['holdings'];assert all(a[k]==v for k,v in pre[aid]['artwork'].items() if k not in i.IGNORE)
   else:assert a['primary_media_id'] is None
  for row in media:
   im=ims[row['id']];ev=row['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert row['adapter_version']==h.OP and ev['selection_sha256']==image_pin and ev['original_catalogue_plan_sha256']==pin and ev['batch_visual_review_sha256']==visual_pin
   assert row['checksum_sha256']==im['sha256'] and row['byte_size']==im['bytes']<=100000 and row['rights_status']=='restricted'
  search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n'];assert search==4
  tables=[x['table_name'] for x in db.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name ILIKE '%%audit%%'")]
  h.save(E/'independent-production-verification.json',dict(at=h.now(),after=after,citations=citations,media=media,metadata_plan_sha256=pin,image_plan_sha256=image_pin,visual_review_sha256=visual_pin,metadata_preimages=str(h.BACKUP/b.b.PHASE/'locked-before.json.gz'),image_preimages=str(h.BACKUP/b.B/'before-000.json.gz'),verified_new_artworks=4,verified_newly_illustrated=3,verified_holdings=4,search_documents=search,audit_tables=tables,attribution='All four absent from locked transaction preimages; persisted own metadata plan checksums and source checksums match. All three primary-image preimages empty; own image selection and visual review checksums match.'))
 files=[];public=[]
 for im in images:
  raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(orig)==im['source_sha256']
  with i.Image.open(io.BytesIO(raw)) as p:p.load();assert p.size==(im['width'],im['height'])
  with i.Image.open(io.BytesIO(orig)) as p:p.load();assert abs(p.width/p.height-im['width']/im['height'])<.03
  files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],original_sha256=im['source_sha256'],bytes=len(raw),complete_decode=True,proportions_preserved=True,actually_viewed=True))
 for aid in ids:
  url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;r=i.session().get(url,timeout=(15,60));
  if after[aid]['artwork']['creation_year_start'] is not None:r.raise_for_status();assert after[aid]['artwork']['title'] in r.text
  else:assert r.status_code==404 and 'NOT_FOUND' in r.text # Unknown creation is production review, API scope unavailable; explicit delivery limitation.
  item=dict(artwork_id=aid,api_status=r.status_code,api_url=url)
  if aid in ims:
   im=ims[aid];assert im['storage_path'] in r.text;imageurl='https://artlines.org'+im['storage_path'];r2=i.session().get(imageurl,timeout=(15,60));r2.raise_for_status();assert h.sha(r2.content)==im['sha256'];item.update(image_status=r2.status_code,image_url=imageurl,sha256=im['sha256'])
  public.append(item)
 h.save(E/'independent-file-verification.json',dict(at=h.now(),rows=files));h.save(E/'independent-public-verification.json',dict(at=h.now(),rows=public))
 creds=i.d.core.GcloudCredentials();creds.refresh(None);client=i.storage.Client(project='artline-508319',credentials=creds);bucket=client.bucket(i.d.core.BUCKET);stored=[]
 for im in images:
  blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();assert blob.size==im['bytes'] and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==h.OP;assert h.sha(blob.download_as_bytes())==im['sha256'];stored.append(dict(artwork_id=im['artwork_id'],generation=blob.generation,sha256=im['sha256'],bytes=blob.size))
 h.save(E/'independent-storage-verification.json',dict(at=h.now(),rows=stored))
 counts=dict(new_painters=0,new_artworks=4,newly_illustrated=3,alternate_images=0,museum_links=4)
 h.save(E/'batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,creation_eligible_new=3,unknown_date_review_new=1,target=b.b.target(),metadata_plan_sha256=pin,image_plan_sha256=image_pin,local_database_connections=0,no_current_display_claims=True))

 nxt='Research another registry institution: Tretyakov official portal Russian icons, bounded metadata first. Athens Koutouzis four inventories complete; preserve one unknown-date image hold and pending creator authority.'
 cp=dict(at=h.now(),stage='independently_verified_complete',verified_counts=counts,production_ids=ids,next_task=nxt,remaining_gaps=['One undated portrait has no selected image; creation date not inferred from artist lifespan','Koutouzis Nikolaos remains original object-level creator label pending globally reconciled painter authority'],resume=dict(creator='koutouzis-nikolaos',creator_complete=True,accessions=[r['accession_number'] for r in plan['records']],next_registry_source='tretyakov_gallery'))
 h.save(E/'CHECKPOINT.json',cp);h.save(b.b.R/'CHECKPOINT.json',cp)
 qp=E.parents[1]/'source-queue.json';queue=json.loads(qp.read_text());route=next(x for x in queue['sources'] if x['source_id']=='national_gallery_athens')
 route.setdefault('prior_resume_cursors',[]).append(route.get('resume_cursor'))
 route.update(last_checked_at=h.now(),status='koutouzis_four_objects_three_primary_images_verified_one_date_review',checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),resume_cursor=cp['resume'],remaining_gaps=cp['remaining_gaps'],verified_counts=counts)
 for f in ['source-register.json','independent-source-verification.json','independent-production-verification.json','independent-file-verification.json','independent-public-verification.json','independent-storage-verification.json','batch-verification-receipt.json','actual-visual-review.json','CHECKPOINT.json']:
  path=str((E/f).relative_to(b.ROOT));route.setdefault('evidence_paths',[])
  if path not in route['evidence_paths']:route['evidence_paths'].append(path)
 tmp=qp.with_suffix('.tmp');tmp.write_text(json.dumps(queue,indent=2));tmp.replace(qp)
 start=datetime.datetime.fromisoformat(h.load(E/'tzanes.receipt.json')['at']);end=datetime.datetime.now(datetime.timezone.utc)
 h.save(E/'milestone-report.json',dict(at=h.now(),measured_research_seconds=(end-start).total_seconds(),verified_counts=counts,stages=dict(discovered=4,selected_metadata=4,imported=4,verified=4,selected_images=3,prepared_images=3,verified_images=3),failures=['Tzanes English guessed index 404','Moskos Greek guessed index 404; no repeated retries'],unresolved=cp['remaining_gaps'],next_task=nxt))
 print(json.dumps(counts))
if __name__=='__main__':
 with (b.b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);verify()
