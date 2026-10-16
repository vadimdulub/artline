"""Persist verified batch 93 and advance only the researched Athens source route."""
import copy,datetime,fcntl,importlib.util,json,os,subprocess,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('b93',Path(__file__).with_name('continuous-greek-batch-000093.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
final=b.E/'final-checkpoint-verification.json'
if final.exists():
 for x in h.load(final)['files']:assert h.sha((b.ROOT/x['path']).read_bytes())==x['sha256']
 assert h.load(b.R/'CHECKPOINT.json')==h.load(b.E/'CHECKPOINT.json');print('Durable checkpoint and immutable verification files unchanged.');sys.exit(0)
rc=h.load(b.E/'batch-verification-receipt.json');replay=h.load(b.E/'independent-resume-verification.json');assert replay['unchanged_snapshot'] and not any(replay['replay_increments'].values())
p,pin=h.pinned(b.PHASE);counts=rc['verified_counts'];assert counts==dict(new_painters=0,new_artworks=5,newly_illustrated=5,alternate_images=0,museum_links=5)
checks=h.load(b.E/'parthenis-global-identity-reconciliation.json')['records'];review=h.load(b.E/'editorial-selection-review.json');assert len(checks)==24 and sum(bool(x['existing']) for x in checks)==4 and len(review['held_versions'])==10 and len(review['date_holds'])==5
parent=h.load(b.E.parents[1]/'CHECKPOINT.json');assert parent['inflight']['batch']==93
at=h.now();start=parent['inflight']['started_at'];elapsed=(datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(start)).total_seconds();runtime=(datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(parent['started_at'])).total_seconds()
pid=parent['supervisor_pid'];proc=subprocess.check_output(['ps','-p',str(pid),'-o','pid=,etime=,command='],text=True).strip();assert 'ops/continuous-production-research.py run' in proc
prev=b.R.parent/'000092/result-001.json';prev_result=h.load(prev);assert prev_result['verified_counts']==parent['previous']['verified_counts'];assert h.load(b.E/'prior-batch-live-reconciliation.json')['previous_batch_verified']
b.save('external-continuation-verification.json',dict(at=at,external_supervisor_process=proc,supervisor_script_sha256=h.sha((b.ROOT/'ops/continuous-production-research.py').read_bytes()),previous_completed_result=dict(path=str(prev),sha256=h.sha(prev.read_bytes())),observed_handoff='Persisted batch 92 result and shared in-flight batch 93 checkpoint, with live existing supervisor. Prior batch 92 production and image rights independently reconciled.',new_supervisors_or_schedules_launched=0,supervisor_configuration_edits=0,scope='Existing external continuation checked read-only; future uptime not guaranteed.'))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 heldids=[h.uid('artwork/athens/'+x['record']['source_id']) for x in p['held']];assert not h.snapshot(db,heldids)
 notes=list(db.execute('SELECT entity_id::text,evidence_note::jsonb->>\'plan_sha256\' pin FROM citations WHERE field_name=%s',(b.FIELD,)));assert len(notes)==5 and all(x['pin']==pin for x in notes)
 assert h.snapshot(db,rc['production_ids'])==h.load(b.E/'independent-production-verification.json')['after']
b.save('independent-held-and-attribution-verification.json',dict(at=at,held_proposed_artwork_ids_absent=heldids,own_plan_citations=notes,metadata_plan_sha256=pin,own_five_objects_only=True,prior_campaigns_excluded=True))
initial=h.load(b.E/'source-queue-before.json');old=next(x for x in initial['sources'] if x['source_id']=='national_gallery_athens');cursor=copy.deepcopy(old['resume_cursor'])
cursor.update(processed_page=4,next_page=5,documented_next_request=dict(method='POST',url='https://www.nationalgallery.gr/wp-admin/admin-ajax.php',form=dict(artist_id='91',lang='en',page=5,action='get_artist_artworks'),evidence=str((b.E/'parthenis-page4-capture.json').relative_to(b.ROOT)),executed=False),parthenis_notices_reviewed=old['resume_cursor']['parthenis_notices_reviewed']+24,processed_urls=list(dict.fromkeys(cursor['processed_urls']+[x['url'] for x in checks])),verified_source_ids=list(dict.fromkeys(cursor['verified_source_ids']+review['selected'])),verified_artwork_ids=list(dict.fromkeys(cursor['verified_artwork_ids']+rc['production_ids'])))
cursor['held_versions'].update(review['held_versions']);cursor['held_date_source_ids']=list(dict.fromkeys(cursor['held_date_source_ids']+[r['source_id'] for r in review['date_holds']]))
cursor['next_step']='After institution rotation, resume artist 91 page 5 (last reported page); skip all processed URLs. Preserve date, exact-version, compound-unit and Aphrodite image-date holds.'
next_task='Research QAGOMA’s nine untouched frozen image gaps via approved WikiArt, preserving its native access hold. Athens Parthenis resumes at page 5; Warsaw icons page 10 is also queued. Skip the exhausted French reserve.'
inputs=h.load(b.E/'required-input-reconciliation.json');reg=inputs['registry'];regref=next(x for x in inputs['inputs'] if x['path'].endswith('GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'))
b.save('source-register-final.json',dict(at=at,registry=regref,registry_rows=111,complete_original_registry_used=True,researched=[dict(registry_entry=next(x for x in reg if x['source_id']=='national_gallery_athens'),policy_reference='docs/ARTLINE_IMAGE_USE.md: nationwide Greek museum delivery and Greek painter extension through 1955',access_status='One documented public page-4 index request, 24 exact notices and five selected images HTTP 200',last_checked_at=at,discovered=24,selected=5,prepared=5,imported=5,verified=5,existing_exact_objects_excluded=4,identity_version_or_unit_holds=10,date_holds=5,resume_cursor=cursor,remaining_gaps='Page 5 unreviewed; existing date and physical-version/unit holds remain. Two native image/support dimension discrepancies explicitly reviewed; no distortion or metadata correction.')],directory_coverage_changes=0,whole_institution_coverage_complete=False,unrelated_routes_researched=False))
b.save('research-holds.json',dict(at=at,source_id='national_gallery_athens',identity_version_or_unit=review['held_versions'],date_holds=review['date_holds'],existing_excluded=[x for x in checks if x['existing']],image_dimension_review='source-dimension-review.json',prior_holds_preserved=True,do_not_repeat_unchanged_holds=True))
b.save('failure-ledger.json',dict(at=at,provider_access_failures=0,production_write_failures=0,resolved_interlocks=[dict(stage='global title reconciliation',attempt=1,reason='Harvest title collisions included unlinked but differently named artists; reviewed source identities and preserved snapshots before retry.'),dict(stage='global title reconciliation',attempt=2,reason='Saint Sebastian title collisions included 15th–18th-century anonymous and qualified attributions; explicitly separated from 1935–1938 Parthenis work before retry.')],local_tool_correction='Inspection initially used Python without bs4; switched to established environment, no source or database effects.',secondary_web_tool_cache_misses=['https://www.nationalgallery.gr/en/artwork/harvest/','https://www.nationalgallery.gr/en/artwork/table-with-flowers/'],canonical_captures='Direct official pages already returned HTTP 200 and were checksum captured; no provider restriction bypass or repeated failed fetch.',parser_correction='Candle Lighting support-only description retained as medium, dimensions null.',paid_services_or_new_budget=0))
names=['batch-verification-receipt.json','independent-production-verification.json','independent-audit-history-verification.json','independent-source-verification.json','independent-file-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-existing-preservation-verification.json','independent-held-and-attribution-verification.json','independent-resume-verification.json','actual-visual-review.json','actual-existing-composition-review.json','source-dimension-review.json','local-recovery-verification.json','research-holds.json','source-register-final.json','failure-ledger.json','external-continuation-verification.json','prior-batch-live-reconciliation.json']
paths=[str((b.E/n).relative_to(b.ROOT)) for n in names];qp=b.E.parents[1]/'source-queue.json'
with (qp.parent/'source-queue.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);before_bytes=qp.read_bytes();q=json.loads(before_bytes);before=copy.deepcopy(q);assert len(q['sources'])==111
 row=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens');assert row['resume_cursor']==old['resume_cursor']
 row.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(row['resume_cursor']));row.setdefault('verified_count_history',[]).append(dict(checkpoint=row.get('checkpoint'),verified_counts=row.get('latest_batch_verified_counts'),scope='Prior batch counts retained, not recounted'))
 row.setdefault('prior_remaining_gaps',[]).append(dict(at=row.get('last_checked_at'),gaps=copy.deepcopy(row.get('remaining_gaps',[]))))
 row.update(status='page4_five_new_parthenis_review_paintings_holdings_primary_images_verified',last_batch=93,last_checked_at=at,access_status='24 page-4 notices and five selected images HTTP 200',checkpoint=str((b.E/'CHECKPOINT.json').relative_to(b.ROOT)),resume_cursor=cursor,verified_counts=counts,latest_batch_verified_counts=counts)
 row.setdefault('research_history',[]).append(dict(batch=93,at=at,evidence_path=str((b.E/'source-register-final.json').relative_to(b.ROOT)),discovered=24,verified_counts=counts,existing_excluded=4,identity_version_or_unit_holds=10,date_holds=5))
 row['evidence_paths']=list(dict.fromkeys(row.get('evidence_paths',[])+paths+[str((b.E/'CHECKPOINT.json').relative_to(b.ROOT))]))
 row['remaining_gaps']=['Parthenis page 5 remains; 96 of 115 source notices reviewed, not 96 eligible or delivered artworks.','All earlier exact-version, custody, compound-unit and date holds remain in preserved cursors and batch ledgers.','Page 4: ten identity/version/unit holds, five date holds, four exact existing objects excluded.','Aphrodite 1950–1960 remains subject to museum-source image cutoff; no unchanged image retry.','Whole institution and nationwide museum artwork coverage incomplete.']
 unrelated={x['source_id']:x for x in before['sources'] if x['source_id']!='national_gallery_athens'};assert len(unrelated)==110
 assert {x['source_id']:x for x in q['sources'] if x['source_id']!='national_gallery_athens'}==unrelated
 tmp=qp.with_name('source-queue.batch-000093.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');assert qp.read_bytes()==before_bytes;os.replace(tmp,qp)
 assert {x['source_id']:x for x in h.load(qp)['sources'] if x['source_id']!='national_gallery_athens'}==unrelated
b.save('independent-queue-verification.json',dict(at=at,before_sha256=h.sha(before_bytes),after_sha256=h.sha(qp.read_bytes()),entries=111,changed_source_ids=['national_gallery_athens'],unrelated_entries_preserved=110,prior_athens_cursor_retained=True,resume_page=5,unrelated_routes_untouched=True));paths.append(str((b.E/'independent-queue-verification.json').relative_to(b.ROOT)))
limitations=['Fifteen candidates remain on date/version/unit review holds; four existing works excluded.','Five derivatives individually viewed; two flagged originals viewed; other originals technically decoded. Fifty existing reproductions viewed in six prior immutable sheets; 18 unillustrated creator works metadata-only.','Two native image/support aspect discrepancies (about 6%) retained, reviewed individually, not distorted. Candle Lighting physical dimensions remain unknown.','Recovery contains schema plus scoped affected rows and locked preimages, not a full catalogue export.','Source rights remain restricted and separate from user approval; no current display claims.','Catalogue-wide goal totals not re-counted by this bounded operation.']
cp=dict(at=at,batch=93,stage='independently_verified_complete',outcome='progress',started_at=start,elapsed_seconds=elapsed,verified_counts=counts,discovered_objects=24,selected_objects=5,prepared_images=5,imported_objects=5,verified_objects=5,existing_objects_excluded=4,identity_version_or_unit_holds=10,date_holds=5,production_ids=rc['production_ids'],metadata_plan_sha256=pin,image_selection_sha256=rc['image_selection_sha256'],resume_cursor=cursor,next_task=next_task,resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-greek-000093-resume.py',verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-greek-000093-verify.py',evidence_paths=paths,delivery_complete_do_not_count_again=True,external_supervisor_unchanged=True,no_local_catalogue_connections=True,limitations=limitations)
b.save('CHECKPOINT.json',cp);h.save(b.R/'CHECKPOINT.json',cp)
b.save('milestone-report.json',dict(at=at,batch=93,batch_elapsed_seconds=elapsed,programme_measured_elapsed_seconds=runtime,prior_supervisor_verified_totals=parent['totals'],batch_verified_increments=counts,reconciled_programme_totals_including_this_batch={k:parent['totals'][k]+counts[k] for k in counts},totals_scope='Programme receipt totals only; prior campaigns excluded. External supervisor owns cumulative checkpoint and scheduled hourly/100-hour reports.',next_task=next_task,continue_after_100_hours=True,provider_access_failures=0,production_failures=0,resolved_identity_interlocks=2,limitations=limitations))
(b.E/'README.md').write_text('''# Batch 93: Athens Parthenis page 4

Verified five new review paintings, five authentic primary images and five documented
museum holdings: Harvest, Table with Flowers, Saint Sebastian, Portrait of Zacharias
Papantoniou and Candle Lighting. The existing artist was reused; no new painters.

Of 24 native notices, four already matched exact existing objects. Ten version or
compound-unit questions and five date questions remain held. No dates invented;
Candle Lighting dimensions remain null. The next Athens page is 5 (96/115 notices
reviewed, not 96 new artworks). Coverage remains incomplete.

All five derivatives were individually viewed, decoded, hashed and delivered under
100,000 bytes. Two originals with image/support proportion discrepancies were viewed
separately and preserved without distortion. Fifty existing images were compared in
six checksum-verified prior sheets. The source rights remain restricted; explicit
Greek user approval is recorded separately from a copyright-holder licence.

Independent production, audit, storage and API/image receipts attribute every increment
to this plan and its empty/null locked preimages. Replay produced zero database, audit
or storage-generation changes. All 164 compared existing artworks and one artist stayed
unchanged. Scoped recovery exports and originals remain outside Documents.

The existing external supervisor was checked read-only; no supervisor, schedule,
subagent, deployment, commit or local database mutation occurred. Only the Athens source
queue entry changed; all 110 unrelated entries remained unchanged. Rotate next to the
nine untouched QAGOMA WikiArt image candidates; retain its native access hold.
''')
manifest=[]
for name in names+['independent-queue-verification.json','CHECKPOINT.json','milestone-report.json','README.md','required-input-reconciliation.json','final-global-identity-reconciliation.json','editorial-selection-review.json','other-title-candidates-before.json.gz']:
 f=b.E/name;assert f.exists();manifest.append(dict(path=str(f.relative_to(b.ROOT)),sha256=h.sha(f.read_bytes()),bytes=f.stat().st_size))
for f in sorted((b.ROOT/'ops').glob('*000093*.py')):manifest.append(dict(path=str(f.relative_to(b.ROOT)),sha256=h.sha(f.read_bytes()),bytes=f.stat().st_size))
b.save('final-checkpoint-verification.json',dict(at=h.now(),files=manifest,evidence_files_exist=True,runtime_checkpoint_equal=h.load(b.R/'CHECKPOINT.json')==cp,verified_counts=counts,source_queue_other_110_unchanged=True,supervisor_configuration_unmodified=True))
print(json.dumps(dict(verified_counts=counts,elapsed_seconds=elapsed,unrelated_source_entries_preserved=110,next_page=5)))
