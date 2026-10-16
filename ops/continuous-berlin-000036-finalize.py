#!/usr/bin/env python3
"""Persist verified batch handoff and update only the researched registry route."""
import copy,datetime,fcntl,importlib.util,json,os
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000036.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;E=b.E
receipt=h.load(E/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts==dict(new_painters=0,new_artworks=2,newly_illustrated=2,alternate_images=0,museum_links=2)
assert h.load(E/'independent-resume-verification.json')['no_new_writes_on_resume']
recon=h.load(E/'global-identity-reconciliation.json');held=[x for x in recon['records'] if x['outcome']!='selected_new']
b.save('research-holds.json',dict(at=h.now(),objects=held,ignored_discovery=dict(capture='source-captures/icon-search.receipt.json',url='https://search.smb.museum/en?doc_types=Ikone',reason='Legacy doc_types parameter ignored by current portal; returned broad unrelated catalogue. No objects from this result selected. Use a verified current filter or exact native objects next time.'),no_image_requests_for_held_objects=True))
resume=dict(route='exact_official_SMB_native_objects',inspected_object_ids=b.ALL,delivered_object_ids=b.SELECTED,delivered_inventory_numbers=['6430','6431'],held_object_ids=[x['source_id'] for x in held],next_step='Research new exact Byzantine object IDs or resolve native long-term-loan ownership/custody representation for the three held IDs. Do not replay delivered objects or legacy ignored doc_types search.',institution_id=b.MID,metadata_plan_sha256=receipt['plan_sha256'],image_selection_sha256=receipt['image_selection_sha256'])
next_task='Review up to 25 existing Te Papa image gaps using exact object identities and record-specific reusable rights; begin with institution da3b80d7-dc07-5573-90ff-25a76a7b8d2e. Preserve all source holds and Berlin’s saved loan/custody queue.'
evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-file-verification.json','independent-image-source-verification.json','independent-storage-verification.json','independent-public-verification.json','actual-visual-review.json','independent-resume-verification.json','prior-write-reconciliation.json','global-identity-reconciliation.json','institution-reconciliation.json','research-holds.json','source-register.json']
checkpoint=dict(at=h.now(),batch=36,stage='verified_complete',verified_counts=counts,new_institutions=1,discovered=5,selected=2,prepared=2,imported=2,verified=2,held=3,creators='No named creators supplied by source; no new artist records or invented links.',next_task=next_task,resume=resume,evidence=[str((E/x).relative_to(b.ROOT)) for x in evidence],local_catalogue_connections=0,external_supervisor_unchanged=True)
b.save('CHECKPOINT.json',checkpoint);h.save(b.R/'CHECKPOINT.json',checkpoint)
qp=E.parents[1]/'source-queue.json'
if not (E/'source-queue-update-verification.json').exists():
 with (b.R.parent.parent/'source-queue-update.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);q=h.load(qp);old=copy.deepcopy(q)
  row=next(x for x in q['sources'] if x['source_id']=='staatliche_museen_berlin')
  if row.get('resume_cursor'):row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(row['resume_cursor']))
  row.update(status='two_new_byzantine_mosaic_icons_holdings_and_public_domain_primary_images_verified',last_checked_at=h.now(),checkpoint=str((E/'CHECKPOINT.json').relative_to(b.ROOT)),resume_cursor=resume,verified_counts=counts,access_status='Native official object pages and two selected PDM front-view JPEGs HTTP 200; robots allows public search and AI input.',policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',remaining_gaps=['Only five objects researched; directory and wider collection coverage incomplete.','Three long-term loans to Frankfurt held for explicit ownership/custody treatment; no current-display assertion.','Legacy doc_types query ignored; do not use broad result as selected icon evidence.'])
  for name in evidence:
   path=str((E/name).relative_to(b.ROOT))
   if path not in row.setdefault('evidence_paths',[]):row['evidence_paths'].append(path)
  assert [x for x in old['sources'] if x['source_id']!='staatliche_museen_berlin']==[x for x in q['sources'] if x['source_id']!='staatliche_museen_berlin']
  assert all(q[k]==v for k,v in old.items() if k!='sources') and len(q['sources'])==111
  b.save('source-queue-immediately-before-update.json',old);tmp=qp.with_suffix('.batch36.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2));os.replace(tmp,qp);assert h.load(qp)==q
  b.save('source-queue-update-verification.json',dict(at=h.now(),updated_sources=['staatliche_museen_berlin'],before_semantic_sha256=h.sha(json.dumps(old,sort_keys=True).encode()),after_file_sha256=h.sha(qp.read_bytes()),unrelated_entries_preserved=True,entry=row))
root=h.load(E.parents[1]/'CHECKPOINT.json');assert root['inflight']['batch']==36
now=datetime.datetime.now(datetime.timezone.utc);start=datetime.datetime.fromisoformat(root['inflight']['started_at']);overall=datetime.datetime.fromisoformat(root['started_at'])
b.save('milestone-report.json',dict(at=now.isoformat(),measured_batch_runtime_seconds=(now-start).total_seconds(),measured_programme_runtime_hours=(now-overall).total_seconds()/3600,prior_supervisor_verified_totals=root['totals'],verified_batch=counts,cumulative_programme_after_batch={k:root['totals'][k]+counts[k] for k in counts},not_a_live_whole_catalogue_census=True,failures=['Default Python lacked existing research dependencies; established /tmp/artline-cyprus-venv used.','Initial Nuxt Set decoder did not handle a zero-member tagged value; corrected using saved HTTP 200 captures before staging.','Legacy doc_types query ignored by current portal; result discarded.'],unresolved=held,next_task=next_task,external_supervisor_responsible_for_hourly_and_100_hour_reports=True,supervisor_not_modified=True))
paths=evidence+['source-queue-update-verification.json','milestone-report.json','CHECKPOINT.json']
result=dict(outcome='progress',summary='Verified two new Byzantine mosaic icons, two primary images and two documented Berlin museum holdings. Both images individually viewed; production attribution, storage, public delivery and no-write resume verified. Anonymous creators preserved; local catalogue untouched.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[str((E/x).relative_to(b.ROOT)) for x in paths])
b.save('result.json',result)
assert h.load(b.R/'CHECKPOINT.json')==h.load(E/'CHECKPOINT.json')
for path in result['evidence_paths']:assert (b.ROOT/path).is_file()
b.save('final-checkpoint-verification.json',dict(at=h.now(),evidence_files=[dict(path=x,sha256=h.sha((b.ROOT/x).read_bytes())) for x in result['evidence_paths']],runtime_checkpoint_matches=True,source_queue_111_entries=len(h.load(qp)['sources'])==111,verified_counts=counts,supervisor_prompt_schema_launchagent_untouched=True))
print(json.dumps(result,ensure_ascii=False))
