#!/usr/bin/env python3
"""One bounded primary-image batch, using the established production adapter."""
import ast, copy, csv, datetime, fcntl, gzip, importlib.util, io, json, os, subprocess, sys
from pathlib import Path
from PIL import Image
import requests
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
base=module('base166','continuous-image-batch-000002.py');h=module('prod166','india-300-delivery-20261011.py');i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000166';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000166'
OP='continuous-athens-20261013-b000166-images';B='athens-native-000';MID='052007aa-11f7-4d57-90e6-d3b62bb0bf4b';TARGET='artline-508319:europe-west1:artline-postgres'
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
   assert a['date_display']==r['source_date'] and r['source_date_bounds'][1]<=1955
   assert any(x['source_url']==r['source_url'] and x['review_state']=='accepted' for x in state['holdings'])
   creators=db.execute('SELECT id::text,display_name FROM artists WHERE id=ANY(%s::uuid[])',([x['artist_id'] for x in state['creators']],)).fetchall();assert len(creators)==1
   assert a['primary_media_id'] is None
   rc=r['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256']
   from bs4 import BeautifulSoup
   soup=BeautifulSoup(raw,'html.parser');collection=soup.select_one('p.obtainment');credit=collection.get_text(' ',strip=True) if collection else 'National Gallery – Alexandros Soutsos Museum'
   citation=db.execute("SELECT evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name='official_object_identity' AND source_record_id=%s",(aid,n['external_id'])).fetchone();assert citation
   original_identity=json.loads(citation['evidence_note']);assert original_identity['accession']==r['source_accession'] and r['creator_url'] in original_identity['museum_maker_link']
   assert original_identity['date']['display']==r['source_date'] and original_identity['medium_dimensions']==r['description'] and original_identity['collection_credit']==credit
   r=dict(r,collection_credit=credit,original_persisted_source_identity=original_identity)

   date_review=dict(source_label=r['source_date'],source_bounds=r['source_date_bounds'],decision='Explicit museum creation bounds wholly before1955, qualifications preserved. Catalogue structured dates remain unchanged.',confidence_basis='Exact persisted native ID, accession, title, creator, support and dimensions, matching original date display and accepted holding.');decisions.append(dict(artwork_id=aid,native_id=n['external_id'],source_sha256=rc['sha256'],source_creation_date_review=date_review,creator=creators[0],collection_credit=credit,original_persisted_source_identity=original_identity,confidence=0.99,decision='accept_image_only'))
   rows.append(dict(artwork_id=aid,provider='athens',native_id=n['external_id'],title=a['title'],accession_number=a['accession_number'],creator_label=r['creator_label'],source_credit=credit,source_url=r['source_url'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],expected_primary_artist_id=creators[0]['id'],plan_sha256=h.sha((E/'athens-source-reconciliation.json').read_bytes()),image=dict(image_url=r['image_url'],source=r,receipt=rc),rights_basis='Selected authentic Greek museum reproduction; qualified museum creation bounds before1955. Restricted actual museum rights retained separately from explicit Greek source approval.',source_creation_date_review=date_review,manual_visual_required=True))
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
 with h.connect() as db:
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images]))]
 assert len(events)==len(ids) and {x['entity_id'] for x in events}==set(ids)
 for event in events:
  aid=event['entity_id'];assert event['before_json']==before[aid]['artwork'] and event['after_json']==after[aid]['artwork']
 save('independent-audit-history-verification.json',dict(at=h.now(),events=events,passed=True,preimage_sha256=h.sha(preimage.read_bytes()),selection_sha256=selection))
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
 save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,selection_sha256=selection,transaction_preimage_sha256=h.sha(preimage.read_bytes()),production_target=TARGET,attribution='Null primary media in transaction preimage; unique batch166 operation and selection/source checksums in persisted rights evidence; fresh production/search/storage/public reads. Earlier or concurrent additions excluded.'))
 queue_path=E.parents[1]/'source-queue.json'
 with queue_path.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);queue=h.load(queue_path);old=copy.deepcopy(queue);q=next(x for x in queue['sources'] if x['source_id']=='national_gallery_athens');research=h.load(E/'athens-source-reconciliation.json')
  cursor=dict(route='existing_native_primary_gaps_source_date_review',processed_artwork_ids=[x['artwork_id'] for x in research['rows']],processed_urls=[x['source_url'] for x in research['rows']],last_gap_uuid=research['next_after_artwork_id'],frozen_gap_page_last_uuid=h.load(E/'athens-all-gap-input.json.gz')['rows'][-1]['id'],source_evidence=rel(E/'athens-source-reconciliation.json'),delivered_artwork_ids=ids,next_step='Continue untouched native gaps after last_gap_uuid, excluding recorded unknown/open-date/source-cutoff holds; SAAM shard21 available for rotation.')
  q['resume_cursor']['batch166_native_primary_gaps']=cursor;q.update(last_checked_at=h.now(),last_batch=166,checkpoint=rel(E/'CHECKPOINT.json'),latest_batch_verified_counts=counts,status='existing_native_primary_images_verified_unknown_catalogue_dates_preserved')
  q.setdefault('research_history',[]).append(dict(at=h.now(),batch=166,route=cursor['route'],notices_reviewed=sum('receipt' in x for x in research['rows']),gap_records_classified=len(research['rows']),selected=len(ids),verified_counts=counts,evidence=rel(E/'batch-verification-receipt.json')))
  q['access_status']=f"{len(research['rows'])} untouched image-gap records classified; {len(ids)} selected images HTTP200. Earlier date/version/provider holds preserved."
  q.setdefault('evidence_paths',[]).extend([rel(E/x) for x in ['athens-source-reconciliation.json','independent-production-verification.json','independent-public-verification.json','independent-storage-verification.json']])
  y=next(x for x in queue['sources'] if x['source_id']=='yale_lux');assert y['resume_cursor']['unimported']==0 and y['resume_cursor']['retry_allowed'] is False
  y.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(y['resume_cursor']))
  y['resume_cursor']['exact_evidence']=rel(E/'french-reserve-live-reconciliation.json');y.update(last_checked_at=h.now(),last_batch=166)
  y.setdefault('evidence_paths',[]).extend([rel(E/'french-reserve-live-reconciliation.json'),rel(E/'independent-reserve-evidence-verification.json')])
  y.setdefault('research_history',[]).append(dict(at=h.now(),batch=166,required_live_reconciliation_only=True,inspected=188,unimported=0,new_increments=0,evidence=rel(E/'french-reserve-live-reconciliation.json')))
  updated={'national_gallery_athens','yale_lux'}
  unchanged=[x for x in old['sources'] if x['source_id'] not in updated]==[x for x in queue['sources'] if x['source_id'] not in updated] and old['supplementary_image_routes']==queue['supplementary_image_routes'];assert unchanged
  tmp=queue_path.with_suffix('.166.tmp');tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,queue_path)
  save('source-queue-update-verification.json',dict(at=h.now(),updated_sources=['national_gallery_athens','yale_lux'],unrelated_entries_preserved=unchanged,previous_holds_preserved=True,resume_cursor=cursor,queue_sha256=h.sha(queue_path.read_bytes())))
 registry=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')))
 save('source-register-final.json',dict(at=h.now(),provider=next(x for x in registry if x['source_id']=='national_gallery_athens'),policy_reference='docs/ARTLINE_IMAGE_USE.md Greek museum source extension; by1955.',access_status=q['access_status'],directory_coverage_count=0,notices_reviewed=sum('receipt' in x for x in research['rows']),gap_records_classified=len(research['rows']),selected=len(ids),prepared=len(images),imported=len(ids),verified=len(ids),remaining_gaps='Other native gaps and unknown/open-date cases remain unresolved; source date labels preserved separately from unknown catalogue years.',resume_cursor=cursor))
 save('failures-and-holds.json',dict(at=h.now(),provider_failures=[],records=[x for x in research['rows'] if x['decision']!='selected_source_dated_image_only'],unchanged_failed_retries=0,previous_holds_preserved=True,resolved_local_failures=[dict(stage='initial_selection',error='One nonmuseum native identifier contained a slash and could not be captured at the slug file path after its metadata GET; status and body were not retained.',resolution='Retained frozen selection and marked four nondirect identities held without further request. Only exact nationalgallery-gr-work identities requested thereafter.'),dict(stage='local_parser',error='Default interpreter lacked bs4.',resolution='Reused established artline-cyprus-venv; no dependency installation.')]))
 nxt='Rotate to Smithsonian SAAM shard21 for exact existing primary gaps. Athens native-source-date cursor is saved after '+research['next_after_artwork_id']+'; continue untouched native notices and preserve all unknown/open-date/version holds.'
 names=['required-input-verification.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','independent-audit-history-verification.json','production-target-reconciliation.json','production-target-before-storage-write.json','production-target-before-database-write.json','batch107-live-reconciliation.json','athens-source-reconciliation.json','exact-identity-decisions.json','batches/'+B+'/visual-review.json','independent-production-verification.json','independent-public-verification.json','independent-storage-verification.json','batch-verification-receipt.json','source-queue-update-verification.json','source-register-final.json','failures-and-holds.json']
 start=h.load(E/'required-input-verification.json')['at'];finish=h.now();seconds=(datetime.datetime.fromisoformat(finish)-datetime.datetime.fromisoformat(start)).total_seconds()
 cp=dict(at=finish,batch=166,stage='independently_verified_complete',researched=dict(french_reserve_reconciled=188,parent_frozen_native_gaps=100,gap_records_classified=len(research['rows']),source_notices=sum('receipt' in x for x in research['rows'])),selected=len(ids),prepared=len(images),imported=len(ids),verified=len(ids),verified_counts=counts,next_task=nxt,blocker='',evidence=[rel(E/x) for x in names],started_at=start,finished_at=finish,measured_runtime_seconds=seconds,external_supervisor_unchanged=True,local_catalogue_connections=0)
 save('CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
 result=dict(outcome='progress',summary=f"Batch166 verified {len(ids)} authentic primary images for existing National Gallery Athens artworks after classifying {len(research['rows'])} untouched image-gap records and reviewing {sum('receipt' in x for x in research['rows'])} official notices. All selected originals and derivatives were individually viewed; production, audit history, storage and public delivery passed independent checks. French188 reserve was already delivered and excluded. Catalogue metadata, dates, holdings and statuses remained unchanged; batch107 reconciled.",next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in names]+[rel(E/'CHECKPOINT.json')])
 assert all((ROOT/x).exists() for x in result['evidence_paths']);save('worker-result.json',result);h.save(R/'verified-batch-result.json',result);print(json.dumps(result),flush=True)

def preflight():
 target('reconciliation')
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()));qp=E.parents[1]/'source-queue.json';queue=h.load(qp)
 assert len(reg)==111 and {x['source_id'] for x in reg}=={x['source_id'] for x in queue['sources']}
 required=[ROOT/'AGENTS.md',registry,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',qp]
 save('required-input-verification.json',dict(at=h.now(),complete_original_registry_used=True,registry_rows=111,files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],real_local_catalogue_read_only=True,external_supervisor_unchanged=True))
 prevpath=E.parent/'000107/independent-production-verification.json';prev=h.load(prevpath)
 with h.connect() as db:live=h.snapshot(db,list(prev['after']))
 assert live==prev['after']
 save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(live),prior_receipt_sha256=h.sha(prevpath.read_bytes()),previous_increments_counted=0))
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';plan=h.load(pp);assert len(plan['rows'])==188;evidence=[]
 for row in plan['rows']:
  path=ROOT/row['source_record_reference'];assert h.sha(path.read_bytes())==row['source_record_sha256'];obj=h.load(path)
  for key,rc_key in [('raw','receipt'),('manifest','manifest_receipt')]:
   rc=obj[rc_key];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256'] and json.loads(raw)==obj[key]
  visual=row['continuation_visual_evidence'];decision=ROOT/visual['decision_reference'];assert h.sha(decision.read_bytes())==visual['decision_sha256'];v=h.load(decision);assert row['artwork_id'] in v['approved']
  sheet=ROOT/'docs/research/french-printmaking-20261011/visual-sheets'/decision.name;sv=h.load(sheet);assert h.sha(Path(sv['sheet']).read_bytes())==v['sheet_sha256']
  im=plan['images'][row['artwork_id']];assert im['sha256']==visual['image_sha256'];img=Path(im['local_path']);assert h.sha(img.read_bytes())==im['sha256'] and img.stat().st_size<=100000
  with Image.open(img) as d:d.load();assert list(d.size)==[im['width'],im['height']]
  evidence.append(dict(artwork_id=row['artwork_id'],native_id=row['native_id'],source_record_reference=row['source_record_reference'],source_sha256=row['source_record_sha256'],prior_actual_visual_review=visual,prior_sheet_sha256=v['sheet_sha256'],derivative_sha256=im['sha256']))
 ids=[r['artwork_id'] for r in plan['rows']];digest=h.sha(pp.read_bytes())
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');live=h.snapshot(db,ids)
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
 assert len(live)==len(citations)==188 and all(x['plan_sha256']==digest for x in citations)
 assert all(live[x['artwork_id']]['artwork']['primary_media_id']==plan['images'][x['artwork_id']]['media_id'] and live[x['artwork_id']]['artwork']['status']!='archived' for x in plan['rows'])
 save('independent-reserve-evidence-verification.json',dict(at=h.now(),rows=evidence,passed=True,prior_visual_decisions_preserved=True,no_new_visual_review_claim=True))
 save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,plan_sha256=digest,live_source_citations=citations,immutable_plan_unchanged=True,switch_to='national_gallery_athens'))
 q=next(x for x in queue['sources'] if x['source_id']=='national_gallery_athens')
 ledgers=[]
 for name in q.get('evidence_paths',[]):
  if 'hold' in name:
   p=ROOT/name
   if p.exists():ledgers.append(dict(path=name,sha256=h.sha(p.read_bytes()),contents=h.load(p)))
 for provider in ['000164','000165']:
  p=E.parent/provider/'failures-and-holds.json'
  if p.exists():ledgers.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),contents=h.load(p)))
 save('source-register.json',dict(at=h.now(),provider=next(x for x in reg if x['source_id']=='national_gallery_athens'),prior_cursor=q['resume_cursor'],source_access_hold_ledgers=ledgers,policy_reference='Original111-source CSV plus docs/ARTLINE_IMAGE_USE.md Greek museum extension through1955. Museum restrictions retained separately from user approval.',remaining_gaps=q['remaining_gaps'],production_target=TARGET))
 print('PREFLIGHT PASSED: reserve188 already imported; batch107 exact live snapshot confirmed',flush=True)

def research():
 import re
 from bs4 import BeautifulSoup
 if not (E/'production-target-before-research.json').exists():target('before-research')
 qp=E.parents[1]/'source-queue.json';q=next(x for x in h.load(qp)['sources'] if x['source_id']=='national_gallery_athens');cursor=q['resume_cursor']['batch164_native_primary_gaps'];last=cursor['last_gap_uuid'];old=h.load(E.parent/'000164/athens-all-gap-input.json.gz')
 processed=set();held_slugs=set()
 def collect(v,key=''):
  if isinstance(v,dict):
   for k,x in v.items():
    if 'hold' in key and isinstance(x,str):held_slugs.add(k)
    collect(x,k)
  elif isinstance(v,list):
   if 'processed' in key and 'url' in key:processed.update(x for x in v if isinstance(x,str))
   for x in v:collect(x,key)
 collect(q['resume_cursor'])
 native={x['entity_id']:x for x in old['native']};candidates=[];skips=[]
 for r in old['rows']:
  aid=r['id'];n=native.get(aid)
  if aid<=last:continue
  reason=None
  if not n:reason='no_native_identity'
  elif n['canonical_url'] in processed or n['external_id'] in held_slugs:reason='prior_research_or_hold_preserved_no_request'
  elif r['creation_year_end'] is not None and r['creation_year_end']>1955:reason='museum_source_image_date_cutoff_hold_no_request'
  if reason:skips.append(dict(artwork_id=aid,native=n,decision=reason));continue
  candidates.append(r)
  if len(candidates)==20:break
 assert candidates
 with h.connect() as db:before=h.snapshot(db,[r['id'] for r in candidates])
 if (E/'athens-all-gap-input.json.gz').exists():
  frozen=h.load(E/'athens-all-gap-input.json.gz');assert frozen['rows']==candidates and frozen['before']==before
 else:save('athens-all-gap-input.json.gz',dict(at=h.now(),rows=candidates,before=before,native=[native[r['id']] for r in candidates],parent_frozen_gap_page=rel(E.parent/'000164/athens-all-gap-input.json.gz'),parent_sha256=h.sha((E.parent/'000164/athens-all-gap-input.json.gz').read_bytes()),cursor_before=cursor))
 source_dir=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000166';source_dir.mkdir(parents=True,exist_ok=True);rows=[];chosen=[];session=requests.Session();session.headers['User-Agent']='Artline source-backed research; bounded selected metadata review'
 for r in candidates:
  aid=r['id'];n=native[aid];url=n['canonical_url'];row=dict(artwork_id=aid,native=n,source_url=url)
  if before[aid]['artwork']['primary_media_id'] is not None:row['decision']='concurrent_primary_preserved';rows.append(row);continue
  if n['scheme']!='nationalgallery-gr-work':row['decision']='no_direct_native_museum_identity_hold_no_request';rows.append(row);continue
  receipt_path=E/'source-captures'/(n['external_id']+'.receipt.json')
  if receipt_path.exists():
   rc=h.load(receipt_path);raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256']
  else:
   response=session.get(url,timeout=(15,45));raw=response.content;body=source_dir/(n['external_id']+'.html.gz');body.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(body),retry_after=response.headers.get('Retry-After'));h.save(receipt_path,rc)
  row['receipt']=rc
  if rc['status'] in [401,403,429]:
   row['decision']='provider_access_hold';rows.append(row);save('source-access-holds.json',dict(at=h.now(),host='www.nationalgallery.gr',receipt=rc,do_not_retry_unchanged=True));break
  if rc['status']!=200:row['decision']='source_http_failure';rows.append(row);continue
  soup=BeautifulSoup(raw,'html.parser');head=soup.select_one('h1.artwork');image=soup.select_one('#magnifyimage');acc=soup.select_one('.artwork-no');creator=soup.select_one('p.artist a');description=soup.select_one('p.description')
  if not all([head,image,acc,creator,description]):row['decision']='source_structure_hold';rows.append(row);continue
  date=head.select_one('span');label=date.get_text(' ',strip=True) if date else '';title=head.get_text(' ',strip=True);title=title[:title.rfind(label)].rstrip(', ') if label else title.rstrip(', ')
  row.update(source_title=title,source_date=label,source_accession=acc.get_text(' ',strip=True).removeprefix('Inv. Number').strip(),creator_label=creator.get_text(' ',strip=True),creator_url=creator.get('href'),description=description.get_text(' ',strip=True),image_url=image.get('src'))
  a=before[aid]['artwork'];bounds=re.fullmatch(r'\[?(\d{4})(?:\s*[-–]\s*(\d{4}))?\s*(?:\(\?\)|\?)?\]?',label)
  if not label:row['decision']='unknown_source_date_hold'
  elif not bounds:row['decision']='open_or_unreviewed_source_date_hold'
  elif int(bounds[2] or bounds[1])>1955:row['decision']='museum_source_image_date_cutoff_hold'
  elif (title,row['source_accession'],row['description'])!=(a['title'],a['accession_number'],(a['medium_text'] or '')+', '+(a['dimensions_text'] or '')):row['decision']='source_metadata_identity_conflict_hold'
  elif a['date_display']!=label:row['decision']='source_catalogue_date_label_conflict_hold'
  else:
   row['source_date_bounds']=[int(bounds[1]),int(bounds[2] or bounds[1])];row['decision']='selected_source_dated_image_only';chosen.append(row)
  rows.append(row);print(n['external_id'],repr(label),row['decision'],flush=True)
 assert rows
 save('athens-source-reconciliation.json',dict(at=h.now(),rows=rows,selected=chosen,skipped_without_request=skips,next_after_artwork_id=rows[-1]['artwork_id'],prior_cursor=last,metadata_updates=0,prior_holds_preserved=True))
 save('RESEARCH_CHECKPOINT.json',dict(at=h.now(),batch=166,stage='researched',researched=len(rows),selected=len(chosen),next_action='prepare' if chosen else 'select_another_registry_route',resume_cursor=rows[-1]['artwork_id']))
 print('RESEARCH',len(rows),'SELECTED',len(chosen),flush=True)

if __name__=='__main__':
 R.mkdir(parents=True,exist_ok=True);E.mkdir(parents=True,exist_ok=True)
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
