#!/usr/bin/env python3
"""Persist this bounded delivery and update only its researched Warsaw route."""
import copy, datetime, fcntl, importlib.util, json, os
from pathlib import Path

s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-warsaw-batch-000072.py'))
b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i;E=b.E
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);receipt=h.load(E/'batch-verification-receipt.json')
counts=receipt['verified_counts'];ids=receipt['production_ids']
assert counts==dict(new_painters=0,new_artworks=7,newly_illustrated=7,alternate_images=0,museum_links=7)
assert h.load(E/'independent-resume-verification.json')['live_snapshots_equal']
prod=h.load(E/'independent-production-verification.json');assert prod['plan_sha256']==pin
holdingids=[x['holdings'][0]['id'] for x in prod['rows'].values()]
with h.connect() as db,db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    assert h.snapshot(db,ids)==prod['rows']
    events=[dict(x) for x in db.execute("SELECT entity_type,entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='location_assertion' AND entity_id=ANY(%s::uuid[]) AND action='insert' ORDER BY entity_id",(holdingids,))]
    assert len(events)==7 and {x['entity_id'] for x in events}==set(holdingids)
    assert all(x['before_json'] in [None,{}] and x['after_json']['claim_type']=='holding' and x['after_json']['display_state'] is None for x in events)
b.save('independent-holding-audit-verification.json',dict(at=h.now(),insertions=7,records=events,current_display_claims=0))
now=h.now();before=h.load(E/'source-queue-before.json')
old=next(x for x in before['sources'] if x['source_id']=='national_museum_warsaw')
prev=old['resume_cursor'];oldprocessed=set(prev['processed_native_ids']);oldheld=set(prev['held_native_ids'])
newids=[r['source_id'] for r in p['records']]
checks={r['source_id']:r for r in h.load(E/'global-identity-reconciliation.json')['records']}
reasons={
 '481493':'Source creation date 1820 (?) is explicitly tentative. Preserve question mark and resolve inscription/date treatment and similarly titled physical versions before import; no exact-year assertion.',
 '498270':'Composite IK 412/a-b: E.Cz. is a goldsmith, with 1852 cover hallmark evidence. Reconcile component-specific creator/date roles; do not create or link a painter from the goldsmith label.',
 '498330':'Source second half nineteenth/twentieth century range crosses the through-1970 boundary. No invented eligible end year.',
 '498338':'IK 117/a-b icon and cover: structured second-half-nineteenth-century date differs from narrative nineteenth/twentieth-century cover and potentially earlier painted panel. Resolve component dates and physical-unit representation.',
 '498424':'Title matches existing IK 377 but proposed inventory is IK 199. Not declared a duplicate; compare two physical compositions, dimensions and provenance before adding.',
 '498490':'IK 26/a-b is icon with metal cover, not two independent artworks. Preserve fourth-quarter-nineteenth-century date and review complete component/image coverage before selection.',
 '498527':'Source describes possible canvas cut from a larger composition and historical police deposit. Establish complete surviving physical unit and custody/ownership distinction; retain open-ended before-1917 date without inventing a lower bound.',
 '498532':'Title matches existing IK 305 but proposed inventory is IK 299. Not declared a duplicate; compare compositions, dimensions and provenance before adding.',
 '498570':'Source says end of nineteenth century. Preserve qualifier; exact physical-version comparison against other Saint Nicholas inventories is outstanding. No invented exact year.',
 '498639':'Title matches existing IK 10 but proposed inventory is IK 394. Not declared a duplicate; compare exact physical composition and dimensions before adding.',
 '498643':'Source explicitly describes contemporary repainting of a nineteenth-century icon. Physical-version and creation-versus-repainting evidence require review; do not silently date modern painted layers to the nineteenth century.',
 '498670':'IK 56/a-b: structured seventeenth-century icon/eighteenth-century cover; narrative also permits eighteenth-century painting. Reconcile component dates, workshop roles and complete image before selection.',
 '498707':'IK 85/a-b includes icon and stamped metal cover with applied halo. Save as one composite inventory lead; review complete component/image representation before selection.'
}
reserve={'498583','498603','499394','499461'}
page=h.load(E/'warsaw-icons-page6.json')['data'];assert len(page['items'])==24
records=[]
for item in page['items']:
    oid=str(item['id']);assert oid not in oldprocessed
    o,rc=b.capture(int(oid))
    if oid in newids:
        decision='delivered_verified';reason='Globally reconciled inventory/native identity; own plan/source/rights checksums and empty transaction preimages, insert audits, storage and public bytes verified.'
    elif oid in reserve:
        decision='saved_cast_candidate_not_selected';reason='Historical devotional cast retained for a separate physical-cast and version review; this delivery selected painted icons. No image requested or production eligibility claimed.'
    else:
        decision='targeted_editorial_hold';reason=reasons[oid]
    records.append(dict(source_id=oid,title=o['title'],inventory=o['noEvidence'],source_date=o['createDates'],creators=o['authors'],owner=o['owner'],dimensions=o['dimensionText'],source_sha256=rc['sha256'],decision=decision,reason=reason,global_identity_checks=checks.get(oid),image_requested=oid in newids))
held=[r['source_id'] for r in records if r['decision']=='targeted_editorial_hold'];assert len(held)==13
b.save('page-six-editorial-dispositions.json',dict(at=now,page_items=24,new_detail_captures=24,selected=7,verified=7,held=13,saved_cast_candidates=4,search_hits=page['paginatorDetails']['totalItemsCount'],search_hits_are_not_eligible_artworks=True,records=records))
b.save('research-holds.json',dict(at=now,prior_held_ids=sorted(oldheld),held_native_ids=held,records=[r for r in records if r['decision']=='targeted_editorial_hold'],unchanged_holds_not_retried=True))
b.save('saved-cast-candidates.json',dict(at=now,source_ids=sorted(reserve),records=[r for r in records if r['source_id'] in reserve],next_step='Reuse saved metadata; reconcile individual casts globally and inspect complete native images only after selection. Do not create one record per scene or substitute a different casting.',production_increment=0))
b.save('failure-ledger.json',dict(at=now,production_failures=[],source_access_failures=[],resolved_local_prewrite_errors=[dict(stage='Interpreter',error='System Python lacked psycopg',resolution='Used established /tmp/artline-cyprus-venv/bin/python; no database writes occurred.'),dict(stage='Local overlap prevention',error='Images command could not acquire worker lock while preflight was running',resolution='Lock prevented overlap; after preflight exited, image stage succeeded. No source or production operation occurred in rejected invocation.')],provider_retries=0,unchanged_held_provider_requests=0))
next_task='Research up to 50 selected works from National Gallery of Ireland, an available undercovered original-registry route; inspect established access holds and official object-level evidence first. Warsaw resumes page 7; four saved cast candidates and 70 editorial holds remain separate. French reserve remains exhausted.'
source_final=dict(h.load(E/'source-register.json'),verified_at=now,verified_counts=counts,discovered_page_items=24,new_metadata_captures=24,metadata_candidates=10,selected_prepared_imported_verified=7,individually_viewed=7,prior_holds=57,new_holds=13,saved_cast_candidates=4,next_discovery_page=7,policy_evidence='Native object rights retrieved this batch; museum commercial-reuse policy capture reused from batch 57 and hash-verified, not newly fetched.',directory_coverage='One registry institution researched; directory coverage is not artwork coverage.',remaining_gaps='70 specific editorial holds, four saved cast leads, and page 7 onward. No claim of complete Warsaw coverage or current display.')
b.save('source-register-final.json',source_final)
evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-holding-audit-verification.json','independent-file-verification.json','independent-image-source-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','prior-batch-live-reconciliation.json','global-identity-reconciliation.json','creator-global-reconciliation.json','independent-historical-inventory-verification.json','page-six-editorial-dispositions.json','source-register-final.json','research-holds.json','saved-cast-candidates.json','source-access-holds.json','local-recovery-verification.json','failure-ledger.json']
q=copy.deepcopy(before);source=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw')
source.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(prev));c=source['resume_cursor']
c['processed_native_ids']=list(dict.fromkeys(c['processed_native_ids']+[r['source_id'] for r in records]))
c['delivered_native_ids']=list(dict.fromkeys(c['delivered_native_ids']+newids))
c['held_native_ids']=list(dict.fromkeys(c['held_native_ids']+held));assert len(c['held_native_ids'])==70
c['saved_cast_candidate_native_ids']=list(dict.fromkeys(c.get('saved_cast_candidate_native_ids',[])+sorted(reserve)))
c.update(query_url=h.load(E/'warsaw-icons-page6.receipt.json')['url'],captured_page=6,next_page_after_pending=7,next_discovery_page=7,pending_native_ids_current_page=[],priority_native_ids=[],metadata_page_sha256=h.load(E/'warsaw-icons-page6.receipt.json')['sha256'],production_authentication_required=False,authentication_last_verified_at=now,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],saved_discovery=str((E/'warsaw-icons-page6.json').relative_to(b.ROOT)),review_ledger=str((E/'page-six-editorial-dispositions.json').relative_to(b.ROOT)),cast_candidate_ledger=str((E/'saved-cast-candidates.json').relative_to(b.ROOT)),next_step='Rotate institutions, then discover page 7. Reuse saved captures for four cast candidates. Do not retry 70 editorial holds without new resolving evidence.')
source.update(status='seven_page6_painted_icons_holdings_images_verified_page7_next',checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),last_checked_at=now,access_status='Official page 6 and 24 metadata records HTTP 200; seven native images and production/public delivery verified.',verified_counts=counts,latest_batch_verified_counts=counts)
source['programme_verified_counts']={k:source['programme_verified_counts'][k]+v for k,v in counts.items()}
source['remaining_gaps']=['70 editorial holds: 57 preserved and 13 new.','Four saved historical cast candidates require physical-version review, not an access hold.','Page 7 onward; 306 search hits do not equal eligible works.','Whole-museum coverage incomplete; no directory coverage increment.']
source.setdefault('research_history',[]).append(dict(batch=72,at=now,new_metadata_objects=24,selected_for_import=7,held=13,saved_cast_candidates=4,live_reconciliation=True,verified_counts=counts,evidence=str((E/'batch-verification-receipt.json').relative_to(b.ROOT))))
source['evidence_paths']=list(dict.fromkeys(source['evidence_paths']+[str((E/x).relative_to(b.ROOT)) for x in evidence]))
desired=b.save('source-queue-after.json',q);queue=E.parents[1]/'source-queue.json'
with (b.R/'queue-update.lock').open('a+') as qlock:
    fcntl.flock(qlock,fcntl.LOCK_EX);current=h.load(queue);assert current in [before,desired],'Concurrent queue change requires merge'
    if current==before:
        temp=queue.with_name('source-queue.batch000072.tmp')
        with temp.open('w') as f:json.dump(desired,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(temp,queue)
after=h.load(queue);assert after==desired
assert {x['source_id']:x for x in before['sources'] if x['source_id']!='national_museum_warsaw'}=={x['source_id']:x for x in after['sources'] if x['source_id']!='national_museum_warsaw'}
b.save('independent-queue-verification.json',dict(at=h.now(),before_sha256=h.sha((E/'source-queue-before.json').read_bytes()),after_sha256=h.sha(queue.read_bytes()),total_sources=111,unrelated_entries_preserved=110,changed_source_ids=['national_museum_warsaw'],newly_delivered_native_ids=newids,current_page_held_ids=held,saved_cast_candidates=sorted(reserve),all_prior_hold_ids_preserved=True,next_discovery_page=7))
master=h.load(E.parents[1]/'CHECKPOINT.json');assert master['inflight']['batch']==72
started=master['inflight']['started_at'];finished=h.now();elapsed=(datetime.datetime.fromisoformat(finished)-datetime.datetime.fromisoformat(started)).total_seconds()
assert datetime.datetime.fromisoformat(h.load(h.BACKUP/b.PHASE/'locked-before.json.gz')['at'])>=datetime.datetime.fromisoformat(started)
cp=b.save('CHECKPOINT.json',dict(at=finished,started_at=started,batch=72,outcome='progress',stage='independently_verified_complete',elapsed_seconds=elapsed,verified_counts=counts,discovered_page_items=24,new_metadata_captures=24,metadata_candidates=10,selected=7,prepared=7,individually_viewed=7,imported=7,verified=7,held_current_page=13,saved_cast_candidates=4,production_ids=ids,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],production_target='artline-508319:europe-west1:artline-postgres',local_catalogue_connections=0,unrelated_queue_entries_preserved=110,next_task=next_task,blocker='',resume_commands=['/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000072-verify.py','/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000072-resume.py','/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000072-finalize.py'],source_queue_cursor=c,delivered_batch_do_not_count_again=True,external_supervisor_unchanged=True,supervisor_running_claim=False,reporting='External supervisor owns continuation and hourly/milestone reports. This worker executed one bounded batch.',limitations=['315-pixel-wide supplied reproductions; no tiny inscription or absent reverse-view claim.','Source workshops remain qualified object labels, no fabricated painter.','Scoped schema and affected-row recovery, not full database backup.','70 holds, four cast candidates and later pages remain.']))
h.save(b.R/'CHECKPOINT.json',cp)
b.save('batch-summary.json',dict(at=finished,batch=72,elapsed_seconds=elapsed,verified_counts=counts,next_task=next_task,failures=h.load(E/'failure-ledger.json'),external_supervisor_unmodified=True))
b.save('milestone-report.json',dict(at=finished,elapsed_seconds_this_batch=elapsed,verified_counts_this_batch=counts,supervisor_reported_prior_totals=master['totals'],expected_cumulative_after_supervisor_accepts_this_result={k:master['totals'][k]+v for k,v in counts.items()},prior_totals_not_reaudited_in_full=True,previous_batch_live_rows_reverified=7,previous_batch_increment_claimed=0,next_task=next_task,hourly_reports_owned_by_external_supervisor=True))
paths=evidence+['independent-queue-verification.json','CHECKPOINT.json','batch-summary.json','milestone-report.json']
b.save('final-checkpoint-verification.json',dict(at=h.now(),batch=72,verified_counts=counts,runtime_checkpoint=str(b.R/'CHECKPOINT.json'),runtime_checkpoint_matches=h.load(b.R/'CHECKPOINT.json')==h.load(E/'CHECKPOINT.json'),evidence=[dict(path=str((E/x).relative_to(b.ROOT)),sha256=h.sha((E/x).read_bytes()),bytes=(E/x).stat().st_size) for x in paths],all_evidence_exists=True,unrelated_queue_entries_preserved=110,source_queue_after_sha256=h.sha(queue.read_bytes()),no_supervisor_changes=True))
print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,unrelated_queue_entries_preserved=110,next_task=next_task)))
