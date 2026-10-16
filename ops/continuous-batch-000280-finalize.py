"""Finalize independently verified batch 280; leave external supervisor untouched."""
import copy, csv, datetime, fcntl, importlib.util, json, os, subprocess
from pathlib import Path

s=importlib.util.spec_from_file_location('batch','ops/continuous-norway-images-000280.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h,i,N,R=b.h,b.i,b.E,b.RUNTIME
E=N.parent;Q=E.parents[1]/'source-queue.json'
rel=lambda p:str(Path(p).relative_to(b.ROOT))
if (E/'independent-final-artifact-verification.json').exists():
    assert h.load(E/'CHECKPOINT.json')==h.load(R/'CHECKPOINT.json')
    print(json.dumps(h.load(E/'worker-result.json')));raise SystemExit

receipt=h.load(N/'batch-verification-receipt.json');counts=receipt['verified_counts']
assert counts==dict(new_painters=0,new_artworks=0,newly_illustrated=7,alternate_images=0,museum_links=0)
assert h.load(N/'independent-resume-verification.json')['new_production_increments_on_resume']==0
images,audit,visual=i.accepted(b.B);ids=[im['artwork_id'] for im in images]
assert len(images)==len(visual['decisions'])==7
assert all(d['viewed_individually'] for d in visual['decisions'])
assert sum(d['original_separately_viewed'] for d in visual['decisions'])==2
assert len(h.load(N/'independent-public-verification.json')['rows'])==7
assert len(h.load(N/'independent-storage-verification.json')['checks'])==7
french=h.load(E/'french-reserve-live-reconciliation.json')
assert french['already_imported_active_and_illustrated']==188 and french['genuinely_unimported']==0
assert h.load(E/'independent-reserve-source-verification.json')['verified']==188
frozen=h.load(N/'oslo-bounded-gap-input.json.gz');held=h.load(N/'research-holds.json')['records']
assert len(frozen['rows'])==12 and len(held)==5
pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes())
selected={r['artwork_id']:r for r in i.selected(b.B)['rows']}
cursor_after=frozen['rows'][-1]['id']
next_task=('Research RMFAB’s unprocessed Léon Abry creator route '
    'https://fine-arts-museum.be/fr/la-collection/artist/abry-leon for source-backed through1970 '
    'metadata and museum connections, reconciling creators and exact inventories globally. '
    'Native museum image permission holds remain. Norway resumes after UUID '+cursor_after+
    '; Athens resumes at paintings page4. The French188 reserve is exhausted; do not replay '
    'or recount it without new evidence. Preserve all existing rights, date and identity holds.')

outcomes=[dict(artwork_id=x['id'],title=x['title'],inventory=x['accession_number'],
    outcome='primary_image_delivered_and_independently_verified' if x['id'] in ids else
    next(v['reason'] for v in held if v['artwork_id']==x['id'])) for x in frozen['rows']]
h.save(E/'research-outcomes-verification.json',dict(at=h.now(),french_inspected=188,
    french_previously_delivered=188,french_new_additions=0,norway_researched=12,
    selected=7,prepared=7,imported=7,verified=7,held=5,rows=outcomes,
    directory_coverage_additions=0,metadata_rewritten=0,
    hold_clarification=rel(N/'research-hold-clarification.json')))
failures=dict(at=h.now(),provider_http_failures=[],production_write_failures=0,
    unchanged_held_provider_retries=0,object_holds=held,
    hold_clarification=h.load(N/'research-hold-clarification.json'),
    french_physical_date_holds_preserved=['80082','80437','81054'],
    prior_provider_holds_preserved=True,digitaltmuseum_api_not_accessed=True,
    visual_review=dict(derivatives=7,originals=2,contact_sheets=0),
    spending_limits_changed=False,translation_calls=0,local_catalogue_connections=0)
h.save(E/'failures-and-holds.json',failures)

nfiles=['batch-verification-receipt.json','independent-source-verification.json',
    'independent-file-verification.json','independent-production-verification.json',
    'independent-audit-history-verification.json','independent-held-objects-verification.json',
    'independent-public-verification.json','independent-storage-verification.json',
    'independent-resume-verification.json','actual-visual-review.json','research-holds.json',
    'research-hold-clarification.json']
ffiles=['french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json',
    'independent-reserve-source-verification.json']
with Q.with_suffix('.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    q=h.load(Q);before=copy.deepcopy(q);h.save(E/'source-queue-before-final-update.json',before)
    nr=next(x for x in q['sources'] if x['source_id']=='nasjonalmuseet_norway')
    cursor=nr['resume_cursor'];assert cursor['after_artwork_id']==frozen['after_artwork_id']
    assert nr.get('last_batch')!=280
    nr.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(cursor))
    nr.update(status='seven_further_CC_BY_primary_images_verified_batch280',last_batch=280,
        last_checked_at=h.now(),checkpoint=rel(E/'CHECKPOINT.json'),
        latest_batch_verified_counts=counts,verified_counts=counts,
        access_status='12 native pages and copyright policy HTTP200; seven full-object CC BY images delivered and verified. DigitaltMuseum access hold preserved.',
        policy_reference='Original111-source CSV nasjonalmuseet_norway; docs/ARTLINE_IMAGE_USE.md; native CC BY4.0 policy and per-object copyright checks.')
    oldcounts=nr.get('programme_verified_counts')
    if oldcounts and all(k in oldcounts for k in counts):
        nr['programme_verified_counts']={k:oldcounts[k]+counts[k] for k in counts}
    cursor.update(previous_after_artwork_id=frozen['after_artwork_id'],after_artwork_id=cursor_after,
        selection_sha256=pin,latest_frozen_input=rel(N/'oslo-bounded-gap-input.json.gz'),
        latest_hold_ledger=rel(N/'research-holds.json'),latest_hold_clarification=rel(N/'research-hold-clarification.json'),
        latest_verified_batch=280,
        latest_rights_hold_ids=[v['artwork_id'] for v in held if v['reason']=='Object-specific copyright restriction'],
        latest_identity_hold_ids=[v['artwork_id'] for v in held if v['reason']!='Object-specific copyright restriction'],
        latest_visual_hold_ids=[],latest_source_404_hold_ids=[],no_repeat_of_unchanged_holds=True,next_step=next_task)
    for key,values in [('inspected_ids',[x['id'] for x in frozen['rows']]),('delivered_ids',ids),('held_ids',[x['artwork_id'] for x in held])]:
        cursor[key]=list(dict.fromkeys(cursor.get(key,[])+values))
    nr.setdefault('remaining_gaps',[]).append('Batch280: three copyright restrictions, one century-date phrase and one translated title require further review. Phrase/title holds are not established factual conflicts. Catalogue unchanged; full institution coverage incomplete.')
    nr.setdefault('research_history',[]).append(dict(batch=280,at=h.now(),verified_counts=counts,
        selection_sha256=pin,receipt=rel(N/'batch-verification-receipt.json')))
    for name in nfiles:
        path=rel(N/name)
        if path not in nr.setdefault('evidence_paths',[]):nr['evidence_paths'].append(path)
    yr=next(x for x in q['sources'] if x['source_id']=='yale_lux')
    yr.update(status='french_reserve_exhausted_188_live_source_and_visual_evidence_verified_batch280',
        last_checked_at=h.now(),last_batch=280,checkpoint=rel(E/'CHECKPOINT.json'),
        latest_batch_verified_counts={k:0 for k in counts})
    yr['resume_cursor'].update(french_reserve_total=188,already_imported_active_and_illustrated=188,
        genuinely_unimported=0,do_not_replay=True,held_source_ids=['80082','80437','81054'],
        next_step='Prepared French reserve exhausted; select another route without repeating unchanged reserve checks absent new evidence.')
    for name in ffiles:
        path=rel(E/name)
        if path not in yr.setdefault('evidence_paths',[]):yr['evidence_paths'].append(path)
    fr=next(x for x in q['supplementary_image_routes'] if x.get('route_id')=='french-printmaking-prepared-reserve')
    fr.update(status='exhausted_all188_active_illustrated_live_verified_batch280',last_checked_at=h.now(),
        last_batch=280,checkpoint=rel(E/'CHECKPOINT.json'),latest_batch_verified_counts={k:0 for k in counts},
        verification_receipt=rel(E/'french-reserve-live-reconciliation.json'),
        access_status='All188 already imported. Native source, primary associations, historical plan citations and prior visual checksums verified; zero new increments.',
        next_task='Switch to another registry route; no unchanged reserve replay or recount.')
    modified={'yale_lux','nasjonalmuseet_norway'}
    assert len(q['sources'])==111
    assert [x for x in q['sources'] if x['source_id'] not in modified]==[x for x in before['sources'] if x['source_id'] not in modified]
    assert [x for x in q['supplementary_image_routes'] if x.get('route_id')!=fr['route_id']]==[x for x in before['supplementary_image_routes'] if x.get('route_id')!=fr['route_id']]
    assert {k:v for k,v in q.items() if k not in ['sources','supplementary_image_routes']}=={k:v for k,v in before.items() if k not in ['sources','supplementary_image_routes']}
    temp=Q.with_suffix('.280.tmp');temp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(temp,Q)
    assert h.load(Q)==q
    h.save(E/'source-queue-update-verification.json',dict(at=h.now(),modified_registry_routes=sorted(modified),
        unrelated_registry_routes_preserved=109,modified_supplementary_routes=[fr['route_id']],
        other_supplementary_routes_unchanged=True,source_queue_sha256=h.sha(Q.read_bytes()),
        prior_queue_sha256=h.sha((E/'source-queue-before-final-update.json').read_bytes()),
        french_genuinely_unimported=0,norway_after_artwork_id=cursor_after,norway_verified_new_primary_images=7,norway_new_holds=5))

registry=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')))
h.save(E/'source-register-final.json',dict(at=h.now(),original_registry_rows=len(registry),
    original_registry_sha256=h.sha(Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv').read_bytes()),
    sources=[dict(registry_record=r,queue_record=nr if r['source_id']=='nasjonalmuseet_norway' else yr) for r in registry if r['source_id'] in modified],
    directory_coverage_is_not_artwork_coverage=True))
state=h.load(E.parents[1]/'CHECKPOINT.json');assert state['inflight']['batch']==280
start=state['inflight']['started_at'];end=h.now()
seconds=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
command=subprocess.check_output(['ps','-p',str(state['supervisor_pid']),'-o','command='],text=True).strip()
assert 'continuous-production-research.py run' in command
h.save(E/'supervisor-final-observation.json',dict(at=end,pid=state['supervisor_pid'],command=command,
    external_supervisor_live=True,inflight_batch=280,supervisor_modified=False,new_supervisors=0,new_schedules=0,subagents=0,
    continuation_and_hourly_reporting_owned_by_existing_supervisor=True))
h.save(E/'batch-verification-receipt.json',dict(receipt,batch=280,
    french_reserve_previously_delivered_excluded_from_counts=188,norway_researched=12,norway_held=5,
    child_receipt=rel(N/'batch-verification-receipt.json'),child_receipt_sha256=h.sha((N/'batch-verification-receipt.json').read_bytes())))
h.save(E/'verified-delivery-manifest.json',dict(at=end,selection_sha256=pin,verified_counts=counts,
    rows=[dict(artwork_id=im['artwork_id'],native_id=selected[im['artwork_id']]['native_id'],
        inventory=selected[im['artwork_id']]['accession_number'],source_url=selected[im['artwork_id']]['source_url'],
        image_sha256=im['sha256'],bytes=im['bytes'],storage_path=im['storage_path'],media_id=im['media_id']) for im in images]))
h.save(E/'batch-runtime-report.json',dict(at=end,started_at=start,finished_at=end,measured_runtime_seconds=seconds,
    verified_counts=counts,prior_supervisor_totals=state['totals'],
    cumulative_including_current_batch={k:state['totals'][k]+counts[k] for k in counts},
    cumulative_basis='Supervisor verified ledger plus this attributed batch; not a whole catalogue census.',
    hourly_reports_owned_by_external_supervisor=True,next_task=next_task,failures_and_uncertainty=failures))
files=[E/name for name in ['required-input-verification.json','inherited-holds-verification.json','limits-verification.json',
    'production-target-reconciliation.json','batch107-live-reconciliation.json',*ffiles,'research-outcomes-verification.json',
    'failures-and-holds.json','source-queue-update-verification.json','source-register-final.json','batch-verification-receipt.json',
    'verified-delivery-manifest.json','batch-runtime-report.json','supervisor-final-observation.json']]
files += [N/name for name in nfiles+['local-recovery-verification.json','independent-prewrite-verification.json']]
cp=dict(at=end,batch=280,stage='independently_verified_complete',outcome='progress',started_at=start,finished_at=end,
    measured_runtime_seconds=seconds,verified_counts=counts,production_ids=ids,
    stage_counts=dict(french_checked=188,french_previously_delivered=188,norway_checked=12,selected=7,prepared=7,imported=7,verified=7,held=5),
    actual_visual_review=dict(derivatives=7,originals=2,contact_sheets=0),next_task=next_task,blocker='',
    external_supervisor_unchanged=True,local_catalogue_connections=0,evidence_paths=[rel(p) for p in files])
for path in [E/'CHECKPOINT.json',R/'CHECKPOINT.json']:
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(cp,ensure_ascii=False,indent=2)+'\n');os.replace(temp,path)
result=dict(outcome='progress',summary='Verified seven new primary images on existing Norwegian artworks. All188 French reserve objects were previously delivered and excluded. Five holds saved; production, storage, public delivery and replay checks passed.',
    next_task=next_task,blocker='',verified_counts=counts,
    evidence_paths=[rel(E/name) for name in ['CHECKPOINT.json','batch-verification-receipt.json','french-reserve-live-reconciliation.json',
        'independent-reserve-source-verification.json','source-queue-update-verification.json','independent-final-artifact-verification.json']]+
        [rel(N/name) for name in ['independent-production-verification.json','independent-audit-history-verification.json',
            'independent-public-verification.json','independent-storage-verification.json','independent-resume-verification.json','actual-visual-review.json']])
h.save(E/'worker-result.json',result);h.save(R/'verified-batch-result.json',result)
(E/'README.md').write_text('# Batch 280\n\nSeven existing Norwegian artworks gained independently verified primary images. No new painters, artworks, alternate images or museum links. Twelve native object pages were researched: seven delivered, three copyright holds, one century-date wording hold and one translated-title hold. The latter two are unresolved review requirements, not demonstrated factual conflicts. All previous metadata, creators, holdings and statuses remained unchanged.\n\nAll seven derivatives were actually viewed individually; two originals were separately viewed. Other originals were technically decoded and hashed, not visually reviewed. No contact-sheet visual review is claimed. Largest served image: '+str(max(im['bytes'] for im in images))+' bytes. Originals and scoped recovery are outside Documents. Recovery comprises a fully decoded schema dump plus exact affected rows, not a full database backup.\n\nAll188 French reserve works already belonged to a prior campaign. Live source-plan citations, active artwork/image identities, original captures and immutable visual evidence were verified. No French additions or duplicate writes. Batch107 matches its verified postimage.\n\nIndependent source, file, row, audit, storage and public API/image checks passed. Exact transaction preimages and persisted selection/source/visual checksums prove this batch’s seven null-to-primary changes. Replay produced zero new changes. Only Norway, Yale and the supplementary French reserve queue route were updated;109 unrelated registry routes were preserved. The existing external supervisor remains live and owns continuation and hourly reports; it was not modified.\n\nNext: '+next_task+'\n\nMeasured runtime: '+str(round(seconds,1))+' seconds.\n')
assert h.load(E/'CHECKPOINT.json')==h.load(R/'CHECKPOINT.json')
assert h.load(E/'worker-result.json')==h.load(R/'verified-batch-result.json')
files += [E/name for name in ['CHECKPOINT.json','worker-result.json','README.md']]
h.save(E/'independent-final-artifact-verification.json',dict(at=h.now(),
    files=[dict(path=rel(p),bytes=p.stat().st_size,sha256=h.sha(p.read_bytes())) for p in files],
    all_verification_files_present=True,runtime_checkpoint_equal=True,runtime_result_equal=True,verified_counts=counts,passed=True))
assert all((b.ROOT/p).exists() for p in result['evidence_paths'])
print(json.dumps(result,ensure_ascii=False))
