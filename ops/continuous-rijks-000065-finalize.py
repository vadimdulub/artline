#!/usr/bin/env python3
"""Persist verified batch 65 and advance only its researched source route."""
import copy,datetime,fcntl,gzip,hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/research/continuous-production-20261011';E=BASE/'batches/000065';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000065'
def load(p):
 p=Path(p);raw=p.read_bytes();return json.loads(gzip.decompress(raw) if p.suffix=='.gz' else raw)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);raw=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode();p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw,'Immutable evidence differs: '+str(p)
 else:
  with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def atomic(p,v):
 tmp=p.with_suffix('.final.tmp')
 with tmp.open('w') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def rel(p):return str(Path(p).relative_to(ROOT))
def main():
 if (E/'final-checkpoint-verification.json').exists():
  for f in load(E/'final-checkpoint-verification.json')['files']:assert sha(f['path'])==f['sha256']
  assert load(R/'CHECKPOINT.json')==load(E/'CHECKPOINT.json');print('Final checkpoint and evidence verified; no repeated queue update.');return
 receipt=load(E/'batch-verification-receipt.json');counts=receipt['verified_counts'];ids=receipt['production_ids']
 assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=16,alternate_images=0,museum_links=0) and len(set(ids))==16
 resume=load(E/'independent-resume-verification.json');assert resume['unchanged_snapshot'] and resume['audit_events_before']==resume['audit_events_after'] and not any(resume['replay_increments'].values())
 now=datetime.datetime.now(datetime.timezone.utc);at=now.isoformat();checks=load(E/'reserve-reconciliation.json')
 pending=[r for r in checks['rows'] if r['artwork_id'] not in ids];assert len(pending)==384
 variety=[r for r in pending if r['reason']=='creator_variety_deferred'];creators=[r for r in pending if r['reason']=='New creator reconciliation required'];assert len(variety)==210 and len(creators)==174
 save(E/'research-dispositions.json',dict(at=at,existing_reserve_rows_examined=400,selected_and_verified=16,creator_variety_deferred=variety,creator_link_reconciliation_pending=creators,interpretation='The 174 linked-creator rows require a link-aware precondition check; this is not evidence that their attribution is wrong or that their provider is held. None were downloaded or mutated. All pending positions remain resumable.',new_provider_access_holds=[],prior_provider_holds_preserved=True))
 save(E/'failures.json',dict(at=at,failures=[dict(stage='preparation',reason='Adapter initially used medium instead of medium_text. Corrected before any writes; diagnostic evidence preserved. No provider retry.',evidence=rel(E/'diagnostics/field-name-correction/failure.json'),resolved=True)],unresolved_execution_failures=0,provider_retries=0,new_provider_downloads=0,paid_services_started=0,cloud_backups_created=0))
 reg=load(E/'required-input-reconciliation.json');selection=load(E/'batches/rijks-065/selection.json.gz');dates=sorted(set(r['image']['receipt']['retrieved_at'] for r in selection['rows']))
 save(E/'source-register-final.json',dict(at=at,registry_path=reg['registry_path'],registry_sha256=reg['registry_sha256'],original_registry_records=111,source=next(r for r in reg['complete_registry'] if r['source_id']=='rijksmuseum'),policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='Archived official OAI records and native IIIF photographs checksum-verified; no provider downloads or source-access retries. All 16 local derivatives individually viewed, attached, and verified from production storage and public delivery.',source_capture_dates=dates,last_checked_at=at,source_images_actual_rights='Public Domain Mark 1.0 per exact native reproduction record',user_approval='Current user explicitly authorizes production primary-image enrichment; recorded separately and not represented as a copyright-holder licence.',source_records_examined=400,selected=16,prepared=16,verified_primary_images=16,resume_position=500,pending_positions=384,remaining_gaps='210 creator-variety deferrals and 174 linked-creator preconditions; unexamined reserve positions 500 onward. Earlier cursor history and all source holds retained.',directory_coverage_complete=False,artwork_coverage_complete=False))
 save(E/'web-source-documentation-check.json',dict(at=at,url='https://data.rijksmuseum.nl/',tool='web.run open',result='Official source documentation accessible; supports object metadata and photographic open-data discovery. Delivery eligibility rests on each archived record, not a blanket inference.',other_url='https://data.rijksmuseum.nl/docs/api/iiif',other_result='Internal web-tool access error for this documentation path; no source access hold or image failure inferred; no retry.'))
 evidence=['batch-verification-receipt.json','independent-production-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-audit-history-verification.json','independent-resume-verification.json','actual-visual-review.json','local-recovery-verification.json','source-register-final.json','research-dispositions.json','reserve-evidence-reuse.json','prior-batch-live-reconciliation.json']
 for f in evidence:assert (E/f).exists()
 with (R.parent.parent/'source-queue.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);path=BASE/'source-queue.json';raw=path.read_bytes();q=json.loads(raw);before=copy.deepcopy(q)
  save(E/'source-queue-immediately-before-update.json',before)
  route=next(s for s in q['sources'] if s['source_id']=='rijksmuseum');old=copy.deepcopy(route['resume_cursor'])
  assert old==dict(reserve_batch='rijks-044',position=100),'Route advanced elsewhere; reconcile instead of overwriting'
  route.setdefault('prior_resume_cursors',[]).append(old)
  cursor=dict(reserve_batch='rijks-044',position=500,pending_positions=[r['position'] for r in pending],creator_variety_deferred_positions=[r['position'] for r in variety],creator_link_review_positions=[r['position'] for r in creators],processed_positions=[r['position'] for r in checks['rows']],delivered_positions=[r['position'] for r in checks['rows'] if r['artwork_id'] in ids],delivered_artwork_ids=ids,disposition_ledger=rel(E/'research-dispositions.json'),retry_semantics='Do not replay delivered objects. Deferred positions remain eligible after their specific preconditions; positions 500 onward are unexamined. Use a separate continuation campaign, preserving completed campaign stop files.')
  route.update(status='sixteen_further_existing_primary_gaps_verified_384_positions_deferred',checkpoint=rel(E/'CHECKPOINT.json'),last_checked_at=at,verified_counts=counts,latest_batch_verified_counts=counts,resume_cursor=cursor,access_status='Pinned OAI records and native Public Domain Mark images verified; no new provider requests.',latest_attempt=dict(batch=65,at=at,outcome='progress',verified_counts=counts))
  route['evidence_paths']=list(dict.fromkeys(route.get('evidence_paths',[])+[rel(E/f) for f in evidence]))
  route.setdefault('research_history',[]).append(dict(batch=65,at=at,existing_gaps_examined=400,selected=16,verified_counts=counts,deferred_positions=384,evidence=rel(E/'batch-verification-receipt.json')))
  route['remaining_gaps']=['Reserve positions 500 onward unexamined; 210 earlier creator-variety deferrals and 174 linked-creator checks remain explicitly queued. No exhaustive collection coverage claim.']
  unchanged=[s for s in q['sources'] if s['source_id']!='rijksmuseum'];assert len(unchanged)==110 and unchanged==[s for s in before['sources'] if s['source_id']!='rijksmuseum']
  assert len(q['sources'])==111 and {s['source_id'] for s in q['sources']}=={s['source_id'] for s in reg['complete_registry']} and path.read_bytes()==raw
  atomic(path,q);save(E/'source-queue-after.json',q)
  save(E/'source-queue-update-verification.json',dict(at=at,before_sha256=hashlib.sha256(raw).hexdigest(),after_sha256=sha(path),modified_source_ids=['rijksmuseum'],unrelated_entries_preserved=110,all_111_registry_routes_preserved=True,delivered_positions=len(cursor['delivered_positions']),pending_positions=384,frontier_position=500,all_400_positions_dispositioned=True))
 root=load(BASE/'CHECKPOINT.json');start=root['inflight']['started_at'];elapsed=(now-datetime.datetime.fromisoformat(start)).total_seconds()
 nxt='Research the saved Warsaw icon page 5, preserving all 47 prior holds. For the next Rijks image batch use reserve position 500 onward or the explicitly saved 384 deferred positions; reconcile linked creators before attachment. French reserves remain exhausted.'
 cp=dict(at=at,started_at=start,elapsed_seconds=elapsed,batch=65,stage='independently_verified_complete',outcome='progress',verified_counts=counts,existing_reserve_gaps_examined=400,selected=16,prepared=16,individually_viewed=16,imported=16,verified=16,deferred=384,new_provider_image_downloads=0,production_ids=ids,selection_sha256=receipt['selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],source_queue_resume_cursor=cursor,next_task=nxt,blocker='',resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-rijks-000065-resume.py',verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-rijks-000065-verify.py',evidence_paths=[rel(E/f) for f in evidence]+[rel(E/'source-queue-update-verification.json')],local_catalogue_connections=0,external_supervisor_unchanged=True,supervisor_running_claim=False,hourly_reporting='External supervisor owns cumulative, hourly and 100-hour reporting; this worker executed one bounded batch.')
 save(E/'pre-delivery-checkpoint.json',load(E/'CHECKPOINT.json'));atomic(E/'CHECKPOINT.json',cp);atomic(R/'CHECKPOINT.json',cp);save(R/'verification-receipt.json',receipt)
 save(E/'batch-summary.json',dict(at=at,measured_elapsed_seconds=elapsed,verified_counts=counts,prior_campaign_increments=0,resolved_execution_failures=1,unresolved_execution_failures=0,unresolved_research_positions=384,next_task=nxt))
 save(E/'milestone-report.json',dict(at=at,batch=65,measured_batch_elapsed_seconds=elapsed,programme_started_at=root['started_at'],measured_programme_wall_seconds=(now-datetime.datetime.fromisoformat(root['started_at'])).total_seconds(),prior_supervisor_totals=root['totals'],independently_verified_batch_increment=counts,projected_totals_pending_supervisor_aggregation={k:root['totals'][k]+counts[k] for k in counts},supervisor_checkpoint_not_modified=True,one_hundred_hour_milestone_is_not_a_stop=True))
 manifest=[dict(path=str(p),sha256=sha(p)) for p in sorted(E.glob('*.json'))]
 save(E/'final-checkpoint-verification.json',dict(at=at,files=manifest,runtime_checkpoint_equal=load(R/'CHECKPOINT.json')==cp,evidence_paths_exist=all((ROOT/f).exists() for f in cp['evidence_paths']),final_counts_equal_independent_receipt=cp['verified_counts']==receipt['verified_counts'],external_supervisor_unchanged=True))
 print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,unrelated_queue_entries_preserved=110,next_task=nxt)))
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
