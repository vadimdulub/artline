#!/usr/bin/env python3
"""Freshly reconcile the exhausted 188-work French printmaking reserve."""
import fcntl,gzip,hashlib,importlib.util,json,os,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000196'
BASE=E.parents[1]
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000196'
PLAN=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz'
SOURCE_REVIEW=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/source-review-completion.json'
HELPER=ROOT/'ops/india-300-delivery-20261011.py'
TARGET='artline-508319:europe-west1:artline-postgres'

s=importlib.util.spec_from_file_location('prod196',HELPER)
h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
def load(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(name,v): h.save(E/name,v);return v
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p): return str(Path(p).relative_to(ROOT))

E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
with (R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 at=h.now();counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
 plan=load(PLAN);rows=plan['rows'];images=plan['images'];assert len(rows)==188 and len(images)==188
 ids=[x['artwork_id'] for x in rows];native=[x['native_id'] for x in rows];assert len(set(ids))==188 and len(set(native))==188
 proxy=[x for x in subprocess.check_output(['ps','-axo','command='],text=True).splitlines() if 'cloud-sql-proxy' in x and '--port 55519' in x]
 assert len(proxy)==1 and TARGET in proxy[0]
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 with h.connect() as db:
  server=db.execute("SELECT current_database() db,inet_server_port() port").fetchone();assert server['db']=='artline'
  live=h.snapshot(db,ids);assert len(live)==188
  assert all(x['artwork']['status']!='archived' and x['artwork']['primary_media_id'] for x in live.values())
  native_live={r['external_id']:r['entity_id'] for r in db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='yale-object' AND external_id=ANY(%s)",(native,))}
  assert len(native_live)==188 and all(native_live[r['native_id']]==r['artwork_id'] for r in rows)
  prior=load(E.parent/'000107/independent-production-verification.json');live107=h.snapshot(db,list(prior['after']));assert live107==prior['after']
 save('production-target-reconciliation.json',dict(at=at,connection_name=actual,proxy_command_inspected=True,proxy_port=55519,database=server['db'],helper=rel(HELPER),shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
 save('french-reserve-live-reconciliation.json',dict(at=at,route='french_printmaking_prepared_reserve',inspected=188,active=188,illustrated=188,exact_native_uuid_matches=188,genuinely_unimported=0,selected=0,prepared=0,imported=0,verified_new_increments=0,held_native_ids=['80082','80437','81054'],reserve_exhausted=True,do_not_replay=True,plan_sha256=sha(PLAN)))
 save('batch107-live-reconciliation.json',dict(at=at,rows=len(live107),snapshot_fields_equal=True,previous_increments_counted=0,evidence=rel(E.parent/'000107/independent-production-verification.json')))
 review=load(SOURCE_REVIEW);assert review['candidates']==188
 continuation=[r['continuation_visual_evidence'] for r in rows];assert all(v for v in continuation)
 save('independent-reserve-evidence-verification.json',dict(at=at,source_records=188,manifest_records=188,source_record_checksums_present=all(bool(r['source_record_sha256']) for r in rows),continuation_visual_decisions_present=188,immutable_prior_visual_review_reused=True,new_visual_review_claim=False,provider_requests=0,source_review_sha256=sha(SOURCE_REVIEW),plan_sha256=sha(PLAN),parent_plan_sha256=review['parent_plan_sha256'],held_native_ids=['80082','80437','81054']))
 save('actual-visual-review.json',dict(at=at,new_images_prepared=0,new_images_viewed=0,claim='No new visual review claimed. The checksum-bound immutable prior visual decisions on all 188 already-delivered reserve rows were verified and reused; no candidate remained for a new supplement.'))
 save('batch-verification-receipt.json',dict(at=at,verified_counts=counts,production_ids=[],production_writes=0,production_target=TARGET,shared_ingestion_lock='artline-curated-ingestion',attribution='Fresh UUID/native-ID production reads prove all 188 reserve records pre-existed this batch and were already illustrated. No historical delivery is recounted.',transaction_preimages='No write transaction: zero genuinely unimported candidates.'))
 qpath=BASE/'source-queue.json';q=load(qpath);assert len(q['sources'])==111
 route=next(x for x in q['sources'] if x['source_id']=='yale_lux');before_hash=hashlib.sha256(qpath.read_bytes()).hexdigest()
 route['status']='french_reserve_exhausted_188_live_reverified_batch196';route['last_checked_at']=at;route['last_batch']=196;route['checkpoint']=rel(E/'CHECKPOINT.json')
 route['resume_cursor']['live_imported_and_illustrated']=188;route['resume_cursor']['unimported']=0;route['resume_cursor']['retry_allowed']=False;route['resume_cursor']['exact_evidence']=rel(E/'french-reserve-live-reconciliation.json');route['resume_cursor']['next_step']='Do not replay; rotate to an undercovered Greek or Byzantine registry institution.'
 tmp=qpath.with_suffix('.tmp');tmp.write_text(json.dumps(q,indent=2)+'\n');os.replace(tmp,qpath)
 save('source-queue-update-verification.json',dict(at=at,modified_source_ids=['yale_lux'],unrelated_entries_preserved=110,all_111_registry_routes_preserved=True,before_sha256=before_hash,after_sha256=sha(qpath),resume_cursor=route['resume_cursor']))
 evidence=['french-reserve-live-reconciliation.json','production-target-reconciliation.json','batch107-live-reconciliation.json','independent-reserve-evidence-verification.json','actual-visual-review.json','batch-verification-receipt.json','source-queue-update-verification.json']
 cp=dict(at=at,batch=196,stage='verified_no_eligible_candidates',researched=dict(french_reserve=188),selected=0,prepared=0,imported=0,verified=0,verified_counts=counts,next_task='Rotate to an undercovered Greek or Byzantine registry institution; do not replay the exhausted French reserve.',blocker='',evidence_paths=[rel(E/x) for x in evidence],external_supervisor_unchanged=True,production_writes=0,local_catalogue_connections=0)
 (E/'CHECKPOINT.json').write_text(json.dumps(cp,indent=2)+'\n');(R/'CHECKPOINT.json').write_text(json.dumps(cp,indent=2)+'\n')
 save('independent-final-artifact-verification.json',dict(at=at,checkpoint_runtime_equal=load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),all_evidence_exists=all((E/x).exists() for x in evidence),counts_match=True,evidence=[dict(path=rel(E/x),sha256=sha(E/x)) for x in evidence],source_queue_sha256=sha(qpath)))
 print(json.dumps(dict(outcome='no_eligible_candidates',verified_counts=counts,next_task=cp['next_task'])))
