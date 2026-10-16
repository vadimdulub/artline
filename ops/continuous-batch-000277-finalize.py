"""Finalize one bounded verified batch without modifying its supervisor."""
import copy, csv, datetime, fcntl, importlib.util, json, os, subprocess
from pathlib import Path

s = importlib.util.spec_from_file_location('b', 'ops/continuous-norway-images-000277.py')
b = importlib.util.module_from_spec(s); s.loader.exec_module(b)
h, i, N, R = b.h, b.i, b.E, b.RUNTIME
E = N.parent
Q = E.parents[1] / 'source-queue.json'
rel = lambda p: str(Path(p).relative_to(b.ROOT))

if (E / 'independent-final-artifact-verification.json').exists():
    assert h.load(E / 'CHECKPOINT.json') == h.load(R / 'CHECKPOINT.json')
    print(json.dumps(h.load(E / 'worker-result.json')))
    raise SystemExit

receipt = h.load(N / 'batch-verification-receipt.json')
counts = receipt['verified_counts']
assert counts == dict(new_painters=0, new_artworks=0, newly_illustrated=8, alternate_images=0, museum_links=0)
assert h.load(N / 'independent-resume-verification.json')['new_production_increments_on_resume'] == 0
images, audit, visual = i.accepted(b.B)
assert len(images) == len(visual['decisions']) == 8
assert all(x['viewed_individually'] and not x['original_separately_viewed'] for x in visual['decisions'])
assert len(h.load(N / 'independent-public-verification.json')['rows']) == len(h.load(N / 'independent-storage-verification.json')['checks']) == 8
french = h.load(E / 'french-reserve-live-reconciliation.json')
assert french['already_imported_active_and_illustrated'] == 188 and french['genuinely_unimported'] == 0
assert h.load(E / 'independent-reserve-source-verification.json')['verified'] == 188
frozen = h.load(N / 'oslo-bounded-gap-input.json.gz')
held = h.load(N / 'research-holds.json')['records']
assert len(frozen['rows']) == 12 and len(held) == 4
pin = h.sha((i.folder(b.B) / 'selection.json.gz').read_bytes())
selected = {r['artwork_id']: r for r in i.selected(b.B)['rows']}
ids = [im['artwork_id'] for im in images]

outcomes = [dict(artwork_id=x['id'], title=x['title'], inventory=x['accession_number'],
                 outcome='primary_image_delivered_and_independently_verified' if x['id'] in ids else
                 next(v['reason'] for v in held if v['artwork_id'] == x['id'])) for x in frozen['rows']]
h.save(E / 'research-outcomes-verification.json', dict(at=h.now(), french_inspected=188,
       french_previously_delivered=188, french_new_additions=0, norway_researched=12,
       selected=8, prepared=8, imported=8, verified=8, held=4, rows=outcomes,
       directory_coverage_additions=0, unknown_dates_or_metadata_rewritten=0))
failures = dict(at=h.now(), provider_http_failures=[], production_write_failures=0,
                unchanged_held_provider_retries=0, object_holds=held,
                french_physical_date_holds_preserved=['80082', '80437', '81054'],
                prior_provider_holds_preserved=True, digitaltmuseum_api_not_accessed=True,
                local_diagnostics=[dict(failure='System Python lacks psycopg',
                    resolution='Reused established continuous-research/tool-venv; no installation')],
                visual_flag_resolution='Eight manual_visual_required flags individually resolved against actual prepared images.',
                spending_limits_changed=False, translation_calls=0)
h.save(E / 'failures-and-holds.json', failures)
next_task = ('Resume National Gallery Athens official paintings index page 3, using exact object/date/version '
             'reconciliation and the documented Greek museum image approval through 1955. Preserve all prior '
             'date, rights, identity and access holds. Norway can resume after UUID '
             '19187a31-761c-5565-bf9b-e1262a52db0e. The French 188-object reserve is exhausted; '
             'do not replay or recount it absent new evidence.')

nfiles = ['batch-verification-receipt.json', 'independent-source-verification.json',
          'independent-file-verification.json', 'independent-production-verification.json',
          'independent-audit-history-verification.json', 'independent-held-objects-verification.json',
          'independent-public-verification.json', 'independent-storage-verification.json',
          'independent-resume-verification.json', 'actual-visual-review.json', 'research-holds.json']
ffiles = ['french-reserve-live-reconciliation.json', 'independent-reserve-evidence-verification.json',
          'independent-reserve-source-verification.json']
zero = {k: 0 for k in counts}
with Q.with_suffix('.lock').open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    q = h.load(Q); before = copy.deepcopy(q)
    h.save(E / 'source-queue-before-final-update.json', before)
    nr = next(x for x in q['sources'] if x['source_id'] == 'nasjonalmuseet_norway')
    cursor = nr['resume_cursor']; assert cursor['after_artwork_id'] == frozen['after_artwork_id']
    assert nr.get('last_batch') != 277
    nr.setdefault('prior_resume_cursors', []).append(copy.deepcopy(cursor))
    nr.update(status='eight_further_CC_BY_primary_images_verified_batch277', last_batch=277,
              last_checked_at=h.now(), checkpoint=rel(E / 'CHECKPOINT.json'),
              latest_batch_verified_counts=counts, verified_counts=counts,
              access_status='12 native object pages and copyright policy HTTP200; eight exact full-object images and public deliveries verified. DigitaltMuseum route not used.',
              policy_reference='Original111-source CSV nasjonalmuseet_norway; docs/ARTLINE_IMAGE_USE.md; exact museum CC BY4.0 policy and individual absence of artwork copyright labels.')
    prior_counts = nr.get('programme_verified_counts')
    if prior_counts and all(k in prior_counts for k in counts):
        nr['programme_verified_counts'] = {k: prior_counts[k] + counts[k] for k in counts}
    cursor.update(previous_after_artwork_id=frozen['after_artwork_id'],
                  after_artwork_id=frozen['rows'][-1]['id'], selection_sha256=pin,
                  latest_frozen_input=rel(N / 'oslo-bounded-gap-input.json.gz'),
                  latest_hold_ledger=rel(N / 'research-holds.json'), latest_verified_batch=277,
                  latest_rights_hold_ids=[v['artwork_id'] for v in held if v['reason']=='Object-specific copyright restriction'],
                  latest_identity_hold_ids=[v['artwork_id'] for v in held if v['reason']!='Object-specific copyright restriction'],
                  latest_visual_hold_ids=[], latest_source_404_hold_ids=[],
                  no_repeat_of_unchanged_holds=True, next_step=next_task)
    for key, values in [('inspected_ids', [x['id'] for x in frozen['rows']]), ('delivered_ids', ids),
                        ('held_ids', [x['artwork_id'] for x in held])]:
        cursor[key] = list(dict.fromkeys(cursor.get(key, []) + values))
    nr.setdefault('remaining_gaps', []).append('Batch277: three object copyright holds and one Fearnley creation-date conflict (1835/1836 versus1837/1838). Fields preserved. Further UUID queue and full institution coverage remain incomplete.')
    nr.setdefault('research_history', []).append(dict(batch=277, at=h.now(), verified_counts=counts,
        selection_sha256=pin, receipt=rel(N / 'batch-verification-receipt.json')))
    for name in nfiles:
        path=rel(N / name)
        if path not in nr.setdefault('evidence_paths', []): nr['evidence_paths'].append(path)

    yr = next(x for x in q['sources'] if x['source_id'] == 'yale_lux')
    yr.update(status='french_reserve_exhausted_188_live_source_and_visual_evidence_verified_batch277',
              last_checked_at=h.now(), last_batch=277, checkpoint=rel(E / 'CHECKPOINT.json'),
              latest_batch_verified_counts=zero)
    yr['resume_cursor'].update(french_reserve_total=188, already_imported_active_and_illustrated=188,
        genuinely_unimported=0, do_not_replay=True, held_source_ids=['80082','80437','81054'],
        next_step='This prepared French reserve is exhausted. Select other registry-backed routes; do not repeat unchanged reserve checks.')
    for name in ffiles:
        path=rel(E / name)
        if path not in yr.setdefault('evidence_paths', []): yr['evidence_paths'].append(path)
    fr = next(x for x in q['supplementary_image_routes'] if x.get('route_id') == 'french-printmaking-prepared-reserve')
    fr.update(status='exhausted_all188_active_illustrated_live_verified_batch277', last_checked_at=h.now(),
              last_batch=277, checkpoint=rel(E / 'CHECKPOINT.json'), latest_batch_verified_counts=zero,
              verification_receipt=rel(E / 'french-reserve-live-reconciliation.json'),
              access_status='All188 live active illustrated objects, persisted historical plan citations, original source captures/manifests and checksum-bound prior visual decisions verified. Zero genuinely unimported objects.',
              next_task='Select another registry-backed route without repeating unchanged reserve reconciliation absent new evidence.')
    modified={'yale_lux','nasjonalmuseet_norway'}
    assert len(q['sources']) == 111
    assert [x for x in q['sources'] if x['source_id'] not in modified] == [x for x in before['sources'] if x['source_id'] not in modified]
    assert [x for x in q['supplementary_image_routes'] if x.get('route_id') != fr['route_id']] == [x for x in before['supplementary_image_routes'] if x.get('route_id') != fr['route_id']]
    assert {k:v for k,v in q.items() if k not in ['sources','supplementary_image_routes']} == {k:v for k,v in before.items() if k not in ['sources','supplementary_image_routes']}
    temp=Q.with_suffix('.277.tmp'); temp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n'); os.replace(temp,Q)
    assert h.load(Q) == q
    h.save(E / 'source-queue-update-verification.json', dict(at=h.now(), registry_rows=111,
        modified_registry_routes=sorted(modified), unrelated_registry_routes_preserved=109,
        modified_supplementary_routes=[fr['route_id']], other_supplementary_routes_unchanged=True,
        source_queue_sha256=h.sha(Q.read_bytes()), prior_queue_sha256=h.sha((E / 'source-queue-before-final-update.json').read_bytes()),
        french_genuinely_unimported=0, norway_after_artwork_id=cursor['after_artwork_id'],
        norway_verified_new_primary_images=8, norway_new_held_objects=4))

registry=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')))
h.save(E / 'source-register-final.json', dict(at=h.now(), original_registry_rows=len(registry),
    original_registry_sha256=h.sha(Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv').read_bytes()),
    researched_sources=[dict(registry_record=r, queue_record=nr if r['source_id']=='nasjonalmuseet_norway' else yr)
                        for r in registry if r['source_id'] in modified], directory_entries_counted_as_artworks=False))
state=h.load(E.parents[1] / 'CHECKPOINT.json'); assert state['inflight']['batch']==277
start=state['inflight']['started_at']; end=h.now()
seconds=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
cmd=subprocess.check_output(['ps','-p',str(state['supervisor_pid']),'-o','command='],text=True).strip()
assert 'continuous-production-research.py run' in cmd
h.save(E / 'supervisor-final-observation.json', dict(at=end,pid=state['supervisor_pid'],command=cmd,
    external_supervisor_live=True,inflight_batch=277,supervisor_modified=False,new_supervisors=0,new_schedules=0,subagents=0,
    continuation_owned_by_existing_supervisor=True))
h.save(E / 'batch-verification-receipt.json', dict(receipt, batch=277,
    french_reserve_previously_delivered_excluded_from_counts=188,
    norwegian_research_checked=12, norwegian_held=4, child_receipt=rel(N / 'batch-verification-receipt.json'),
    child_receipt_sha256=h.sha((N / 'batch-verification-receipt.json').read_bytes())))
manifest=[dict(artwork_id=im['artwork_id'], native_id=selected[im['artwork_id']]['native_id'],
    inventory=selected[im['artwork_id']]['accession_number'], source_url=selected[im['artwork_id']]['source_url'],
    image_sha256=im['sha256'], bytes=im['bytes'], storage_path=im['storage_path'], media_id=im['media_id']) for im in images]
h.save(E / 'verified-delivery-manifest.json', dict(at=end, selection_sha256=pin, rows=manifest, verified_counts=counts))
h.save(E / 'batch-runtime-report.json', dict(at=end,started_at=start,finished_at=end,measured_runtime_seconds=seconds,
    verified_counts=counts,prior_supervisor_totals=state['totals'],
    cumulative_including_current_batch={k:state['totals'][k]+counts[k] for k in counts},
    cumulative_basis='Prior supervisor ledger plus independently verified batch277; not a new whole-catalogue census.',
    hourly_and_milestone_reporting_owned_by_external_supervisor=True,next_task=next_task,
    translation_calls=0,local_catalogue_connections=0,failures_and_uncertainty=failures))
files=[E / name for name in ['required-input-verification.json','inherited-holds-verification.json',
    'production-target-reconciliation.json','batch107-live-reconciliation.json',*ffiles,
    'research-outcomes-verification.json','failures-and-holds.json','source-queue-update-verification.json',
    'source-register-final.json','batch-verification-receipt.json','verified-delivery-manifest.json',
    'batch-runtime-report.json','supervisor-final-observation.json']]
files += [N / name for name in nfiles+['local-recovery-verification.json','independent-prewrite-verification.json']]
cp=dict(at=end,batch=277,stage='independently_verified_complete',outcome='progress',started_at=start,finished_at=end,
    measured_runtime_seconds=seconds,verified_counts=counts,production_ids=ids,
    stage_counts=dict(french_checked=188,french_previously_delivered=188,norway_checked=12,selected=8,prepared=8,imported=8,verified=8,held=4),
    actual_visual_review=dict(derivatives=8,originals=0,contact_sheets=0),
    next_task=next_task,blocker='',external_supervisor_unchanged=True,local_catalogue_connections=0,evidence_paths=[rel(p) for p in files])
temp=E / 'CHECKPOINT.tmp';temp.write_text(json.dumps(cp,ensure_ascii=False,indent=2)+'\n');os.replace(temp,E / 'CHECKPOINT.json')
h.save(R / 'CHECKPOINT.json',cp)
result=dict(outcome='progress',summary='Verified eight authentic primary images for existing Norwegian artworks. All188 French reserve objects were already delivered and are excluded from increments. Four Norwegian holds preserved; production, audit, storage, public delivery and resume checks passed.',next_task=next_task,blocker='',verified_counts=counts,
    evidence_paths=[rel(E / name) for name in ['CHECKPOINT.json','batch-verification-receipt.json','french-reserve-live-reconciliation.json','independent-reserve-source-verification.json','source-queue-update-verification.json','independent-final-artifact-verification.json']]+[rel(N / name) for name in ['independent-production-verification.json','independent-audit-history-verification.json','independent-public-verification.json','independent-storage-verification.json','independent-resume-verification.json']])
h.save(E / 'worker-result.json',result);h.save(R / 'verified-batch-result.json',result)
(E / 'README.md').write_text('# Batch 277\n\nEight existing Norwegian artworks gained authentic primary images; no new painters, artworks, alternate images or holdings. Twelve exact native object pages were researched: eight eligible image gaps delivered, three copyright restrictions and one creation-date conflict held. Source credits and CC BY4.0 labels remain preserved. All eight served JPEGs were individually viewed and fully decoded; originals were technically verified, not separately viewed. Largest derivative: '+str(max(x['bytes'] for x in images))+' bytes.\n\nThe French188 reserve was already fully delivered by the prior campaign. Live active records, primary associations, historical plan citations, original raw/manifest capture checksums and prior visual-decision checksums were reverified. Zero French increments and no repeat writes. Batch107 live postimages match.\n\nIndependent production, audit, source, file, storage and public API/image checks passed. Exact null-to-own-media transitions and persisted selection/source/visual checksums establish attribution. All four held objects remain unchanged. Reconciled replay produced no extra changes. Recovery uses a verified schema archive and affected-row snapshots outside Documents, not a full database export.\n\nOnly Norway, Yale reserve and the corresponding supplementary reserve queue route changed;109 unrelated registry routes preserved. The existing external supervisor remains responsible for continuation and hourly reports. No supervisor, schedule, deployment, Translation call or local catalogue connection was created.\n\nNext: '+next_task+'\n\nMeasured runtime: '+str(round(seconds,1))+' seconds.\n')
assert h.load(E / 'CHECKPOINT.json') == h.load(R / 'CHECKPOINT.json')
assert h.load(E / 'worker-result.json') == h.load(R / 'verified-batch-result.json')
files += [E / name for name in ['CHECKPOINT.json','worker-result.json','README.md']]
h.save(E / 'independent-final-artifact-verification.json',dict(at=h.now(),
    files=[dict(path=rel(p),bytes=p.stat().st_size,sha256=h.sha(p.read_bytes())) for p in files],
    all_verification_files_present=True,runtime_checkpoint_equal=True,runtime_result_equal=True,verified_counts=counts,passed=True))
assert all((b.ROOT / p).exists() for p in result['evidence_paths'])
print(json.dumps(result,ensure_ascii=False))
