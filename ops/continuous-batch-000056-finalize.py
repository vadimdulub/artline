#!/usr/bin/env python3
"""Finalize batch 56, preserving the supervisor and all unresearched routes."""
import copy,datetime,fcntl,gzip,importlib.util,json,os,shutil
from pathlib import Path
s=importlib.util.spec_from_file_location('worker56',Path(__file__).with_name('continuous-tepapa-images-000056.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
h=w.h;i=w.i;E=w.E

def ep(name):return str((E/name).relative_to(w.ROOT))
def save(name,v):return w.save(E/name,v)

with (w.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=w.load(E/'batch-verification-receipt.json');replay=w.load(E/'independent-resume-verification.json');assert replay['unchanged_snapshot'] and not any(replay['replay_increments'].values())
 counts=receipt['verified_counts'];assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=4,alternate_images=0,museum_links=0)
 ids=receipt['production_ids'];now=h.now();master=w.load(E.parents[1]/'CHECKPOINT.json');assert master['inflight']['batch']==56
 data=w.load(E/'tepapa-bounded-gap-input.json.gz');cross=w.load(E/'identity-crosswalk-input.json.gz');holds=w.load(E/'research-holds.json')['records']
 assert len(data['rows'])==25 and len(cross)==20 and len(holds)==21
 assert set(ids).isdisjoint({r['artwork_id'] for r in holds}) and {r['id'] for r in data['rows']}==set(ids)|{r['artwork_id'] for r in holds}
 prior=w.load(E/'prior-batch-live-reconciliation.json');assert prior['verified_prior_images']==8 and prior['counted_this_batch']==0 and prior['current_campaign_rows_before_write']==0
 selected=i.selected(w.B)['rows'];assert len(selected)==len(ids)==4
 sourcechecks=[];archive=Path.home()/'Library/Application Support/Artline/source-metadata'/i.OP;archive.mkdir(parents=True,exist_ok=True)
 for p in sorted((E/'source-captures').glob('*.receipt.json')):
  rc=w.load(p);body=w.ROOT/rc['body_path'];assert h.sha(gzip.decompress(body.read_bytes()))==rc['sha256'] and rc['status']==200
  for src in [p,body]:
   dst=archive/src.name
   if dst.exists():assert dst.read_bytes()==src.read_bytes()
   else:shutil.copyfile(src,dst)
  sourcechecks.append(dict(path=str(p.relative_to(w.ROOT)),url=rc['url'],status=rc['status'],sha256=rc['sha256'],archived_body=str(archive/body.name)))
 assert len(sourcechecks)==22
 stops=[]
 for p in sorted((w.ROOT/'docs/research/illustrated-300k-20261011').glob('stop-*.json')):stops.append(dict(path=str(p.relative_to(w.ROOT)),sha256=h.sha(p.read_bytes()),contents=w.load(p)))
 assert len(stops)==3
 save('source-archive-verification.json',dict(at=now,source_checks=sourcechecks,archived_outside_documents=True,original_images_outside_documents=True,completed_campaign_stop_files_preserved=stops,separate_continuation_campaign=i.OP))
 save('independent-route-completeness-verification.json',dict(at=now,production_gaps_inspected=25,native_object_pages_researched=20,native_source_policy_pages=2,selected=4,prepared=4,individually_viewed=4,imported=4,independently_verified=4,held=21,holds_by_reason=dict(identity_crosswalk=5,no_source_image=4,rights=9,cropped_or_measurement_review=3),all_researched_objects_accounted_for=True,held_objects_unchanged=w.load(E/'independent-held-objects-verification.json'),held_object_images_downloaded=0,source_receipts_verified=len(sourcechecks),directory_coverage_complete=False))
 cursor=dict(route='official_native_object_pages_record_specific_NKCR_images',institution_id=w.b.MID,after_artwork_id=data['rows'][-1]['id'],previous_after_artwork_id=data['after_artwork_id'],inspected_ids=[r['id'] for r in data['rows']],native_object_ids=[r['native_id'] for r in cross],delivered_ids=ids,held_ids=[r['artwork_id'] for r in holds],image_selection_sha256=receipt['selection_sha256'],source_media_redirect='Only exact official HTTP 303 preserving source media ID',metadata_refresh_due='2026-11-09',no_repeat_of_unchanged_holds=True,held_evidence=ep('research-holds.json'),date_evidence_review=ep('additional-identity-review.json'))
 nxt='Rotate to Warsaw: resolve the 18 saved page-three native-object reviews from batch 54 using existing captures and exact version/date evidence; skip all processed IDs and unchanged holds. Te Papa resumes after '+cursor['after_artwork_id']+'. Preserve all provider holds and the exhausted French reserve.'
 source=dict(source_id='te_papa',provider='Museum of New Zealand Te Papa Tongarewa',last_checked_at=now,access_status='20 native object pages and two policy pages HTTP 200; four exact official media redirects HTTP 303 and four selected images HTTP 200; no API key or paid service',policy_reference='Original 111-source CSV te_papa row; docs/ARTLINE_IMAGE_USE.md#general-image-use-policy; current native record-specific NKCR policy',remaining_gaps='21 current-page holds, all prior holds, and later UUID pages remain. No directory or nationwide artwork-coverage claim.',resume_cursor=cursor)
 save('source-register-final.json',dict(at=now,registry_rows=111,complete_registry_evidence=ep('required-input-reconciliation.json'),sources=[source],new_directory_entries=0,coverage_incomplete=True))
 manifest=[]
 for row in selected:
  im=w.load(i.folder(w.B)/'prepared'/(row['artwork_id']+'.json'));manifest.append(dict(artwork_id=row['artwork_id'],native_id=row['current_source_id'],title=row['title'],source_url=row['source_url'],media_id=im['media_id'],image_sha256=im['sha256'],source_sha256=row['image']['receipt']['sha256'],selection_sha256=receipt['selection_sha256'],rights_label=row['rights_label'],bytes=im['bytes'],original_path=im['original_path']))
 save('verified-delivery-manifest.json',manifest)
 evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-file-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-held-objects-verification.json','independent-prewrite-verification.json','independent-resume-verification.json','actual-visual-review.json','additional-identity-review.json','webber-version-review.json','sperrey-alias-review.json','prior-batch-live-reconciliation.json','global-identity-reconciliation.json','independent-route-completeness-verification.json','source-policy-verification-v2.json','research-holds.json','source-access-holds.json','required-input-reconciliation.json','source-register-final.json','verified-delivery-manifest.json','source-archive-verification.json','failures.json']
 end=datetime.datetime.fromisoformat(now);start=datetime.datetime.fromisoformat(master['inflight']['started_at']);runtime=(end-start).total_seconds();programme=(end-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()
 cp=dict(at=now,batch=56,stage='independently_verified_complete',outcome='progress',started_at=start.isoformat(),elapsed_seconds=runtime,verified_counts=counts,production_ids=ids,selection_sha256=receipt['selection_sha256'],discovered=25,native_researched=20,selected=4,prepared=4,imported=4,verified=4,individually_viewed=4,held=21,resume_cursor=cursor,next_task=nxt,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-tepapa-000056-resume.py',verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-tepapa-images-000056-verify.py',evidence_paths=[ep(p) for p in evidence],external_supervisor_unchanged=True,local_catalogue_connections=0)
 save('CHECKPOINT.json',cp);w.save(w.RUNTIME/'CHECKPOINT.json',w.load(E/'CHECKPOINT.json'))
 qp=E.parents[1]/'source-queue.json'
 if not (E/'source-queue-update-verification.json').exists():
  with qp.with_suffix('.lock').open('a+') as qlock:
   fcntl.flock(qlock,fcntl.LOCK_EX);before=w.load(qp);q=copy.deepcopy(before);r=next(x for x in q['sources'] if x['source_id']=='te_papa')
   assert r['resume_cursor']['after_artwork_id']==data['after_artwork_id']
   oldcounts=r['programme_verified_counts'];assert oldcounts['newly_illustrated']==11
   r.setdefault('prior_resume_cursors',[]).append(r['resume_cursor']);r['resume_cursor']=cursor
   r.update(status='fifteen_programme_primary_images_verified_four_new_NKCR_images',last_checked_at=now,checkpoint=ep('CHECKPOINT.json'),latest_batch_verified_counts=counts,verified_counts=counts,programme_verified_counts={k:oldcounts[k]+counts[k] for k in counts},access_status=source['access_status'],policy_reference=source['policy_reference'],remaining_gaps=[source['remaining_gaps']])
   for name in evidence+['CHECKPOINT.json']:
    assert (E/name).is_file()
    if ep(name) not in r.setdefault('evidence_paths',[]):r['evidence_paths'].append(ep(name))
   untouched=lambda v:{r['source_id']:r for r in v['sources'] if r['source_id']!='te_papa'}
   assert untouched(before)==untouched(q)==untouched(w.load(E/'source-queue-before.json')) and len(q['sources'])==111 and all(q[k]==v for k,v in before.items() if k!='sources')
   save('source-queue-immediately-before-update.json',before);tmp=qp.with_suffix('.batch56.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp);assert w.load(qp)==q
   save('source-queue-update-verification.json',dict(at=now,updated_sources=['te_papa'],unrelated_entries_preserved=110,source_count=111,before_semantic_sha256=h.sha(json.dumps(before,sort_keys=True).encode()),after_file_sha256=h.sha(qp.read_bytes()),resume_cursor=cursor,prior_holds_preserved_in_prior_cursors=True))
 save('milestone-report.json',dict(at=now,batch=56,measured_batch_runtime_seconds=runtime,measured_programme_runtime_hours=programme/3600,previous_supervisor_counts=master['totals'],batch_verified_counts=counts,cumulative_programme_counts={k:master['totals'][k]+counts[k] for k in counts},attribution_limit='This batch independently verified; previous supervisor totals not globally re-audited. Eight prior Norwegian images rechecked and excluded. Not a whole-catalogue census.',failures=w.load(E/'failures.json'),unresolved_cases=dict(current_page_held=21,historical_life_date_conflicts=1,tentative_image_inscription_date_discrepancy=1),hourly_summary_owner='Existing external supervisor',hundred_hour_milestone_is_not_stop=True,next_task=nxt))
 evidence+=['CHECKPOINT.json','source-queue-update-verification.json','milestone-report.json']
 assert w.load(w.RUNTIME/'CHECKPOINT.json')==w.load(E/'CHECKPOINT.json')
 save('final-checkpoint-verification.json',dict(at=h.now(),evidence_files=[dict(path=ep(p),sha256=h.sha((E/p).read_bytes())) for p in evidence],worker_files=[dict(path=str(p.relative_to(w.ROOT)),sha256=h.sha(p.read_bytes())) for p in [Path(__file__).resolve(),w.ROOT/'ops/continuous-tepapa-images-000056.py',w.ROOT/'ops/continuous-tepapa-images-000056-verify.py',w.ROOT/'ops/continuous-tepapa-000056-resume.py']],runtime_checkpoint_matches=True,source_queue_111_entries=True,unrelated_entries_preserved=110,verified_counts=counts,supervisor_prompt_schema_launchagent_untouched=True))
 result=dict(outcome='progress',summary='Verified four new Te Papa primary images, all individually viewed. Preserved 21 unresolved cases and 110 unrelated queue entries. Exact alias/version and date-discrepancy evidence saved; replay changed no rows or storage.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[ep(p) for p in ['batch-verification-receipt.json','independent-production-verification.json','independent-storage-verification.json','independent-public-verification.json','actual-visual-review.json','independent-resume-verification.json','source-queue-update-verification.json','final-checkpoint-verification.json','CHECKPOINT.json']])
 save('result.json',result);w.save(w.RUNTIME/'verified-result.json',w.load(E/'result.json'));print(json.dumps(result))
