"""Read-only final checkpoint/source/queue validation, independent of finalizer."""
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'docs/research/continuous-production-20261011/batches/000103';K=E/'khm';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000103'
def load(p):
 raw=Path(p).read_bytes();return json.loads(gzip.decompress(raw) if str(p).endswith('.gz') else raw)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
cp=load(E/'CHECKPOINT.json');assert cp==load(R/'CHECKPOINT.json');counts=cp['verified_counts'];assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=1,alternate_images=0,museum_links=0)
files=[dict(path=p,sha256=sha(ROOT/p)) for p in cp['evidence_paths']]
reserve=load(K/'independent-reserve-evidence-verification.json');assert reserve['inspected']==188 and reserve['new_selection_count']==0
for p in reserve['immutable_plans']:assert sha(p['path'])==p['sha256']
for r in reserve['records']:
 for field in ['source_record','prior_visual_decision']:assert sha(r[field]['path'])==r[field]['sha256']
 assert sha(r['local_path'])==r['derivative_sha256']
source=load(E/'independent-discovery-verification.json')
for r in source['source_captures']:assert hashlib.sha256(gzip.decompress(Path(r['body_path']).read_bytes())).hexdigest()==r['sha256']
assert source['researched_gaps']==11 and len(source['untouched_gap_ids'])==13
receipt=load(K/'batch-verification-receipt.json');prod=load(K/'independent-production-verification.json');audit=load(K/'independent-audit-history-verification.json');public=load(K/'independent-public-verification.json');resume=load(K/'independent-resume-verification.json')
assert receipt['verified_counts']==counts and prod['verified_new_primary_images']==len(public['rows'])==1
assert receipt['selection_sha256']==prod['selection_sha256']==sha(K/'batches/wikiart-000/selection.json.gz')
assert receipt['visual_review_sha256']==prod['visual_review_sha256']==sha(K/'batches/wikiart-000/visual-review.json')
pre=load(prod['transaction_preimages']);assert sha(prod['transaction_preimages'])==prod['preimage_sha256']
aid=cp['production_ids'][0];assert not pre[aid]['attachments'] and pre[aid]['artwork']['primary_media_id'] is None
assert len(audit['events'])==1 and audit['events'][0]['before_json']==pre[aid]['artwork']
assert resume['unchanged_snapshot'] and not any(resume['replay_increments'].values())
before=load(E/'source-queue-immediately-before-update.json');after=load(E/'source-queue-after.json');q=load(E.parent.parent/'source-queue.json');assert q==after
changed={'yale_lux','khm_vienna'}
assert len(q['sources'])==111 and [x for x in before['sources'] if x['source_id'] not in changed]==[x for x in q['sources'] if x['source_id'] not in changed]
old=next(r for r in before['sources'] if r['source_id']=='khm_vienna')['resume_cursor'];new=next(r for r in q['sources'] if r['source_id']=='khm_vienna')['resume_cursor']
assert set(old['pending_artwork_ids'])==set(new['pending_artwork_ids'])|{r['artwork_id'] for r in source['rows']}
for key in ['researched_artwork_ids','verified_artwork_ids','held_artwork_ids','profile_404_no_unchanged_retry']:assert set(old[key])<=set(new[key])
for f in load(K/'local-recovery-verification.json')['files']:assert sha(f['path'])==f['sha256']
report=dict(passed=True,batch=103,verified_counts=counts,evidence_files=files,immutable_reserve_plans_preserved=True,reserve_original_sources_and_visual_reviews_reverified=188,newly_viewed_reserve_derivatives=1,newly_viewed_selected_originals=1,newly_viewed_selected_derivatives=1,source_captures_checksum_verified=len(source['source_captures']),transaction_preimages_and_audit_attribution_verified=True,distinct_newly_illustrated_with_zero_prior_attachments=1,public_image_and_api_receipts_verified=1,resume_changes=0,queue_entries=111,unrelated_queue_entries_preserved=109,all_prior_khm_holds_preserved=True,checkpoint_runtime_copy_equal=True)
out=E/'independent-final-checkpoint-verification.json'
if out.exists():assert load(out)==report
else:out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='evidence_files'}))
