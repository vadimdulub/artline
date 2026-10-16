#!/usr/bin/env python3
"""Persist bounded batch 253 after production authentication prevented a fresh read."""
import csv, datetime, gzip, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000253'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000253'
Q=E.parents[1]/'source-queue.json'; PLAN=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz'
PRIOR=E.parent/'000061/independent-french-reserve-evidence-verification.json'; LIVE=E.parent/'000214/french-reserve-live-reconciliation.json'
COUNTS=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 p=Path(p); b=p.read_bytes(); return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def save(p,v): p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n')
E.mkdir(parents=True,exist_ok=True); R.mkdir(parents=True,exist_ok=True)
plan=load(PLAN); prior=load(PRIOR); live=load(LIVE)
assert len(plan['rows'])==len(prior['records'])==188
assert live['inspected']==live['already_imported_and_illustrated']==188 and live.get('genuinely_unimported',live.get('unimported'))==0
assert len(list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'))))==111
for x in plan['rows']:
 assert sha(ROOT/x['source_record_reference'])==x['source_record_sha256']
save(E/'authentication-hold.json',dict(at=now(),service='Google Cloud CLI authentication for Cloud SQL/Secret Manager',attempts=1,error_class='noninteractive_reauthentication_required',message='Configured account token refresh requires gcloud auth login; no interactive prompt is possible in this bounded worker.',proxy_still_running=True,proxy_target_from_process='artline-508319:europe-west1:artline-postgres',proxy_port=55519,production_writes=0,retry_rule='Do not repeat until authentication state changes.'))
save(E/'reserve-local-evidence-verification.json',dict(at=now(),records=188,plan_sha256=sha(PLAN),source_records_checksum_verified=188,prior_visual_evidence=str(PRIOR.relative_to(ROOT)),prior_visual_evidence_sha256=sha(PRIOR),prior_visual_decisions=188,prior_review_reused_without_new_view_claim=True,new_visual_review_claim=False,latest_live_reconciliation=str(LIVE.relative_to(ROOT)),latest_live_reconciliation_sha256=sha(LIVE),latest_live_result='188 already active and illustrated; zero unimported',fresh_live_query_completed=False,limitation='Production authentication expired before a fresh database read; prior live receipt is not represented as current verification.'))
save(E/'actual-visual-review.json',dict(at=now(),prepared_images=0,images_actually_viewed_this_batch=0,new_visual_review_claim=False,prior_actual_review_reused=True,prior_evidence=str(PRIOR.relative_to(ROOT)),reason='No object could be selected: latest verified live receipt has zero unimported reserve rows, and fresh production reconciliation was authentication-blocked.'))
q=load(Q); before=Q.read_bytes(); changed=0
for x in q['supplementary_image_routes']:
 if x.get('route_id')=='french-printmaking-prepared-reserve':
  x.update(status='exhausted_188_last_live_verified_batch214_fresh_batch253_auth_hold',last_checked_at=now(),last_batch=253,access_status='Immutable reserve evidence verified locally; fresh production read blocked by noninteractive gcloud reauthentication. Do not replay. Retry live reconciliation only after authentication changes.',resume_cursor=None,latest_batch_verified_counts=COUNTS,checkpoint='docs/research/continuous-production-20261011/batches/000253/CHECKPOINT.json',next_task='After production authentication is restored, perform one fresh read-only reconciliation of French188 only if required; otherwise rotate directly to an undercovered Greek, Byzantine, Russian-icon or post-Byzantine registry route.'); changed+=1
assert changed==1
save(Q,q)
save(E/'source-queue-update-verification.json',dict(at=now(),route_id='french-printmaking-prepared-reserve',before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=sha(Q),updated_entries=1,unrelated_entries_preserved=True,resume_cursor=None))
next_task='Restore the already-authorized production account authentication, then rotate to an undercovered Greek, Byzantine, Russian-icon or post-Byzantine registry route; do not replay French188.'
paths=[str((E/n).relative_to(ROOT)) for n in ['authentication-hold.json','reserve-local-evidence-verification.json','actual-visual-review.json','source-queue-update-verification.json','CHECKPOINT.json']]
cp=dict(at=now(),batch=253,stage='blocked_production_authentication',discovered=188,selected=0,prepared=0,imported=0,verified=0,verified_counts=COUNTS,production_writes=0,next_task=next_task,blocker='Configured gcloud account requires interactive reauthentication; fresh production reconciliation and any authorized write are unavailable.',evidence=paths[:-1])
save(E/'CHECKPOINT.json',cp); save(R/'CHECKPOINT.json',cp)
save(E/'batch-verification-receipt.json',dict(at=now(),verified_counts=COUNTS,production_writes=0,attribution='No production increments. No fresh live verification completed; latest independent batch214 receipt reports all 188 already live.',blocked=True,authentication_hold='authentication-hold.json'))
result=dict(outcome='blocked',summary='Batch 253 verified all 188 immutable French reserve source records and checksum-bound prior visual decisions locally. The latest independent live receipt already found all 188 active and illustrated, so none should be replayed; a fresh production read could not be completed because the configured gcloud account now requires interactive reauthentication. No writes occurred and no prior additions were counted.',next_task=next_task,blocker=cp['blocker'],verified_counts=COUNTS,evidence_paths=paths[:-1]+[str((E/'batch-verification-receipt.json').relative_to(ROOT)),paths[-1]])
save(R/'verified-batch-result.json',result)
print(json.dumps(result))
