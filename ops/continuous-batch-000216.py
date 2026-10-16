#!/usr/bin/env python3
"""Finalize bounded Roots Singapore registry research for batch 216."""
import copy, csv, datetime, fcntl, importlib.util, json, os, re, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000216'
R=Path('/Users/vadimdulub/Library/Application Support/Artline/continuous-research/batches/000216')
C=R/'captures'; E.mkdir(parents=True,exist_ok=True); R.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('delivery216',ROOT/'ops/india-300-delivery-20261011.py'); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
now=datetime.datetime.now(datetime.timezone.utc).isoformat(); counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
required=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',ROOT/'docs/research/creators-deep-continuation-20261011/source-registry-review.json']
assert sum(1 for _ in csv.DictReader(required[1].open()))==111
h.save(E/'required-input-verification.json',dict(at=now,files=[dict(path=str(p),bytes=p.stat().st_size,sha256=h.sha(p.read_bytes()),read_complete=True) for p in required],registry_rows=111,complete_csv_primary=True,supplementary_json_not_replacement=True))

target=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip(); assert target=='artline-508319:europe-west1:artline-postgres'
cmds=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines(); assert sum(x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target in x for x in cmds)==1
with h.connect() as db: state=dict(db.execute("select current_database() database,pg_is_in_recovery() recovery,current_setting('default_transaction_read_only') read_only").fetchone())
assert state=={'database':'artline','recovery':False,'read_only':'on'}
h.save(E/'production-target-reconciliation.json',dict(at=now,connection_name=target,proxy_port=55519,database=state,helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),shared_ingestion_lock='artline-curated-ingestion',write_transaction_entered=False,local_catalogue_connections=0))
prior=h.load(E.parent/'000107/independent-production-verification.json')
with h.connect() as db: live=h.snapshot(db,list(prior['after']))
assert live==prior['after']
h.save(E/'batch107-live-reconciliation.json',dict(at=now,production_ids_checked=len(live),snapshot_equal=True,uncertain_writes_found=False,prior_receipt_sha256=h.sha((E.parent/'000107/independent-production-verification.json').read_bytes()),previous_increments_counted=0))

files=sorted(C.glob('*.html')); assert len(files)==3
landing=max(files,key=lambda p:p.stat().st_size); text=landing.read_text(errors='replace')
ids=list(dict.fromkeys(re.findall(r'collection-landing/listing/(\d+)',text,re.I)))
object_ids=list(dict.fromkeys(re.findall(r'\\"object_id\\":\\"(\d+)',text)))
assert len(ids)>=25 and len(object_ids)>=25
captures=[dict(path=str(p),bytes=p.stat().st_size,sha256=h.sha(p.read_bytes())) for p in files]
h.save(E/'roots-singapore-route-research.json',dict(at=now,source_id='roots_singapore',route='current official Collection Landing first bounded page plus registry sample and terms',official_requests=3,captures=captures,directory_records_reviewed=len(object_ids),distinct_listing_links=len(ids),selected_artworks=0,decision='The current first bounded collection page contains heritage directory objects (equipment, documents, signs, photographs, containers and related material), not eligible paintings, drawings, prints or icons. Directory entries are not counted as artworks. The registry sample route currently renders a 404 shell, and the terms do not provide per-object explicit-open image rights. No image URL was requested or downloaded.',resume_cursor=dict(collection_landing_page=1,reviewed_object_ids=object_ids,next_step='Resume at the next distinct official collection page/filter only if it exposes stable pictorial object records; otherwise rotate to another untouched registry institution with explicit-open object images.')))
h.save(E/'actual-visual-review.json',dict(at=now,prepared_images=0,actually_viewed_files=[],claim='No eligible image was selected or prepared, so no visual inspection is claimed.'))

Q=E.parents[1]/'source-queue.json'
with (Q.parent/'source-queue.worker.lock').open('a+') as a,(Q.parent/'source-queue.lock').open('a+') as b:
 fcntl.flock(a,fcntl.LOCK_EX); fcntl.flock(b,fcntl.LOCK_EX); before=h.load(Q); after=copy.deepcopy(before)
 row=next(x for x in after['sources'] if x['source_id']=='roots_singapore')
 row.update(status='first_bounded_collection_page_researched_no_eligible_pictorial_objects',last_batch=216,last_checked_at=now,checkpoint='docs/research/continuous-production-20261011/batches/000216/CHECKPOINT.json',access_status='Official collection landing and terms HTTP 200; registry sample currently 404; no image requests.')
 row['resume_cursor']=dict(route='official_collection_landing',completed_page=1,reviewed_object_ids=object_ids,skip_completed_page=True,next_step='Research the next distinct pictorial filter/page if stable; rotate first to an untouched Greek, Byzantine or Russian-icon route with explicit-open images.')
 refs=['docs/research/continuous-production-20261011/batches/000216/roots-singapore-route-research.json']; row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+refs)); row.setdefault('research_history',[]).append(dict(batch=216,at=now,directory_records_reviewed=len(object_ids),selected=0,verified_counts=counts,evidence=refs))
 assert len(after['sources'])==111 and [x for x in before['sources'] if x['source_id']!='roots_singapore']==[x for x in after['sources'] if x['source_id']!='roots_singapore']
 tmp=Q.with_suffix('.batch216.tmp'); tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n'); os.replace(tmp,Q)
h.save(E/'source-queue-update-verification.json',dict(at=now,updated_source='roots_singapore',unrelated_entries_preserved=110,original_registry_routes=111,queue_sha256=h.sha(Q.read_bytes()),evidence='roots-singapore-route-research.json'))
next_task='Research another untouched registry institution with stable pictorial object IDs and explicit-open image rights, prioritizing Greek, Byzantine, post-Byzantine or Russian-icon collections; do not repeat Roots page 1.'
h.save(E/'batch-verification-receipt.json',dict(at=now,batch=216,outcome='no_eligible_candidates',discovered_directory_records=len(object_ids),selected=0,prepared=0,imported=0,verified_counts=counts,production_writes=0,storage_writes=0,local_catalogue_writes=0,attribution_basis='Fresh official captures and live row-scoped batch-107 reconciliation; no prior additions recounted.'))
evidence=['production-target-reconciliation.json','batch107-live-reconciliation.json','roots-singapore-route-research.json','actual-visual-review.json','source-queue-update-verification.json','batch-verification-receipt.json']
checkpoint=dict(at=now,batch=216,stage='complete_no_eligible_candidates',researched_directory_records=len(object_ids),selected=0,prepared=0,imported=0,verified_counts=counts,next_task=next_task,blocker='',production_target=target,external_supervisor_unmodified=True,evidence_paths=[str((E/x).relative_to(ROOT)) for x in evidence])
h.save(E/'CHECKPOINT.json',checkpoint); h.save(R/'CHECKPOINT.json',checkpoint)
paths=evidence+['CHECKPOINT.json']; h.save(E/'independent-final-artifact-verification.json',dict(at=now,files=[dict(path=str((E/p).relative_to(ROOT)),sha256=h.sha((E/p).read_bytes())) for p in paths],verified_counts=counts,production_writes=0))
result=dict(outcome='no_eligible_candidates',summary=f'Batch 216 researched {len(object_ids)} distinct records on the first live Roots Singapore collection page. They are heritage directory objects rather than eligible pictorial artworks, the registry sample is currently unavailable, and object-level open image rights were not established. No image or production write occurred. The production target and all 12 batch-107 records were freshly reconciled.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[str((E/p).relative_to(ROOT)) for p in ['production-target-reconciliation.json','batch107-live-reconciliation.json','roots-singapore-route-research.json','actual-visual-review.json','source-queue-update-verification.json','batch-verification-receipt.json','independent-final-artifact-verification.json','CHECKPOINT.json']])
h.save(E/'worker-result.json',dict(batch=216,attempt=1,finished_at=now,result=result)); h.save(R/'result-001.json',result); print(json.dumps(result))
