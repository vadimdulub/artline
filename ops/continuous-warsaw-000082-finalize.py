#!/usr/bin/env python3
"""Finalize bounded batch 82; only the two researched queue routes change."""
import copy, datetime, fcntl, importlib.util, json, os
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-warsaw-batch-000082.py'))
b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i;E=b.E
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);receipt=h.load(E/'batch-verification-receipt.json');counts=receipt['verified_counts'];ids=receipt['production_ids']
assert counts==dict(new_painters=0,new_artworks=4,newly_illustrated=4,alternate_images=0,museum_links=4)
assert h.load(E/'independent-resume-verification.json')['live_snapshots_equal']
prod=h.load(E/'independent-production-verification.json');assert prod['plan_sha256']==pin
holdingids=[v['holdings'][0]['id'] for v in prod['rows'].values()]
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');assert h.snapshot(db,ids)==prod['rows']
 events=[dict(x) for x in db.execute("SELECT entity_type,entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='location_assertion' AND entity_id=ANY(%s::uuid[]) AND action='insert' ORDER BY entity_id",(holdingids,))]
 assert len(events)==4 and {x['entity_id'] for x in events}==set(holdingids)
 assert all(x['before_json'] in [None,{}] and x['after_json']['claim_type']=='holding' and x['after_json']['display_state'] is None for x in events)
b.save('independent-holding-audit-verification.json',dict(at=h.now(),insertions=4,records=events,current_display_claims=0))
now=h.now();before=h.load(E/'source-queue-before.json');old=next(x for x in before['sources'] if x['source_id']=='national_museum_warsaw');prev=old['resume_cursor'];oldprocessed=set(prev['processed_native_ids'])
checks={r['source_id']:r for r in h.load(E/'global-identity-reconciliation.json')['records']};newids=[r['source_id'] for r in p['records']]
reasons={
 '1045516':'Detached cover IK 183/b is not a painted icon. Preserve as component research; no painted-work or image-gap count.',
 '498526':'Composite IK 293/a-b includes painted panel and brass cover; complete inventory-unit and component-date review remains before selection.',
 '498615':'Composite IK 373/a-b combines painting, fabric, artificial stones and brass cover. Resolve full physical unit and dates before selecting the primary reproduction.',
 '498660':'XIX/XX-century source wording retained. Conservative full-century range would cross 1970; no invented narrower date or automatic eligibility.',
 '498422':'Separately inventoried IK 197 is a surviving component of group IK 195–197, with tentative P. F. Burmistrow attribution. Resolve group/component duplication and qualified creator identity before selection.',
 '498419':'Native description records contemporary conservation. Date and extent of changes and exact physical painted version remain to be assessed; no modern treatment date substituted for creation.',
 '498507':'Native description explicitly records overpainting, particularly clothing of Joachim and Anna. Resolve original versus later painted layers before image selection.'
}
casts={'498465','499395','499393','498438','499444'}
page=h.load(E/'warsaw-icons-page8.json')['data'];records=[];skipped=[]
for item in page['items']:
 oid=str(item['id'])
 if oid in oldprocessed:skipped.append(oid);continue
 o,rc=b.capture(int(oid))
 if oid in newids:decision='delivered_verified';reason='Empty locked preimages, batch-specific persisted plan/source/visual evidence, insert audits, storage and public file hashes independently verified.'
 elif oid in casts:decision='saved_cast_candidate_not_selected';reason='Historical cast saved for exact physical casting/version review; no image request or production eligibility claim in this painted-icon batch.'
 else:
  decision='targeted_editorial_hold'
  if oid in checks:
   reason='Same-title production candidate(s), but different current inventory: '+', '.join(str(a['accession_number']) for a in checks[oid]['scoped_title_or_accession'])+'. Not declared a duplicate; compare exact composition, dimensions and history before insertion.'
  else:reason=reasons[oid]
 records.append(dict(source_id=oid,title=o['title'],inventory=o['noEvidence'],source_date=o['createDates'],creators=o['authors'],owner=o['owner'],dimensions=o['dimensionText'],source_sha256=rc['sha256'],decision=decision,reason=reason,global_identity_checks=checks.get(oid),image_requested=oid in newids))
held=[r['source_id'] for r in records if r['decision']=='targeted_editorial_hold']
assert len(page['items'])==24 and len(records)==23 and len(skipped)==1 and len(held)==14 and len(casts)==5
b.save('page-eight-editorial-dispositions.json',dict(at=now,page_items=24,new_detail_captures=23,previously_processed_skipped=skipped,metadata_candidates=11,selected=4,verified=4,held=14,saved_cast_candidates=5,search_hits=page['paginatorDetails']['totalItemsCount'],search_hits_are_not_eligible_artworks=True,records=records))
b.save('research-holds.json',dict(at=now,prior_held_ids=prev['held_native_ids'],held_native_ids=held,records=[r for r in records if r['decision']=='targeted_editorial_hold'],unchanged_holds_not_retried=True))
b.save('saved-cast-candidates.json',dict(at=now,source_ids=sorted(casts),records=[r for r in records if r['source_id'] in casts],production_increment=0,next_step='Reuse saved metadata; assess exact historical cast/date/version identity before selecting any image.'))
b.save('failure-ledger.json',dict(at=now,production_failures=[],provider_retries=0,held_provider_requests=0,prewrite_assertion_failures=[dict(step='Previous Pola receipt reconciliation',reason='Initial adapter used a different citation field name; then used missing plan_sha256 instead of actual metadata_plan_sha256.',resolution='Read established Pola adapter and receipt keys; corrected query; nine live objects and persisted citation checksum matched before new writes.',production_writes_before_resolution=0)],web_tool_limitation=dict(url='https://cyfrowe.mnw.art.pl/pl/zbiory/443561',outcome='web tool internal accessibility error, not an HTTP access denial; independently established public native API had already returned the exact object.'),new_access_holds=[]))
next_task='Resume saved SHUZO Yokosuka W35623 and Fuchu W278530 candidates with exact native museum and production reconciliation; preserve discovery offset 25 and all Pola image-permission holds. Warsaw next discovery page is 9, with 93 editorial holds and 17 saved cast candidates. French reserve is exhausted: all 188 previously delivered, do not replay.'
b.save('source-register-final.json',dict(at=now,original_registry_rows=111,registry_reference='required-input-reconciliation.json',researched_routes=['yale_lux/french_reserve','national_museum_warsaw/painted_icons/page8'],provider_policies=[dict(provider='Yale University Art Gallery / LUX',policy='docs/ARTLINE_IMAGE_USE.md#continued-illustrated-expansion--11-october-2026',access_status='No network request; original source/manifest/visual checksums and live rows verified.',remaining_gaps='No unimported reserve. Physical-date uncertainties 80082, 80437, 81054 preserved.'),dict(provider=b.MUSEUM,policy='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='Official API page and 23 native records HTTP 200; four selected native images HTTP 200.',rights='Exact DOMENA PUBLICZNA and restricted=false. Prior commercial-reuse policy capture hash verified; actual source label retained, no CC0 claim.',remaining_gaps='Page 9 onward; 93 editorial holds and 17 saved cast candidates; incomplete museum coverage.')],last_checked_at=now,verified_counts=counts,discovered_page_items=24,metadata_captured=23,metadata_candidates=11,selected=4,prepared=4,actually_viewed=4,imported=4,verified=4,directory_coverage_increment=0,whole_museum_coverage_claim=False))
evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-holding-audit-verification.json','independent-file-verification.json','independent-image-source-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','prior-batch-live-reconciliation.json','global-identity-reconciliation.json','creator-global-reconciliation.json','independent-historical-inventory-verification.json','page-eight-editorial-dispositions.json','source-register-final.json','research-holds.json','saved-cast-candidates.json','source-access-holds.json','local-recovery-verification.json','failure-ledger.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','reserve-actual-visual-sample.json']
q=copy.deepcopy(before);src=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw');src.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(prev));c=src['resume_cursor']
c['processed_native_ids']=list(dict.fromkeys(c['processed_native_ids']+[r['source_id'] for r in records]));c['delivered_native_ids']=list(dict.fromkeys(c['delivered_native_ids']+newids));c['held_native_ids']=list(dict.fromkeys(c['held_native_ids']+held));c['saved_cast_candidate_native_ids']=list(dict.fromkeys(c.get('saved_cast_candidate_native_ids',[])+sorted(casts)))
assert len(c['held_native_ids'])==93 and len(c['saved_cast_candidate_native_ids'])==17
c.update(query_url=h.load(E/'warsaw-icons-page8.receipt.json')['url'],captured_page=8,next_page_after_pending=9,next_discovery_page=9,pending_native_ids_current_page=[],priority_native_ids=[],metadata_page_sha256=h.load(E/'warsaw-icons-page8.receipt.json')['sha256'],production_authentication_required=False,authentication_last_verified_at=now,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],saved_discovery=str((E/'warsaw-icons-page8.json').relative_to(b.ROOT)),review_ledger=str((E/'page-eight-editorial-dispositions.json').relative_to(b.ROOT)),prior_cast_candidate_ledger=prev.get('cast_candidate_ledger'),cast_candidate_ledger=str((E/'saved-cast-candidates.json').relative_to(b.ROOT)),next_step='Rotate institutions, then page 9; do not repeat 93 unchanged editorial holds without resolving evidence.')
src.update(status='four_page8_painted_icons_holdings_images_verified_page9_next',checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),last_checked_at=now,last_batch=82,access_status='Page 8 and 23 new metadata captures HTTP 200; four native images and public/production delivery independently verified.',verified_counts=counts,latest_batch_verified_counts=counts)
src['programme_verified_counts']={k:src['programme_verified_counts'][k]+v for k,v in counts.items()};src['remaining_gaps']=['93 editorial holds: 79 preserved and fourteen new.','17 saved historical cast candidates: twelve preserved and five new.','Page 9 onward; no complete museum or directory coverage claim.']
src.setdefault('research_history',[]).append(dict(batch=82,at=now,new_metadata_objects=23,metadata_candidates=11,selected_for_import=4,held=14,saved_cast_candidates=5,prior_processed_skipped=skipped,verified_counts=counts,evidence=str((E/'batch-verification-receipt.json').relative_to(b.ROOT))))
src['evidence_paths']=list(dict.fromkeys(src['evidence_paths']+[str((E/x).relative_to(b.ROOT)) for x in evidence]))
yale=next(x for x in q['sources'] if x['source_id']=='yale_lux');zero={k:0 for k in counts}
yale.update(last_checked_at=now,last_batch=82,checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),latest_batch_verified_counts=zero,access_status='All 188 current production objects/images and persisted historical plan checksums matched; 376 saved source/manifest captures and 188 prior visual decisions verified. No provider request. One actual image sample re-viewed.')
yale['resume_cursor']=dict(yale['resume_cursor'],next_action='Reserve exhausted; do not replay. Continue saved SHUZO candidates or other undercovered registry routes.',last_live_reconciliation=str((E/'french-reserve-live-reconciliation.json').relative_to(b.ROOT)))
yale.setdefault('research_history',[]).append(dict(batch=82,at=now,inspected=188,already_imported=188,selected=0,verified_counts=zero,evidence=str((E/'french-reserve-live-reconciliation.json').relative_to(b.ROOT))))
yale['evidence_paths']=list(dict.fromkeys(yale['evidence_paths']+[str((E/x).relative_to(b.ROOT)) for x in ['french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','reserve-actual-visual-sample.json']]))
desired=b.save('source-queue-after.json',q);queue=E.parents[1]/'source-queue.json'
with (b.R/'queue-update.lock').open('a+') as qlock:
 fcntl.flock(qlock,fcntl.LOCK_EX);current=h.load(queue);assert current in [before,desired],'Concurrent queue change requires merge'
 if current==before:
  temp=queue.with_name('source-queue.batch000082.tmp')
  with temp.open('w') as f:json.dump(desired,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(temp,queue)
after=h.load(queue);assert after==desired;changed={'yale_lux','national_museum_warsaw'}
assert {x['source_id']:x for x in before['sources'] if x['source_id'] not in changed}=={x['source_id']:x for x in after['sources'] if x['source_id'] not in changed}
b.save('source-queue-update-verification.json',dict(at=h.now(),before_sha256=h.sha((E/'source-queue-before.json').read_bytes()),after_sha256=h.sha(queue.read_bytes()),total_sources=111,unrelated_entries_preserved=109,changed_source_ids=sorted(changed),all_prior_hold_ids_preserved=True,next_discovery_page=9,french_reserve_remaining=0,newly_delivered_native_ids=newids))
master=h.load(E.parents[1]/'CHECKPOINT.json');assert master['inflight']['batch']==82
started=master['inflight']['started_at'];finished=h.now();elapsed=(datetime.datetime.fromisoformat(finished)-datetime.datetime.fromisoformat(started)).total_seconds()
assert datetime.datetime.fromisoformat(h.load(h.BACKUP/b.PHASE/'locked-before.json.gz')['at'])>=datetime.datetime.fromisoformat(started)
cp=b.save('CHECKPOINT.json',dict(at=finished,started_at=started,batch=82,outcome='progress',stage='independently_verified_complete',elapsed_seconds=elapsed,verified_counts=counts,french_reserve_already_delivered_excluded=188,discovered_page_items=24,new_metadata_captures=23,metadata_candidates=11,selected=4,prepared=4,individually_viewed=4,imported=4,verified=4,new_editorial_holds=14,saved_cast_candidates=5,production_ids=ids,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],production_target='artline-508319:europe-west1:artline-postgres',local_catalogue_connections=0,next_task=next_task,blocker='',source_queue_cursor=c,external_supervisor_unchanged=True,delivered_batch_do_not_count_again=True,resume_commands=['/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000082-verify.py','/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000082-resume.py','/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000082-finalize.py'],limitations=['Four museum-supplied images are 315 pixels wide; tiny inscriptions and unseen reverse sides not visually verified.','Scoped schema and exact affected-row recovery, not a full database export.','No painter was invented for workshop/anonymous attributions; original labels and qualifications retained.']))
h.save(b.R/'CHECKPOINT.json',cp)
b.save('batch-summary.json',dict(at=finished,batch=82,elapsed_seconds=elapsed,verified_counts=counts,next_task=next_task,failure_ledger='failure-ledger.json'))
b.save('milestone-report.json',dict(at=finished,elapsed_seconds_this_batch=elapsed,verified_counts_this_batch=counts,supervisor_reported_prior_totals=master['totals'],expected_cumulative_after_supervisor_accepts_result={k:master['totals'][k]+v for k,v in counts.items()},prior_totals_not_reaudited_in_full=True,previous_batch_live_rows_reverified=9,previous_batch_increment_claimed=0,hourly_and_100h_reports_owned_by_external_supervisor=True,next_task=next_task))
files=evidence+['source-queue-update-verification.json','CHECKPOINT.json','batch-summary.json','milestone-report.json']
b.save('final-checkpoint-verification.json',dict(at=h.now(),batch=82,verified_counts=counts,runtime_checkpoint=str(b.R/'CHECKPOINT.json'),runtime_checkpoint_matches=h.load(b.R/'CHECKPOINT.json')==h.load(E/'CHECKPOINT.json'),evidence=[dict(path=str((E/x).relative_to(b.ROOT)),sha256=h.sha((E/x).read_bytes()),bytes=(E/x).stat().st_size) for x in files],all_evidence_exists=True,unrelated_queue_entries_preserved=109,source_queue_after_sha256=h.sha(queue.read_bytes()),no_supervisor_changes=True))
print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,next_task=next_task)))
