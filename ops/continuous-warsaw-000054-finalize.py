#!/usr/bin/env python3
"""Persist one verified batch; update only the researched registry route."""
import copy, datetime, fcntl, importlib.util, json, os
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-warsaw-batch-000054.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i;E=b.E
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
receipt=h.load(E/'batch-verification-receipt.json')
assert receipt['verified_counts']==dict(new_painters=0,new_artworks=6,newly_illustrated=6,alternate_images=0,museum_links=6)
assert h.load(E/'independent-resume-verification.json')['live_snapshots_equal']
p,pin=h.pinned(b.PHASE);ids=receipt['production_ids']
production=h.load(E/'independent-production-verification.json')
holdingids=[x['holdings'][0]['id'] for x in production['rows'].values()]
with h.connect() as db,db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    audit=[dict(x) for x in db.execute("SELECT entity_type,entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='location_assertion' AND entity_id=ANY(%s::uuid[]) AND action='insert' ORDER BY entity_id",(holdingids,))]
    assert len(audit)==6 and {x['entity_id'] for x in audit}==set(holdingids)
    assert all(x['before_json'] in [None,{}] and x['after_json']['claim_type']=='holding' and x['after_json']['review_state']=='accepted' and x['after_json']['display_state'] is None for x in audit)
b.save('independent-holding-audit-verification.json',dict(at=h.now(),records=audit,insertions=6,current_display_claims=0))
register=b.save('source-register-final.json',dict(h.load(E/'source-register.json'),at=h.now(),last_checked_at=h.now(),metadata_access='Six checksum-verified official native object captures reused from batch 52; no repeated object downloads',image_access='Six selected primary native museum JPEGs returned HTTP 200',metadata_capture_origin='docs/research/continuous-production-20261011/batches/000052/warsaw-discovery.json',selected_native_ids=[r['source_id'] for r in p['records']],verified_counts=receipt['verified_counts'],existing_institution_artworks_before=899,selection_rationale='Undercovered Russian/Old Believer icon object queue at original-registry institution; museum-wide coverage is not declared complete',remaining_gaps='18 page-three cast, composite, qualified creator and date reviews remain unselected; 27 earlier holds unchanged. No directory-coverage or current-display claim.'))
next_task='Reconcile batch-54 receipts, then rotate to Princeton native API image gaps: process up to 25 of the 50 saved unresearched native IDs in the original batch-26 bounded-gap-input.json, beginning 37715, 42188, 15819. Preserve the Princeton website access hold; use the established API workflow. Retain the 18 Warsaw page-three reviews before advancing to page 4.'
before=h.load(E/'source-queue-before.json');q=copy.deepcopy(before)
source=next(x for x in q['sources'] if x['source_id']=='national_museum_warsaw')
source['prior_resume_cursors'].append(copy.deepcopy(source['resume_cursor']))
cursor=source['resume_cursor'];newids=[r['source_id'] for r in p['records']]
cursor['processed_native_ids']=list(dict.fromkeys(cursor['processed_native_ids']+newids))
cursor['delivered_native_ids']=list(dict.fromkeys(cursor['delivered_native_ids']+newids))
cursor['pending_native_ids_current_page']=[x for x in cursor['pending_native_ids_current_page'] if x not in newids]
assert len(cursor['pending_native_ids_current_page'])==18
cursor['priority_native_ids']=[]
cursor['production_authentication_required']=False
cursor['authentication_last_verified_at']=register['at']
cursor['metadata_plan_sha256']=pin
cursor['image_selection_sha256']=receipt['image_selection_sha256']
cursor['review_ledger']=str((E/'research-holds.json').relative_to(b.ROOT))
cursor['next_step']='Rotate to Princeton native image-gap queue. On return, resolve saved remaining 18 page-three cast, component, date and creator cases from existing captures; do not reharvest them or advance page 4 before dispositions are persisted.'
source.update(status='six_page3_russian_old_believer_icons_and_primary_images_verified_eighteen_saved_reviews_pending',checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),last_checked_at=register['at'],access_status='Saved official metadata checksum-verified; six native JPEG HTTP 200; production authentication verified',verified_counts=receipt['verified_counts'],latest_batch_verified_counts=receipt['verified_counts'])
source['programme_verified_counts']={k:source['programme_verified_counts'][k]+v for k,v in receipt['verified_counts'].items()}
source['remaining_gaps']=['27 earlier exact date/unit/version holds unchanged; no repeated requests.','18 remaining page-three records need saved cast, composite, date or creator review; none counted or selected.','Page 4 is next after pending page-three dispositions. Native result total 306 is not an eligible or delivered count.','Museum-wide artwork and directory coverage remain incomplete.']
source.setdefault('research_history',[]).append(dict(batch=54,at=register['at'],reused_saved_objects=6,new_metadata_requests=0,selected_for_import=6,live_reconciliation=True,verified_counts=receipt['verified_counts'],evidence=str((E/'batch-verification-receipt.json').relative_to(b.ROOT))))
evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-holding-audit-verification.json','independent-file-verification.json','independent-image-source-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-resume-verification.json','actual-visual-review.json','prior-batch-live-reconciliation.json','global-identity-reconciliation.json','creator-global-reconciliation.json','source-register-final.json','research-holds.json','source-access-holds.json']
source['evidence_paths']=list(dict.fromkeys(source['evidence_paths']+[str((E/x).relative_to(b.ROOT)) for x in evidence]))
desired=b.save('source-queue-after.json',q)
queue=E.parent.parent/'source-queue.json'
with (b.R/'queue-update.lock').open('a+') as qlock:
    fcntl.flock(qlock,fcntl.LOCK_EX)
    current=h.load(queue)
    assert current in [before,desired], 'Concurrent queue modification: preserve and reconcile before updating'
    if current==before:
        temp=queue.with_name('source-queue.batch000054.tmp')
        with temp.open('w') as f:
            json.dump(desired,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(temp,queue)
after=h.load(queue)
assert after==desired
old_other={x['source_id']:x for x in before['sources'] if x['source_id']!='national_museum_warsaw'}
new_other={x['source_id']:x for x in after['sources'] if x['source_id']!='national_museum_warsaw'}
assert old_other==new_other and len(old_other)==110
b.save('independent-queue-verification.json',dict(at=h.now(),source_queue=str(queue.relative_to(b.ROOT)),before_sha256=h.sha((E/'source-queue-before.json').read_bytes()),after_sha256=h.sha(queue.read_bytes()),unrelated_entries_preserved=110,total_sources=111,changed_source_ids=['national_museum_warsaw'],delivered_native_ids=newids,pending_native_ids=cursor['pending_native_ids_current_page'],prior_held_ids_preserved=cursor['held_native_ids'],next_page_after_pending=4,programme_source_counts=source['programme_verified_counts']))
started=h.load(E.parent.parent/'CHECKPOINT.json')['inflight']['started_at']
finished=register['at'];seconds=(datetime.datetime.fromisoformat(finished)-datetime.datetime.fromisoformat(started)).total_seconds()
checkpoint=b.save('CHECKPOINT.json',dict(at=finished,started_at=started,batch=54,outcome='progress',stage='six_new_illustrated_icons_and_holdings_independently_verified_resume_checked',elapsed_seconds=seconds,verified_counts=receipt['verified_counts'],reused_saved_native_records=6,newly_discovered=0,selected=6,prepared=6,individually_viewed=6,imported=6,verified=6,pending_page3_reviews=18,production_ids=ids,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],production_target='artline-508319:europe-west1:artline-postgres',local_catalogue_connections=0,unrelated_queue_entries_preserved=110,blocker='',next_task=next_task,resume=dict(verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000054-verify.py',resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000054-resume.py',finalize_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-warsaw-000054-finalize.py',receipt=str((E/'batch-verification-receipt.json').relative_to(b.ROOT)),delivered_batch_do_not_count_again=True),external_supervisor_unchanged=True,supervisor_running_claim=False,cumulative_counts='This batch contributes 6 new artworks, 6 newly illustrated and 6 holdings; no prior deliveries counted. External supervisor owns programme totals and hourly/100-hour reporting.',limitations=['All six actual derivatives individually viewed; source rendition width 315 px limits fine detail review.','Existing 899 Warsaw artwork rows verified unchanged.','18 saved page-three objects remain unselected; wider museum coverage incomplete.']))
h.save(b.R/'CHECKPOINT.json',checkpoint)
b.save('batch-summary.json',dict(at=finished,batch=54,elapsed_seconds=seconds,verified_counts=receipt['verified_counts'],metadata_plan_sha256=pin,next_task=next_task,failures=[dict(surface='web open tool',finding='Native page cache miss and exploratory policy URL inaccessible; no repeated request. Authoritative saved official API captures and earlier correct museum policy URL used instead.',production_impact='None')],unresolved_cases=18,continuous_execution='Bounded worker only; existing external supervisor unchanged',hourly_milestone='Worker duration under one hour; external supervisor owns cumulative hourly and 100-hour reports'))
paths=evidence+['independent-queue-verification.json','CHECKPOINT.json','batch-summary.json']
verification=b.save('final-checkpoint-verification.json',dict(at=h.now(),batch=54,verified_counts=receipt['verified_counts'],runtime_checkpoint=str(b.R/'CHECKPOINT.json'),runtime_checkpoint_matches=h.load(b.R/'CHECKPOINT.json')==h.load(E/'CHECKPOINT.json'),evidence=[dict(path=str((E/x).relative_to(b.ROOT)),sha256=h.sha((E/x).read_bytes()),bytes=(E/x).stat().st_size) for x in paths],all_evidence_exists=True,unrelated_queue_entries_preserved=110,source_queue_after_sha256=h.sha(queue.read_bytes()),no_supervisor_changes=True))
print(json.dumps(dict(verified_counts=receipt['verified_counts'],elapsed_seconds=seconds,unrelated_queue_entries_preserved=110,next_task=next_task)))
