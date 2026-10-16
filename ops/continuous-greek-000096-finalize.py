"""Save bounded batch receipts; update only the researched registry route."""
import copy,datetime,fcntl,importlib.util,json,os,subprocess,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('b96',Path(__file__).with_name('continuous-greek-batch-000096.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
final=b.E/'final-checkpoint-verification.json'
if final.exists():
 for x in h.load(final)['files']:assert h.sha((b.ROOT/x['path']).read_bytes())==x['sha256']
 assert h.load(b.R/'CHECKPOINT.json')==h.load(b.E/'CHECKPOINT.json');print('Checkpoint files verified unchanged.');sys.exit(0)
rc=h.load(b.E/'batch-verification-receipt.json');replay=h.load(b.E/'independent-resume-verification.json');assert replay['unchanged_snapshot'] and not any(replay['replay_increments'].values())
p,pin=h.pinned(b.PHASE);counts=rc['verified_counts'];assert counts==dict(new_painters=0,new_artworks=3,newly_illustrated=3,alternate_images=0,museum_links=3)
checks=h.load(b.E/'parthenis-global-identity-reconciliation.json')['records'];review=h.load(b.E/'editorial-selection-review.json');assert len(checks)==19 and sum(bool(x['existing']) for x in checks)==4 and len(review['held_versions'])==8 and len(review['date_holds'])==4
parent=h.load(b.E.parents[1]/'CHECKPOINT.json');assert parent['inflight']['batch']==96
at=h.now();start=parent['inflight']['started_at'];elapsed=(datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(start)).total_seconds();runtime=(datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(parent['started_at'])).total_seconds()
pid=parent['supervisor_pid'];proc=subprocess.check_output(['ps','-p',str(pid),'-o','pid=,etime=,command='],text=True).strip();assert 'ops/continuous-production-research.py run' in proc
prev=b.R.parent/'000095/result-001.json';prev_result=h.load(prev);assert prev_result['verified_counts']==parent['previous']['verified_counts'];assert h.load(b.E/'prior-batch-live-reconciliation.json')['previous_batch_verified']
script_sha=h.sha((b.ROOT/'ops/continuous-production-research.py').read_bytes());assert script_sha==h.load(b.E.parent/'000095/external-continuation-verification.json')['supervisor_script_sha256']
b.save('external-continuation-verification.json',dict(at=at,external_supervisor_process=proc,supervisor_script_sha256=script_sha,script_unchanged_from_batch95=True,previous_completed_result=dict(path=str(prev),sha256=h.sha(prev.read_bytes())),observed_inflight=parent['inflight'],observed_handoff='Persisted batch 95 result and in-flight batch 96 checkpoint, plus live existing supervisor; prior production and exact image-rights evidence reconciled read-only.',new_supervisors_or_schedules_launched=0,supervisor_configuration_edits=0,scope='Existing continuation verified read-only; future uptime not guaranteed.'))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 heldids=[h.uid('artwork/athens/'+x['record']['source_id']) for x in p['held']];assert not h.snapshot(db,heldids)
 notes=list(db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s",(b.FIELD,)));assert len(notes)==3 and all(x['pin']==pin for x in notes)
 assert h.snapshot(db,rc['production_ids'])==h.load(b.E/'independent-production-verification.json')['after']
b.save('independent-held-and-attribution-verification.json',dict(at=at,held_proposed_artwork_ids_absent=heldids,own_plan_citations=notes,metadata_plan_sha256=pin,own_objects_only=True,prior_campaigns_excluded=True))
initial=h.load(b.E/'source-queue-before.json');old=next(x for x in initial['sources'] if x['source_id']=='national_gallery_athens');cursor=copy.deepcopy(old['resume_cursor'])
index_rc=h.load(b.E/'parthenis-page5-capture.json');index=json.loads(Path(index_rc['body_path']).read_bytes());assert index['max']==5 and index['have_more'] is False
cursor.update(processed_page=5,next_page=None,documented_next_request=None,index_exhausted=True,index_exhaustion_evidence=str((b.E/'parthenis-page5-capture.json').relative_to(b.ROOT)),parthenis_notices_reviewed=old['resume_cursor']['parthenis_notices_reviewed']+19,processed_urls=list(dict.fromkeys(cursor['processed_urls']+[x['url'] for x in checks])),verified_source_ids=list(dict.fromkeys(cursor['verified_source_ids']+review['selected'])),verified_artwork_ids=list(dict.fromkeys(cursor['verified_artwork_ids']+rc['production_ids'])))
assert cursor['parthenis_notices_reviewed']==cursor['parthenis_source_reported_total']==115
cursor['completed_creator_indexes']=list(dict.fromkeys(cursor['completed_creator_indexes']+['parthenis-konstantinos']))
cursor['held_versions'].update(review['held_versions']);cursor['held_date_source_ids']=list(dict.fromkeys(cursor['held_date_source_ids']+[r['source_id'] for r in review['date_holds']]))
cursor['next_step']='Parthenis official index pages 1–5 complete (115 notices, not 115 new artworks). Rotate institution; later reconcile saved exact-version/date cases or select another verified Greek creator index. Do not request page 6.'
next_task='Resume Warsaw painted icons at page 11. Athens Parthenis index is complete at 115 notices; preserve its unresolved dates and versions. Keep untouched Auckland/KHM image candidates queued and avoid unchanged provider holds.'
inputs=h.load(b.E/'required-input-reconciliation.json');reg=inputs['registry'];regref=next(x for x in inputs['inputs'] if x['path'].endswith('GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'))
b.save('source-register-final.json',dict(at=at,registry=regref,registry_rows=111,complete_original_registry_used=True,researched=[dict(registry_entry=next(x for x in reg if x['source_id']=='national_gallery_athens'),policy_reference='docs/ARTLINE_IMAGE_USE.md: nationwide Greek museum delivery and Greek painter extension through 1955',access_status='Public page-5 index, 19 exact object notices and three selected original images HTTP 200',last_checked_at=at,discovered=19,selected=3,prepared=3,imported=3,verified=3,existing_exact_objects_excluded=4,identity_version_holds=8,date_holds=4,resume_cursor=cursor,remaining_gaps='Parthenis source index exhausted, museum and nationwide artwork coverage incomplete; saved date/version cases remain.')],directory_coverage_changes=0,whole_institution_coverage_complete=False,unrelated_routes_researched=False))
b.save('research-holds.json',dict(at=at,source_id='national_gallery_athens',identity_version=review['held_versions'],date_holds=review['date_holds'],existing_excluded=[x for x in checks if x['existing']],prior_holds_preserved=True,do_not_repeat_unchanged_holds=True))
b.save('failure-ledger.json',dict(at=at,provider_access_failures=0,production_write_failures=0,secondary_web_tool_cache_misses=['https://www.nationalgallery.gr/en/artwork/ariadne-and-pegasus/','https://www.nationalgallery.gr/en/artwork/in-the-studio/'],canonical_captures='Direct official pages already HTTP 200, source hashes retained; web cache misses not retried and no provider restrictions bypassed.',paid_services_or_new_budget=0))
names=['batch-verification-receipt.json','independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-existing-preservation-verification.json','independent-held-and-attribution-verification.json','independent-resume-verification.json','actual-visual-review.json','actual-existing-composition-review.json','source-dimension-review.json','local-recovery-verification.json','research-holds.json','source-register-final.json','failure-ledger.json','external-continuation-verification.json','prior-batch-live-reconciliation.json']
paths=[str((b.E/n).relative_to(b.ROOT)) for n in names];qp=b.E.parents[1]/'source-queue.json'
with (qp.parent/'source-queue.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);before_bytes=qp.read_bytes();q=json.loads(before_bytes);before=copy.deepcopy(q);assert len(q['sources'])==111
 row=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens');assert row['resume_cursor']==old['resume_cursor']
 row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(row['resume_cursor']));row.setdefault('verified_count_history',[]).append(dict(checkpoint=row.get('checkpoint'),verified_counts=row.get('latest_batch_verified_counts'),scope='Prior batch counts retained, not recounted'))
 row.setdefault('prior_remaining_gaps',[]).append(dict(at=row.get('last_checked_at'),gaps=copy.deepcopy(row.get('remaining_gaps',[]))))
 row.update(status='parthenis_index_complete_three_page5_paintings_holdings_primary_images_verified',last_batch=96,last_checked_at=at,access_status='19 page-5 notices and three selected images HTTP 200',checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),resume_cursor=cursor,verified_counts=counts,latest_batch_verified_counts=counts)
 row.setdefault('research_history',[]).append(dict(batch=96,at=at,evidence_path=str((b.E/'source-register-final.json').relative_to(b.ROOT)),discovered=19,verified_counts=counts,existing_excluded=4,identity_version_holds=8,date_holds=4))
 row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+paths+[str((b.E/'CHECKPOINT.json').relative_to(b.ROOT))]))
 row['remaining_gaps']=['All 115 Parthenis index notices reviewed; this is not 115 eligible or delivered artworks.','Page 5: eight identity/version holds, four date holds, four existing exact objects excluded.','All prior exact-version, custody, compound-unit and date holds retained.','Aphrodite 1950–1960 retains museum-source image cutoff hold.','Whole institution and nationwide museum artwork coverage incomplete.']
 unrelated={x['source_id']:x for x in before['sources'] if x['source_id']!='national_gallery_athens'};assert len(unrelated)==110
 assert {x['source_id']:x for x in q['sources'] if x['source_id']!='national_gallery_athens'}==unrelated
 tmp=qp.with_name('source-queue.batch-000096.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');assert qp.read_bytes()==before_bytes;os.replace(tmp,qp)
 assert {x['source_id']:x for x in h.load(qp)['sources'] if x['source_id']!='national_gallery_athens'}==unrelated
b.save('independent-queue-verification.json',dict(at=at,before_sha256=h.sha(before_bytes),after_sha256=h.sha(qp.read_bytes()),entries=111,changed_source_ids=['national_gallery_athens'],unrelated_entries_preserved=110,prior_athens_cursor_retained=True,parthenis_index_complete=True,notices_reviewed=115,unrelated_routes_untouched=True));paths.append(str((b.E/'independent-queue-verification.json').relative_to(b.ROOT)))
limitations=['Twelve date/identity cases remain held from this page; four exact existing works excluded.','All three originals and derivatives individually viewed; 55 existing images viewed on seven immutable sheets, 18 unillustrated works metadata-only.','Recovery is schema plus scoped affected/locked preimages, not full catalogue export.','Actual source rights restricted; user approval separate; no current-display claims.','Catalogue-wide target totals not re-counted by this bounded batch.']
cp=dict(at=at,batch=96,stage='independently_verified_complete',outcome='progress',started_at=start,elapsed_seconds=elapsed,verified_counts=counts,discovered_objects=19,selected_objects=3,prepared_images=3,imported_objects=3,verified_objects=3,existing_objects_excluded=4,identity_version_holds=8,date_holds=4,production_ids=rc['production_ids'],metadata_plan_sha256=pin,image_selection_sha256=rc['image_selection_sha256'],resume_cursor=cursor,next_task=next_task,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-greek-000096-resume.py',verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-greek-000096-verify.py',evidence_paths=paths,delivery_complete_do_not_count_again=True,external_supervisor_unchanged=True,no_local_catalogue_connections=True,limitations=limitations)
b.save('CHECKPOINT.json',cp);h.save(b.R/'CHECKPOINT.json',cp)
b.save('milestone-report.json',dict(at=at,batch=96,batch_elapsed_seconds=elapsed,programme_measured_elapsed_seconds=runtime,prior_supervisor_verified_totals=parent['totals'],batch_verified_increments=counts,reconciled_programme_totals_including_this_batch={k:parent['totals'][k]+counts[k] for k in counts},totals_scope='Programme verified receipts only; previous campaigns excluded. Supervisor owns hourly/100-hour reporting and master checkpoint.',next_task=next_task,continue_after_100_hours=True,provider_access_failures=0,production_failures=0,limitations=limitations))
(b.E/'README.md').write_text('''# Batch 96: Athens Parthenis final index page

Verified three new review paintings, primary images and documented museum holdings:
Ariadne (?) and Pegasus, In the Studio, and The Artist’s Mother. Existing Parthenis
artist reused. Museum title uncertainty retained, no dates or current display invented.

The 19 notices comprise three additions, four existing exact objects, eight held
identity/version cases and four held dates. All 115 Parthenis source index notices
are now reviewed. This does not claim full museum artwork coverage or resolution
of the saved cases. Next: Warsaw painted icons page 11, then varied image queues.

All three original images and derivatives individually viewed. Each derivative
fully decoded, hashed, under 100,000 bytes and publicly verified. Seven immutable
prior sheets containing 55 existing images compared; 18 unillustrated creator
records received metadata-only review. Rights remain restricted, with user approval
recorded separately. Existing creator and artwork records preserved.

Independent citations, locked transaction preimages, audit records, storage and
public API/image checks prove this batch’s increments. Replay changed no rows,
audit counts or storage generations. Source captures, scoped recovery and original
images are outside Documents. Only the Athens registry entry changed; 110 others
preserved. Existing supervisor verified read-only; no new supervisor or schedule,
local catalogue write, infrastructure change, commit, push or deployment.
''')
manifest=[]
for name in names+['independent-queue-verification.json','CHECKPOINT.json','milestone-report.json','README.md','required-input-reconciliation.json','final-global-identity-reconciliation.json','editorial-selection-review.json','other-title-candidates-before.json.gz']:
 f=b.E/name;assert f.exists();manifest.append(dict(path=str(f.relative_to(b.ROOT)),sha256=h.sha(f.read_bytes()),bytes=f.stat().st_size))
for f in sorted((b.ROOT/'ops').glob('*000096*.py')):manifest.append(dict(path=str(f.relative_to(b.ROOT)),sha256=h.sha(f.read_bytes()),bytes=f.stat().st_size))
b.save('final-checkpoint-verification.json',dict(at=h.now(),files=manifest,evidence_files_exist=True,runtime_checkpoint_equal=h.load(b.R/'CHECKPOINT.json')==cp,verified_counts=counts,source_queue_other_110_unchanged=True,supervisor_script_unchanged_from_previous_batch=True))
print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,unrelated_source_entries_preserved=110,parthenis_notices_reviewed=115)))
