#!/usr/bin/env python3
"""Independent persisted-file/receipt consistency checks; no production writes."""
import csv,datetime,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'docs/research/continuous-production-20261011/batches/000102';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000102'
def load(p):
 p=Path(p);raw=p.read_bytes();return json.loads(gzip.decompress(raw) if p.suffix=='.gz' else raw)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
cp=load(E/'CHECKPOINT.json');assert cp==load(R/'CHECKPOINT.json')==load(E/'stage-checkpoints/02-independently-verified.json')
receipt=load(E/'batch-verification-receipt.json');counts=dict(new_painters=0,new_artworks=9,newly_illustrated=0,alternate_images=0,museum_links=9)
assert cp['verified_counts']==receipt['verified_counts']==counts
prod=load(E/'independent-production-verification.json');audit=load(E/'independent-audit-history-verification.json');public=load(E/'independent-public-verification.json');resume=load(E/'independent-resume-verification.json')
assert len(prod['rows'])==len(audit['inserts'])==len(public['rows'])==9
assert set(prod['rows'])==set(cp['production_ids'])=={x['artwork_id'] for x in public['rows']}
assert prod['plan_sha256']==cp['plan_sha256']==sha(E/'painted-icons/plan.json.gz')
assert prod['preimages_sha256']==sha(prod['transaction_preimages']) and load(prod['transaction_preimages'])['artworks']=={}
assert resume['unchanged_snapshot'] and all(x==0 for x in resume['replay_increments'].values())
assert all(x['note']['plan_sha256']==cp['plan_sha256'] for x in prod['citations'])
assert all(x['action']=='insert' and x['before_json'] in [None,{}] for x in audit['inserts'])
for r in load(E/'independent-source-verification.json')['records']:
 p=E/'selected-source-records'/(r['native_id']+'.json');assert sha(p)==r['source_sha256']
for f in load(E/'immutable-source-reuse-verification.json')['files']:
 raw=gzip.decompress(Path(f['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==f['sha256'] and len(raw)==f['bytes']
for f in load(E/'local-recovery-verification.json')['files']:assert sha(f['path'])==f['sha256']
before=load(E/'source-queue-immediately-before-update.json');after=load(E.parents[1]/'source-queue.json');assert after==load(E/'source-queue-after.json')
assert [r for r in before['sources'] if r['source_id']!='walters_art_museum']==[r for r in after['sources'] if r['source_id']!='walters_art_museum']
old=next(r for r in before['sources'] if r['source_id']=='walters_art_museum');cur=next(r for r in after['sources'] if r['source_id']=='walters_art_museum')
assert old['resume_cursor'] in cur['prior_resume_cursors'] and old['access_holds']==cur['access_holds']
reg=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')))
assert len(reg)==len(after['sources'])==111 and {r['source_id'] for r in reg}=={r['source_id'] for r in after['sources']}
assert len(cur['resume_cursor']['verified_native_ids'])==9 and len(cur['resume_cursor']['held_native_ids'])==8
assert load(E/'actual-visual-review.json')['actually_viewed']==[]
files=[ROOT/p for p in cp['evidence_paths']]+[E/'CHECKPOINT.json',E/'batch-summary.json',E/'milestone-report.json']
assert all(p.is_file() for p in files)
report=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,verified_counts=counts,plan_sha256=cp['plan_sha256'],evidence_files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size) for p in files],source_capture_hashes_verified=True,recovery_file_hashes_verified=True,checkpoint_runtime_copy_equal=True,queue_entries=111,unrelated_queue_entries_preserved=110,prior_source_cursor_and_access_holds_preserved=True,production_source_plan_preimage_and_audit_attribution_consistent=True,public_review_rows_verified=9,images_prepared_or_claimed_viewed=0,new_increments_on_resume=0)
path=E/'independent-final-checkpoint-verification.json'
if path.exists():
 oldreport=load(path);assert {k:v for k,v in oldreport.items() if k!='at'}=={k:v for k,v in report.items() if k!='at'}
else:path.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(dict(passed=True,verified_counts=counts,unrelated_routes_preserved=110,resume_new_increments=0)))
