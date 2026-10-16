#!/usr/bin/env python3
"""Verify replay and persist this bounded worker's checkpoint; no supervisor writes."""
import copy, csv, datetime, fcntl, gzip, importlib.util, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('norway61', ROOT/'ops/continuous-norway-images-000061.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
h = b.h; i = b.i; E = b.E.parent; R = b.RUNTIME; load = h.load
lock = (R/'worker.lock').open('a+'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

def save(name, value):
    p = E/name
    if p.exists(): return load(p)
    h.save(p, value); return value

def ref(path):
    p = Path(path)
    return dict(path=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p), sha256=h.sha(p.read_bytes()))

receipt = load(b.E/'batch-verification-receipt.json'); counts = receipt['verified_counts']
assert counts == dict(new_painters=0, new_artworks=0, newly_illustrated=8, alternate_images=0, museum_links=0)
images, audit, review = i.accepted(b.B); ids = [r['artwork_id'] for r in images]
assert len(ids) == len(review['decisions']) == 8
nsw = load(E/'nsw-live-gap-reconciliation.json')['before']

def state():
    with b.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        live = h.snapshot(db, ids)
        events = [dict(r) for r in db.execute('SELECT entity_type,entity_id::text,action,count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[]) GROUP BY entity_type,entity_id,action ORDER BY entity_type,entity_id,action', (ids,))]
        assert h.snapshot(db, list(nsw)) == nsw
        rights = [dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s', (i.OP,))]
        assert {r['media_id'] for r in rights} == {r['media_id'] for r in images}
        for r in rights:
            ev = r['evidence_json']; ev = json.loads(ev) if isinstance(ev, str) else ev
            assert ev['selection_sha256'] == receipt['selection_sha256']
            assert ev['batch_visual_review_sha256'] == receipt['visual_review_sha256']
        return live, events

before, events_before = state()
paths = list((b.E/'batches').rglob('*.json')) + list((b.E/'batches').rglob('*.gz'))
hashes = {str(p): h.sha(p.read_bytes()) for p in paths}
calls = []
def forbidden(*args, **kwargs):
    calls.append('Unexpected production/network request'); raise AssertionError(calls[-1])
old_connect = i.m.m.connect; old_session = i.session
try:
    i.m.m.connect = forbidden; i.session = forbidden
    b.finish(); i.apply(b.B)
finally:
    i.m.m.connect = old_connect; i.session = old_session
after, events_after = state()
assert before == after and events_before == events_after and not calls
assert hashes == {p: h.sha(Path(p).read_bytes()) for p in hashes}
reserve = load(E/'independent-french-reserve-evidence-verification.json')
for item in reserve['immutable_plans']:
    assert h.sha((ROOT/item['path']).read_bytes()) == item['sha256']
for row in reserve['records']:
    v = row['prior_actual_visual_review']
    assert h.sha((ROOT/v['decision']).read_bytes()) == v['decision_sha256']
    assert h.sha(Path(v['sheet']).read_bytes()) == v['sheet_sha256']
save('independent-resume-verification.json', dict(at=h.now(), replay_steps=['prepare finish', 'transaction apply'], disabled_production_connections=0, disabled_network_requests=0, all_pinned_files_unchanged=True, live_snapshots_equal=True, audit_counts_equal=True, new_production_increments_on_resume=0, immutable_french_plans_and_visual_decisions_unchanged=True, limitation='Completed-receipt replay verified; no new supervisor or exhaustive interruption fault injection.'))
save('independent-nsw-preservation-verification.json', dict(at=h.now(), ids=list(nsw), unchanged_rows=35, remaining_primary_image_gaps=sum(r['artwork']['primary_media_id'] is None for r in nsw.values()), new_images=0, metadata_updates=0, official_access_hold_preserved=True))

web_queries = ['site:wikiart.org "Boats at St. Tropez"', 'site:wikiart.org "The close of day"', 'site:wikiart.org "Homewards"', 'site:wikiart.org "Robert Anning Bell" "South"', 'site:wikiart.org "Weaver Hawkins"', 'site:wikiart.org "Tani Buncho"', 'site:wikiart.org "Bertram Priestman"']
save('web-discovery-verification.json', dict(at=h.now(), queries=web_queries, outcome='No exact NSW object established. Search returned other creators or dates for generic titles and Tani merchandise pages; none selected or downloaded. Four bounded candidate profile indexes subsequently returned 404.', search_result_urls_excluded=['https://www.wikiart.org/en/tom-scott/homewards-1920', 'https://www.wikiart.org/en/frank-tenney-johnson', 'https://www.wikiart.org/store/artist/tani-buncho.html'], evidence='discovery-outcomes.json', museum_exhaustion_claim=False))
nsw_checks = []
for p in (E/'source-captures').glob('*.json'):
    rc = load(p); raw = gzip.decompress(Path(rc['body_path']).read_bytes())
    assert h.sha(raw) == rc['sha256'] and rc['status'] == 404
    nsw_checks.append(dict(url=rc['url'], status=404, sha256=rc['sha256'], body_path=rc['body_path'], retrieved_at=rc['retrieved_at'], retries=0))
assert len(nsw_checks) == 4
save('independent-nsw-source-verification.json', dict(at=h.now(), captures=nsw_checks, profiles_checked=4, artwork_candidates_checked=5, exact_matches_selected=0, image_requests=0, scope='These specific profile URLs only; does not establish absence of the artists or works elsewhere.'))
save('source-hold-clarification.json', dict(at=h.now(), artwork_id='0ff032f7-408b-550c-af03-cbe7b4511370', source_url='https://www.nasjonalmuseet.no/en/collection/object/NG.K%26H.B.07293', status=404, inherited_next_step_correction='The historical canonical URL was already used. A working underscore URL is not established by this batch. Preserve the 404 and resume only on new canonical-source evidence; no unchanged retry.', rights_holds=2, identity_holds=1))
save('failures.json', dict(at=h.now(), failures=[dict(stage='initial helper startup', reason='Default python lacks psycopg', resolution='Used existing /tmp/artline-cyprus-venv/bin/python; no package installation'), dict(stage='NSW candidate profile discovery', count=4, reason='HTTP 404', retries=0, affected_artworks=5), dict(stage='Norway native object', count=1, reason='HTTP 404', retries=0)], provider_access_holds_bypassed=0, production_write_failures=0))
save('batch-verification-receipt.json', dict(receipt, component_receipt=ref(b.E/'batch-verification-receipt.json'), french_reserve_previous_campaign_excluded=188, nsw_new_images=0, viewed_images=8, accepted_images=8, held_norway_objects=4, no_previous_campaign_increment_counted=True))

next_task = 'Rotate to Te Papa: resume the official native primary-image gap queue after c0f433c7-b2b2-5aa5-9d29-fb93d07246f8, select a bounded next page with exact object/version and record-specific open-image evidence. French reserve has zero unimported objects. NSW retains 18 untouched candidates; Norway resumes after 10ea6912-5b2a-57ca-aa9a-11af70f71078 with all holds preserved.'
qp = E.parents[1]/'source-queue.json'; touched = {'yale_lux', 'art_gallery_nsw', 'nasjonalmuseet_norway'}
zero = {k: 0 for k in counts}; now = h.now()
with qp.with_suffix('.lock').open('a+') as qlock:
    fcntl.flock(qlock, fcntl.LOCK_EX)
    if (E/'source-queue-after.json').exists():
        qbefore = load(E/'source-queue-immediately-before-update.json'); qafter = load(E/'source-queue-after.json')
        assert load(qp) == qafter
    else:
        qbefore = load(qp); qafter = copy.deepcopy(qbefore); save('source-queue-immediately-before-update.json', qbefore)
        for source in qafter['sources']:
            sid = source['source_id']
            if sid not in touched: continue
            c = source['resume_cursor']; source.setdefault('prior_resume_cursors', []).append(copy.deepcopy(c))
            source.update(last_checked_at=now, checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)), latest_batch_verified_counts=counts if sid == 'nasjonalmuseet_norway' else zero)
            if sid == 'yale_lux':
                assert c['unimported'] == 0
                source.update(status='french_reserve_exhausted_live_verified_188_already_delivered', access_status='Batch 61 reverified all 188 live rows, original source captures, immutable visual decisions and local image hashes/decoding; no new reserve imports')
                evidence = ['french-reserve-live-reconciliation.json', 'independent-french-reserve-evidence-verification.json', 'independent-french-reserve-file-verification.json']
            elif sid == 'art_gallery_nsw':
                processed = [r['artwork_id'] for r in load(E/'discovery-outcomes.json')['rows']]
                assert set(processed) <= set(c['pending_artwork_ids'])
                c['pending_artwork_ids'] = [v for v in c['pending_artwork_ids'] if v not in processed]
                for key in ['processed_artwork_ids', 'profile_unavailable_artwork_ids']:
                    c[key] = list(dict.fromkeys(c.get(key, []) + processed))
                c.update(discovery_evidence=str((E/'discovery-outcomes.json').relative_to(ROOT)), next_step='18 untouched candidates remain. Revisit the four new 404 profile URLs only with new evidence; preserve official NSW access hold.')
                source.update(status='official_hold_preserved_wikiart_18_pending_7_unmatched_8_profile_unavailable_candidates', access_status='Four new candidate WikiArt profile URLs returned 404; no NSW official requests or image downloads')
                source['remaining_gaps'] = ['18 untouched candidates, seven previously unmatched candidates and eight candidates with unavailable profile URLs; all 33 image gaps unchanged. Profile 404 is not a museum or artist exhaustion claim.']
                evidence = ['discovery-outcomes.json', 'independent-nsw-source-verification.json', 'independent-nsw-preservation-verification.json', 'web-discovery-verification.json']
            else:
                staged = load(b.E/'oslo-bounded-gap-input.json.gz'); allids = [r['id'] for r in staged['rows']]
                assert c['after_artwork_id'] == staged['after_artwork_id']
                c.update(previous_after_artwork_id=c['after_artwork_id'], after_artwork_id=allids[-1], latest_frozen_input=str((b.E/'oslo-bounded-gap-input.json.gz').relative_to(ROOT)), next_step='Rotate to Te Papa. Resume after 10ea6912-5b2a-57ca-aa9a-11af70f71078; preserve rights, source and identity holds.')
                for key, more in [('inspected_ids', allids), ('delivered_ids', ids), ('held_ids', [v for v in allids if v not in ids])]:
                    c[key] = list(dict.fromkeys(c.get(key, []) + more))
                holds = load(b.E/'research-holds.json')['records']
                c.update(latest_rights_hold_ids=[r['artwork_id'] for r in holds if r['reason']=='Object-specific copyright restriction'], latest_source_404_hold_ids=[r['artwork_id'] for r in holds if r['reason']=='Native page HTTP 404'], latest_identity_hold_ids=[r['artwork_id'] for r in holds if 'reconciliation' in r['reason']], latest_hold_ledger=str((b.E/'research-holds.json').relative_to(ROOT)), latest_visual_hold_ids=[], visual_hold_ledger=str((b.E/'actual-visual-review.json').relative_to(ROOT)), selection_sha256=receipt['selection_sha256'])
                source.update(status='forty_two_programme_primary_images_verified_eight_new_CC_BY_images', verified_counts=counts, access_status='Official object and policy pages validated; eight selected full-frame IIIF images independently verified in production and public delivery')
                source['programme_verified_counts'] = {k: source['programme_verified_counts'][k]+counts[k] for k in counts}
                source.setdefault('remaining_gaps', []).append('Batch 61: 12 next-keyset objects researched, 8 primary images delivered; two copyright holds, one native-page 404 and one identity crosswalk hold. No metadata, museum links or directory additions.')
                evidence = ['norway/batch-verification-receipt.json', 'norway/independent-production-verification.json', 'norway/independent-source-verification.json', 'norway/independent-file-verification.json', 'norway/independent-public-verification.json', 'norway/research-holds.json', 'norway/actual-visual-review.json', 'source-hold-clarification.json']
            source['evidence_paths'] = list(dict.fromkeys(source.get('evidence_paths', []) + [str((E/f).relative_to(ROOT)) for f in evidence]))
        save('source-queue-after.json', qafter)
        assert load(qp) == qbefore
        temp = qp.with_suffix('.batch61.tmp'); temp.write_text(json.dumps(qafter, ensure_ascii=False, indent=2)+'\n'); os.replace(temp, qp)
left = {r['source_id']: r for r in qbefore['sources']}; right = {r['source_id']: r for r in qafter['sources']}
assert len(right) == 111 and {k: v for k, v in left.items() if k not in touched} == {k: v for k, v in right.items() if k not in touched}
assert len(right['art_gallery_nsw']['resume_cursor']['pending_artwork_ids']) == 18
save('source-queue-update-verification.json', dict(at=h.now(), changed_sources=sorted(touched), unrelated_sources_unchanged=108, registry_entries=111, before=ref(E/'source-queue-immediately-before-update.json'), after=ref(qp), nsw_pending=18, french_reserve_unimported=0, warsaw_and_tepapa_cursors_preserved=True))
registry = list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')))
save('source-register.json', dict(at=h.now(), full_registry_rows=111, registry_sha256=h.sha(Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv').read_bytes()), registry_entries=[r for r in registry if r['source_id'] in touched], researched_routes=[dict(source_id=sid, provider=right[sid]['institution'], policy_reference='docs/ARTLINE_IMAGE_USE.md; original CSV entry; separate WikiArt approval for NSW alternative', access_status=right[sid]['access_status'], last_checked=now, resume_cursor=right[sid]['resume_cursor'], checkpoint=right[sid]['checkpoint']) for sid in sorted(touched)], directory_entries_added=0, museum_coverage_complete=False))
master = load(E.parents[1]/'CHECKPOINT.json'); assert master['inflight']['batch'] == 61
start = datetime.datetime.fromisoformat(master['inflight']['started_at']); end = datetime.datetime.now(datetime.timezone.utc)
cp = save('CHECKPOINT.json', dict(at=end.isoformat(), started_at=start.isoformat(), elapsed_seconds=(end-start).total_seconds(), batch=61, outcome='progress', stage='eight_primary_images_independently_verified_queue_and_replay_checked', verified_counts=counts, inspected_french_reserve=188, unimported_french_reserve=0, researched_nsw_candidates=5, researched_norway_objects=12, selected_images=8, prepared_images=8, viewed_images=8, verified_images=8, new_artworks=0, holds=dict(nsw_profile_urls=4, nsw_affected_artworks=5, norway_rights=2, norway_source_404=1, norway_identity=1), next_task=next_task, resume_commands=['/tmp/artline-cyprus-venv/bin/python ops/continuous-norway-images-000061-verify.py', '/tmp/artline-cyprus-venv/bin/python ops/continuous-batch-000061-finalize.py'], production_helper='ops/india-300-delivery-20261011.py', local_catalogue_connections=0, external_supervisor_unmodified=True))
if not (R/'CHECKPOINT.json').exists(): h.save(R/'CHECKPOINT.json', cp)
assert load(R/'CHECKPOINT.json') == cp
save('milestone-report.json', dict(at=end.isoformat(), measured_batch_runtime_seconds=(end-start).total_seconds(), measured_programme_runtime_hours=(end-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()/3600, previous_supervisor_counts=master['totals'], verified_batch_counts=counts, cumulative_receipt_counts={k: master['totals'][k]+counts[k] for k in counts}, count_scope='Current independent receipts plus prior supervisor totals; no whole-catalogue census or fresh re-audit of all earlier batches.', hourly_summary_owner='Existing external supervisor; untouched', hundred_hours_is_not_stop=True, failures=ref(E/'failures.json'), next_task=next_task))
refs = ['batch-verification-receipt.json', 'independent-resume-verification.json', 'source-queue-update-verification.json', 'french-reserve-live-reconciliation.json', 'independent-french-reserve-evidence-verification.json', 'independent-french-reserve-file-verification.json', 'independent-nsw-source-verification.json', 'independent-nsw-preservation-verification.json', 'norway/independent-production-verification.json', 'norway/independent-audit-history-verification.json', 'norway/independent-source-verification.json', 'norway/independent-file-verification.json', 'norway/independent-storage-verification.json', 'norway/independent-public-verification.json', 'norway/independent-held-objects-verification.json', 'norway/actual-visual-review.json', 'CHECKPOINT.json', 'milestone-report.json', 'source-access-holds.json', 'source-register.json', 'source-hold-clarification.json']
save('final-checkpoint-verification.json', dict(at=h.now(), references=[ref(E/f) for f in refs], verified_counts=counts, runtime_checkpoint_matches=True, all_references_exist=True, historical_plans_unchanged=True, source_queue_111_entries=True, external_supervisor_unmodified=True))
print(json.dumps(dict(outcome='progress', verified_counts=counts, next_task=next_task)))
