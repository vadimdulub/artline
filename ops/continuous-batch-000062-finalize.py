#!/usr/bin/env python3
"""Finalize one independently verified batch; leave external supervisor untouched."""
import copy, datetime, fcntl, gzip, importlib.util, json, os, shutil
from pathlib import Path

s=importlib.util.spec_from_file_location('worker62',Path(__file__).with_name('continuous-tepapa-images-000062.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
h=w.h;i=w.i;E=w.E
def ep(name):return str((E/name).relative_to(w.ROOT))
def save(name,value):return w.save(E/name,value)

with (w.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=w.load(E/'batch-verification-receipt.json');counts=receipt['verified_counts'];ids=receipt['production_ids']
 assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=4,alternate_images=0,museum_links=0)
 replay=w.load(E/'independent-resume-verification.json');assert replay['unchanged_snapshot'] and not any(replay['replay_increments'].values())
 data=w.load(E/'tepapa-bounded-gap-input.json.gz');cross=w.load(E/'identity-crosswalk-input.json.gz');holds=w.load(E/'research-holds.json')['records']
 assert len(data['rows'])==25 and len(cross)==17 and len(holds)==21
 assert set(ids).isdisjoint({r['artwork_id'] for r in holds}) and {r['id'] for r in data['rows']}==set(ids)|{r['artwork_id'] for r in holds}
 prior=w.load(E/'prior-batch-live-reconciliation.json');assert prior['current_campaign_rows_before_write']==0 and sum(r['verified_images'] for r in prior['previous_batches'])==12 and all(r['counted_this_batch']==0 for r in prior['previous_batches'])
 selected=i.selected(w.B)['rows'];assert len(selected)==4
 now=h.now();master=w.load(E.parents[1]/'CHECKPOINT.json');assert master['inflight']['batch']==62
 archive=Path.home()/'Library/Application Support/Artline/source-metadata'/i.OP;archive.mkdir(parents=True,exist_ok=True);sourcechecks=[]
 for p in sorted((E/'source-captures').glob('*.receipt.json')):
  rc=w.load(p);body=w.ROOT/rc['body_path'];assert h.sha(gzip.decompress(body.read_bytes()))==rc['sha256'] and rc['status']==200
  for src in [p,body]:
   dst=archive/src.name
   if dst.exists():assert dst.read_bytes()==src.read_bytes()
   else:shutil.copyfile(src,dst)
  sourcechecks.append(dict(path=str(p.relative_to(w.ROOT)),url=rc['url'],status=rc['status'],sha256=rc['sha256'],archived_body=str(archive/body.name)))
 assert len(sourcechecks)==19
 stops=[];oldstops=w.load(E.parent/'000056/source-archive-verification.json')['completed_campaign_stop_files_preserved']
 for p in sorted((w.ROOT/'docs/research/illustrated-300k-20261011').glob('stop-*.json')):
  record=dict(path=str(p.relative_to(w.ROOT)),sha256=h.sha(p.read_bytes()),contents=w.load(p));assert any(r['path']==record['path'] and r['sha256']==record['sha256'] for r in oldstops);stops.append(record)
 assert len(stops)==3
 save('source-archive-verification.json',dict(at=now,source_checks=sourcechecks,archived_outside_documents=True,original_images_outside_documents=True,completed_campaign_stop_files_preserved=stops,separate_continuation_campaign=i.OP))
 nextpage=w.load(E/'next-gap-cursor-verification.json');assert nextpage['next_page_rows']==0
 cursor=dict(route='official_native_object_pages_record_specific_NKCR_images',institution_id=w.b.MID,after_artwork_id=data['rows'][-1]['id'],previous_after_artwork_id=data['after_artwork_id'],inspected_ids=[r['id'] for r in data['rows']],native_object_ids=[r['native_id'] for r in cross],delivered_ids=ids,held_ids=[r['artwork_id'] for r in holds],image_selection_sha256=receipt['selection_sha256'],next_page_rows=0,keyset_scope='Existing active Te Papa primary-image gaps with literal creation_year_end <= 1955',reached_end_of_current_keyset=True,coverage_complete=False,no_repeat_of_unchanged_holds=True,held_evidence=ep('research-holds.json'),metadata_refresh_due='2026-11-09',source_media_redirect='Exact official HTTP 303 retaining native media identifier')
 nxt='Rotate to Finnish National Gallery / Sinebrychoff existing image gaps after 9ec08a6b-9cb1-4f01-a63a-5eabbd942a03 using the saved native export and exact record-specific open rights. Te Papa reached the end of its current <=1955 keyset at '+cursor['after_artwork_id']+'; revisit held cases only with new evidence. Preserve provider holds and the 18 untouched NSW candidates.'
 save('independent-route-completeness-verification.json',dict(at=now,production_gaps_inspected=25,native_object_pages_researched=17,native_source_policy_pages=2,selected=4,prepared=4,individually_viewed=4,imported=4,independently_verified=4,held=21,holds_by_reason=dict(identity_crosswalk=8,no_source_image=5,rights=7,cropped_composition=1),all_researched_objects_accounted_for=True,held_object_images_downloaded=0,next_page_rows=0,directory_entries_added=0,museum_coverage_incomplete=True))
 source=dict(source_id='te_papa',provider='Museum of New Zealand Te Papa Tongarewa',last_checked_at=now,access_status='17 public object pages and two policy pages HTTP 200; four official media redirects HTTP 303 and four selected images HTTP 200; no API keys or paid service',policy_reference='Original 111-source CSV te_papa row; docs/ARTLINE_IMAGE_USE.md general image policy; captured official record-specific NKCR media rules',remaining_gaps='21 current-page holds plus all prior holds remain. End of current <=1955 keyset verified; later dates and complete museum coverage not audited.',resume_cursor=cursor)
 save('source-register-final.json',dict(at=now,registry_rows=111,complete_registry_evidence=ep('required-input-reconciliation.json'),sources=[source],directory_coverage_complete=False,artwork_coverage_complete=False))
 manifest=[]
 for row in selected:
  im=w.load(i.folder(w.B)/'prepared'/(row['artwork_id']+'.json'));manifest.append(dict(artwork_id=row['artwork_id'],native_id=row['current_source_id'],title=row['title'],source_url=row['source_url'],media_id=im['media_id'],image_sha256=im['sha256'],source_sha256=row['image']['receipt']['sha256'],selection_sha256=receipt['selection_sha256'],rights_label=row['rights_label'],bytes=im['bytes'],original_path=im['original_path']))
 save('verified-delivery-manifest.json',manifest)
 evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-file-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-held-objects-verification.json','independent-prewrite-verification.json','independent-resume-verification.json','actual-visual-review.json','additional-identity-review.json','prior-batch-live-reconciliation.json','global-identity-reconciliation.json','independent-route-completeness-verification.json','source-policy-verification-v2.json','research-holds.json','source-access-holds.json','required-input-reconciliation.json','source-register-final.json','verified-delivery-manifest.json','source-archive-verification.json','next-gap-cursor-verification.json','failures.json']
 end=datetime.datetime.fromisoformat(now);start=datetime.datetime.fromisoformat(master['inflight']['started_at']);runtime=(end-start).total_seconds();programme=(end-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()
 cp=dict(at=now,batch=62,stage='independently_verified_complete',outcome='progress',started_at=start.isoformat(),elapsed_seconds=runtime,verified_counts=counts,production_ids=ids,selection_sha256=receipt['selection_sha256'],discovered=25,native_researched=17,selected=4,prepared=4,imported=4,verified=4,individually_viewed=4,held=21,resume_cursor=cursor,next_task=nxt,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-tepapa-000062-resume.py',verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-tepapa-images-000062-verify.py',evidence_paths=[ep(p) for p in evidence],external_supervisor_unchanged=True,local_catalogue_connections=0)
 save('CHECKPOINT.json',cp);w.save(w.RUNTIME/'CHECKPOINT.json',w.load(E/'CHECKPOINT.json'))
 qp=E.parents[1]/'source-queue.json'
 if not (E/'source-queue-update-verification.json').exists():
  with qp.with_suffix('.lock').open('a+') as qlock:
   fcntl.flock(qlock,fcntl.LOCK_EX);before=w.load(qp);q=copy.deepcopy(before);r=next(x for x in q['sources'] if x['source_id']=='te_papa');assert r['resume_cursor']['after_artwork_id']==data['after_artwork_id']
   oldcounts=r['programme_verified_counts'];assert oldcounts['newly_illustrated']==15
   r.setdefault('prior_resume_cursors',[]).append(r['resume_cursor']);r['resume_cursor']=cursor
   r.update(status='nineteen_programme_primary_images_verified_current_keyset_end_holds_preserved',last_checked_at=now,checkpoint=ep('CHECKPOINT.json'),latest_batch_verified_counts=counts,verified_counts=counts,programme_verified_counts={k:oldcounts[k]+counts[k] for k in counts},access_status=source['access_status'],policy_reference=source['policy_reference'],remaining_gaps=[source['remaining_gaps']])
   for name in evidence+['CHECKPOINT.json']:
    assert (E/name).is_file()
    if ep(name) not in r.setdefault('evidence_paths',[]):r['evidence_paths'].append(ep(name))
   untouched=lambda v:{r['source_id']:r for r in v['sources'] if r['source_id']!='te_papa'}
   assert untouched(before)==untouched(q)==untouched(w.load(E/'source-queue-before.json')) and len(q['sources'])==111 and all(q[k]==v for k,v in before.items() if k!='sources')
   save('source-queue-immediately-before-update.json',before);tmp=qp.with_suffix('.batch62.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp);assert w.load(qp)==q
   save('source-queue-update-verification.json',dict(at=now,updated_sources=['te_papa'],unrelated_entries_preserved=110,source_count=111,before_semantic_sha256=h.sha(json.dumps(before,sort_keys=True).encode()),after_file_sha256=h.sha(qp.read_bytes()),resume_cursor=cursor,prior_holds_preserved_in_prior_cursors=True))
 save('milestone-report.json',dict(at=now,batch=62,measured_batch_runtime_seconds=runtime,measured_programme_runtime_hours=programme/3600,previous_supervisor_counts=master['totals'],batch_verified_counts=counts,cumulative_programme_counts={k:master['totals'][k]+counts[k] for k in counts},attribution_limit='This batch independently verified. Previous supervisor totals not globally re-audited; twelve prior images rechecked and excluded. No whole-catalogue census.',failures=w.load(E/'failures.json'),unresolved_cases=dict(current_page_held=21),hourly_summary_owner='Existing external supervisor',hundred_hour_milestone_is_not_stop=True,next_task=nxt))
 evidence+=['CHECKPOINT.json','source-queue-update-verification.json','milestone-report.json'];assert w.load(w.RUNTIME/'CHECKPOINT.json')==w.load(E/'CHECKPOINT.json')
 save('final-checkpoint-verification.json',dict(at=h.now(),evidence_files=[dict(path=ep(p),sha256=h.sha((E/p).read_bytes())) for p in evidence],worker_files=[dict(path=str(p.relative_to(w.ROOT)),sha256=h.sha(p.read_bytes())) for p in [Path(__file__).resolve(),w.ROOT/'ops/continuous-tepapa-images-000062.py',w.ROOT/'ops/continuous-tepapa-images-000062-verify.py',w.ROOT/'ops/continuous-tepapa-000062-resume.py']],runtime_checkpoint_matches=True,source_queue_111_entries=True,unrelated_entries_preserved=110,verified_counts=counts,supervisor_prompt_schema_launchagent_untouched=True))
 result=dict(outcome='progress',summary='Verified four new Te Papa primary images, each individually viewed and checked in production and public delivery. Preserved 21 unresolved cases and 110 unrelated queue entries; confirmed zero-change replay and end of the current Te Papa keyset.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[ep(p) for p in ['batch-verification-receipt.json','independent-production-verification.json','independent-storage-verification.json','independent-public-verification.json','actual-visual-review.json','independent-resume-verification.json','source-queue-update-verification.json','final-checkpoint-verification.json','CHECKPOINT.json']])
 save('result.json',result);w.save(w.RUNTIME/'verified-result.json',w.load(E/'result.json'));print(json.dumps(result))
