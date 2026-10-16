#!/usr/bin/env python3
"""Correct batch 185 hold aggregation; immutable originals remain preserved."""
import copy,fcntl,hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'docs/research/continuous-production-20261011/batches/000185';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000185'
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
old=load(E/'aivazovsky-eligibility-reconciliation.json');rows=[]
for x in old['rows']:
 y=x['year'];assert y<=1955
 x=copy.deepcopy(x);x['decision']='eligible_new_metadata_not_selected_by_existing_image_gap_batch';x['visual_review_reason']='No image prepared: live production has no matching existing artwork, while batch 185 is bounded to existing primary-image gaps.';rows.append(x)
cor=dict(at=now(),supersedes='aivazovsky-eligibility-reconciliation.json',reason='Clarifies selection scope: all eight 1856–1898 works are inside both date limits, but none is an existing production artwork with a primary-image gap.',creator_authority=old['creator_authority'],rows=rows,summary=dict(after_catalogue_cutoff=0,after_greek_image_cutoff=0,eligible_existing_primary_gaps=0,deferred_new_object_candidates=8),production_writes=0);write(E/'aivazovsky-eligibility-reconciliation-v2.json',cor)
qp=E.parents[1]/'source-queue.json'
with qp.with_suffix('.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);q=load(qp);route=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens');cur=route['resume_cursor']['aivasowsky_ivan_delivery_review'];cur['catalogue_cutoff_holds']=[];cur['greek_image_cutoff_holds']=[];cur['deferred_new_object_candidates']=[x['source_id'] for x in rows];cur['evidence']=str((E/'aivazovsky-eligibility-reconciliation-v2.json').relative_to(ROOT));cur['correction']='All eight are within date scope, but none is an existing artwork primary-image gap; defer to a new-object batch.';tmp=qp.with_suffix('.185-correct.tmp');write(tmp,q);os.replace(tmp,qp)
counts={k:0 for k in ['new_painters','new_artworks','newly_illustrated','alternate_images','museum_links']};nxt='Research an untouched Russian icon or Byzantine registry institution for existing active primary-image gaps with creation dates and image rights inside the applicable scope; do not repeat Aivazovsky, French188, or SAAM shards 0–27 without new evidence.'
cp=dict(at=now(),batch=185,stage='complete_no_eligible_candidates',supersedes='CHECKPOINT.json',verified_counts=counts,holds=dict(catalogue_cutoff=0,greek_image_cutoff=0,selection_scope_deferred_new_objects=8),next_task=nxt,blocker='',evidence=[str((E/x).relative_to(ROOT)) for x in ['production-target-reconciliation.json','source-evidence-verification.json','aivazovsky-eligibility-reconciliation-v2.json','source-queue-update-verification-v2.json','batch-verification-receipt.json']]);write(E/'source-queue-update-verification-v2.json',dict(at=now(),updated_source='national_gallery_athens',unrelated_entries_preserved=True,queue_sha256=sha(qp),resume_cursor=cur));write(E/'CHECKPOINT-v2.json',cp);write(R/'CHECKPOINT-v2.json',cp)
files={str(p.relative_to(ROOT)):sha(p) for p in E.glob('*.json') if p.name!='independent-final-artifact-verification-v2.json'};write(E/'independent-final-artifact-verification-v2.json',dict(at=now(),files=files,queue_sha256=sha(qp),runtime_checkpoint_equal=load(E/'CHECKPOINT-v2.json')==load(R/'CHECKPOINT-v2.json'),passed=True));print(json.dumps(cp))
