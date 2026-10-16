#!/usr/bin/env python3
"""Finalize one verified batch without touching the external supervisor."""
import copy,datetime,fcntl,importlib.util,json,os
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-warsaw-batch-000042.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;E=b.E;R=b.R;ROOT=b.ROOT
with (R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (E/'final-checkpoint-verification.json').exists():
  final=h.load(E/'final-checkpoint-verification.json')
  for x in final['evidence_files']:assert h.sha((ROOT/x['path']).read_bytes())==x['sha256']
  assert h.load(R/'CHECKPOINT.json')==h.load(E/'CHECKPOINT.json')
  print(json.dumps(dict(already_finalized=True,verified_counts=final['verified_counts'])));raise SystemExit(0)
 receipt=h.load(E/'batch-verification-receipt.json');counts=receipt['verified_counts']
 assert counts==dict(new_painters=0,new_artworks=7,newly_illustrated=7,alternate_images=0,museum_links=7)
 assert h.load(E/'independent-resume-verification.json')['no_new_writes_on_resume']
 plan,pin=h.pinned(b.PHASE);ids=receipt['production_ids'];native=[r['source_id'] for r in plan['records']]
 production=h.load(E/'independent-production-verification.json');holdings=[v for a in production['rows'].values() for v in a['holdings']]
 with h.connect() as db:
  audit=[dict(x) for x in db.execute("SELECT entity_type,entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='location_assertion' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id",([x['id'] for x in holdings],))]
 assert len(audit)==7
 for row in audit:
  holding=next(x for x in holdings if x['id']==row['entity_id'])
  assert row['action']=='insert' and row['before_json'] in [None,{}] and row['after_json']==holding
  assert holding['claim_type']=='holding' and holding['display_state'] is None and holding['review_state']=='accepted'
 b.save('independent-holding-audit-verification.json',dict(at=h.now(),records=audit,empty_preimages=True,current_display_claims=0))
 old=h.load(E/'source-queue-before.json');w=next(r for r in old['sources'] if r['source_id']=='national_museum_warsaw');prior=w['resume_cursor']
 research=h.load(E/'research-holds.json');held=[x['source_id'] for x in research['records']]
 assert set(native+held)==set(prior['pending_native_ids_current_page']) and len(held)==10
 resume=copy.deepcopy(prior)
 resume.update(processed_native_ids=list(dict.fromkeys(prior['processed_native_ids']+native+held)),delivered_native_ids=list(dict.fromkeys(prior['delivered_native_ids']+native)),held_native_ids=list(dict.fromkeys(prior['held_native_ids']+held)),pending_native_ids_current_page=[],next_page_after_pending=2,selection_sha256=receipt['image_selection_sha256'],metadata_plan_sha256=pin,review_ledger=str((E/'research-holds.json').relative_to(ROOT)),do_not_repeat_unchanged_holds=True,next_step='Rotate to other registry providers. For future Warsaw work, continue bounded native search page 2 or resolve saved unit/version cases with new evidence; skip every processed native ID.')
 assert len(resume['delivered_native_ids'])==19 and len(resume['held_native_ids'])==13
 next_task='Match the 35 saved NSW image gaps in batch 41 against WikiArt, starting with Charles Conder and exact physical-version checks. Preserve the NSW access hold, ten newly documented Warsaw review cases, three earlier Warsaw holds and all unrelated queues; then rotate to another undercovered registry institution.'
 evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-holding-audit-verification.json','independent-file-verification.json','independent-image-source-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','prewrite-file-verification.json','prior-batch-live-reconciliation.json','global-identity-reconciliation.json','creator-global-reconciliation.json','source-register.json','source-access-holds.json','research-holds.json','discovery-route-verification.json','web-discovery-query-audit.json','required-input-reconciliation.json']
 b.save('source-register-final.json',dict(at=h.now(),registry_rows=111,original_registry_sha256=h.load(E/'required-input-reconciliation.json')['registry']['sha256'],routes=[dict(provider='national_museum_warsaw',policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='17 exact native object responses and seven selected native primary images HTTP 200',last_checked_at=h.now(),object_metadata_captures=17,selected=7,production_verified=7,rights='Native DOMENA PUBLICZNA, restricted=false plus saved museum reuse policy; user authorization recorded separately',remaining_gaps='Ten saved unit/date/version cases and three inherited holds. First metadata page reconciled; native page 2 remains undiscovered. Search total 306 is not an eligible-object count.'),dict(provider='national_gallery_prague',access_status='Exact public catalogue search unavailable in web tool; no HTTP status available',last_checked_at=h.now(),remaining_gaps='Require exact inventory records or a loan catalogue; collection loan context is not ownership evidence.'),dict(provider='lacma',access_status='Search-discovery-only official object 40124 lead',last_checked_at=h.now(),remaining_gaps='Russian avant-garde route requires exact capture and global reconciliation; no image permission assumed.'),dict(provider='national_gallery_athens',access_status='Web discovery only for Tzanes',last_checked_at=h.now(),remaining_gaps='No exact native inventory selected; existing completed creators and source holds unchanged.')],directory_coverage='Unchanged; no museum-directory or whole-collection completion claim.',local_catalogue_connections=0))
 evidence.append('source-register-final.json')
 checkpoint=dict(at=h.now(),batch=42,stage='verified_complete',verified_counts=counts,production_ids=ids,plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],discovered_exact_native_records=17,individually_researched=17,selected=7,prepared=7,metadata_imported=7,images_imported=7,metadata_verified=7,images_verified=7,images_individually_viewed=7,painters_created=0,source_resume=resume,new_review_holds=held,prior_unchanged_holds=prior['held_native_ids'],next_task=next_task,resume_command='/tmp/artline-cesi-venv/bin/python ops/continuous-warsaw-000042-resume.py',verify_command='/tmp/artline-cesi-venv/bin/python ops/continuous-warsaw-000042-verify.py',evidence_paths=[str((E/x).relative_to(ROOT)) for x in evidence],local_database_connections=0,external_supervisor_unchanged=True)
 checkpoint=b.save('CHECKPOINT.json',checkpoint);h.save(R/'CHECKPOINT.json',checkpoint)
 qp=E.parents[1]/'source-queue.json'
 if not (E/'source-queue-update-verification.json').exists():
  with (R.parent.parent/'source-queue-update.lock').open('a+') as qlock:
   fcntl.flock(qlock,fcntl.LOCK_EX);q=h.load(qp);before=copy.deepcopy(q);changed={'national_museum_warsaw','national_gallery_prague','lacma','national_gallery_athens'}
   for row in q['sources']:
    sid=row['source_id']
    if sid not in changed:continue
    row['last_checked_at']=h.now()
    if sid=='national_museum_warsaw':
     assert row['resume_cursor']==prior,'Concurrent queue drift; reconcile before update'
     row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(prior))
     row.update(status='nineteen_programme_whole_icons_holdings_and_primary_images_verified_thirteen_review_holds',checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)),resume_cursor=resume,verified_counts=counts,latest_batch_verified_counts=counts,programme_verified_counts=dict(new_painters=0,new_artworks=19,newly_illustrated=19,alternate_images=0,museum_links=19),policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='Native object API and seven selected image CDN responses HTTP 200',remaining_gaps=['Ten saved unit/date/version cases plus three previous holds require new editorial evidence; no unchanged retries.','First native search page reconciled; continue page 2 when returning to this provider.','Broader museum and national coverage remain incomplete.'])
     ev=evidence
    else:
     finding={'national_gallery_prague':'Official catalogue search unavailable in web tool, no HTTP status. No exact object or accepted holding established.','lacma':'Official search lead 40124 Dancing Soldiers by Mikhail Larionov, 1909–1910. Russian avant-garde, not an icon; no object request/import/image selection.','national_gallery_athens':'Tzanes web query found no exact selected National Gallery inventory; prior creator checkpoints and holds retained.'}[sid]
     row.setdefault('research_history',[]).append(dict(at=h.now(),batch=42,scope='search_discovery_only',finding=finding,evidence_path=str((E/'web-discovery-query-audit.json').relative_to(ROOT))))
     if sid=='national_gallery_prague':
      row.update(status='official_catalogue_search_web_tool_unavailable_exact_objects_unresolved',resume_cursor=dict(route='official_catalogue_search',url='https://sbirky.ngprague.cz/katalog?search=ikona',retry_unchanged_search=False,next_step='Seek an accessible exact inventory/loan catalogue; do not infer ownership from Kondakov collection loan context.'))
     if sid=='lacma':row['resume_cursor']=dict(route='official_object_discovery',url='https://collections.lacma.org/object/40124',source_id='40124',next_step='Bounded exact metadata/global creator/version reconciliation; rights-limited museum reproduction not selected.')
     ev=['web-discovery-query-audit.json','source-register-final.json']
    for name in ev:
     path=str((E/name).relative_to(ROOT))
     if path not in row.setdefault('evidence_paths',[]):row['evidence_paths'].append(path)
   assert len(q['sources'])==111 and [r for r in before['sources'] if r['source_id'] not in changed]==[r for r in q['sources'] if r['source_id'] not in changed]
   assert all(q[k]==v for k,v in before.items() if k!='sources')
   b.save('source-queue-immediately-before-update.json',before);tmp=qp.with_suffix('.batch42.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2));os.replace(tmp,qp);assert h.load(qp)==q
   b.save('source-queue-update-verification.json',dict(at=h.now(),updated_sources=sorted(changed),unrelated_entries_preserved=True,source_queue_entries=111,after_sha256=h.sha(qp.read_bytes()),entries=[r for r in q['sources'] if r['source_id'] in changed]))
 root=h.load(E.parents[1]/'CHECKPOINT.json');assert root['inflight']['batch']==42
 now=datetime.datetime.now(datetime.timezone.utc)
 b.save('milestone-report.json',dict(at=now.isoformat(),measured_batch_runtime_seconds=(now-datetime.datetime.fromisoformat(root['inflight']['started_at'])).total_seconds(),measured_programme_runtime_hours=(now-datetime.datetime.fromisoformat(root['started_at'])).total_seconds()/3600,previous_verified_programme_increments=root['totals'],batch_verified_counts=counts,cumulative_programme_increments_after_this_batch={k:root['totals'][k]+counts[k] for k in counts},prior_campaigns_excluded=True,whole_catalogue_census=False,failures=['Prague public catalogue search unavailable in web tool; no retry or alternate-client bypass.','One discovery query contained accidental space; rejected as evidence.'],unresolved=dict(warsaw_new_review_cases=10,warsaw_prior_holds=3,nsw_saved_image_gaps=35),next_task=next_task,hourly_and_100_hour_reports='External supervisor owns recurring reporting and continuation; worker does not modify scheduler, prompts, schema or LaunchAgent.'))
 evidence+=['source-queue-update-verification.json','milestone-report.json','CHECKPOINT.json']
 result=dict(outcome='progress',summary='Verified seven new Warsaw icon review artworks, seven documented holdings and seven primary images in production and public delivery. All seven images visually inspected. Replay made no changes; queue and checkpoints saved.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[str((E/n).relative_to(ROOT)) for n in evidence])
 b.save('result.json',result)
 assert h.load(R/'CHECKPOINT.json')==h.load(E/'CHECKPOINT.json')
 b.save('final-checkpoint-verification.json',dict(at=h.now(),evidence_files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in result['evidence_paths']],runtime_checkpoint_matches=True,verified_counts=counts,source_queue_111_entries=len(h.load(qp)['sources'])==111,local_catalogue_connections=0,supervisor_prompt_schema_launchagent_untouched=True))
 print(json.dumps(dict(verified_counts=counts,next_task=next_task),ensure_ascii=False))
