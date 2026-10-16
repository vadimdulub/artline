#!/usr/bin/env python3
"""Save independently verified bounded delivery; preserve unrelated queue entries."""
import copy,datetime,fcntl,importlib.util,json,os,subprocess,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('b88',Path(__file__).with_name('continuous-greek-batch-000088.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
final=b.E/'final-checkpoint-verification.json'
if final.exists():
 for x in h.load(final)['files']:assert h.sha((b.ROOT/x['path']).read_bytes())==x['sha256']
 assert h.load(b.R/'CHECKPOINT.json')==h.load(b.E/'CHECKPOINT.json')
 print('Final evidence and durable checkpoint verified without changes.');sys.exit(0)
rc=h.load(b.E/'batch-verification-receipt.json');replay=h.load(b.E/'independent-resume-verification.json');assert replay['unchanged_snapshot'] and not any(replay['replay_increments'].values())
p,pin=h.pinned(b.PHASE);counts=rc['verified_counts'];assert counts==dict(new_painters=0,new_artworks=3,newly_illustrated=3,alternate_images=0,museum_links=3)
checks=h.load(b.E/'parthenis-global-identity-reconciliation.json')['records'];assert len(checks)==24 and sum(bool(x['existing']) for x in checks)==2
review=h.load(b.E/'editorial-selection-review.json');assert len(review['held_versions'])==14 and len(review['date_holds'])==5
parent=h.load(b.E.parents[1]/'CHECKPOINT.json');assert parent['inflight']['batch']==88
at=h.now();start=parent['inflight']['started_at'];elapsed=(datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(start)).total_seconds();runtime=(datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(parent['started_at'])).total_seconds()
pid=parent['supervisor_pid'];proc=subprocess.check_output(['ps','-p',str(pid),'-o','pid=,etime=,command='],text=True).strip();assert 'ops/continuous-production-research.py run' in proc
prev=b.R.parent/'000087/result-001.json';prev_result=h.load(prev);assert prev_result['verified_counts']==parent['previous']['verified_counts'];assert h.load(b.E/'prior-batch-live-reconciliation.json')['previous_batch_verified']
worker=b.ROOT/'ops/continuous-production-research.py'
b.save('external-continuation-verification.json',dict(at=at,external_supervisor_process=proc,supervisor_script_sha256=h.sha(worker.read_bytes()),previous_completed_result=dict(path=str(prev),sha256=h.sha(prev.read_bytes())),observed_handoff='Previous batch 87 result persisted; shared checkpoint records in-flight batch 88; live supervisor process present. Prior batch 87 live production independently reconciled.',new_supervisors_or_schedules_launched=0,supervisor_configuration_edits=0,scope='Read-only verification of existing external continuation, not a promise of future uptime.'))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 heldids=[h.uid('artwork/athens/'+x['record']['source_id']) for x in p['held']];assert not h.snapshot(db,heldids)
 notes=list(db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s",(b.FIELD,)));assert len(notes)==3 and all(x['pin']==pin for x in notes)
 assert h.snapshot(db,rc['production_ids'])==h.load(b.E/'independent-production-verification.json')['after']
b.save('independent-held-and-attribution-verification.json',dict(at=at,held_proposed_artwork_ids_absent=heldids,own_plan_citations=notes,metadata_plan_sha256=pin,only_own_three_objects_counted=True,prior_campaigns_excluded=True))
initial=h.load(b.E/'source-queue-before.json');old=next(x for x in initial['sources'] if x['source_id']=='national_gallery_athens');cursor=copy.deepcopy(old['resume_cursor'])
cursor.update(processed_page=3,next_page=4,documented_next_request=dict(method='POST',url='https://www.nationalgallery.gr/wp-admin/admin-ajax.php',form=dict(artist_id='91',lang='en',page=4,action='get_artist_artworks'),evidence=str((b.E/'parthenis-page3-capture.json').relative_to(b.ROOT)),executed=False),parthenis_notices_reviewed=old['resume_cursor']['parthenis_notices_reviewed']+24,processed_urls=list(dict.fromkeys(cursor['processed_urls']+[x['url'] for x in checks])),verified_source_ids=list(dict.fromkeys(cursor['verified_source_ids']+review['selected'])),verified_artwork_ids=list(dict.fromkeys(cursor['verified_artwork_ids']+rc['production_ids'])))
cursor['held_versions'].update(review['held_versions']);cursor['held_date_source_ids']=list(dict.fromkeys(cursor['held_date_source_ids']+[r['source_id'] for r in review['date_holds']]))
cursor['next_step']='Rotate institutions, then resume native artist 91 page 4; preserve prior held versions, unknown dates and Aphrodite image cutoff hold.'
next_task='Resume National Museum Warsaw painted-icon discovery page 9 via the saved official native API cursor. Skip all processed IDs and 93 unchanged editorial holds; preserve Athens page 4 and M+ pending candidates.'
inputs=h.load(b.E/'required-input-reconciliation.json');reg=inputs['registry'];registry_ref=next(x for x in inputs['inputs'] if x['path'].endswith('GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'))
b.save('source-register-final.json',dict(at=at,registry=registry_ref,registry_rows=111,complete_original_registry_used=True,researched=[dict(registry_entry=next(x for x in reg if x['source_id']=='national_gallery_athens'),policy_reference='docs/ARTLINE_IMAGE_USE.md: Greek museum extension through 1955',access_status='One documented public page-3 index request, 24 exact notices and three selected images HTTP 200',last_checked_at=at,discovered=24,selected=3,prepared=3,imported=3,verified=3,existing_exact_objects_excluded=2,identity_version_custody_holds=14,date_holds=5,resume_cursor=cursor,remaining_gaps='Pages 4–5 unreviewed; held duplicates/versions/custody and unknown/open dates remain. Museum coverage partial.'),dict(registry_entry=next(x for x in reg if x['source_id']=='yale_lux'),policy_reference='docs/ARTLINE_IMAGE_USE.md: selected French printmaking continuation',access_status='Saved original source captures and prior visual decisions checksum verified; 188 exact production objects and primary associations checked live; no new source requests',last_checked_at=at,inspected=188,unimported=0,newly_delivered=0,evidence='french-reserve-live-reconciliation.json',remaining_gaps='This reserve is exhausted, not the entire institution; physical-date review for native IDs 80082, 80437, 81054 preserved.')],directory_coverage_changes=0,whole_institution_coverage_complete=False))
b.save('failures-and-resolutions.json',dict(at=at,provider_failures=[],production_failures=[],research_interlocks=[dict(action='Global The Artist’s Father title reconciliation',finding='Unlinked same-title record stopped planning',resolution='Existing Max Thalmann 1909 lithograph at Met is distinct from Parthenis 1897–1899 oil on cloth; accession, dimensions, medium and creator evidence saved.',evidence='father-global-collision-review.json'),dict(action='Dependent image preparation',finding='Stopped before downloads while pinned plan was absent',resolution='Resolved identity guard; pinned plan then prepared successfully')],unresolved=review,provider_holds_preserved=True))
paths=[str((b.E/name).relative_to(b.ROOT)) for name in ['batch-verification-receipt.json','independent-source-verification.json','independent-production-verification.json','independent-audit-history-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-existing-preservation-verification.json','independent-resume-verification.json','independent-held-and-attribution-verification.json','actual-visual-review.json','actual-existing-composition-review.json','source-register-final.json','source-access-holds.json','prior-batch-live-reconciliation.json','local-recovery-verification.json','external-continuation-verification.json','failures-and-resolutions.json','french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json']]
changed={'national_gallery_athens','yale_lux'};qp=b.E.parents[1]/'source-queue.json'
with (qp.parent/'source-queue.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);before_bytes=qp.read_bytes();q=json.loads(before_bytes);before=copy.deepcopy(q);assert len(q['sources'])==111
 for row in q['sources']:
  if row['source_id']=='national_gallery_athens':
   assert row['resume_cursor']==old['resume_cursor'];row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(row['resume_cursor']));row.setdefault('verified_count_history',[]).append(dict(checkpoint=row.get('checkpoint'),verified_counts=row.get('latest_batch_verified_counts'),scope='Prior batch counts retained, not recounted'))
   row.update(status='page3_three_new_parthenis_works_holdings_primary_images_verified',last_batch=88,last_checked_at=at,access_status='24 page-3 notices and three selected images HTTP 200',checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),resume_cursor=cursor,verified_counts=counts,latest_batch_verified_counts=counts)
   row.setdefault('research_history',[]).append(dict(batch=88,at=at,evidence_path=str((b.E/'source-register-final.json').relative_to(b.ROOT)),discovered=24,verified_counts=counts,existing_excluded=2,identity_or_custody_holds=14,date_holds=5))
   row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+paths+[str((b.E/'CHECKPOINT.json').relative_to(b.ROOT))]))
   row['remaining_gaps']=list(dict.fromkeys(row.get('remaining_gaps',[])+['Current cursor page 4; pages 4–5 unreviewed. Batch 88 retains 14 identity/version/custody holds and five date holds; old holds unchanged.']))
  elif row['source_id']=='yale_lux':
   row.update(status='french_reserve_exhausted_live_verified_188_already_delivered',last_batch=88,last_checked_at=at,latest_batch_verified_counts={k:0 for k in counts})
   row['resume_cursor'].update(last_live_reconciliation=str((b.E/'french-reserve-live-reconciliation.json').relative_to(b.ROOT)))
   row.setdefault('research_history',[]).append(dict(batch=88,at=at,scope='188 prepared reserve audit only',already_imported_and_illustrated=188,remaining_unimported=0,new_programme_increments=0,evidence_path=str((b.E/'french-reserve-live-reconciliation.json').relative_to(b.ROOT))))
   row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+[str((b.E/n).relative_to(b.ROOT)) for n in ['french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','source-register-final.json']]))
 unrelated={x['source_id']:x for x in before['sources'] if x['source_id'] not in changed};assert len(unrelated)==109
 assert {x['source_id']:x for x in initial['sources'] if x['source_id'] not in changed}==unrelated
 assert {x['source_id']:x for x in q['sources'] if x['source_id'] not in changed}==unrelated
 tmp=qp.with_name('source-queue.batch-000088.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');assert qp.read_bytes()==before_bytes;os.replace(tmp,qp)
 assert {x['source_id']:x for x in h.load(qp)['sources'] if x['source_id'] not in changed}==unrelated
b.save('source-queue-update-verification.json',dict(at=at,before_sha256=h.sha(before_bytes),after_sha256=h.sha(qp.read_bytes()),entries=111,changed_source_ids=sorted(changed),unrelated_entries_preserved=109,prior_athens_cursor_retained=True,all_other_recovery_cursors_preserved=True))
paths.append(str((b.E/'source-queue-update-verification.json').relative_to(b.ROOT)))
limitations=['14 identity/version/custody candidates and five unknown/open-date records held; two exact existing records excluded.','Three derivatives individually viewed; 47 existing reproductions viewed in five prior sheets; originals technically decoded, not separately viewed.','Scoped recovery contains schema and affected rows/preimages, not a full database dump.','Restricted museum rights retained separately from user approval.','Catalogue-wide totals and ten-million-row performance not measured by this bounded batch.']
cp=dict(at=at,batch=88,stage='independently_verified_complete',outcome='progress',started_at=start,elapsed_seconds=elapsed,verified_counts=counts,discovered_objects=24,selected_objects=3,prepared_images=3,imported_objects=3,verified_objects=3,existing_objects_excluded=2,identity_or_custody_holds=14,date_holds=5,production_ids=rc['production_ids'],metadata_plan_sha256=pin,image_selection_sha256=rc['image_selection_sha256'],resume_cursor=cursor,next_task=next_task,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-greek-000088-resume.py',verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-greek-000088-verify.py',evidence_paths=paths,delivery_complete_do_not_count_again=True,external_supervisor_unchanged=True,no_local_catalogue_connections=True,limitations=limitations)
b.save('CHECKPOINT.json',cp);h.save(b.R/'CHECKPOINT.json',cp)
b.save('milestone-report.json',dict(at=at,batch=88,batch_elapsed_seconds=elapsed,programme_measured_elapsed_seconds=runtime,prior_supervisor_verified_totals=parent['totals'],batch_verified_increments=counts,reconciled_programme_totals_including_this_batch={k:parent['totals'][k]+counts[k] for k in counts},totals_scope='Programme receipt totals only; previous French campaign excluded. External supervisor owns hourly/100-hour reports and cumulative updates.',next_task=next_task,continue_after_100_hours=True,provider_failures=0,production_failures=0,resolved_research_interlocks=2,limitations=limitations))
(b.E/'README.md').write_text('''# Batch 88: French reserve reconciliation and Athens page 3

All 188 French reserve works already exist in production with their original UUIDs,
source-plan citations and primary images. Original captures, 188 checksum-bound
prior visual decisions and prepared files were verified. No French additions are
counted, and immutable historical plans remain unchanged.

Athens page 3 delivered three new Parthenis review paintings, three authentic
primary images and three documented holdings: Scene in front of an Ancient Temple
(Π.9998), The Artist’s Father (Π.9992), and Temple of Olympian Zeus (Π.3230).
No new painters or alternate images. All 24 notices were researched: three selected,
two exact existing records excluded, fourteen identity/version/custody holds and
five unknown/open-date holds. No current display claim is made.

Every selected derivative was individually viewed, decoded and verified under
100,000 bytes, preserving supplied composition and proportions. Forty-seven
existing reproductions were viewed in five prior contact sheets. Original files
remain outside Documents. Museum rights remain restricted; user approval is
recorded separately. Exact image hashes passed public delivery and storage checks.

Independent source, database, audit and delivery receipts attribute additions to
this plan and its locked empty preimages. Replay changed no database snapshot,
audit counts or storage generation. All 66 compared existing artworks and the
existing creator remain unchanged. Recovery is schema plus scoped affected rows.

The external supervisor was verified read-only; no new supervisor, schedule,
subagent, local catalogue mutation, commit or deployment occurred. Athens resumes
at page 4. Warsaw icon page 9 is the recommended next route. The two researched
source entries were updated; all other 109 queue entries remain unchanged.

See batch-verification-receipt.json, independent-production-verification.json,
independent-public-verification.json, independent-resume-verification.json,
source-queue-update-verification.json, milestone-report.json and CHECKPOINT.json.
''')
manifest=[]
for name in [Path(x).name for x in paths]+['CHECKPOINT.json','milestone-report.json','README.md','required-input-reconciliation.json','final-global-identity-reconciliation.json','editorial-selection-review.json','father-global-collision-review.json']:
 f=b.E/name;assert f.exists();manifest.append(dict(path=str(f.relative_to(b.ROOT)),sha256=h.sha(f.read_bytes()),bytes=f.stat().st_size))
for f in sorted((b.ROOT/'ops').glob('*000088*.py')):manifest.append(dict(path=str(f.relative_to(b.ROOT)),sha256=h.sha(f.read_bytes()),bytes=f.stat().st_size))
b.save('final-checkpoint-verification.json',dict(at=h.now(),files=manifest,evidence_files_exist=True,runtime_checkpoint_equal=h.load(b.R/'CHECKPOINT.json')==cp,verified_counts=counts,source_queue_other_109_unchanged=True,supervisor_configuration_unmodified=True))
print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,unrelated_source_entries_preserved=109,next_page=4)))
