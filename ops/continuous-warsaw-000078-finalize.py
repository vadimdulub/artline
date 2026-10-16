#!/usr/bin/env python3
"""Finalize one verified batch; preserve unrelated queue entries and supervisor."""
import copy, datetime, fcntl, importlib.util, json, os
from pathlib import Path

s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-warsaw-batch-000078.py'))
b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i;E=b.E
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);receipt=h.load(E/'batch-verification-receipt.json')
counts=receipt['verified_counts'];ids=receipt['production_ids']
assert counts==dict(new_painters=0,new_artworks=5,newly_illustrated=5,alternate_images=0,museum_links=5)
assert h.load(E/'independent-resume-verification.json')['live_snapshots_equal']
prod=h.load(E/'independent-production-verification.json');assert prod['plan_sha256']==pin
holdingids=[x['holdings'][0]['id'] for x in prod['rows'].values()]
with h.connect() as db,db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    assert h.snapshot(db,ids)==prod['rows']
    events=[dict(x) for x in db.execute("SELECT entity_type,entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='location_assertion' AND entity_id=ANY(%s::uuid[]) AND action='insert' ORDER BY entity_id",(holdingids,))]
    assert len(events)==5 and {x['entity_id'] for x in events}==set(holdingids)
    assert all(x['before_json'] in [None,{}] and x['after_json']['claim_type']=='holding' and x['after_json']['display_state'] is None for x in events)
b.save('independent-holding-audit-verification.json',dict(at=h.now(),insertions=5,records=events,current_display_claims=0))
now=h.now();before=h.load(E/'source-queue-before.json')
old=next(x for x in before['sources'] if x['source_id']=='national_museum_warsaw')
prev=old['resume_cursor'];oldprocessed=set(prev['processed_native_ids']);oldheld=set(prev['held_native_ids'])
newids=[r['source_id'] for r in p['records']]
checks={r['source_id']:r for r in h.load(E/'global-identity-reconciliation.json')['records']}
reasons={
 '498688':'Composite IK 73/a-b includes a painted icon and 1851 silver cover. K.C. is the stamped metalwork maker. Resolve component dates and roles before importing; no fabricated painter from a goldsmith mark.',
 '498638':'Source says end of nineteenth century; retain that qualifier. Same Pokrow subject as other inventories; composition/version reconciliation remains, without assigning an invented exact year.',
 '498684':'Same source title as existing IK 377, while this inventory is IK 67. Not declared a duplicate. Reconcile both physical compositions, dimensions and source histories before adding.',
 '498373':'Structured dates include 1680s, 1750 and circa 1900; narrative and reverse inscription conflict, with repeated repainting and a named restorer. Resolve creation, restoration and workshop roles; do not treat restoration as original creation.',
 '498519':'Composite IK 284/a-b: painted panel and cover. Review the surviving components and complete source view as a single inventory unit before selection.',
 '498668':'Composite IK 54/a-b includes painted icon, basma and crowns. Review component-specific dates and full physical-unit representation; do not multiply the inventory into separate artworks.',
 '498410':'Source explicitly describes contemporary partial repainting of the nineteenth-century icon. Resolve the physical painted version and creation versus restoration layers before image selection.',
 '498671':'Source names Iwan Aleksandrow and gives the signed date 1721, but narrative explicitly doubts identity with the known seventeenth-century icon painter. Preserve source attribution and signature; resolve person identity without fabricating or falsely linking a painter.',
 '498511':'Same title as existing IK 441, while this inventory is IK 278. Not declared a duplicate. Compare physical compositions, dimensions and provenance before insertion.'
}
reserve={'498523','499385','498580','498577','498559','498599','498587','499391'}
page=h.load(E/'warsaw-icons-page7.json')['data'];assert len(page['items'])==24
records=[];skipped=[]
for item in page['items']:
    oid=str(item['id'])
    if oid in oldprocessed:
        skipped.append(oid);continue
    o,rc=b.capture(int(oid))
    if oid in newids:
        decision='delivered_verified';reason='Exact native inventory, own source/plan/rights checksums, empty transaction preimages, insert audits, storage and public bytes independently verified.'
    elif oid in reserve:
        decision='saved_cast_candidate_not_selected';reason='Historical devotional cast saved for physical casting and version review. This batch selected painted icons. No image requested and no production eligibility claimed.'
    else:
        decision='targeted_editorial_hold';reason=reasons[oid]
    records.append(dict(source_id=oid,title=o['title'],inventory=o['noEvidence'],source_date=o['createDates'],creators=o['authors'],owner=o['owner'],dimensions=o['dimensionText'],source_sha256=rc['sha256'],decision=decision,reason=reason,global_identity_checks=checks.get(oid),image_requested=oid in newids))
held=[r['source_id'] for r in records if r['decision']=='targeted_editorial_hold']
assert len(records)==22 and len(held)==9 and len(skipped)==2
b.save('page-seven-editorial-dispositions.json',dict(at=now,page_items=24,new_detail_captures=22,previously_processed_skipped=skipped,selected=5,verified=5,held=9,saved_cast_candidates=8,search_hits=page['paginatorDetails']['totalItemsCount'],search_hits_are_not_eligible_artworks=True,records=records))
b.save('research-holds.json',dict(at=now,prior_held_ids=sorted(oldheld),held_native_ids=held,records=[r for r in records if r['decision']=='targeted_editorial_hold'],unchanged_holds_not_retried=True))
b.save('saved-cast-candidates.json',dict(at=now,source_ids=sorted(reserve),records=[r for r in records if r['source_id'] in reserve],next_step='Reuse saved metadata and reconcile individual cast/version identities before any image selection. Joined triptychs and crosses are individual inventory units.',production_increment=0))
b.save('failure-ledger.json',dict(at=now,production_failures=[],source_access_failures=[h.load(E/'digitalnz-access-verification.json')],provider_retries=0,unchanged_held_provider_requests=0,prewrite_assertion_failures=[]))
b.save('source-access-holds-final.json',dict(at=now,inherited_ledger=str((E/'source-access-holds.json').relative_to(b.ROOT)),inherited_sha256=h.sha((E/'source-access-holds.json').read_bytes()),new_holds=[h.load(E/'digitalnz-access-verification.json')],no_bypass_or_held_provider_retries=True,warsaw_access='Native API and five selected native images HTTP 200; no Warsaw access hold.',editorial_holds='Separate research-holds.json; not provider access restrictions.'))
next_task='Resume SHUZO’s 19 saved pending museum records after checking source-specific holds and exact production identities; preserve its from=25 cursor. Rotate institutions. Warsaw resumes page 8 with 79 editorial holds and 12 saved cast candidates; DigitalNZ documentation/terms HTTP 403 remains held without retries.'
b.save('source-register-final.json',dict(h.load(E/'source-register.json'),verified_at=now,verified_counts=counts,discovered_page_items=24,new_metadata_captures=22,metadata_candidates=7,selected_prepared_imported_verified=5,individually_viewed=5,prior_holds=70,new_holds=9,saved_cast_candidates=8,next_discovery_page=8,policy_evidence='Native object rights freshly captured; museum commercial-reuse policy capture reused from batch 57 and hash-verified, not freshly fetched.',directory_coverage='One museum object route and one blocked aggregator route researched. No directory coverage increment.',remaining_gaps='79 specific editorial holds, 12 saved cast candidates including four prior leads, and page 8 onward. No whole-museum coverage or current-display claim.'))
evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-holding-audit-verification.json','independent-file-verification.json','independent-image-source-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','prior-batch-live-reconciliation.json','global-identity-reconciliation.json','creator-global-reconciliation.json','independent-historical-inventory-verification.json','page-seven-editorial-dispositions.json','source-register-final.json','research-holds.json','saved-cast-candidates.json','source-access-holds.json','source-access-holds-final.json','local-recovery-verification.json','failure-ledger.json','digitalnz-access-verification.json']
q=copy.deepcopy(before);source=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw')
source.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(prev));c=source['resume_cursor']
c['processed_native_ids']=list(dict.fromkeys(c['processed_native_ids']+[r['source_id'] for r in records]))
c['delivered_native_ids']=list(dict.fromkeys(c['delivered_native_ids']+newids))
c['held_native_ids']=list(dict.fromkeys(c['held_native_ids']+held));assert len(c['held_native_ids'])==79
c['saved_cast_candidate_native_ids']=list(dict.fromkeys(c.get('saved_cast_candidate_native_ids',[])+sorted(reserve)));assert len(c['saved_cast_candidate_native_ids'])==12
c.update(query_url=h.load(E/'warsaw-icons-page7.receipt.json')['url'],captured_page=7,next_page_after_pending=8,next_discovery_page=8,pending_native_ids_current_page=[],priority_native_ids=[],metadata_page_sha256=h.load(E/'warsaw-icons-page7.receipt.json')['sha256'],production_authentication_required=False,authentication_last_verified_at=now,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],saved_discovery=str((E/'warsaw-icons-page7.json').relative_to(b.ROOT)),review_ledger=str((E/'page-seven-editorial-dispositions.json').relative_to(b.ROOT)),cast_candidate_ledger=str((E/'saved-cast-candidates.json').relative_to(b.ROOT)),prior_cast_candidate_ledger=prev.get('cast_candidate_ledger'),next_step='Rotate institutions, then discover page 8. Reuse saved cast captures. Do not retry 79 unchanged editorial holds without resolving evidence.')
source.update(status='five_page7_painted_icons_holdings_images_verified_page8_next',checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),last_checked_at=now,access_status='Page 7 and 22 new metadata captures HTTP 200; five native images and production/public delivery verified.',verified_counts=counts,latest_batch_verified_counts=counts)
source['programme_verified_counts']={k:source['programme_verified_counts'][k]+v for k,v in counts.items()}
source['remaining_gaps']=['79 editorial holds: 70 preserved and nine new.','12 saved historical cast candidates: four preserved and eight new.','Page 8 onward; source search hits are not eligible artwork counts.','Whole-museum coverage incomplete; no directory coverage increment.']
source.setdefault('research_history',[]).append(dict(batch=78,at=now,new_metadata_objects=22,selected_for_import=5,held=9,saved_cast_candidates=8,prior_processed_skipped=2,live_reconciliation=True,verified_counts=counts,evidence=str((E/'batch-verification-receipt.json').relative_to(b.ROOT))))
source['evidence_paths']=list(dict.fromkeys(source['evidence_paths']+[str((E/x).relative_to(b.ROOT)) for x in evidence]))
digital=next(x for x in q['sources'] if x['source_id']=='digitalnz')
digital.update(status='documentation_and_terms_web_http403_access_hold',checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),last_checked_at=now,policy_reference='Original 111-source registry digitalnz row; current docs and terms inaccessible; no source rules inferred.',access_status='web.run returned HTTP 403 for official API documentation and terms; API and objects unrequested.',resume_cursor=dict(route='official_api_docs_and_terms',urls=['https://digitalnz.org/developers/api-docs-v3','https://digitalnz.org/about/terms-of-use'],object_requests=0,image_requests=0,retry_allowed=False,external_state_change_required='Permitted access to official documentation and terms',next_step='Rotate to other eligible sources; no repeated unchanged 403 requests.'),remaining_gaps=['No museum object evidence captured or selected. API access and actual unauthenticated limits remain unverified.'])
digital['evidence_paths']=list(dict.fromkeys(digital.get('evidence_paths',[])+[str((E/'digitalnz-access-verification.json').relative_to(b.ROOT))]))
desired=b.save('source-queue-after.json',q);queue=E.parents[1]/'source-queue.json'
with (b.R/'queue-update.lock').open('a+') as qlock:
    fcntl.flock(qlock,fcntl.LOCK_EX);current=h.load(queue);assert current in [before,desired],'Concurrent queue change requires merge'
    if current==before:
        temp=queue.with_name('source-queue.batch000078.tmp')
        with temp.open('w') as f:json.dump(desired,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(temp,queue)
after=h.load(queue);assert after==desired
changed={'national_museum_warsaw','digitalnz'}
assert {x['source_id']:x for x in before['sources'] if x['source_id'] not in changed}=={x['source_id']:x for x in after['sources'] if x['source_id'] not in changed}
b.save('independent-queue-verification.json',dict(at=h.now(),before_sha256=h.sha((E/'source-queue-before.json').read_bytes()),after_sha256=h.sha(queue.read_bytes()),total_sources=111,unrelated_entries_preserved=109,changed_source_ids=sorted(changed),newly_delivered_native_ids=newids,current_page_held_ids=held,saved_cast_candidates=sorted(reserve),all_prior_hold_ids_preserved=True,next_discovery_page=8))
master=h.load(E.parents[1]/'CHECKPOINT.json');assert master['inflight']['batch']==78
started=master['inflight']['started_at'];finished=h.now();elapsed=(datetime.datetime.fromisoformat(finished)-datetime.datetime.fromisoformat(started)).total_seconds()
assert datetime.datetime.fromisoformat(h.load(h.BACKUP/b.PHASE/'locked-before.json.gz')['at'])>=datetime.datetime.fromisoformat(started)
cp=b.save('CHECKPOINT.json',dict(at=finished,started_at=started,batch=78,outcome='progress',stage='independently_verified_complete',elapsed_seconds=elapsed,verified_counts=counts,discovered_page_items=24,new_metadata_captures=22,previously_processed_skipped=skipped,metadata_candidates=7,selected=5,prepared=5,individually_viewed=5,imported=5,verified=5,held_current_page=9,saved_cast_candidates=8,production_ids=ids,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],production_target='artline-508319:europe-west1:artline-postgres',local_catalogue_connections=0,unrelated_queue_entries_preserved=109,next_task=next_task,blocker='',resume_commands=['/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000078-verify.py','/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000078-resume.py','/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000078-finalize.py'],source_queue_cursor=c,delivered_batch_do_not_count_again=True,external_supervisor_unchanged=True,supervisor_running_claim=False,reporting='Existing external supervisor owns continuation and hourly/milestone reports. One bounded batch executed.',limitations=['315-pixel-wide supplied museum images; no tiny-inscription or absent-reverse-view claim.','Workshop and school attributions remain object-level labels.','Scoped schema and affected-row recovery, not full database backup.','79 editorial holds, 12 cast candidates and later pages remain.']))
h.save(b.R/'CHECKPOINT.json',cp)
b.save('batch-summary.json',dict(at=finished,batch=78,elapsed_seconds=elapsed,verified_counts=counts,next_task=next_task,failures=h.load(E/'failure-ledger.json'),external_supervisor_unmodified=True))
b.save('milestone-report.json',dict(at=finished,elapsed_seconds_this_batch=elapsed,verified_counts_this_batch=counts,supervisor_reported_prior_totals=master['totals'],expected_cumulative_after_supervisor_accepts_this_result={k:master['totals'][k]+v for k,v in counts.items()},prior_totals_not_reaudited_in_full=True,previous_batch_live_rows_reverified=11,previous_batch_increment_claimed=0,next_task=next_task,hourly_reports_owned_by_external_supervisor=True))
paths=evidence+['independent-queue-verification.json','CHECKPOINT.json','batch-summary.json','milestone-report.json']
b.save('final-checkpoint-verification.json',dict(at=h.now(),batch=78,verified_counts=counts,runtime_checkpoint=str(b.R/'CHECKPOINT.json'),runtime_checkpoint_matches=h.load(b.R/'CHECKPOINT.json')==h.load(E/'CHECKPOINT.json'),evidence=[dict(path=str((E/x).relative_to(b.ROOT)),sha256=h.sha((E/x).read_bytes()),bytes=(E/x).stat().st_size) for x in paths],all_evidence_exists=True,unrelated_queue_entries_preserved=109,source_queue_after_sha256=h.sha(queue.read_bytes()),no_supervisor_changes=True))
print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,unrelated_queue_entries_preserved=109,next_task=next_task)))
