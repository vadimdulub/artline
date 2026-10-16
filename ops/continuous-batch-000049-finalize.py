#!/usr/bin/env python3
"""Finalize one verified batch; merge only researched routes, never supervisor state."""
import copy, datetime, fcntl, gzip, importlib.util, json, os
from pathlib import Path
s=importlib.util.spec_from_file_location('worker49',Path(__file__).with_name('continuous-tepapa-images-000049.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
h=w.h;i=w.i;E=w.E
def ep(name):return str((E/name).relative_to(w.ROOT))
def save(name,value):return w.save(E/name,value)
with (w.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=w.load(E/'batch-verification-receipt.json');replay=w.load(E/'independent-resume-verification.json')
 assert replay['unchanged_snapshot'] and all(v==0 for v in replay['replay_increments'].values())
 counts=receipt['verified_counts'];assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=3,alternate_images=0,museum_links=0)
 zero={k:0 for k in counts};ids=receipt['production_ids'];now=h.now()
 master=w.load(E.parents[1]/'CHECKPOINT.json');assert master['inflight']['batch']==49
 data=w.load(E/'tepapa-bounded-gap-input.json.gz');cross=w.load(E/'identity-crosswalk-input.json.gz');holds=w.load(E/'research-holds.json')['records']
 assert len(data['rows'])==25 and len(cross)==20 and len(holds)==22
 assert {r['id'] for r in data['rows']}==set(ids)|{r['artwork_id'] for r in holds}
 french=w.load(E/'french-reserve-live-reconciliation.json');assert french['unimported']==0 and french['already_imported_and_illustrated']==188
 fe=w.load(E/'independent-french-reserve-evidence-verification.json')
 for p in fe['immutable_plans']:assert h.sha((w.ROOT/p['path']).read_bytes())==p['sha256']
 discovery=w.load(E/'discovery-outcomes.json')['rows'];assert len(discovery)==6
 processed={r['artwork_id'] for r in discovery};new_unmatched=[r['artwork_id'] for r in discovery if r['outcome']=='no_unique_exact_title_in_index'];unavailable=[r['artwork_id'] for r in discovery if r['outcome']=='index_unavailable']
 assert len(new_unmatched)==len(unavailable)==3
 beforequeue=w.load(E/'source-queue-before.json');oldnsw=next(r for r in beforequeue['sources'] if r['source_id']=='art_gallery_nsw')['resume_cursor']
 nsw=copy.deepcopy(oldnsw);nsw.update(processed_artwork_ids=sorted(set(oldnsw['processed_artwork_ids'])|processed),pending_artwork_ids=[aid for aid in oldnsw['pending_artwork_ids'] if aid not in processed],unmatched_artwork_ids=sorted(set(oldnsw['unmatched_artwork_ids'])|set(new_unmatched)),profile_unavailable_artwork_ids=unavailable,discovery_evidence=ep('discovery-outcomes.json'),profile_unavailability_scope='Only the three recorded candidate profile URLs returned 404; this is not a claim the artists or images are unavailable everywhere.',retry_rule='Revisit unmatched or unavailable candidates only with new object/profile evidence. No held official NSW requests.')
 assert len(nsw['pending_artwork_ids'])==23
 cursor=dict(route='official_native_object_pages_record_specific_NKCR_images',institution_id=w.b.MID,after_artwork_id=data['rows'][-1]['id'],previous_after_artwork_id=data['after_artwork_id'],inspected_ids=[r['id'] for r in data['rows']],native_object_ids=[r['native_id'] for r in cross],delivered_ids=ids,held_ids=[r['artwork_id'] for r in holds],image_selection_sha256=receipt['selection_sha256'],source_media_redirect='Only exact official HTTP 303 preserving source media ID',metadata_refresh_due='2026-11-08',no_repeat_of_unchanged_holds=True,held_evidence=ep('research-holds.json'))
 sourcechecks=[]
 for p in (E/'source-captures').glob('*.receipt.json'):
  rc=w.load(p);assert h.sha(gzip.decompress((w.ROOT/rc['body_path']).read_bytes()))==rc['sha256']
  sourcechecks.append(dict(path=str(p.relative_to(w.ROOT)),url=rc['url'],status=rc['status'],sha256=rc['sha256']))
 # WikiArt uses hash-named receipts and archives directly outside Documents.
 for p in (E/'source-captures').glob('*.json'):
  if p.name.endswith('.receipt.json'):continue
  rc=w.load(p)
  if 'body_path' not in rc:continue
  assert h.sha(gzip.decompress(Path(rc['body_path']).read_bytes()))==rc['sha256']
  sourcechecks.append(dict(path=str(p.relative_to(w.ROOT)),url=rc['url'],status=rc['status'],sha256=rc['sha256']))
 save('independent-route-completeness-verification.json',dict(at=now,french_reserve_inspected=188,french_unimported=0,nsw_candidates_checked=6,nsw_images_selected=0,nsw_unmatched=3,nsw_profile_url_404=3,tepapa_gap_records=25,tepapa_native_objects=20,tepapa_images_selected_prepared_imported_verified=3,tepapa_explicit_holds=22,all_researched_objects_accounted_for=True,source_receipts=sourcechecks,held_object_images_downloaded=0,directory_coverage_complete=False))
 nxt='Resume Warsaw native icon search at page 3, maximum 24 leads; skip saved native IDs and date/unit/version holds. NSW has 23 untouched candidates; Te Papa resumes after '+cursor['after_artwork_id']+'. French reserve is exhausted: do not replay its 188 earlier deliveries.'
 sources=[dict(source_id='yale_lux',access_status='Read-only reconciliation, no new provider requests',policy_reference='docs/ARTLINE_IMAGE_USE.md#continued-illustrated-expansion--11-october-2026',remaining_gaps='No unimported works in the 188 reviewed reserves; prior printing-date holds unchanged'),dict(source_id='art_gallery_nsw',access_status='Three approved alternate WikiArt indexes HTTP 200, three candidate profile URLs HTTP 404; official museum access hold untouched',policy_reference='Original art_gallery_nsw CSV entry; separate 6 October WikiArt source approval',remaining_gaps='23 untouched candidates, seven unmatched to captured indexes, three unavailable profile URLs; all 33 production image gaps unchanged',resume_cursor=nsw),dict(source_id='te_papa',access_status='20 public native object pages HTTP 200; three exact media redirects HTTP 303 and selected images HTTP 200; no API keys used',policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy; native record-specific NKCR and territorial policy',remaining_gaps='22 current-page holds and all prior holds retained; later UUID pages pending',resume_cursor=cursor)]
 for r in sources:r['last_checked_at']=now
 save('source-register-final.json',dict(at=now,complete_original_registry_rows=111,complete_registry_evidence=ep('required-input-reconciliation.json'),sources=sources,new_directory_entries=0,museum_nationwide_coverage_complete=False))
 save('research-outcomes.json',dict(at=now,discovered_tepapa_gaps=25,researched_tepapa_objects=20,selected=3,prepared=3,imported=3,independently_verified=3,actual_individual_image_views=3,prior_blomfield_version_comparison_views=1,tepapa_holds=22,nsw_processed=6,nsw_pending=23,nsw_new_images=0,earlier_campaign_increments=0,verified_counts=counts))
 manifest=[]
 for row in i.selected(w.B)['rows']:
  im=w.load(i.folder(w.B)/'prepared'/(row['artwork_id']+'.json'))
  manifest.append(dict(artwork_id=row['artwork_id'],native_id=row['current_source_id'],title=row['title'],source_url=row['source_url'],media_id=im['media_id'],image_sha256=im['sha256'],source_sha256=row['image']['receipt']['sha256'],selection_sha256=receipt['selection_sha256'],rights_label=row['rights_label'],bytes=im['bytes'],original_path=im['original_path']))
 save('verified-delivery-manifest.json',manifest)
 evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-file-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-held-objects-verification.json','independent-prewrite-verification.json','independent-resume-verification.json','actual-visual-review.json','blomfield-version-verification.json','french-reserve-live-reconciliation.json','independent-french-reserve-evidence-verification.json','prior-batch-live-reconciliation.json','global-identity-reconciliation.json','independent-route-completeness-verification.json','independent-nsw-preservation-verification.json','source-policy-verification-v2.json','research-holds.json','discovery-outcomes.json','source-access-holds.json','required-input-reconciliation.json','source-register-final.json','verified-delivery-manifest.json','source-archive-verification.json','template-carryover-correction.json']
 cp=dict(at=now,batch=49,stage='independently_verified_complete',verified_counts=counts,production_ids=ids,selection_sha256=receipt['selection_sha256'],selected=3,prepared=3,imported=3,verified=3,individually_viewed=3,french_reserve_unimported=0,tepapa_holds=22,tepapa_resume=cursor,nsw_resume=nsw,next_task=nxt,resume_command='/tmp/artline-cesi-venv/bin/python ops/continuous-tepapa-000049-resume.py',verify_command='/tmp/artline-cesi-venv/bin/python ops/continuous-tepapa-images-000049-verify.py',evidence_paths=[ep(p) for p in evidence],external_supervisor_unchanged=True,local_catalogue_connections=0)
 save('CHECKPOINT.json',cp);w.save(w.RUNTIME/'CHECKPOINT.json',w.load(E/'CHECKPOINT.json'))
 qp=E.parents[1]/'source-queue.json';changed=['yale_lux','art_gallery_nsw','te_papa']
 if not (E/'source-queue-update-verification.json').exists():
  with qp.with_suffix('.lock').open('a+') as qlock:
   fcntl.flock(qlock,fcntl.LOCK_EX);before=w.load(qp);q=copy.deepcopy(before)
   for r in q['sources']:
    if r['source_id'] not in changed:continue
    r.update(last_checked_at=now,checkpoint=ep('CHECKPOINT.json'),latest_batch_verified_counts=counts if r['source_id']=='te_papa' else zero)
    register=next(z for z in sources if z['source_id']==r['source_id']);r['access_status']=register['access_status'];r['policy_reference']=register['policy_reference'];r['remaining_gaps']=[register['remaining_gaps']]
    if r['source_id']=='yale_lux':
     r['status']='french_reserve_exhausted_live_verified_188_already_delivered';r['resume_cursor'].update(french_reserve_remaining=0,unimported=0,do_not_replay=True)
     add=['french-reserve-live-reconciliation.json','independent-french-reserve-evidence-verification.json','CHECKPOINT.json']
    elif r['source_id']=='art_gallery_nsw':
     r.setdefault('prior_resume_cursors',[]).append(r.get('resume_cursor'));r['resume_cursor']=nsw;r['status']='official_hold_preserved_wikiart_23_pending_7_unmatched_3_profile_urls_unavailable'
     add=['discovery-outcomes.json','wikiart-index-research.json','independent-nsw-preservation-verification.json','CHECKPOINT.json']
    else:
     oldcounts=r.get('programme_verified_counts',r.get('verified_counts',zero));r.setdefault('prior_resume_cursors',[]).append(r.get('resume_cursor'));r['resume_cursor']=cursor
     r.update(status='eleven_programme_primary_images_verified_three_new_NKCR_images',verified_counts=counts,programme_verified_counts={k:oldcounts[k]+counts[k] for k in counts});assert r['programme_verified_counts']['newly_illustrated']==11
     add=evidence+['CHECKPOINT.json']
    for name in add:
     assert (E/name).is_file()
     if ep(name) not in r.setdefault('evidence_paths',[]):r['evidence_paths'].append(ep(name))
   untouched=lambda z:{r['source_id']:r for r in z['sources'] if r['source_id'] not in changed}
   assert untouched(before)==untouched(q) and len(q['sources'])==111 and all(q[k]==v for k,v in before.items() if k!='sources')
   save('source-queue-immediately-before-update.json',before);tmp=qp.with_suffix('.batch49.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp);assert w.load(qp)==q
   save('source-queue-update-verification.json',dict(at=now,updated_sources=changed,unrelated_entries_preserved=108,source_count=111,before_semantic_sha256=h.sha(json.dumps(before,sort_keys=True).encode()),after_file_sha256=h.sha(qp.read_bytes()),tepapa_cursor=cursor,nsw_cursor=nsw))
 end=datetime.datetime.fromisoformat(now);start=datetime.datetime.fromisoformat(master['inflight']['started_at']);elapsed=(end-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()
 save('milestone-report.json',dict(at=now,batch=49,started_at=start.isoformat(),measured_batch_runtime_seconds=(end-start).total_seconds(),measured_programme_runtime_hours=elapsed/3600,previous_supervisor_counts=master['totals'],batch_verified_counts=counts,cumulative_programme_counts={k:master['totals'][k]+counts[k] for k in counts},attribution_limit='Current increments independently verified; prior supervisor totals not globally re-audited here. Not a whole-catalogue census.',failures=['Eight web discovery queries returned no results','Three candidate WikiArt profile URLs returned 404; three captured indexes lacked exact title matches','Diagnostic summary printing met a missing native photo title; title absence preserved and optional title handling corrected before delivery'],unresolved_cases=dict(tepapa_current_page=22,nsw_image_gaps=33),hourly_summary_owner='Existing external supervisor',hundred_hour_milestone_is_not_stop=True,next_task=nxt))
 evidence+=['CHECKPOINT.json','source-queue-update-verification.json','milestone-report.json']
 assert w.load(w.RUNTIME/'CHECKPOINT.json')==w.load(E/'CHECKPOINT.json')
 save('final-checkpoint-verification.json',dict(at=h.now(),evidence_files=[dict(path=ep(p),sha256=h.sha((E/p).read_bytes())) for p in evidence],worker_files=[dict(path=str(p.relative_to(w.ROOT)),sha256=h.sha(p.read_bytes())) for p in [Path(__file__).resolve(),w.ROOT/'ops/continuous-tepapa-images-000049.py',w.ROOT/'ops/continuous-tepapa-images-000049-verify.py',w.ROOT/'ops/continuous-tepapa-000049-resume.py',w.ROOT/'ops/continuous-nsw-images-000049.py']],runtime_checkpoint_matches=True,source_queue_111_entries=True,unrelated_source_entries_preserved=108,historical_french_plans_unchanged=True,verified_counts=counts,supervisor_prompt_schema_launchagent_untouched=True))
 result=dict(outcome='progress',summary='Verified three new Te Papa primary images, all individually viewed. All 188 French reserves were previously delivered and excluded. Six NSW outcomes, 22 Te Papa holds and exact resume cursors saved; replay changed nothing. Local catalogue untouched.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[ep(p) for p in ['batch-verification-receipt.json','independent-production-verification.json','independent-public-verification.json','actual-visual-review.json','independent-resume-verification.json','french-reserve-live-reconciliation.json','source-queue-update-verification.json','final-checkpoint-verification.json','CHECKPOINT.json']])
 for path in result['evidence_paths']:assert (w.ROOT/path).is_file()
 save('result.json',result);w.save(w.RUNTIME/'verified-result.json',w.load(E/'result.json'))
 print(json.dumps(result,ensure_ascii=False))
