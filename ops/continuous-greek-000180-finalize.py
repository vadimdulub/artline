#!/usr/bin/env python3
"""One verified bounded worker handoff; the external supervisor stays unchanged."""
import copy, datetime, fcntl, importlib.util, json, os, subprocess
from pathlib import Path

s=importlib.util.spec_from_file_location('batch180',Path(__file__).with_name('continuous-greek-batch-000180.py'))
b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i;E=b.E
def rel(p):return str(Path(p).relative_to(b.ROOT))
def atomic(p,v):
 temp=p.with_suffix('.180.tmp');temp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');os.replace(temp,p)

with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=h.load(E/'batch-verification-receipt.json');p,pin=h.pinned(b.PHASE);counts=receipt['verified_counts']
 assert counts==dict(new_painters=1,new_artworks=4,newly_illustrated=4,alternate_images=0,museum_links=4)
 assert pin==receipt['metadata_plan_sha256'] and h.load(E/'independent-read-only-resume-verification.json')['passed']
 with h.connect() as db:
  assert h.snapshot(db,receipt['production_ids'])==h.load(E/'independent-production-verification.json')['after']
  assert db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(b.NEW_ARTIST,)).fetchone()['v']==h.load(E/'independent-new-painter-verification.json')['artist']
 if (E/'verified-batch-result.json').exists():
  for f in h.load(E/'independent-final-artifact-verification.json')['files']:assert h.sha((b.ROOT/f['path']).read_bytes())==f['sha256']
  assert h.load(b.R/'CHECKPOINT.json')==h.load(E/'CHECKPOINT.json')
  print(json.dumps(h.load(E/'verified-batch-result.json')));raise SystemExit(0)
 now=h.now();initial=h.load(E/'source-queue-preimage.json');source=next(x for x in initial['sources'] if x['source_id']=='national_gallery_athens')
 reconciliation=h.load(E/'ionian-global-identity-reconciliation.json')['records']
 assert len(reconciliation)==13 and len({x['source_id'] for x in reconciliation})==13
 held=[x for x in reconciliation if x['outcome'] not in ['selected','Existing object; excluded from new-artwork additions']]
 existing=[x for x in reconciliation if x['outcome']=='Existing object; excluded from new-artwork additions']
 assert len(held)==5 and len(existing)==4
 next_task='Resume Smithsonian SAAM official open metadata shard27 for exact existing primary-image gaps; preserve the search403/API-key holds and require native object/image CC0. Then rotate to another untouched registry Greek/Byzantine or other undercovered institution route. Kantounis9 and Koutouzis4 notices are now reviewed: four Kantounis paintings delivered, four Koutouzis objects already present, four undated Kantounis objects and one grouped-heads notice held. Do not replay these notices, completed SAAM00–26 or the exhausted French188 reserve without new evidence.'
 b.save('research-holds.json',dict(at=now,held=held,existing_not_new=existing,unrequested_selected_images=0,prior_holds_preserved=True,next_task=next_task))
 b.save('source-access-holds.json',dict(at=now,provider='national_gallery_athens',metadata='Two official creator indexes and13 native notices HTTP200',selected_images='Four native source images HTTP200',new_access_failures=[],automatic_retries=0,inherited_ledger=rel(E/'inherited-holds-verification.json'),unchanged_provider_holds_not_retried=True))
 cursors={}
 discovery=h.load(E/'creator-index-discovery.json')['records']
 for key,idx in zip(['kantounis_nikolaos','koutouzis_nikolaos'],discovery):
  reviewed=[r for r in reconciliation if r['url'] in idx['object_urls']]
  delivered=[r for r in p['records'] if r['source_url'] in idx['object_urls']]
  cursors[key]=dict(route='official_creator_index_native_inventory_reconciliation',creator_index=idx['creator_index'],source_index_sha256=idx['receipt']['sha256'],source_reported_total=len(idx['object_urls']),notices_reviewed=len(reviewed),processed_object_urls=idx['object_urls'],index_complete=True,next_object_url=None,verified_source_ids=[r['source_id'] for r in delivered],verified_artwork_ids=[r['artwork_id'] for r in delivered],existing_source_ids=[r['source_id'] for r in reviewed if r['outcome']=='Existing object; excluded from new-artwork additions'],held_reasons={r['source_id']:r['outcome'] for r in reviewed if r in held},metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],evidence=rel(E/'batch-verification-receipt.json'),coverage='Captured native notices reviewed; directory and institution-wide coverage are separate and incomplete',do_not_repeat_unchanged_holds=True)
 b.save('source-register-final.json',dict(at=now,original_registry_rows=111,provider=h.load(E/'required-input-verification.json')['museum_source'],policy_reference=['Original111-source CSV national_gallery_athens','docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026','docs/ARTLINE_IMAGE_USE.md#greek-painter-continuation--20-september-2026'],access_status='Native indexes, notices and four selected images HTTP200; no access holds retried',last_checked_at=now,directory_additions=0,source_object_notices_discovered=13,notices_reviewed=13,selected_distinct_artworks=4,prepared_artworks=4,prepared_images=4,imported_artworks=4,verified_artworks=4,verified_counts=counts,actual_originals_viewed=4,actual_derivatives_viewed=4,image_rights='Restricted; actual museum copyright/site notice retained; user source approval is separate from a rights-holder licence',current_display_claims=0,whole_institution_complete=False,resume_cursors=cursors,remaining_gaps=['Four unknown-date notices and grouped drawing unit held; no inferred dates or split sheets','Four Koutouzis source objects already present; excluded from increments','Museum-wide coverage, older held identities and other creator routes remain incomplete']))
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as qlock:
  fcntl.flock(qlock,fcntl.LOCK_EX);before=h.load(qp);after=copy.deepcopy(before);route=next(x for x in after['sources'] if x['source_id']=='national_gallery_athens')
  history=[x for x in route.get('batch_history',[]) if x.get('batch')==180]
  if history:
   assert len(history)==1 and history[0]['metadata_plan_sha256']==pin and history[0]['verified_counts']==counts
   assert all(route['resume_cursor'][key]==value for key,value in cursors.items())
  else:
   assert next(x for x in before['sources'] if x['source_id']=='national_gallery_athens')==source,'Concurrent Athens route update requires reconciliation'
   b.save('source-queue-immediately-before-update.json',before)
   route.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(route['resume_cursor']))
   route.update(status='ionian_kantounis_four_illustrated_review_works_one_painter_four_holdings_verified',last_batch=180,last_checked_at=now,checkpoint=rel(E/'CHECKPOINT.json'),latest_batch_verified_counts=counts,access_status='Native metadata and selected image surfaces HTTP200; unchanged prior source holds preserved',policy_reference='Original111-source registry plus explicit Greek museum/painter extensions in docs/ARTLINE_IMAGE_USE.md')
   route['resume_cursor'].update(cursors);route['resume_cursor']['next_step']=next_task
   route['resume_cursor']['processed_urls']=list(dict.fromkeys(route['resume_cursor'].get('processed_urls',[])+[r['url'] for r in reconciliation]))
   route['resume_cursor']['completed_creator_indexes']=list(dict.fromkeys(route['resume_cursor'].get('completed_creator_indexes',[])+['kantounis-nikolaos','koutouzis-nikolaos']))
   route['resume_cursor']['next_undercovered_creator_route']='Rotate institution to Smithsonian SAAM shard27; retain all existing and newly saved date/unit holds.'
   route.setdefault('remaining_gaps',[]).append('Batch180: Kantounis9/Koutouzis4 source notices reviewed; four new Kantounis paintings illustrated, four Koutouzis already present, four unknown-date notices and one grouped drawing-unit held. Institution-wide coverage incomplete.')
   route.setdefault('batch_history',[]).append(dict(batch=180,verified_counts=counts,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],verification_receipt=rel(E/'batch-verification-receipt.json')))
   route.setdefault('evidence_paths',[]).extend([rel(E/x) for x in ['batch-verification-receipt.json','independent-new-painter-verification.json','independent-production-verification.json','independent-public-verification.json','source-register-final.json','research-holds.json']])
   assert len(after['sources'])==111
   assert [x for x in before['sources'] if x['source_id']!='national_gallery_athens']==[x for x in after['sources'] if x['source_id']!='national_gallery_athens']
   assert {k:v for k,v in before.items() if k!='sources'}=={k:v for k,v in after.items() if k!='sources'}
   atomic(qp,after)
 assert h.load(qp)==after
 b.save('source-queue-update-verification.json',dict(at=h.now(),passed=True,changed_routes=['national_gallery_athens'],unrelated_original_sources_preserved=110,all111_original_sources_preserved=True,all_other_top_level_fields_preserved=True,source_queue_sha256=h.sha(qp.read_bytes()),resume_cursors=cursors,smithsonian_cursor_preserved=next(x for x in after['sources'] if x['source_id']=='smithsonian_open_access')['resume_cursor']))
 root=h.load(E.parents[1]/'CHECKPOINT.json');assert root['inflight']['batch']==180
 os.kill(root['supervisor_pid'],0)
 cmd=subprocess.check_output(['ps','-p',str(root['supervisor_pid']),'-o','command='],text=True).strip();assert 'continuous-production-research.py run' in cmd
 b.save('external-supervisor-handoff-verification.json',dict(at=h.now(),pid=root['supervisor_pid'],process_verified_live=True,command=cmd,inflight_batch=180,prior_completed_batch=root['previous']['evidence_paths'][-1],external_supervisor_unchanged=True,new_supervisors_schedulers_sessions_subagents=0,next_task=next_task,read_only_resume_verified=True))
 start=root['inflight']['started_at'];finished=h.now();runtime=(datetime.datetime.fromisoformat(finished)-datetime.datetime.fromisoformat(start)).total_seconds()
 b.save('milestone-report.json',dict(at=finished,batch=180,started_at=start,finished_at=finished,measured_batch_wall_clock_seconds=runtime,programme_wall_clock_seconds_including_pauses=(datetime.datetime.fromisoformat(finished)-datetime.datetime.fromisoformat(root['started_at'])).total_seconds(),previous_supervisor_accounted_totals=root['totals'],expected_totals_after_supervisor_accounts_this_result={k:root['totals'][k]+v for k,v in counts.items()},verified_counts=counts,source_notices_discovered=13,selected=4,prepared=4,imported=4,verified=4,unresolved_source_notices=5,existing_objects_excluded=4,hourly_and_cumulative_reporting_owner='Existing external supervisor',hour100_is_milestone_not_stop=True,next_task=next_task))
 b.save('failures-and-resolutions.json',dict(at=finished,provider_failures=[],automatic_source_retries=0,new_paid_services=0,translation_calls=0,local_catalogue_connections=0,cloud_backups_created=0,events=[dict(stage='read-only SQL diagnostic',failure='Literal percent pattern in parametrized SQL needed parameters',resolution='Corrected to bound patterns before production writes'),dict(stage='new-painter plan preparation',failure='Existing immutable v2 input represented object-only creator labels',resolution='Preserved v2 untouched, created pinned v3 with validated source-backed creator; v2 never imported'),dict(stage='independent source parser',failure='Optional collection-credit paragraph absent',resolution='Verified absent credit as empty source field, no invented credit'),dict(stage='creator reconciliation',failure='William Say shares1768–1834 lifetime',resolution='Preserved coincidence explicitly; separate name and native authority identities, no merging')],unused_plan='greek-objects-v2 retained, never applied',recovery=rel(E/'local-recovery-verification.json')))
 evidence=['batch-verification-receipt.json','independent-production-verification.json','independent-new-painter-verification.json','independent-source-verification.json','independent-file-verification.json','actual-visual-review.json','independent-storage-verification.json','independent-public-verification.json','independent-audit-history-verification.json','independent-existing-preservation-verification.json','independent-read-only-resume-verification.json','source-queue-update-verification.json','source-register-final.json','research-holds.json','source-access-holds.json','milestone-report.json','failures-and-resolutions.json','external-supervisor-handoff-verification.json']
 cp=dict(at=finished,batch=180,stage='independently_verified_complete',outcome='progress',started_at=start,finished_at=finished,measured_runtime_seconds=runtime,verified_counts=counts,production_ids=receipt['production_ids'],new_painter_ids=[b.NEW_ARTIST],metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],discovered_source_notices=13,selected=4,prepared=4,imported=4,verified=4,held=5,already_existing_excluded=4,originals_actually_viewed=4,derivatives_actually_viewed=4,next_task=next_task,blocker='',external_supervisor_unchanged=True,local_catalogue_connections=0,completed_delivery_do_not_count_again=True,resume_command='/tmp/artline-cesi-venv/bin/python ops/continuous-greek-000180-resume.py',evidence_paths=[rel(E/x) for x in evidence])
 atomic(E/'CHECKPOINT.json',cp);atomic(b.R/'CHECKPOINT.json',cp);assert h.load(b.R/'CHECKPOINT.json')==cp
 result=dict(outcome='progress',summary='Batch180 independently verified one new review painter, four new review Kantounis paintings, four newly illustrated artworks and four documented Athens holdings. All eight original/derivative views, audit attribution, production, Storage and public checks passed. Four existing Koutouzis objects excluded; five date/unit holds preserved. Batch107 reconciled; existing supervisor unchanged.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(E/x) for x in ['batch-verification-receipt.json','independent-new-painter-verification.json','independent-production-verification.json','actual-visual-review.json','independent-storage-verification.json','independent-public-verification.json','independent-audit-history-verification.json','independent-read-only-resume-verification.json','source-queue-update-verification.json','external-supervisor-handoff-verification.json','CHECKPOINT.json']])
 b.save('verified-batch-result.json',result);h.save(b.R/'verified-batch-result.json',result)
 files=[]
 for name in evidence+['CHECKPOINT.json','verified-batch-result.json']:
  path=E/name;h.load(path);files.append(dict(path=rel(path),sha256=h.sha(path.read_bytes()),bytes=path.stat().st_size))
 b.save('independent-final-artifact-verification.json',dict(at=h.now(),passed=True,files=files,runtime_checkpoint_equal=True,all_evidence_files_decoded=True))
 print(json.dumps(result),flush=True)
