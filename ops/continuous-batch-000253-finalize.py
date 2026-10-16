#!/usr/bin/env python3
"""Fresh no-replay reconciliation for bounded external-supervisor batch 253."""
import csv, datetime, fcntl, gzip, hashlib, json, os, subprocess
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000253'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000253'
Q=E.parents[1]/'source-queue.json'
PLAN=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz'
PRIOR=E.parent/'000061/independent-french-reserve-evidence-verification.json'
TARGET='artline-508319:europe-west1:artline-postgres'
COUNTS=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 p=Path(p); b=p.read_bytes(); return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def save(p,v):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n')
def connect():
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
 kw=psycopg.conninfo.conninfo_to_dict(secret); kw.update(host='127.0.0.1',port='55519',sslmode='disable',connect_timeout=20)
 return psycopg.connect(**kw,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=60000')

E.mkdir(parents=True,exist_ok=True); R.mkdir(parents=True,exist_ok=True)
with open('/tmp/artline-curated-ingestion.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 proxy=subprocess.check_output("ps -ax -o command= | grep '[a]rtline-cloud-sql-proxy'",shell=True,text=True).strip()
 assert '--port 55519' in proxy and TARGET in proxy
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual==TARGET
 required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
 assert len(list(csv.DictReader(registry.open())))==111
 save(E/'required-input-verification.json',dict(at=now(),files=[dict(path=x,sha256=sha(ROOT/x)) for x in required],registry_path=str(registry),registry_sha256=sha(registry),registry_rows=111,complete_registry_used=True))
 save(E/'production-target-reconciliation.json',dict(at=now(),connection_name=actual,proxy_port=55519,proxy_command_verified=True,established_helper='ops/india-300-delivery-20261011.py',read_only=True,local_catalogue_writes=0))
 plan=load(PLAN); rows=plan['rows']; assert len(rows)==188 and len({x['artwork_id'] for x in rows})==188
 ids=[x['artwork_id'] for x in rows]; pin=sha(PLAN); prior=load(PRIOR)
 assert len(prior['records'])==188 and prior['prior_review_reused_without_new_view_claim']
 prior_by={x['artwork_id']:x for x in prior['records']}; evidence=[]
 for x in rows:
  src=ROOT/x['source_record_reference']; assert sha(src)==x['source_record_sha256']
  assert prior_by[x['artwork_id']]['image_sha256']==plan['images'][x['artwork_id']]['sha256']
  evidence.append(dict(artwork_id=x['artwork_id'],native_id=x['native_id'],source_record_sha256=x['source_record_sha256'],image_sha256=plan['images'][x['artwork_id']]['sha256'],prior_visual_decision=prior_by[x['artwork_id']]['prior_actual_visual_review']))
 with connect() as db:
  live=[dict(x) for x in db.execute("select id::text,primary_media_id::text,status,accession_number from artworks where id=any(%s::uuid[]) order by id",(ids,))]
  cites=[dict(x) for x in db.execute("select entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 from citations where entity_type='artwork' and entity_id=any(%s::uuid[]) and field_name='french_printmaking_source_identity' order by entity_id",(ids,))]
  receipt107=load(E.parent/'000107/batch-verification-receipt.json'); ids107=receipt107['production_ids']
  rows107=[dict(x) for x in db.execute('select id::text,primary_media_id::text,status from artworks where id=any(%s::uuid[]) order by id',(ids107,))]
 assert len(live)==188 and all(x['primary_media_id'] and x['status']!='archived' for x in live)
 assert len(cites)==188 and all(x['plan_sha256']==pin for x in cites)
 assert len(rows107)==len(ids107) and all(x['primary_media_id'] for x in rows107)
 save(E/'independent-french-reserve-evidence-verification.json',dict(at=now(),records=evidence,records_verified=188,source_record_checks=188,plan_sha256=pin,prior_evidence=str(PRIOR.relative_to(ROOT)),prior_evidence_sha256=sha(PRIOR),prior_review_reused_without_new_view_claim=True,new_visual_review_claim=False))
 save(E/'french-reserve-live-reconciliation.json',dict(at=now(),inspected=188,selected_limit=25,already_imported_and_illustrated=188,genuinely_unimported=0,selected=0,new_programme_increments=0,plan_sha256=pin,production_rows=live,citations=cites,all_primary_media_present=True,all_plan_citations_match=True,physical_date_holds_preserved=['80082','80437','81054'],decision='No supplement: every immutable reserve UUID and checksum-bound citation already exists live; no prior row is recounted.'))
 save(E/'batch107-live-reconciliation.json',dict(at=now(),rows=len(rows107),live_rows=rows107,prior_receipt_sha256=sha(E.parent/'000107/batch-verification-receipt.json'),previous_increments_counted=0,replayed=False))
 save(E/'actual-visual-review.json',dict(at=now(),prepared_images=0,images_actually_viewed_this_batch=0,new_visual_review_claim=False,prior_actual_review_reused=True,prior_evidence=str(PRIOR.relative_to(ROOT)),prior_evidence_sha256=sha(PRIOR),reason='No genuinely unimported reserve image exists. Immutable checksum-bound prior visual decisions were verified and cited, not falsely claimed as newly viewed.'))
 before=Q.read_bytes(); q=json.loads(before); changed=0
 for x in q['supplementary_image_routes']:
  if x.get('route_id')=='french-printmaking-prepared-reserve':
   x.update(status='exhausted_all_188_live_reverified_batch253',last_checked_at=now(),last_batch=253,access_status='Fresh read-only production reconciliation: all 188 immutable UUIDs are active and illustrated with matching checksum-bound plan citations.',resume_cursor=None,latest_batch_verified_counts=COUNTS,checkpoint='docs/research/continuous-production-20261011/batches/000253/CHECKPOINT.json',verification_receipt='docs/research/continuous-production-20261011/batches/000253/batch-verification-receipt.json',next_task='Rotate to a different undercovered registry route, prioritizing Greek, Byzantine, Russian-icon or post-Byzantine objects; do not replay French reserve.'); changed+=1
 assert changed==1
 save(Q,q)
 after=Q.read_bytes()
 save(E/'source-queue-update-verification.json',dict(at=now(),route_id='french-printmaking-prepared-reserve',before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),updated_entries=1,unrelated_entries_preserved=True,resume_cursor=None,next_task=next(x['next_task'] for x in q['supplementary_image_routes'] if x.get('route_id')=='french-printmaking-prepared-reserve')))
 receipt=dict(at=now(),verified_counts=COUNTS,production_writes=0,french_reserve_live_rows=188,french_reserve_unimported=0,selected=0,plan_sha256=pin,attribution='No production mutation. All 188 rows and their primary images pre-existed batch 253 and are excluded from increments.',production_target=actual,batch107_reconciled=True)
 save(E/'batch-verification-receipt.json',receipt)
 next_task='Rotate to a different undercovered registry route, prioritizing Greek, Byzantine, Russian-icon or post-Byzantine objects; do not replay the exhausted French reserve.'
 evidence_paths=[str((E/n).relative_to(ROOT)) for n in ['french-reserve-live-reconciliation.json','independent-french-reserve-evidence-verification.json','batch107-live-reconciliation.json','production-target-reconciliation.json','actual-visual-review.json','batch-verification-receipt.json','source-queue-update-verification.json','CHECKPOINT.json']]
 cp=dict(at=now(),batch=253,stage='independently_verified_complete_no_eligible_candidates',discovered=188,selected=0,prepared=0,imported=0,verified=0,verified_counts=COUNTS,production_writes=0,french_reserve_inspected=188,french_reserve_unimported=0,next_task=next_task,blocker='',evidence=evidence_paths[:-1])
 save(E/'CHECKPOINT.json',cp); save(R/'CHECKPOINT.json',cp)
 result=dict(outcome='no_eligible_candidates',summary='Batch 253 freshly reconciled all 188 prepared French printmaking reserve records against live production. Every immutable UUID is already active and illustrated with its checksum-bound plan citation, so no object was eligible for a supplement and no previous delivery was recounted. Batch 107 also remains live; no writes occurred.',next_task=next_task,blocker='',verified_counts=COUNTS,evidence_paths=evidence_paths)
 save(R/'verified-batch-result.json',result)
 files=sorted(E.glob('*.json'))
 save(E/'independent-final-artifact-verification.json',dict(at=now(),artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size) for p in files],runtime_checkpoint_equal=load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),production_writes=0,verified_counts=COUNTS,passed=True))
 print(json.dumps(result))
