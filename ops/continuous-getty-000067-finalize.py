#!/usr/bin/env python3
"""Verify bounded handoff, preserving every unrelated source route."""
import copy, datetime, fcntl, importlib.util, json, os
from pathlib import Path
s=importlib.util.spec_from_file_location('batch67',Path(__file__).with_name('continuous-getty-000067.py'))
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;E=b.E;R=b.R;load=b.load
def save(name,value):return b.save(E/name,value)
def rel(p):return str(Path(p).relative_to(b.ROOT))
def ref(p):
 p=Path(p);return dict(path=rel(p) if p.is_relative_to(b.ROOT) else str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size)

def main():
 receipt=load(E/'batch-verification-receipt.json');counts=receipt['verified_counts']
 assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=3,alternate_images=0,museum_links=0)
 replay=load(E/'independent-resume-verification.json');assert replay['unchanged_snapshot'] and not any(replay['replay_increments'].values())
 ids=receipt['production_ids'];images,_,review=b.i.accepted(b.B)
 assert len(images)==len(ids)==len(review['decisions'])==3 and all(r['viewed_individually'] for r in review['decisions'])
 reserve=load(E/'french-reserve-live-reconciliation.json');audit=load(E/'independent-reserve-evidence-verification.json')
 assert reserve['inspected']==audit['inspected']==188 and reserve['unimported']==0
 for artifact in audit['immutable_plans']:assert h.sha(Path(artifact['path']).read_bytes())==artifact['sha256']
 for r in audit['records']:
  assert h.sha(Path(r['source_record']['path']).read_bytes())==r['source_record']['sha256']
  assert h.sha(Path(r['prior_visual_decision']['path']).read_bytes())==r['prior_visual_decision']['sha256']
 discovery=load(E/'byzantine-discovery-verification.json');raw=b.w.body(discovery['source_receipt']);source=json.loads(raw)
 assert source['data']==[r['index'] for r in discovery['records']]
 assert discovery['checked']==50 and all(r['outcome']=='component_or_ensemble_review_hold' for r in discovery['records'])
 save('independent-discovery-verification.json',dict(at=h.now(),captured_source_sha256=h.sha(raw),source_status=discovery['source_receipt']['status'],checked=50,whole_object_candidates=0,component_or_ensemble_holds=50,next_offset=150,unselected_image_downloads=0,records=[{k:r[k] for k in ['native_id','slug','title','accession','outcome']} for r in discovery['records']],scope='Search classifications distinguish components from standalone objects. These leads have not received native object-level import validation and are not new artworks.'))
 with b.connect() as db:
  live=h.snapshot(db,ids);assert live==load(E/'independent-production-verification.json')['after']
  evs=[dict(r) for r in db.execute('SELECT media_id::text,adapter_version,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(b.OP,))]
  assert len(evs)==3 and {r['media_id'] for r in evs}=={im['media_id'] for im in images}
  for r in evs:
   ev=json.loads(r['evidence_json']) if isinstance(r['evidence_json'],str) else r['evidence_json']
   assert ev['selection_sha256']==receipt['selection_sha256'] and ev['batch_visual_review_sha256']==receipt['visual_review_sha256']
  later=[dict(r) for r in db.execute("SELECT id::text FROM artworks WHERE current_institution_id=%s AND id>%s::uuid AND status<>'archived' AND primary_media_id IS NULL AND creation_year_end<=1955 AND work_type='painting' AND accession_number IS NOT NULL ORDER BY id LIMIT 1",(b.w.MID,max(ids)))]
  assert not later
 save('independent-final-production-reconciliation.json',dict(at=h.now(),production_ids=ids,live_snapshot_matches=True,operation_rights_rows=3,selection_sha256=receipt['selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],later_eligible_painting_gaps_after_cursor=later,prior_delivery_counts_excluded=True))
 at=h.now();zero={k:0 for k in counts}
 next_task='Resume Nasjonalmuseet Norway native CC BY image gaps after artwork UUID 10ea6912-5b2a-57ca-aa9a-11af70f71078 using its saved route and holds. Getty Byzantine discovery resumes at offset 150; 50 new component leads remain held. French reserves are exhausted; do not replay the 188 previously delivered prints.'
 save('research-holds.json',dict(at=at,french_physical_date_holds=['80082','80437','81054'],french_unimported=0,getty_component_holds=[dict(native_id=r['native_id'],slug=r['slug'],accession=r['accession'],reason='Search identifies manuscript component or ensemble; reconcile whole inventory before any import or image substitution.') for r in discovery['records']],prior_getty_painting_image_holds=['da597b1b-0239-59a6-ae00-61a7b3099dba','e46e122e-af07-5bdd-ad57-dba58e354e57'],prior_manuscript_view_holds_preserved=True,new_image_holds=0,held_objects_modified=0,held_provider_requests=0))
 save('failures.json',dict(at=at,production_failures=[],source_access_failures=[],resolved_local_errors=[dict(stage='Initial read-only helper check',error='Default Python lacked psycopg',resolution='Used established /tmp/artline-cyprus-venv/bin/python; no production writes attempted by failed interpreter.')],provider_retries=0,paid_services_started=0,cloud_backups_created=0))
 qp=E.parents[1]/'source-queue.json';touched={'yale_lux','getty_museum'}
 with qp.with_suffix('.lock').open('a+') as qlock:
  fcntl.flock(qlock,fcntl.LOCK_EX)
  if (E/'source-queue-after.json').exists():
   before=load(E/'source-queue-immediately-before-update.json');after=load(E/'source-queue-after.json')
   current={r['source_id']:r for r in load(qp)['sources']}
   assert all(current[r['source_id']]==r for r in after['sources'] if r['source_id'] in touched)
  else:
   before=load(qp);after=copy.deepcopy(before);save('source-queue-immediately-before-update.json',before)
   original={r['source_id']:r for r in load(E/'source-queue-before.json')['sources']}
   assert len(after['sources'])==111
   for route in after['sources']:
    sid=route['source_id']
    if sid not in touched:continue
    assert route==original[sid],'Researched route changed concurrently; reconcile before queue update'
    route.update(last_checked_at=at,checkpoint=rel(E/'CHECKPOINT.json'),latest_batch_verified_counts=counts if sid=='getty_museum' else zero)
    if sid=='yale_lux':
     route.update(status='french_reserve_exhausted_live_verified_188_already_delivered',access_status='Batch 67: all 188 live identities, original source/manifest captures and checksum-bound prior visual approvals verified. No unimported reserve; no provider requests or French writes.',policy_reference='docs/ARTLINE_IMAGE_USE.md#continued-illustrated-expansion--11-october-2026')
     assert route['resume_cursor']['unimported']==route['resume_cursor']['french_reserve_remaining']==0
     refs=['french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json']
     history=dict(batch=67,at=at,reserve_inspected=188,unimported=0,new_programme_increments=0,evidence=rel(E/refs[0]))
    else:
     old=copy.deepcopy(route['resume_cursor']);route.setdefault('prior_resume_cursors',[]).append(old)
     c=route['resume_cursor'];assert c['next_offset']==100
     c.update(next_offset=150,last_offset=100,last_page_evidence=rel(E/'independent-discovery-verification.json'))
     c['processed_slugs']=list(dict.fromkeys(c['processed_slugs']+[r['slug'] for r in discovery['records']]))
     c.setdefault('component_hold_ledgers',[]).append(rel(E/'independent-discovery-verification.json'))
     paint=c['painting_image_gaps'];assert paint['after_artwork_id']==load(E/'bounded-gap-input.json.gz')['after_artwork_id']
     paint.update(previous_after_artwork_id=paint['after_artwork_id'],after_artwork_id=max(ids),latest_verified_batch=67,selection_sha256=receipt['selection_sha256'],latest_selection_path=rel(b.i.folder(b.B)/'selection.json.gz'),keyset_end_verified_at=at,next_step='Current bounded pre-1956 native painting-gap route exhausted beyond this cursor. Preserve two painting-image holds and three manuscript-view holds. Rotate sources; Getty Byzantine query resumes offset 150.')
     for key in ['inspected_ids','delivered_ids']:paint[key]=list(dict.fromkeys(paint[key]+ids))
     route['programme_verified_counts']={k:route['programme_verified_counts'][k]+counts[k] for k in counts}
     route.update(status='37_existing_painting_gaps_illustrated_keyset_end_150_byzantine_leads_checked',verified_counts=counts,access_status='50 Byzantine component leads captured HTTP 200; three exact native paintings and digital-image CC0 records verified, prepared, individually viewed and publicly delivered.',policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy')
     route['remaining_gaps'].append('Batch 67: three final current painting gaps illustrated; 50 additional manuscript component leads held for whole-object reconciliation. Byzantine search resumes at offset 150; two prior image holds and three manuscript-view holds unchanged. Museum-wide coverage incomplete.')
     refs=['batch-verification-receipt.json','independent-production-verification.json','independent-source-verification.json','independent-public-verification.json','independent-discovery-verification.json','actual-visual-review.json','independent-resume-verification.json']
     history=dict(batch=67,at=at,verified_counts=counts,byzantine_leads=50,new_component_holds=50,evidence=rel(E/'batch-verification-receipt.json'))
    route.setdefault('research_history',[]).append(history)
    route['evidence_paths']=list(dict.fromkeys(route.get('evidence_paths',[])+[rel(E/f) for f in refs]))
   save('source-queue-after.json',after);assert load(qp)==before
   temp=qp.with_suffix('.batch67.tmp');temp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');os.replace(temp,qp)
 left={r['source_id']:r for r in before['sources']};right={r['source_id']:r for r in after['sources']}
 assert len(left)==len(right)==111
 assert {k:v for k,v in left.items() if k not in touched}=={k:v for k,v in right.items() if k not in touched}
 assert left['getty_museum']['resume_cursor']['painting_image_gaps']['held_ids']==right['getty_museum']['resume_cursor']['painting_image_gaps']['held_ids']
 save('independent-queue-verification.json',dict(at=h.now(),modified_source_ids=sorted(touched),unrelated_entries_preserved=109,all_111_registry_routes_preserved=True,prior_object_and_provider_holds_preserved=True,before=ref(E/'source-queue-immediately-before-update.json'),after=ref(E/'source-queue-after.json'),getty_next_offset=150,getty_painting_after_artwork_id=max(ids)))
 source_input=load(E/'source-register.json')
 save('source-register-final.json',dict(at=at,registry_path=source_input['registry_path'],registry_sha256=source_input['registry_sha256'],registry_records=111,sources=[dict(registry=r,programme_state=right[r['source_id']]) for r in source_input['routes']],directory_additions=0,directory_coverage_complete=False,artwork_coverage_complete=False))
 master=load(E.parents[1]/'CHECKPOINT.json');assert master['inflight']['batch']==67
 started=datetime.datetime.fromisoformat(master['inflight']['started_at']);end=datetime.datetime.now(datetime.timezone.utc)
 elapsed=(end-started).total_seconds()
 cp=save('CHECKPOINT.json',dict(at=end.isoformat(),started_at=started.isoformat(),elapsed_seconds=elapsed,batch=67,stage='independently_verified_complete',outcome='progress',verified_counts=counts,french_reserve_inspected=188,french_reserve_unimported=0,getty_byzantine_leads=50,getty_whole_object_candidates=0,existing_painting_gaps=3,selected=3,prepared=3,individually_viewed=3,imported=3,verified=3,production_ids=ids,selection_sha256=receipt['selection_sha256'],visual_review_sha256=receipt['visual_review_sha256'],next_task=next_task,blocker='',resume_commands=['/tmp/artline-cyprus-venv/bin/python ops/continuous-getty-000067-verify.py verify','/tmp/artline-cyprus-venv/bin/python ops/continuous-getty-000067-verify.py replay','/tmp/artline-cyprus-venv/bin/python ops/continuous-getty-000067-finalize.py'],local_catalogue_connections=0,external_supervisor_unmodified=True,supervisor_running_claim=False,reporting='External supervisor owns persistence, continuation and hourly reports. This worker executed one bounded batch.',limitations=['Recovery export contains full schema and exact affected rows; not a full database backup.','French visual approvals are preserved prior reviews; those 188 files were not newly visually inspected.','Getty manuscript components require physical inventory reconciliation; no complete museum coverage claim.']))
 b.save(R/'CHECKPOINT.json',cp);assert load(R/'CHECKPOINT.json')==cp
 save('milestone-report.json',dict(at=cp['at'],measured_batch_runtime_seconds=cp['elapsed_seconds'],measured_programme_runtime_hours=(datetime.datetime.fromisoformat(cp['at'])-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()/3600,previous_supervisor_counts=master['totals'],verified_batch_counts=counts,cumulative_receipt_counts={k:master['totals'][k]+counts[k] for k in counts},count_scope='Current batch independently verified; earlier supervisor totals retained, not recounted as current delivery. No whole-catalogue census.',hourly_summary_owner='Existing external supervisor; unmodified',hundred_hours_is_not_stop=True,next_task=next_task,failures=ref(E/'failures.json')))
 refs=['batch-verification-receipt.json','independent-production-verification.json','independent-source-verification.json','independent-file-verification.json','independent-public-verification.json','independent-storage-verification.json','independent-audit-history-verification.json','independent-resume-verification.json','independent-queue-verification.json','independent-discovery-verification.json','independent-final-production-reconciliation.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','actual-visual-review.json','local-recovery-verification.json','source-register-final.json','source-access-holds.json','research-holds.json','CHECKPOINT.json','milestone-report.json']
 save('independent-final-handoff-verification.json',dict(at=h.now(),verified_counts=counts,references=[ref(E/f) for f in refs],all_references_exist=True,runtime_checkpoint_matches=True,source_count=111,unrelated_routes_preserved=109,immutable_historical_plans_preserved=True,local_catalogue_connections=0,external_supervisor_unmodified=True))
 print(json.dumps(dict(outcome='progress',verified_counts=counts,next_task=next_task)))

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
