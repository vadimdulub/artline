#!/usr/bin/env python3
"""Finalize no-write batch 152 with live reconciliation and durable receipts."""
import copy,csv,fcntl,hashlib,importlib.util,json,os
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000152'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000152'
Q=ROOT/'docs/research/continuous-production-20261011/source-queue.json'
REG=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
for p in (E,R):p.mkdir(parents=True,exist_ok=True)
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 with open(p) as f:return json.load(f)
def save(name,obj,base=E):
 p=base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');return obj
spec=importlib.util.spec_from_file_location('prod',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

recon=load(E/'saam-shard08-identity-reconciliation.json')
assert recon['captured_records']==60 and recon['selected']==0 and len(recon['classified_before_selection'])==60
required=[ROOT/'AGENTS.md',REG,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',Q]
assert len(list(csv.DictReader(REG.open())))==111
save('required-input-verification.json',dict(at=now(),registry_rows=111,complete_original_registry_used=True,files=[dict(path=str(p),sha256=sha(p)) for p in required],local_catalogue_connections=0))

with h.connect() as db:
 target=dict(db.execute("SELECT current_database() database, current_setting('port')::int port, inet_server_addr()::text server_addr").fetchone())
 prev=load(E.parent/'000107/independent-production-verification.json')
 assert h.snapshot(db,list(prev['after']))==prev['after']
save('production-target-reconciliation.json',dict(at=now(),connection_name='artline-508319:europe-west1:artline-postgres',proxy_port=55519,proxy_process_verified=True,database=target,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',write=False,backup_required=False,local_catalogue_connections=0))
save('batch107-live-reconciliation.json',dict(at=now(),snapshot_equal=True,rows=len(prev['after']),previous_increments_counted=0))
fr=load(E.parent/'000142/french-reserve-live-reconciliation.json');assert fr['unimported']==0 and fr['already_imported_and_illustrated']==188
save('french-reserve-live-reconciliation.json',dict(at=now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,prior_verified_evidence=str((E.parent/'000142/french-reserve-live-reconciliation.json').relative_to(ROOT)),plan_sha256=fr['plan_sha256'],prior_actual_visual_review_reused=True,new_visual_review_claim=False))

queue=load(Q);before=copy.deepcopy(queue);q=next(x for x in queue['sources'] if x['source_id']=='smithsonian_open_access')
q.update(status='saam_shard08_fully_classified_no_eligible_exact_missing_image_match',last_checked_at=now(),last_batch=152,checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)),resume_cursor=dict(unit='saam',completed_shard='08',next_shard='09',source_sha256=load(E/'source-captures/saam-08.receipt.json')['sha256'],records_classified=60,eligible_exact_missing_image_matches=0,newly_illustrated_native_ids=[],scope='All 60 shard records classified; none was an exact existing SAAM legacy work with a missing primary image and no conflicting native identity. No image was prepared, viewed, uploaded or attached.'))
q['evidence_paths']=[str((E/x).relative_to(ROOT)) for x in ['saam-shard08-identity-reconciliation.json','production-target-reconciliation.json','batch107-live-reconciliation.json','CHECKPOINT.json']]
with Q.with_suffix('.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);tmp=Q.with_suffix('.152.tmp');tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q)
save('source-queue-update-verification.json',dict(at=now(),updated_source='smithsonian_open_access',unrelated_entries_preserved=[x for x in before['sources'] if x['source_id']!='smithsonian_open_access']==[x for x in queue['sources'] if x['source_id']!='smithsonian_open_access'],queue_sha256=sha(Q),resume_cursor=q['resume_cursor']))
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
save('independent-production-verification.json',dict(at=now(),verified_counts=counts,production_writes=0,selected=0,prepared=0,uploaded=0,attached=0,visual_review_required=False,visual_review_claimed=False,reason='No eligible exact missing-image match among all 60 source records.',metadata_unchanged=True,local_database_connections=0))
save('batch-verification-receipt.json',dict(at=now(),verified_counts=counts,production_ids=[],production_writes=0,source_sha256=recon['source_sha256'],attribution='No production increment: all shard-08 records were classified before selection and none met the exact existing-work missing-primary criteria.',production_target='artline-508319:europe-west1:artline-postgres',shared_ingestion_lock='artline-curated-ingestion',lock_not_acquired_because_no_write=True))
nxt='Process bounded Smithsonian SAAM shard 09 or rotate to another undercovered permitted registry museum if shard 09 is unavailable; do not replay shards 01–08 or the exhausted French reserve.'
evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','saam-shard08-identity-reconciliation.json','independent-production-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']
cp=dict(at=now(),batch=152,stage='independently_verified_complete_no_write',researched=dict(french_reserve=188,saam_shard08_records=60),selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task=nxt,blocker='',evidence=[str((E/x).relative_to(ROOT)) for x in evidence],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0);save('CHECKPOINT.json',cp);save('CHECKPOINT.json',cp,R)
checked=[]
for n in evidence+['CHECKPOINT.json']:
 p=E/n;load(p);checked.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size))
save('independent-final-artifact-verification.json',dict(at=now(),artifacts=checked,runtime_checkpoint_equal=load(R/'CHECKPOINT.json')==cp,passed=True))
result=dict(outcome='progress',summary='Batch 152 fully classified all 60 Smithsonian SAAM shard-08 records. None was an exact existing through-1970 artwork with a missing primary image and nonconflicting native identity, so no image was prepared, visually reviewed, uploaded or attached and no production increment is claimed. Live batch-107 state and the exhausted 188-record French reserve were reconciled; the local catalogue remained untouched.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[str((E/x).relative_to(ROOT)) for x in evidence+['CHECKPOINT.json','independent-final-artifact-verification.json']]);save('worker-result.json',result);save('worker-result.json',result,R);print(json.dumps(result))
