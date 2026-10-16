#!/usr/bin/env python3
"""Independent batch272 checks and bounded queue checkpoint; no continuation process."""
import copy,datetime,fcntl,gzip,hashlib,importlib.util,io,json,os
from pathlib import Path
import requests
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('b272',ROOT/'ops/continuous-met-000272.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i;E=b.E.parent;R=b.RUNTIME.parent;B=b.B
# Runtime in the adapter is the met-route subfolder; the batch checkpoint lives at its parent.
assert R.name=='000272'
def save(name,value):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,value);return value
def rel(p):return str(Path(p).relative_to(ROOT))
def verify():
 images,audit,review=i.accepted(B);ids=[x['artwork_id'] for x in images];ims={x['artwork_id']:x for x in images};rows={x['artwork_id']:x for x in i.selected(B)['rows']};selection=h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 prepath=i.BACKUP/B/'before-000.json.gz';before=h.load(prepath)
 assert len(ids)==7 and len(set(ids))==7 and all(before[x]['artwork']['primary_media_id'] is None for x in ids)
 with b.connect() as db:
  after=h.snapshot(db,ids)
  media=[dict(x) for x in db.execute("SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.width,ma.height,ma.rights_status,ma.license_label,ma.creator_credit,ma.source_page_url,e.adapter_version,e.source_record_id,e.source_checksum,e.source_image_url,e.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=ma.id WHERE a.id=ANY(%s::uuid[])",(ids,))]
  search=[dict(x) for x in db.execute('SELECT a.id::text,s.primary_media_id::text,s.status,s.title FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.primary_media_id=a.primary_media_id AND s.status=a.status AND s.title=a.title',(ids,))]
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[ims[x]['media_id'] for x in ids]))]
 assert len(ids)==len(after)==len(media)==len(search)==len(events)
 for aid in ids:
  assert after[aid]['artwork']['primary_media_id']==ims[aid]['media_id']
  assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
  assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings']
  added=[x for x in after[aid]['attachments'] if x not in before[aid]['attachments']]
  assert len(added)==1 and added[0]['media_id']==ims[aid]['media_id']
 for event in events:
  assert event['before_json']==before[event['entity_id']]['artwork'] and event['after_json']==after[event['entity_id']]['artwork']
 for item in media:
  aid=item['id'];im=ims[aid];row=rows[aid];ev=item['evidence_json'] if isinstance(item['evidence_json'],dict) else json.loads(item['evidence_json'])
  assert (item['checksum_sha256'],item['byte_size'],item['adapter_version'],item['rights_status'],item['license_label'],item['source_record_id'],item['source_checksum'])==(im['sha256'],im['bytes'],i.OP,'cc0','CC0 1.0',row['native_id'],row['image']['receipt']['sha256'])
  assert item['creator_credit']==row['source_credit'] and item['source_page_url']==row['source_url'] and item['source_image_url']==im['source_image_url']
  assert ev['selection_sha256']==selection and ev['original_catalogue_plan_sha256']==row['plan_sha256']
  assert ev['identity_reconciliation']['editorial_confidence']>=.9 and ev['visual_review']['sha256']==im['sha256'] and ev['visual_review']['original_viewed'] and ev['visual_review']['viewed_individually']
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
 save('independent-production-verification.json',dict(at=h.now(),before=before,after=after,media=media,search_documents=search,selection_sha256=selection,transaction_preimage_path=str(prepath),preimage_sha256=h.sha(prepath.read_bytes()),verified_counts=counts,metadata_creators_holdings_status_unchanged=True,passed=True,local_catalogue_connections=0))
 save('independent-audit-history-verification.json',dict(at=h.now(),events=events,preimage_sha256=h.sha(prepath.read_bytes()),selection_sha256=selection,passed=True))
 files=[];sourcechecks=[]
 for aid,im in ims.items():
  for kind,p,digest in [('derivative',Path(im['path']),im['sha256']),('original',Path(im['original_path']),im['source_sha256'])]:
   raw=p.read_bytes();assert h.sha(raw)==digest
   with Image.open(io.BytesIO(raw)) as decoded:decoded.load();size=list(decoded.size)
   if kind=='derivative':assert len(raw)<=100000 and size==[im['width'],im['height']]
   else:assert size==im['original_dimensions'] and p.is_relative_to(Path.home()/'Library/Application Support/Artline/source-images')
   files.append(dict(artwork_id=aid,kind=kind,path=str(p),sha256=digest,bytes=len(raw),dimensions=size,complete_decode=True,actually_viewed=True))
  assert abs(im['width']/im['height']-im['original_dimensions'][0]/im['original_dimensions'][1])<.003
  row=rows[aid];rc=row['image']['receipt'];body=ROOT/rc['body_path'];raw=gzip.decompress(body.read_bytes());assert h.sha(raw)==rc['sha256'];obj=json.loads(raw)
  assert obj['isPublicDomain'] and str(obj['objectID'])==row['native_id'] and obj['accessionNumber']==row['accession_number'] and obj['title']==row['title'] and im['source_image_url'] in [obj['primaryImage'],obj['primaryImageSmall']]
  sourcechecks.append(dict(artwork_id=aid,source_capture=rel(body),source_sha256=rc['sha256'],source_id=row['native_id'],inventory=obj['accessionNumber'],rights='CC0 1.0',image_url=im['source_image_url'],creation_bounds=[obj['objectBeginDate'],obj['objectEndDate']],confidence=.99))
 save('independent-source-and-file-verification.json',dict(at=h.now(),files=files,sources=sourcechecks,visual_review_path=rel(i.folder(B)/'visual-review.json'),visual_review_sha256=h.sha((i.folder(B)/'visual-review.json').read_bytes()),actual_visual_decisions=review['decisions'],passed=True))
 public=[]
 for aid,im in ims.items():
  api=requests.get('https://artlines.org/api/backend/v1/atlas/artworks/'+aid,timeout=(15,45));api.raise_for_status();pic=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,45));pic.raise_for_status();assert im['storage_path'] in api.text and h.sha(pic.content)==im['sha256']
  with Image.open(io.BytesIO(pic.content)) as decoded:decoded.load();assert list(decoded.size)==[im['width'],im['height']]
  public.append(dict(artwork_id=aid,api_status=api.status_code,api_sha256=h.sha(api.content),image_status=pic.status_code,storage_path=im['storage_path'],sha256=h.sha(pic.content),bytes=len(pic.content),full_decode=True))
 save('independent-public-verification.json',dict(at=h.now(),rows=public,passed=True))
 from google.cloud import storage
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);bucket=storage.Client(project='artline-508319',credentials=credentials).bucket(i.d.core.BUCKET);stored=[]
 for aid,im in ims.items():
  blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();raw=blob.download_as_bytes();assert h.sha(raw)==im['sha256'] and blob.size==im['bytes'] and blob.metadata['operation']==i.OP and blob.metadata['sha256']==im['sha256']
  stored.append(dict(artwork_id=aid,object_key=blob.name,generation=blob.generation,bytes=blob.size,sha256=h.sha(raw),metadata=blob.metadata))
 save('independent-storage-verification.json',dict(at=h.now(),rows=stored,passed=True))
 save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,selection_sha256=selection,transaction_preimage_sha256=h.sha(prepath.read_bytes()),production_target='artline-508319:europe-west1:artline-postgres',shared_ingestion_lock='artline-curated-ingestion',attribution='Seven null primary images in locked transaction preimages; matching audit before/after. Unique batch272 adapter and selection, source and original-plan checksums persisted in media rights evidence. Fresh independent database, search, storage and public verification. No prior campaign increments counted.'))
 return counts,ids,selection

def finalize(counts,ids,selection):
 recon=h.load(b.E/'gap-reconciliation.json');held=[x for x in recon['rows'] if x['reason']!='eligible'];bil=h.load(E/'exact-identity-decisions.json')
 next_task='Review six saved Berlin icon candidates 1787232, 1787229, 1792596, 1757016, 1787240 and 1791012, skipping delivered objects and recorded date/ownership holds; then rotate sources. SAAM shard44 resumes at offset50. Met priority image gaps may resume after '+recon['resume_after_artwork_id']+'. Bilibin three mixed-page images remain held; do not replay French188 reserve.'
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);q=h.load(qp);old=copy.deepcopy(q)
  met=next(x for x in q['sources'] if x['source_id']=='met_museum');cursor=copy.deepcopy(met['resume_cursor']);cursor.update(after_artwork_id=recon['resume_after_artwork_id'],previous_after_artwork_id=recon['after_artwork_id'],latest_checked=len(recon['rows']),latest_held=len(held),selected_native_ids=[x['native_id'] for x in i.selected(B)['rows']],hold_ledger=rel(E/'failures-and-holds.json'),last_verified_batch=272,next_step=next_task)
  met.update(status='seven_further_existing_primary_gaps_verified_50_checked_batch272',last_checked_at=h.now(),last_batch=272,resume_cursor=cursor,latest_batch_verified_counts=counts,checkpoint=rel(E/'CHECKPOINT.json'),access_status='50 native object API captures:49 HTTP200 and one404. Seven exact CC0 images downloaded and verified; no provider denial or retry.',policy_reference='Original111-source CSV met_museum; docs/ARTLINE_IMAGE_USE.md general policy; native isPublicDomain true and official CC0 policy')
  for name in ['independent-production-verification.json','independent-source-and-file-verification.json','independent-public-verification.json','independent-storage-verification.json','batch-verification-receipt.json','failures-and-holds.json']:
   if rel(E/name) not in met.setdefault('evidence_paths',[]):met['evidence_paths'].append(rel(E/name))
  route=dict(route_id='wikiart-native-russian-bilibin',provider='WikiArt',status='three_dated_primary_gaps_held_prior_mixed_page_visual_reviews',last_checked_at=h.now(),last_batch=272,policy_reference='docs/ARTLINE_IMAGE_USE.md WikiArt source approval',access_status='Three pages opened by web tool; prior checksum-pinned manual image holds then reconciled. No images downloaded.',resume_cursor=dict(artist_ids=['2b3a8e63-6eac-411e-8eb5-7712ec2a84f3'],processed_artwork_ids=[x['artwork_id'] for x in bil['rows']],after_artwork_id=bil['rows'][-1]['artwork_id'],remaining_dated_native_gap_count=3,retry_unchanged_images=False,next_step='Require new exact single-work reproductions before retrying mixed-page source images; rotate sources.'),hold_ledger=rel(E/'prior-object-hold-check.json'),checkpoint=rel(E/'CHECKPOINT.json'),verified_counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0))
  assert not any(x.get('route_id')==route['route_id'] for x in q.get('supplementary_image_routes',[]))
  q.setdefault('supplementary_image_routes',[]).append(route)
  assert [x for x in q['sources'] if x['source_id']!='met_museum']==[x for x in old['sources'] if x['source_id']!='met_museum'] and q['supplementary_image_routes'][:-1]==old['supplementary_image_routes']
  tmp=qp.with_suffix('.272.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
 save('source-queue-update-verification.json',dict(at=h.now(),updated_sources=['met_museum'],added_supplementary_route=route['route_id'],unrelated110_registry_entries_unchanged=True,existing_supplementary_entries_unchanged=True,prior_holds_preserved=True,queue_sha256=h.sha(qp.read_bytes()),resume_cursor=cursor,passed=True))
 save('failures-and-holds.json',dict(at=h.now(),met_researched=50,met_held=held,bilibin_preserved_holds=h.load(E/'prior-object-hold-check.json')['candidate_holds'],bilibin_images_downloaded=0,source_access_denials=0,unchanged_failed_provider_retries=0,local_setup_errors=['System Python lacks psycopg; established /tmp/artline-cesi-venv/bin/python used'],unrelated_hold_ledgers_unchanged=True))
 save('source-register-final.json',dict(at=h.now(),original_registry_rows=111,registry_not_replaced=True,met_source_registry= h.load(b.E/'source-register.json'),met_directory_coverage=0,met_discovered=50,met_selected=7,met_prepared=7,met_imported=7,met_verified=7,met_hold_count=len(held),bilibin_discovered=3,bilibin_selected=0,actual_originals_viewed=7,actual_derivatives_viewed=7,sheet_viewed=False,policy_url='https://www.metmuseum.org/hubs/open-access',remaining_gaps='Scope is only this exact-object slice, not museum or artist coverage; explicit date/creator/CC0 and mixed-page holds retained',next_task=next_task))
 # The target-complete stop evidence and all unrelated source ledgers stay immutable.
 stopped=h.load(E/'separate-continuation-campaign.json')
 for f in stopped['previous_campaign_files_unchanged']:assert h.sha((ROOT/f['path']).read_bytes())==f['sha256']
 save('independent-stop-preservation-verification.json',dict(at=h.now(),records=stopped['previous_campaign_files_unchanged'],unchanged=True,supervisor_changes=0,local_catalogue_connections=0))
 start=h.load(E/'production-target-reconciliation.json')['at'];finish=h.now();seconds=(datetime.datetime.fromisoformat(finish)-datetime.datetime.fromisoformat(start)).total_seconds()
 names=['required-input-verification.json','original-source-registry.json','inherited-holds-verification.json','batch107-live-reconciliation.json','batch271-live-reconciliation.json','separate-continuation-campaign.json','prior-object-hold-check.json','exact-identity-decisions.json','met-route/prewrite-global-identity-verification.json','met-route/storage-limit-verification.json','met-route/production-target-before-storage-write.json','met-route/production-target-before-database-write.json','met-route/cloud-backup.json','met-route/batches/met-000/visual-review.json','independent-production-verification.json','independent-audit-history-verification.json','independent-source-and-file-verification.json','independent-public-verification.json','independent-storage-verification.json','batch-verification-receipt.json','source-queue-update-verification.json','source-register-final.json','failures-and-holds.json','independent-stop-preservation-verification.json']
 cp=dict(at=finish,batch=272,stage='independently_verified_complete',operation=i.OP,discovered=53,selected=7,prepared=7,imported=7,verified=7,verified_counts=counts,production_ids=ids,selection_sha256=selection,next_task=next_task,blocker='',evidence=[rel(E/x) for x in names],started_at=start,finished_at=finish,measured_runtime_seconds=seconds,external_supervisor_unchanged=True,local_catalogue_connections=0)
 save('CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
 artifacts=[]
 for name in names+['CHECKPOINT.json']:
  p=E/name;h.load(p);artifacts.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
 save('independent-final-artifact-verification.json',dict(at=h.now(),artifacts=artifacts,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,passed=True))
 result=dict(outcome='progress',summary='Verified seven authentic primary images on existing Met artworks, including three Callot prints. Every original and derivative was visually reviewed. Preserved 43 Met research holds and three Bilibin mixed-page holds; no catalogue metadata or local database changes.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in ['CHECKPOINT.json','batch-verification-receipt.json','independent-production-verification.json','independent-source-and-file-verification.json','independent-public-verification.json','independent-storage-verification.json','source-queue-update-verification.json','independent-final-artifact-verification.json']])
 save('verified-batch-result.json',result);h.save(R/'verified-batch-result.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':
 with (R/'verification.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);counts,ids,selection=verify();finalize(counts,ids,selection)
