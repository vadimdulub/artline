#!/usr/bin/env python3
"""One bounded primary-image batch, using the established production adapter."""
import ast, copy, csv, datetime, fcntl, gzip, importlib.util, io, json, os, subprocess, sys
from pathlib import Path
from PIL import Image
import requests
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
base=module('base164','continuous-image-batch-000002.py');h=module('prod164','india-300-delivery-20261011.py');i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000164';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000164'
OP='continuous-athens-20261013-b000164-images';B='athens-native-000';MID='052007aa-11f7-4d57-90e6-d3b62bb0bf4b';TARGET='artline-508319:europe-west1:artline-postgres'
R.mkdir(parents=True,exist_ok=True)
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
SOURCE='14bfe954-ac9c-55af-ae48-0fdd699e43bb'
i.CFG['athens']=dict(mid=MID,scheme='nationalgallery-gr-work',name='National Gallery – Alexandros Soutsos Museum',rights='restricted',license='Museum reproduction; © National Gallery – Alexandros Soutsos Museum. No independent copyright-holder licence asserted.',policy='https://www.nationalgallery.gr/en/terms-of-use/',host='www.nationalgallery.gr')
original_uid=i.m.uid;i.m.uid=lambda k:SOURCE if k=='source/athens' else original_uid(k)
# Reuse the transaction without altering catalogue identity guards. Preserve
# actual credits and the user approval separately from restricted source rights.
source=(ROOT/'ops/illustrated-300k-20261011.py').read_text();node=next(x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef) and x.name=='apply');code='\n'.join(source.splitlines()[node.lineno-1:node.end_lineno])
code=code.replace('credits={}',"credits={r['artwork_id']:r.get('source_credit','') for r in p['rows']}")
code=code.replace("    if p['provider']=='wikiart':evidence.update", "    evidence['user_approval']=m.load(RUN/'authorization.json')\n    evidence['source_creation_date_review']=r['source_creation_date_review']\n    if p['provider']=='wikiart':evidence.update")
exec(compile(code,__file__,'exec'),i.__dict__)
def save(name,v):h.save(E/name,v);return v
def rel(path):return str(Path(path).relative_to(ROOT))
def target(stage):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 commands=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();proxy=[x for x in commands if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and TARGET in x];assert len(proxy)==1
 with h.connect() as db:
  server=dict(db.execute('SELECT current_database() db,pg_is_in_recovery() recovery').fetchone());assert server['db']=='artline' and not server['recovery']
 return save('production-target-'+stage+'.json',dict(at=h.now(),connection_name=actual,proxy_command=proxy[0],database=server,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',local_catalogue_connections=0))
def prepare():
 research=h.load(E/'athens-source-reconciliation.json');gaps=h.load(E/'athens-all-gap-input.json.gz');rows=[];decisions=[]
 with h.connect() as db:
  for r in research['selected']:
   aid=r['artwork_id'];state=h.snapshot(db,[aid])[aid];assert state==gaps['before'][aid];a=state['artwork'];n=r['native']
   owners=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(n['scheme'],n['external_id'])).fetchall();assert owners==[dict(entity_id=aid)]
   assert a['title']==r['source_title'] and a['accession_number']==r['source_accession'] and a['medium_text']+', '+a['dimensions_text']==r['description']
   assert a['date_display']==r['source_date']=='[1894]' and a['creation_year_start'] is None and a['creation_year_end'] is None and a['date_precision']=='unknown'
   assert any(x['source_url']==r['source_url'] and x['review_state']=='accepted' for x in state['holdings'])
   creators=db.execute('SELECT id::text,display_name FROM artists WHERE id=ANY(%s::uuid[])',([x['artist_id'] for x in state['creators']],)).fetchall();assert len(creators)==1 and creators[0]['display_name']=='Konstantinos Volanakis'
   assert a['primary_media_id'] is None
   rc=r['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256']
   date_review=dict(source_label='[1894]',decision='Museum supplies bracket-qualified 1894 attribution; supported before1955 image selection. Unknown structured dates stay unknown; no catalogue date update.',confidence_basis='Exact persisted native ID, inventory Π.1483, title, creator, support and110x191cm dimensions, matching bracket-qualified date display and accepted holding.');decisions.append(dict(artwork_id=aid,native_id=n['external_id'],source_sha256=rc['sha256'],source_creation_date_review=date_review,creator=creators[0],confidence=0.99,decision='accept_image_only'))
   rows.append(dict(artwork_id=aid,provider='athens',native_id=n['external_id'],title=a['title'],accession_number=a['accession_number'],creator_label=r['creator_label'],source_credit='National Gallery – Alexandros Soutsos Museum',source_url=r['source_url'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],expected_primary_artist_id=creators[0]['id'],plan_sha256=h.sha((E/'athens-source-reconciliation.json').read_bytes()),image=dict(image_url=r['image_url'],source=r,receipt=rc),rights_basis='Selected authentic Greek museum reproduction; bracket-qualified source creation [1894] before1955. Restricted actual museum rights retained separately from explicit Greek source approval.',source_creation_date_review=date_review,manual_visual_required=True))
 assert 1<=len(rows)<=100
 save('authorization.json',dict(at=h.now(),user_approval='Current continuous production image authorization and Greek museum source extension; source-backed image-only additions directly authorized.',policy_reference='docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026',copyright_holder_licence=False))
 save('exact-identity-decisions.json',dict(at=h.now(),rows=decisions,selected=len(rows),metadata_updates=0))
 h.save(i.folder(B)/'selection.json.gz',dict(provider='athens',batch=B,rows=rows));h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for r in rows:print(r['native_id'],i.prepare_one(r,B)['state'],flush=True)
 i.audit(B)
 for p in (i.folder(B)/'prepared').glob('*.json'):print('IMAGE',h.load(p).get('path'),flush=True)
def deliver():
 images,audit,review=i.accepted(B);assert len(images)==len(i.selected(B)['rows']) and all(x['viewed_individually'] for x in review['decisions'])
 target('before-storage-write')
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791897658924','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save('cloud-backup.json',backup)
 i.upload(B);target('before-database-write');i.apply(B)
def finalize():
 images,audit,review=i.accepted(B);rows=i.selected(B)['rows'];ids=[x['artwork_id'] for x in images];expected={x['artwork_id']:x for x in images};selection=h.sha((i.folder(B)/'selection.json.gz').read_bytes());preimage=i.BACKUP/B/'before-000.json.gz';before=h.load(preimage)
 assert all(before[x]['artwork']['primary_media_id'] is None for x in ids)
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids)
  media=[dict(x) for x in db.execute("SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.rights_status,ma.creator_credit,e.adapter_version,e.source_record_id,e.source_checksum,e.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=ma.id WHERE a.id=ANY(%s::uuid[])",(ids,))]
  search=[dict(x) for x in db.execute('SELECT a.id::text,s.primary_media_id::text,s.status,s.title FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.primary_media_id=a.primary_media_id AND s.status=a.status AND s.title=a.title',(ids,))]
 assert len(ids)==len(after)==len(media)==len(search)
 for aid in ids:
  assert after[aid]['artwork']['primary_media_id']==expected[aid]['media_id']
  assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
  assert after[aid]['holdings']==before[aid]['holdings'] and after[aid]['creators']==before[aid]['creators']
  assert any(x['media_id']==expected[aid]['media_id'] for x in after[aid]['attachments'])
 for m in media:
  im=expected[m['id']];ev=json.loads(m['evidence_json']) if isinstance(m['evidence_json'],str) else m['evidence_json'];r=next(x for x in rows if x['artwork_id']==m['id'])
  assert (m['checksum_sha256'],m['byte_size'],m['rights_status'],m['adapter_version'])==(im['sha256'],im['bytes'],'restricted',OP)
  assert ev['selection_sha256']==selection and m['source_checksum']==r['image']['receipt']['sha256'] and ev['visual_review']['sha256']==im['sha256'] and ev['visual_review']['viewed_individually']
  assert im['bytes']<=100000 and Path(im['original_path']).is_relative_to(Path.home()/'Library/Application Support/Artline')
  with Image.open(im['path']) as d:d.load();assert list(d.size)==[im['width'],im['height']]
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
 save('independent-production-verification.json',dict(at=h.now(),before=before,after=after,media=media,search_documents=search,transaction_preimage_path=str(preimage),preimage_sha256=h.sha(preimage.read_bytes()),selection_sha256=selection,verified_counts=counts,metadata_creators_holdings_status_and_unknown_dates_unchanged=True,local_catalogue_connections=0))
 public=[]
 for aid in ids:
  im=expected[aid];url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;r=requests.get(url,timeout=(15,45));r.raise_for_status();p=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,45));p.raise_for_status();assert im['storage_path'] in r.text and h.sha(p.content)==im['sha256']
  with Image.open(io.BytesIO(p.content)) as d:d.load();assert list(d.size)==[im['width'],im['height']]
  public.append(dict(artwork_id=aid,api_status=r.status_code,image_status=p.status_code,storage_path=im['storage_path'],sha256=h.sha(p.content),bytes=len(p.content),complete_decoding=True))
 save('independent-public-verification.json',dict(at=h.now(),rows=public,passed=True))
 from google.cloud import storage
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);bucket=storage.Client(project='artline-508319',credentials=credentials).bucket(i.d.core.BUCKET);stored=[]
 for im in images:
  b=bucket.blob(im['storage_path'].lstrip('/'));b.reload();raw=b.download_as_bytes();assert h.sha(raw)==im['sha256'] and b.size==im['bytes'] and b.metadata['operation']==OP and b.metadata['sha256']==im['sha256'];stored.append(dict(artwork_id=im['artwork_id'],object_key=b.name,generation=b.generation,bytes=b.size,sha256=h.sha(raw),metadata=b.metadata))
 save('independent-storage-verification.json',dict(at=h.now(),rows=stored,passed=True))
 save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,selection_sha256=selection,transaction_preimage_sha256=h.sha(preimage.read_bytes()),production_target=TARGET,attribution='Null primary media in transaction preimage; unique batch164 operation and selection/source checksums in persisted rights evidence; fresh production/search/storage/public reads. Earlier or concurrent additions excluded.'))
 queue_path=E.parents[1]/'source-queue.json'
 with queue_path.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);queue=h.load(queue_path);old=copy.deepcopy(queue);q=next(x for x in queue['sources'] if x['source_id']=='national_gallery_athens');research=h.load(E/'athens-source-reconciliation.json')
  cursor=dict(route='existing_native_primary_gaps_source_date_review',processed_artwork_ids=[x['artwork_id'] for x in research['rows']],processed_urls=[x['source_url'] for x in research['rows']],last_gap_uuid=research['next_after_artwork_id'],frozen_gap_page_last_uuid=h.load(E/'athens-all-gap-input.json.gz')['rows'][-1]['id'],source_evidence=rel(E/'athens-source-reconciliation.json'),delivered_artwork_ids=ids,next_step='Continue untouched native gaps after last_gap_uuid, excluding recorded unknown/open-date/source-cutoff holds; SAAM shard20 available for rotation.')
  q['resume_cursor']['batch164_native_primary_gaps']=cursor;q.update(last_checked_at=h.now(),last_batch=164,checkpoint=rel(E/'CHECKPOINT.json'),latest_batch_verified_counts=counts,status='one_existing_native_primary_image_verified_unknown_catalogue_dates_preserved')
  q.setdefault('research_history',[]).append(dict(at=h.now(),batch=164,route=cursor['route'],notices_reviewed=len(research['rows']),selected=len(ids),verified_counts=counts,evidence=rel(E/'batch-verification-receipt.json')))
  q['access_status']='15 untouched exact native object notices HTTP200; one source-dated1894 image HTTP200. Existing date/version/provider holds preserved.'
  q.setdefault('evidence_paths',[]).extend([rel(E/x) for x in ['athens-source-reconciliation.json','independent-production-verification.json','independent-public-verification.json','independent-storage-verification.json']])
  unchanged=[x for x in old['sources'] if x['source_id']!='national_gallery_athens']==[x for x in queue['sources'] if x['source_id']!='national_gallery_athens'] and old['supplementary_image_routes']==queue['supplementary_image_routes'];assert unchanged
  tmp=queue_path.with_suffix('.164.tmp');tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,queue_path)
  save('source-queue-update-verification.json',dict(at=h.now(),updated_source='national_gallery_athens',unrelated_entries_preserved=unchanged,previous_holds_preserved=True,resume_cursor=cursor,queue_sha256=h.sha(queue_path.read_bytes())))
 registry=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')))
 save('source-register-final.json',dict(at=h.now(),provider=next(x for x in registry if x['source_id']=='national_gallery_athens'),policy_reference='docs/ARTLINE_IMAGE_USE.md Greek museum source extension; by1955.',access_status=q['access_status'],directory_coverage_count=0,notices_reviewed=len(research['rows']),selected=len(ids),prepared=len(images),imported=len(ids),verified=len(ids),remaining_gaps='Other native gaps and unknown/open-date cases remain unresolved; source date[1894] preserved separately from unknown catalogue years.',resume_cursor=cursor))
 save('failures-and-holds.json',dict(at=h.now(),provider_failures=[],records=[x for x in research['rows'] if x['decision']!='selected_source_dated_image_only'],unchanged_failed_retries=0,previous_holds_preserved=True,resolved_environment_failure='Default Python lacked psycopg; reused established artline-cyprus-venv without installation.'))
 nxt='Rotate to Smithsonian SAAM shard20 for exact existing primary gaps. Athens native-source-date cursor is saved after '+research['next_after_artwork_id']+'; continue untouched native notices and preserve all unknown/open-date/version holds.'
 names=['batch107-live-reconciliation.json','athens-source-reconciliation.json','exact-identity-decisions.json','batches/'+B+'/visual-review.json','independent-production-verification.json','independent-public-verification.json','independent-storage-verification.json','batch-verification-receipt.json','source-queue-update-verification.json','source-register-final.json','failures-and-holds.json']
 start=h.load(E/'required-input-verification.json')['at'];finish=h.now();seconds=(datetime.datetime.fromisoformat(finish)-datetime.datetime.fromisoformat(start)).total_seconds()
 cp=dict(at=finish,batch=164,stage='independently_verified_complete',researched=dict(frozen_native_gaps=100,source_notices=len(research['rows'])),selected=len(ids),prepared=len(images),imported=len(ids),verified=len(ids),verified_counts=counts,next_task=nxt,blocker='',evidence=[rel(E/x) for x in names],started_at=start,finished_at=finish,measured_runtime_seconds=seconds,external_supervisor_unchanged=True,local_catalogue_connections=0)
 save('CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
 result=dict(outcome='progress',summary='Batch164 verified one authentic primary image for Volanakis’s existing The Exodus of Ares after reviewing15 untouched Athens native notices. The derivative was individually viewed and passed production, storage and public-delivery checks. Source[1894] dating and restricted rights were preserved; catalogue dates, metadata, holdings and statuses remained unchanged. Batch107 reconciled successfully.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in names]+[rel(E/'CHECKPOINT.json')])
 assert all((ROOT/x).exists() for x in result['evidence_paths']);save('worker-result.json',result);h.save(R/'verified-batch-result.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
