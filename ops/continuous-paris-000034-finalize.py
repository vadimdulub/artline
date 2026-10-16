#!/usr/bin/env python3
"""Checkpoint one completed bounded batch without altering the supervisor."""
import copy, datetime, fcntl, importlib.util, json, os
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-paris-images-000034.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
receipt=b.load(b.E/'batch-verification-receipt.json');ids=receipt['production_ids'];counts=receipt['verified_counts']
def state():
 with b.connect() as db:
  return dict(artworks=b.h.snapshot(db,ids),rights=[dict(r) for r in db.execute('SELECT media_id::text,adapter_version,source_checksum,evidence_json FROM media_rights_evidence WHERE adapter_version=%s ORDER BY media_id',(i.OP,))],audit_events=[dict(r) for r in db.execute("SELECT id::text,entity_id::text,action,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,))])
if not (b.E/'independent-resume-verification.json').exists():
 before=state();assert len(before['rights'])==1
 prior=b.h.sha((i.folder(b.B)/'applied/000.json').read_bytes());b.deliver();after=state();assert before==after
 assert b.h.sha((i.folder(b.B)/'applied/000.json').read_bytes())==prior
 b.save(b.E/'independent-resume-verification.json',dict(at=b.h.now(),actual_resume_invoked='deliver',persisted_receipt_sha256=prior,before=before,after=after,new_rows=0,duplicate_attachments=0,unchanged=True))
french=b.mod('french34final','french-printmaking-delivery-20261011.py');_,pin=french.final_plan();assert pin==b.load(b.E/'french-reserve-live-reconciliation.json')['historical_plan_sha256']
b.save(b.E/'independent-historical-plan-verification.json',dict(at=b.h.now(),original_french_plan_sha256=pin,unchanged=True,reserve_unimported=0,previous_campaign_additions_excluded=188))
next_task='Research up to 25 National Palace Museum Taiwan painting/calligraphy image gaps through the registry public open-data catalogue. Require exact collection/inventory and full-object matches plus record-specific open image rights; preserve Chinese titles, qualified creators, through-1970 scope, and all provider holds. Do not revisit the exhausted French reserve or automate Paris portal extraction without an established permitted access route.'
evidence=['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-file-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-held-objects-verification.json','actual-visual-review.json','independent-resume-verification.json','independent-historical-plan-verification.json','french-reserve-live-reconciliation.json','prior-batch-live-reconciliation.json','portal-discovery-hold.json','gap-reconciliation.json']
checkpoint=dict(at=b.h.now(),batch=34,stage='verified_complete',verified_counts=counts,selected=1,prepared=1,imported=1,verified=1,discovered_existing_gaps=25,archived_joconde_crosswalks=24,native_objects_researched=1,next_task=next_task,resume=b.load(b.E/'gap-reconciliation.json'),evidence=[str((b.E/p).relative_to(b.ROOT)) for p in evidence],external_supervisor_unchanged=True,local_catalogue_connections=0,unresolved='One Wikidata-only image identity; 23 other native candidates not researched because wider automated portal discovery is held. No current-display or new holding claims.')
b.save(b.E/'CHECKPOINT.json',checkpoint);b.save(b.RUNTIME/'CHECKPOINT.json',checkpoint)
qp=b.E.parents[1]/'source-queue.json'
if not (b.E/'source-queue-update-verification.json').exists():
 q=b.load(qp);old=copy.deepcopy(q);changed={'yale_lux','paris_musees','france_pop_joconde'}
 for row in q['sources']:
  sid=row['source_id']
  if sid not in changed:continue
  row.setdefault('prior_resume_cursors',[])
  if row.get('resume_cursor') and row['resume_cursor'] not in row['prior_resume_cursors']:row['prior_resume_cursors'].append(copy.deepcopy(row['resume_cursor']))
  row['checkpoint']=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT));row['last_checked_at']=b.h.now()
  if sid=='yale_lux':
   row['status']='french_reserve_exhausted_live_verified_188_already_delivered';row['resume_cursor']=dict(french_reserve_remaining=0,unimported=0,do_not_replay=True,next_topic='Other Yale queues retain their own immutable cursors')
   ev=['french-reserve-live-reconciliation.json','independent-historical-plan-verification.json']
  elif sid=='france_pop_joconde':
   row['status']='24_archived_exact_reference_crosswalks_verified_one_carnavalet_image_bridge_completed';row['resume_cursor']=dict(route='archived_Joconde_to_Paris_inventory_crosswalk',reference_ids=[x['source_note']['object_id'] for x in b.load(b.E/'joconde-inventory-crosswalk.json.gz')['rows'] if not x.get('hold')],live_source_requests=0,completed_native_bridge='M1104320026898',unresolved='Other crosswalks are leads only; native source image research pending permitted access')
   ev=['global-identity-reconciliation.json','independent-source-verification.json']
  else:
   row['status']='one_carnavalet_cc0_primary_image_verified_broader_automated_discovery_access_terms_hold'
   row['resume_cursor']=dict(route='carnavalet_existing_primary_gaps',museum_id=b.MID,after_artwork_id=ids[0],completed_native_ids=['320026898'],completed_joconde_ids=['M1104320026898'],completed_inventory=['P1515'],interrupted_node='153161',unresearched_artwork_ids=b.load(b.E/'gap-reconciliation.json')['unresearched_native_ids'],identity_held_artwork_ids=['03371e25-2e11-5664-b661-c1dbf0c20c98'],automated_portal_retry_allowed=False,graphql_account_required=True,existing_captured_CC0_image_delivered=True)
   row['verified_counts']=counts
   row['access_holds']=row.get('access_holds',[])+[dict(surface='Paris Musées portal automated discovery / account-based API',reason='Current CGU sections 1.6 and 1.10; established account/permitted automated route not verified. Explicit per-image CC0 download remains allowed under 1.3.1.a/1.4.',evidence=str((b.E/'portal-discovery-hold.json').relative_to(b.ROOT)),retry_without_access_change=False)]
   row['remaining_gaps']=['Original pre1956 screen had 44 gaps; one now filled. This is not complete museum artwork or directory coverage.','23 other bounded native-image candidates remain unresearched; one independent identity crosswalk remains held.']
   ev=['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-public-verification.json','portal-discovery-hold.json','gap-reconciliation.json']
  for name in ev:
   p=str((b.E/name).relative_to(b.ROOT))
   if p not in row.setdefault('evidence_paths',[]):row['evidence_paths'].append(p)
 assert [r for r in old['sources'] if r['source_id'] not in changed]==[r for r in q['sources'] if r['source_id'] not in changed]
 for k,v in old.items():
  if k!='sources':assert q[k]==v
 b.save(b.E/'source-queue-immediately-before-update.json',old)
 tmp=qp.with_suffix('.batch34.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2));os.replace(tmp,qp)
 assert b.load(qp)==q
 b.save(b.E/'source-queue-update-verification.json',dict(at=b.h.now(),updated_sources=sorted(changed),before_semantic_sha256=b.h.sha(json.dumps(old,sort_keys=True).encode()),after_file_sha256=b.h.sha(qp.read_bytes()),unrelated_entries_preserved=True,entries=[r for r in q['sources'] if r['source_id'] in changed]))
root=b.load(b.E.parents[1]/'CHECKPOINT.json');now=datetime.datetime.now(datetime.timezone.utc);start=datetime.datetime.fromisoformat(root['inflight']['started_at']);overall=datetime.datetime.fromisoformat(root['started_at'])
b.save(b.E/'milestone-report.json',dict(at=now.isoformat(),measured_batch_runtime_seconds=(now-start).total_seconds(),measured_programme_runtime_hours=(now-overall).total_seconds()/3600,previous_verified_programme_increments=root['totals'],batch_verified_counts=counts,cumulative_programme_increments_after_this_batch={k:root['totals'][k]+counts[k] for k in counts},not_a_whole_catalogue_census=True,failures=['Legacy registry terms URL returned 404; current footer CGU successfully captured.','Second native object request stopped during terms review; no image downloaded for it.'],holds=['Broader automated Paris portal and unconfigured account-based API discovery held; permitted selected CC0 download completed.'],next_task=next_task,external_supervisor_responsible_for_hourly_and_100_hour_reports=True,no_supervisor_changes=True))
summary='Verified one new CC0 primary image for an existing Carnavalet artwork. All 188 French reserve works were already delivered and excluded. Exact Joconde/native inventory, visual review, file/storage/public checks and audit attribution passed. Broader automated Paris discovery held under current access terms; local catalogue untouched.'
result=dict(outcome='progress',summary=summary,next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[str((b.E/name).relative_to(b.ROOT)) for name in evidence+['source-queue-update-verification.json','milestone-report.json','CHECKPOINT.json']])
b.save(b.E/'result.json',result)
for path in result['evidence_paths']:assert (b.ROOT/path).is_file()
assert b.load(b.RUNTIME/'CHECKPOINT.json')==b.load(b.E/'CHECKPOINT.json')
b.save(b.E/'final-checkpoint-verification.json',dict(at=b.h.now(),evidence_files=[dict(path=p,sha256=b.h.sha((b.ROOT/p).read_bytes())) for p in result['evidence_paths']],runtime_checkpoint_matches=True,source_queue_has111_entries=len(b.load(qp)['sources'])==111,verified_counts=counts,supervisor_prompt_schema_launchagent_untouched=True))
print(json.dumps(result,ensure_ascii=False))
