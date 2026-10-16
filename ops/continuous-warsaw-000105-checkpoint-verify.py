#!/usr/bin/env python3
"""Independent persisted-checkpoint and source-capture verification; no writes to production."""
import csv,datetime,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000105';W=E/'warsaw'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000105'
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
assert cp['verified_counts']==receipt['verified_counts']==dict(new_painters=0,new_artworks=3,newly_illustrated=3,alternate_images=0,museum_links=3)
production=load(W/'independent-production-verification.json');audit=load(W/'independent-audit-history-verification.json');public=load(W/'independent-public-verification.json');storage=load(W/'independent-storage-verification.json');resume=load(W/'independent-resume-verification.json')
assert len(production['rows'])==len(audit['inserts'])==len(public['rows'])==len(storage['checks'])==3
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
for p in [W/'warsaw-icons-page13.receipt.json']+sorted(W.glob('object-*.receipt.json')):
 r=load(p);data=gzip.decompress(Path(r['body_path']).read_bytes());assert r['status']==200 and hashlib.sha256(data).hexdigest()==r['sha256'] and len(data)==r['bytes'];captures.append(ref(p))
assert len(captures)==19
before=load(E/'source-queue-immediately-before-update.json');after=load(E.parents[1]/'source-queue.json');assert after==load(E/'source-queue-after.json')
touched={'national_museum_warsaw'}
assert [x for x in before['sources'] if x['source_id'] not in touched]==[x for x in after['sources'] if x['source_id'] not in touched]
reg=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')))
assert len(reg)==len(after['sources'])==111 and {x['source_id'] for x in reg}=={x['source_id'] for x in after['sources']}
old=next(x for x in before['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor'];cur=next(x for x in after['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor']
for key in ['processed_native_ids','delivered_native_ids','held_native_ids']:assert set(old[key])<=set(cur[key])
assert cur['next_discovery_page'] is None and cur['next_page_after_pending'] is None and cur['query_exhausted'] and cur['captured_page']==13
rows=load(E/'page-thirteen-editorial-dispositions.json')['rows'];assert len(rows)==18 and sum(x['outcome']=='verified_new_illustrated_artwork' for x in rows)==3
assert len(load(W/'actual-visual-review.json')['decisions'])==3
files=[ROOT/x for x in cp['evidence_paths']]+[E/'CHECKPOINT.json',E/'batch-summary.json']
assert all(p.is_file() for p in files)
report=dict(at=now,passed=True,verified_counts=cp['verified_counts'],metadata_plan_sha256=cp['metadata_plan_sha256'],image_selection_sha256=cp['image_selection_sha256'],evidence_files=[ref(p) for p in files],source_captures_verified=19,recovery_file_hashes_verified=True,checkpoint_runtime_copy_equal=True,queue_entries=111,unrelated_queue_entries_preserved=110,all_prior_warsaw_processed_delivered_and_held_ids_preserved=True,new_primary_images=3,individually_viewed_originals=3,individually_viewed_derivatives=3,production_attribution_and_public_receipts_consistent=True,new_increments_on_resume=0)
save(E/'independent-final-checkpoint-verification.json',report)
summary=load(E/'batch-summary.json');start=datetime.datetime.fromisoformat(load(E.parents[1]/'CHECKPOINT.json')['started_at']);end=datetime.datetime.fromisoformat(cp['finished_at'])
save(E/'milestone-report.json',dict(at=now,milestone='Batch 105 bounded completion; not a 100-hour milestone',batch_runtime_seconds=cp['measured_runtime_seconds'],programme_elapsed_seconds=(end-start).total_seconds(),current_batch_independently_verified=cp['verified_counts'],reported_programme_cumulative_counts=summary['recorded_cumulative_after_batch'],cumulative_scope='Prior supervisor totals plus independently verified current increments; does not re-audit earlier campaigns or recount live catalogue.',next_task=cp['next_task'],failures=load(E/'failure-ledger.json'),holds=ref(E/'research-holds.json'),continuation='Existing external supervisor owns next bounded run; it was neither launched nor modified here. No 100-hour stopping rule.'))
print(json.dumps(dict(passed=True,verified_counts=cp['verified_counts'],source_captures=19,unrelated_routes_preserved=110,resume_new_increments=0)))
