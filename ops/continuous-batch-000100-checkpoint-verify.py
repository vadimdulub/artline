#!/usr/bin/env python3
"""Independent persisted-checkpoint and source-capture verification; no writes to production."""
import csv,datetime,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000100';W=E/'warsaw'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000100'
def load(p):
 p=Path(p);data=p.read_bytes();return json.loads(gzip.decompress(data) if p.suffix=='.gz' else data)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
 p=Path(p);return dict(path=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),sha256=sha(p),bytes=p.stat().st_size)
def save(p,d):
 raw=json.dumps(d,ensure_ascii=False,indent=2).encode()
 if p.exists():assert p.read_bytes()==raw
 else:p.write_bytes(raw)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
cp=load(E/'CHECKPOINT.json');receipt=load(E/'batch-verification-receipt.json');assert cp==load(R/'CHECKPOINT.json')
assert cp['verified_counts']==receipt['verified_counts']==dict(new_painters=0,new_artworks=10,newly_illustrated=10,alternate_images=0,museum_links=10)
production=load(W/'independent-production-verification.json');audit=load(W/'independent-audit-history-verification.json');public=load(W/'independent-public-verification.json');storage=load(W/'independent-storage-verification.json');resume=load(W/'independent-resume-verification.json')
assert len(production['rows'])==len(audit['inserts'])==len(public['rows'])==len(storage['checks'])==10
assert set(production['rows'])==set(cp['production_ids'])=={x['artwork_id'] for x in public['rows']}
assert production['plan_sha256']==cp['metadata_plan_sha256']==sha(W/'warsaw-icons/plan.json.gz')
assert production['selection_sha256']==cp['image_selection_sha256']==sha(W/'batches/warsaw-000/selection.json.gz')
assert production['preimages_sha256']==sha(production['transaction_preimages']) and load(production['transaction_preimages'])['artworks']=={}
assert production['image_preimages_sha256']==sha(production['image_preimages'])
assert resume['live_snapshots_equal'] and resume['new_production_increments_on_resume']==0 and resume['audit_counts_before']==resume['audit_counts_after']
for path,digest in resume['immutable_file_checksums'].items():assert sha(path)==digest
for r in production['citations']:assert r['note']['plan_sha256']==cp['metadata_plan_sha256']
for r in production['media']:
 ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
 assert ev['selection_sha256']==cp['image_selection_sha256'] and ev['batch_visual_review_sha256']==sha(W/'actual-visual-review.json')
for x in load(W/'local-recovery-verification.json')['files']:assert sha(x['path'])==x['sha256']
captures=[]
for p in [W/'warsaw-icons-page12.receipt.json']+sorted(W.glob('object-*.receipt.json')):
 r=load(p);data=gzip.decompress(Path(r['body_path']).read_bytes());assert r['status']==200 and hashlib.sha256(data).hexdigest()==r['sha256'] and len(data)==r['bytes'];captures.append(ref(p))
assert len(captures)==25
reserve=load(E/'independent-reserve-evidence-verification.json');assert reserve['inspected']==188 and reserve['new_selection_count']==0
for x in reserve['immutable_plans']:assert sha(x['path'])==x['sha256']
for x in reserve['records']:
 for k in ['source_record','prior_visual_decision']:assert sha(x[k]['path'])==x[k]['sha256']
 assert sha(x['local_path'])==x['derivative_sha256']
before=load(E/'source-queue-immediately-before-update.json');after=load(E.parents[1]/'source-queue.json');assert after==load(E/'source-queue-after.json')
touched={'yale_lux','national_museum_warsaw'}
assert [x for x in before['sources'] if x['source_id'] not in touched]==[x for x in after['sources'] if x['source_id'] not in touched]
reg=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')))
assert len(reg)==len(after['sources'])==111 and {x['source_id'] for x in reg}=={x['source_id'] for x in after['sources']}
old=next(x for x in before['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor'];cur=next(x for x in after['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor']
for key in ['processed_native_ids','delivered_native_ids','held_native_ids']:assert set(old[key])<=set(cur[key])
assert cur['next_discovery_page']==cur['next_page_after_pending']==13
rows=load(E/'page-twelve-editorial-dispositions.json')['rows'];assert len(rows)==24 and sum(x['outcome']=='verified_new_illustrated_artwork' for x in rows)==10
assert len(load(W/'actual-visual-review.json')['decisions'])==10
files=[ROOT/x for x in cp['evidence_paths']]+[E/'CHECKPOINT.json',E/'batch-summary.json']
assert all(p.is_file() for p in files)
report=dict(at=now,passed=True,verified_counts=cp['verified_counts'],metadata_plan_sha256=cp['metadata_plan_sha256'],image_selection_sha256=cp['image_selection_sha256'],evidence_files=[ref(p) for p in files],source_captures_verified=25,prior_reserve_decisions_and_files_verified=188,immutable_historical_plans_verified=True,recovery_file_hashes_verified=True,checkpoint_runtime_copy_equal=True,queue_entries=111,unrelated_queue_entries_preserved=109,all_prior_warsaw_processed_delivered_and_held_ids_preserved=True,new_primary_images=10,individually_viewed_originals=10,individually_viewed_derivatives=10,production_attribution_and_public_receipts_consistent=True,new_increments_on_resume=0)
save(E/'independent-final-checkpoint-verification.json',report)
summary=load(E/'batch-summary.json');start=datetime.datetime.fromisoformat(load(E.parents[1]/'CHECKPOINT.json')['started_at']);end=datetime.datetime.fromisoformat(cp['finished_at'])
save(E/'milestone-report.json',dict(at=now,milestone='100th bounded programme batch',batch_runtime_seconds=cp['measured_runtime_seconds'],programme_elapsed_seconds=(end-start).total_seconds(),current_batch_independently_verified=cp['verified_counts'],reported_programme_cumulative_counts=summary['recorded_cumulative_after_batch'],cumulative_scope='Prior supervisor totals plus independently verified current increments; does not re-audit earlier campaigns or recount live catalogue.',next_task=cp['next_task'],failures=load(E/'failure-ledger.json'),holds=ref(E/'research-holds.json'),continuation='Existing external supervisor owns next bounded run; it was neither launched nor modified here. No 100-hour stopping rule.'))
print(json.dumps(dict(passed=True,verified_counts=cp['verified_counts'],source_captures=25,unrelated_routes_preserved=109,resume_new_increments=0)))
