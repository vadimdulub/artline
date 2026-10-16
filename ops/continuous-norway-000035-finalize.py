#!/usr/bin/env python3
"""Persist one verified bounded batch, preserving external supervisor state."""
import copy, datetime, fcntl, importlib.util, json, os
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-norway-images-000035.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
receipt=b.load(b.E/'batch-verification-receipt.json');ids=receipt['production_ids'];counts=receipt['verified_counts'];assert counts['newly_illustrated']==6
def state():
 with b.connect() as db:
  return dict(artworks=b.h.snapshot(db,ids),rights=[dict(r) for r in db.execute('SELECT media_id::text,adapter_version,source_checksum,evidence_json FROM media_rights_evidence WHERE adapter_version=%s ORDER BY media_id',(i.OP,))],audit_events=[dict(r) for r in db.execute("SELECT id::text,entity_id::text,action,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,))])
if not (b.E/'independent-resume-verification.json').exists():
 before=state();assert len(before['rights'])==6
 prior=b.h.sha((i.folder(b.B)/'applied/000.json').read_bytes());b.deliver();after=state();assert before==after
 assert b.h.sha((i.folder(b.B)/'applied/000.json').read_bytes())==prior
 b.save(b.E/'independent-resume-verification.json',dict(at=b.h.now(),actual_resume_invoked='deliver',persisted_receipt_sha256=prior,before=before,after=after,new_rows=0,duplicate_attachments=0,unchanged=True))
stops={'stop-audit.json':'a37d70a524cb540d2b8ea5bddb64cb346078b234c231b6f1957bc7d6fde42827','stop-prefetch.json':'9923b016e616114bc204a7cf323d282efc0af3b09e73f0f247a9c4e00ca6af6b','stop-deliver.json':'914697dfa9309078a5639d149a64aa585f2b631ac268f72eca1318b98f3218f5'}
for name,digest in stops.items():assert b.h.sha((b.ROOT/'docs/research/illustrated-300k-20261011'/name).read_bytes())==digest
b.save(b.E/'completed-campaign-stop-verification.json',dict(at=b.h.now(),stops=stops,unchanged=True,separate_continuation_operation=i.OP,completed_campaign_restarted=False))
data=b.load(b.E/'oslo-bounded-gap-input.json.gz');holds=b.load(b.E/'research-holds.json')['records']
resume=dict(route='official_native_object_pages_and_explicit_CC_BY_primary_images',institution_id=b.MID,after_artwork_id=data['rows'][-1]['id'],inspected_ids=[r['id'] for r in data['rows']],delivered_ids=ids,held_ids=[r['artwork_id'] for r in holds],URL_corrections_pending=[dict(artwork_id=r['artwork_id'],canonical_url=next(e['canonical_url'] for e in data['identifiers'] if e['entity_id']==r['artwork_id'] and e['scheme']=='nasjonalmuseet-object')) for r in holds if 'HTTP 404' in r['reason']],no_repeat_of_unchanged_rights_holds=True)
next_task='Research up to 25 existing Te Papa primary-image gaps using official object pages and record-specific reusable image licences. Start with institution da3b80d7-dc07-5573-90ff-25a76a7b8d2e; the production screen found 125 gaps with creation through 1955. Use the API only if an existing configured key permits it. Preserve all holds, especially NPM HTTP 403; keep Norway at its saved cursor, including three documented underscore-URL corrections.'
evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-file-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-held-objects-verification.json','actual-visual-review.json','independent-resume-verification.json','completed-campaign-stop-verification.json','prior-write-reconciliation.json','global-identity-reconciliation.json','npm-access-hold.json','npm-date-gap-verification.json','norway-institution-reconciliation.json','research-holds.json']
checkpoint=dict(at=b.h.now(),batch=35,stage='verified_complete',verified_counts=counts,selected=6,prepared=6,imported=6,verified=6,discovered_existing_gaps=12,native_objects_researched=12,native_object_pages_http200=9,next_task=next_task,resume=resume,evidence=[str((b.E/p).relative_to(b.ROOT)) for p in evidence],external_supervisor_unchanged=True,local_catalogue_connections=0,unresolved='Two Norwegian copyright restrictions, three canonical-URL corrections, one separate native identity crosswalk; 38 Taiwan unknown-date gaps remain held pending source access and date review. No new museum or display assertions.')
b.save(b.E/'CHECKPOINT.json',checkpoint);b.save(b.RUNTIME/'CHECKPOINT.json',checkpoint)
qp=b.E.parents[1]/'source-queue.json'
if not (b.E/'source-queue-update-verification.json').exists():
 with (b.RUNTIME.parent.parent/'source-queue-update.lock').open('a+') as qlock:
  fcntl.flock(qlock,fcntl.LOCK_EX)
  q=b.load(qp);old=copy.deepcopy(q);changed={'national_palace_museum_taiwan','nasjonalmuseet_norway'}
  for row in q['sources']:
   sid=row['source_id']
   if sid not in changed:continue
   row.setdefault('prior_resume_cursors',[])
   if row.get('resume_cursor') and row['resume_cursor'] not in row['prior_resume_cursors']:row['prior_resume_cursors'].append(copy.deepcopy(row['resume_cursor']))
   row['checkpoint']=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT));row['last_checked_at']=b.h.now()
   if sid=='national_palace_museum_taiwan':
    row['status']='official_terms_web_http403_access_hold_38_unknown_date_gaps'
    row['resume_cursor']=dict(route='official_open_data_policy',url='https://digitalarchive.npm.gov.tw/opendata/Pub/EngVersion',retry_without_access_change=False,existing_primary_gaps=38,unknown_date_gaps=38,image_requests=0,next_step='Restore permitted access before exact-inventory and source-date image review; do not invent creation dates.')
    row['access_status']='HTTP 403 observed via web retrieval; not retried with another client'
    row['access_holds']=row.get('access_holds',[])+[dict(surface='https://digitalarchive.npm.gov.tw/opendata/Pub/EngVersion',status=403,reason='First terms request failed with Forbidden; provider switched without bypass',evidence=str((b.E/'npm-access-hold.json').relative_to(b.ROOT)),retry_without_access_change=False)]
    row['remaining_gaps']=['38 active primary-image gaps all have unknown catalogue creation dates; source-specific date review and exact inventory/version/rights checks remain necessary.']
    ev=['npm-access-hold.json','npm-date-gap-verification.json']
   else:
    row['status']='six_existing_primary_gaps_verified_native_CC_BY_images'
    row['resume_cursor']=resume;row['verified_counts']=counts
    row['access_status']='Official native object pages, policy and six selected native IIIF JPEGs HTTP 200. No API/key or retired API used.'
    row['policy_reference']='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy'
    row['remaining_gaps']=['Main Oslo institution began with 1,227 dated image gaps; 6 filled. Legacy separate Oslo institution has 4 illustrated works; institution records unchanged.','Of twelve reviewed candidates: two copyright holds, three corrected canonical URLs pending, one native identifier/title crosswalk pending.','Museum object and nationwide directory coverage remain incomplete; no current-display claims.']
    ev=['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-public-verification.json','research-holds.json','norway-institution-reconciliation.json','norway-policy.json']
   for name in ev:
    p=str((b.E/name).relative_to(b.ROOT))
    if p not in row.setdefault('evidence_paths',[]):row['evidence_paths'].append(p)
  assert [r for r in old['sources'] if r['source_id'] not in changed]==[r for r in q['sources'] if r['source_id'] not in changed]
  for k,v in old.items():
   if k!='sources':assert q[k]==v
  b.save(b.E/'source-queue-immediately-before-update.json',old)
  tmp=qp.with_suffix('.batch35.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2));os.replace(tmp,qp);assert b.load(qp)==q
  b.save(b.E/'source-queue-update-verification.json',dict(at=b.h.now(),updated_sources=sorted(changed),before_semantic_sha256=b.h.sha(json.dumps(old,sort_keys=True).encode()),after_file_sha256=b.h.sha(qp.read_bytes()),unrelated_entries_preserved=True,entries=[r for r in q['sources'] if r['source_id'] in changed]))
reg=b.load(b.E/'required-input-reconciliation.json')['registry'];q=b.load(qp)
b.save(b.E/'source-register.json',dict(at=b.h.now(),original_registry_path=reg['path'],original_registry_sha256=reg['sha256'],registry_rows=111,providers=[r for r in q['sources'] if r['source_id'] in ['national_palace_museum_taiwan','nasjonalmuseet_norway']],original_source_rows=[r for r in reg['rows'] if r['source_id'] in ['national_palace_museum_taiwan','nasjonalmuseet_norway']],separate_source_approval_and_actual_CC_BY_license=True,unchanged_other_provider_holds=True))
b.save(b.E/'source-access-holds.json',dict(at=b.h.now(),inherited_queue_snapshot='source-queue-before.json',inherited_ledger='docs/research/continuous-production-20261011/batches/000034/source-access-holds.json',paris_automated_access_hold='docs/research/continuous-production-20261011/batches/000034/portal-discovery-hold.json',new_hold='npm-access-hold.json',object_holds='research-holds.json',no_held_provider_retries=True))
root=b.load(b.E.parents[1]/'CHECKPOINT.json');assert root['inflight']['batch']==35
now=datetime.datetime.now(datetime.timezone.utc);start=datetime.datetime.fromisoformat(root['inflight']['started_at']);overall=datetime.datetime.fromisoformat(root['started_at'])
b.save(b.E/'milestone-report.json',dict(at=now.isoformat(),measured_batch_runtime_seconds=(now-start).total_seconds(),measured_programme_runtime_hours=(now-overall).total_seconds()/3600,previous_verified_programme_increments=root['totals'],batch_verified_counts=counts,cumulative_programme_increments_after_this_batch={k:root['totals'][k]+counts[k] for k in counts},not_a_whole_catalogue_census=True,failures=['NPM terms web request HTTP 403; no retry.','Three naive ampersand inventory URLs returned 404; historical canonical underscore URLs preserved for follow-up.','Preselection validator initially needed the established fragment JSON wrapper and separation of framed from artwork dimensions; both corrected before selection and any writes.','Default Python lacked psycopg; established project research virtualenv used.'],holds=holds,next_task=next_task,external_supervisor_responsible_for_hourly_and_100_hour_reports=True,no_supervisor_changes=True))
result=dict(outcome='progress',summary='Verified six new National Museum Oslo primary images with individual visual review, exact source/version checks, transaction attribution and public delivery. Resume made no duplicate writes. NPM HTTP 403 and six Norwegian object holds recorded; local catalogue untouched.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[str((b.E/name).relative_to(b.ROOT)) for name in evidence+['source-queue-update-verification.json','source-register.json','milestone-report.json','CHECKPOINT.json']])
b.save(b.E/'result.json',result)
for path in result['evidence_paths']:assert (b.ROOT/path).is_file()
assert b.load(b.RUNTIME/'CHECKPOINT.json')==b.load(b.E/'CHECKPOINT.json')
b.save(b.E/'final-checkpoint-verification.json',dict(at=b.h.now(),evidence_files=[dict(path=p,sha256=b.h.sha((b.ROOT/p).read_bytes())) for p in result['evidence_paths']],runtime_checkpoint_matches=True,source_queue_has111_entries=len(b.load(qp)['sources'])==111,verified_counts=counts,supervisor_prompt_schema_launchagent_untouched=True))
print(json.dumps(dict(verified_counts=counts,next_task=next_task),ensure_ascii=False))
