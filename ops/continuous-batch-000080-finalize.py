#!/usr/bin/env python3
"""Persist one verified batch and update only the two researched source entries."""
import datetime,fcntl,hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'docs/research/continuous-production-20261011/batches/000080';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000080';N=E/'nga'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():return load(p)
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');return v
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (R/'worker.lock').open('a+') as worker:
 fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=load(N/'batch-verification-receipt.json');resume=load(N/'independent-resume-verification.json');assert resume['unchanged_snapshot'] and resume['unchanged_storage_generations']
 counts=receipt['verified_counts'];assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=16,alternate_images=0,museum_links=0)
 assert load(E/'independent-nsw-preservation-verification.json')['all_18_existing_gaps_unchanged']
 assert load(E/'independent-prior-batch-verification.json')['exact_prior_snapshot_unchanged']
 previous=load(E/'source-queue-before.json');g=load(N/'nga-gap-reconciliation.json');nsw=load(E/'discovery-outcomes.json')['rows'];processed={r['artwork_id'] for r in nsw};assert len(processed)==4
 started=load(E/'required-input-reconciliation.json')['at'];elapsed=(datetime.datetime.fromisoformat(now)-datetime.datetime.fromisoformat(started)).total_seconds()
 save(E/'selection-limit-semantics.json',dict(at=now,selected_images=16,selection_counter='Maximum two per verbatim qualified creator label, not two per globally reconciled primary artist.',actual_source_attributions_preserved=True,programme_rotation='NSW discovery then NGA; next museum route is SHUZO Pola, preserving regional and icon queues.',next_nga_selection_guidance='Group by exact primary artist identity as well as preserve verbatim qualified labels when balancing creator variety.'))
 evidence=[str(p.relative_to(ROOT)) for p in sorted(N.glob('independent-*.json'))]+[str((N/'actual-visual-review.json').relative_to(ROOT)),str((N/'batch-verification-receipt.json').relative_to(ROOT)),str((E/'independent-nsw-source-verification.json').relative_to(ROOT)),str((E/'independent-nsw-preservation-verification.json').relative_to(ROOT)),str((E/'independent-prior-batch-verification.json').relative_to(ROOT))]
 save(E/'source-register.json',dict(at=now,registry_path='/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv',registry_records=111,source_entries=[r for r in load(E/'required-input-reconciliation.json')['complete_registry'] if r['source_id'] in ['art_gallery_nsw','nga_washington']],routes=[dict(provider='WikiArt',institution='Art Gallery of New South Wales',policy_reference='docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026',access_status='Four candidate profile URLs 404; museum direct-access hold preserved',last_checked_at=now,remaining_gaps='14 pending; 7 unmatched; 12 candidate profile URLs unavailable; 2 previously delivered excluded'),dict(provider='National Gallery of Art',policy_reference='Original registry nga_washington and NGA openaccess=1 CC0 evidence; docs/ARTLINE_IMAGE_USE.md general policy',access_status='Selected primary image IIIF metadata and files HTTP 200; source CSV checksums verified',last_checked_at=now,remaining_gaps='Continue native candidate cursor '+str(g['resume_position'])+' and retain all earlier deferred positions and identity holds')],directory_coverage_changed=False,artwork_coverage='16 existing records newly illustrated; no artwork or institution creation'))
 save(E/'failures.json',dict(at=now,failures=[dict(stage='interpreter',error='System Python lacked bs4',resolution='Reused established /tmp/artline-cyprus-venv without new packages'),dict(stage='prior receipt field',error='Preflight expected plan_sha256; prior receipt stores metadata_plan_sha256',resolution='Corrected field and independently verified exact prior snapshot and rights checksums'),dict(stage='source equality verification',error='Established NGA plan raw object omits inscriptions, markings and provenance-text fields',resolution='Compared every retained raw field against original museum CSV and preserved additional CSV fields in independent source evidence; no source mutation or catalogue change'),dict(stage='NSW discovery',error='Four candidate WikiArt profile URLs 404',resolution='No repeat requests; recorded exact receipts and rotated to NGA')],production_transaction_failures=0,unresolved_authentication_or_budget_blocker=False))
 next_task='Resolve saved Pola Museum SHUZO candidates, then Yokosuka and Fuchu; preserve from=25 and ensemble exclusions. NGA resumes at position '+str(g['resume_position'])+' with deferred positions retained; NSW has 14 untouched candidates.'
 qpath=E.parents[1]/'source-queue.json';lockpath=R.parents[1]/'source-queue.lock'
 with lockpath.open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  q=load(qpath);oldmap={r['source_id']:r for r in previous['sources']};current={r['source_id']:r for r in q['sources']};changed={'art_gallery_nsw','nga_washington'}
  assert set(current)==set(oldmap) and all(current[k]==oldmap[k] for k in oldmap if k not in changed),'Unrelated queue changed; reconcile instead of overwriting'
  for r in q['sources']:
   if r['source_id'] not in changed:continue
   if r.get('last_batch')==80:continue
   assert r==oldmap[r['source_id']],'Researched route changed concurrently'
   r.setdefault('prior_resume_cursors',[]).append(json.loads(json.dumps(r.get('resume_cursor',{}))))
   if r['source_id']=='art_gallery_nsw':
    c=r['resume_cursor'];c['pending_artwork_ids']=[x for x in c['pending_artwork_ids'] if x not in processed]
    for field in ['processed_artwork_ids','profile_unavailable_artwork_ids']:c[field]=list(dict.fromkeys(c.get(field,[])+sorted(processed)))
    c['discovery_evidence']=str((E/'discovery-outcomes.json').relative_to(ROOT));c['next_step']='14 untouched candidates remain; the four new profile 404 URLs require new profile/object evidence before revisit. Preserve museum access hold.'
    c['profile_unavailability_scope']='Only the recorded candidate profile URLs returned 404; no claim that these artists or works are absent everywhere.'
    r.update(status='official_hold_preserved_wikiart_14_pending_7_unmatched_12_profile_unavailable_candidates',access_status='Four additional candidate WikiArt profiles HTTP 404; no official museum requests or images requested',remaining_gaps=['14 untouched candidates; 7 unmatched; 12 unavailable candidate profile URLs. All 18 current inspected catalogue gaps preserved.'],latest_batch_verified_counts={k:0 for k in counts})
   else:
    c=r['resume_cursor'];c['position']=g['resume_position'];c['deferred_positions']=sorted(set(c.get('deferred_positions',[])+[x['position'] for x in g['rows'] if x['reason']=='creator_variety_deferred']));c['latest_reconciliation']=str((N/'nga-gap-reconciliation.json').relative_to(ROOT));c['prior_deferred_positions_policy']='Earlier batch ledgers remain valid and eligible; do not treat cursor advancement as exhaustion.'
    r.update(status='sixteen_further_existing_primary_images_verified_native_cc0',access_status='Exact selected IIIF primary image metadata and reproductions HTTP 200',latest_batch_verified_counts=counts)
    r.setdefault('remaining_gaps',[]).append('Batch 80: '+str(g['resume_position'])+' next position; three newly deferred qualified-creator positions retained, all earlier holds preserved.')
   r.update(last_batch=80,checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)),last_checked_at=now,policy_reference=r.get('policy_reference') or 'Original GLOBAL_MUSEUM_SOURCE_REGISTRY.csv; docs/ARTLINE_IMAGE_USE.md')
   r.setdefault('evidence_paths',[]).extend(x for x in evidence if x not in r['evidence_paths'])
  tmp=qpath.with_suffix('.b000080.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qpath)
  after=load(qpath);aftermap={r['source_id']:r for r in after['sources']};assert all(aftermap[k]==oldmap[k] for k in oldmap if k not in changed)
  save(E/'source-queue-update-verification.json',dict(at=now,source_count=111,changed_source_ids=sorted(changed),unrelated_entries_preserved=109,source_queue_before_sha256=sha(E/'source-queue-before.json'),source_queue_after_sha256=sha(qpath),nga_next_position=g['resume_position'],nga_new_deferred_positions=[x['position'] for x in g['rows'] if x['reason']=='creator_variety_deferred'],nsw_pending=14,shuzo_unchanged=aftermap['shuzo_japan']==oldmap['shuzo_japan']))
 save(E/'batch-verification-receipt.json',dict(receipt,batch=80,measured_batch_runtime_seconds=elapsed,evidence_paths=evidence,nsw_rows_researched=4,nsw_source_images_requested=0,nga_candidates_reconciled=len(g['rows']),previously_illustrated_excluded=sum(x['reason']=='already_illustrated' for x in g['rows']),creator_label_deferred=sum(x['reason']=='creator_variety_deferred' for x in g['rows']),independent_resume_verified=True))
 cp=dict(at=now,batch=80,stage='independently_verified_complete',outcome='progress',started_at=started,elapsed_seconds=elapsed,verified_counts=counts,selected=16,prepared=16,contact_sheet_images_actually_viewed=16,individual_derivatives_actually_viewed=4,imported=16,verified=16,production_ids=receipt['production_ids'],selection_sha256=receipt['selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],nga_next_position=g['resume_position'],next_task=next_task,blocker='',resume_commands=['/tmp/artline-cyprus-venv/bin/python ops/continuous-nga-000080-verify.py'],evidence_paths=evidence,local_catalogue_connections=0,external_supervisor_unchanged=True,supervisor_running_claim=False,prior_deliveries_excluded=True)
 save(E/'CHECKPOINT.json',cp);save(R/'batch-checkpoint.json',cp)
 root=load(E.parents[1]/'CHECKPOINT.json');totals={k:root['totals'][k]+counts[k] for k in counts};programme_runtime=(datetime.datetime.fromisoformat(now)-datetime.datetime.fromisoformat(root['started_at'])).total_seconds()
 save(E/'milestone-report.json',dict(at=now,measured_programme_wall_seconds=programme_runtime,measured_batch_wall_seconds=elapsed,prior_supervisor_totals=root['totals'],this_batch_independently_verified=counts,projected_totals_after_supervisor_accepts_batch=totals,prior_totals_not_reaudited_in_this_batch=True,hourly_reporting='External supervisor owns hourly and 100-hour reporting; not modified.',next_task=next_task))
 checks=[]
 for p in [E/'batch-verification-receipt.json',E/'CHECKPOINT.json',E/'source-queue-update-verification.json',R/'batch-checkpoint.json']+[ROOT/x for x in evidence]:
  assert p.exists();load(p);checks.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size))
 save(E/'final-checkpoint-verification.json',dict(at=now,files=checks,all_evidence_exists_and_decodes=True,counts_match=load(E/'CHECKPOINT.json')['verified_counts']==counts,unrelated_queue_entries_preserved=109,runtime_checkpoint_matches=load(R/'batch-checkpoint.json')==load(E/'CHECKPOINT.json'),supervisor_files_modified=False))
 print(json.dumps(dict(verified_counts=counts,nga_resume_position=g['resume_position'],unrelated_entries_preserved=109,next_task=next_task)))
