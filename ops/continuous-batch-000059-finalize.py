#!/usr/bin/env python3
"""Persist one verified batch and update only the two researched source routes."""
import collections, copy, csv, datetime, fcntl, importlib.util, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('getty59', ROOT/'ops/continuous-getty-images-000059.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
h = w.h; E = w.E.parent; R = w.RUNTIME; load = w.load
lock = (R/'worker.lock').open('a+'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
def save(name, value): return w.save(E/name, value)
def ref(p):
    p = Path(p)
    return dict(path=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p), sha256=h.sha(p.read_bytes()))

receipt = load(w.E/'batch-verification-receipt.json'); counts = receipt['verified_counts']
assert counts == dict(new_painters=0, new_artworks=0, newly_illustrated=16, alternate_images=0, museum_links=0)
images, audit, review = w.i.accepted(w.B); ids = receipt['production_ids']
assert len(images) == len(ids) == review['individually_viewed'] == 16
replay = load(w.E/'independent-resume-verification.json')
assert replay['unchanged_snapshot'] and not any(replay['replay_increments'].values())
smk = load(E/'independent-smk-source-verification.json')
assert smk['checked'] == 80 and smk['metadata_captures'] == 78 and smk['selected_images'] == 0
with w.connect() as db:
    live = h.snapshot(db, ids)
    assert live == load(w.E/'independent-production-verification.json')['after']
    rights = [dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s', (w.i.OP,))]
    assert len(rights) == 16 and {r['media_id'] for r in rights} == {im['media_id'] for im in images}
    for r in rights:
        ev = r['evidence_json']; ev = json.loads(ev) if isinstance(ev, str) else ev
        assert ev['selection_sha256'] == receipt['selection_sha256'] and ev['batch_visual_review_sha256'] == receipt['visual_review_sha256']
save('batch-verification-receipt.json', dict(receipt, component_receipt=ref(w.E/'batch-verification-receipt.json'), inspected_existing_gaps=96, selected=16, prepared=16, individually_viewed=16, imported=16, independently_verified=16, smk_increments=0, prior_batch_increments_excluded=8, no_new_artworks_or_museum_connections=True))

now = h.now(); zero = {k: 0 for k in counts}
next_task = 'Resume the 23 saved NSW WikiArt image gaps in source-queue.json, beginning with 0113ff70-900b-576b-8412-27c91494b99a and 0194e1fd-4e9c-52c2-897c-bef9454acc46. Reconcile live primary images before selection; preserve the official NSW access hold and all previously unmatched/profile-unavailable cases. Warsaw icon page 4 remains available for the priority metadata route. French reserves are exhausted.'
qp = E.parent.parent/'source-queue.json'; touched = {'smk_denmark', 'getty_museum'}
with qp.with_suffix('.lock').open('a+') as qlock:
    fcntl.flock(qlock, fcntl.LOCK_EX)
    if (E/'source-queue-after.json').exists():
        before = load(E/'source-queue-immediately-before-update.json'); after = load(E/'source-queue-after.json')
        current = {r['source_id']: r for r in load(qp)['sources']}
        assert all(current[r['source_id']] == r for r in after['sources'] if r['source_id'] in touched)
    else:
        before = load(qp); after = copy.deepcopy(before); save('source-queue-immediately-before-update.json', before)
        assert len(after['sources']) == 111
        for source in after['sources']:
            sid = source['source_id']
            if sid not in touched: continue
            source.setdefault('prior_resume_cursors', []).append(copy.deepcopy(source['resume_cursor']))
            source.update(last_checked_at=now, checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)), latest_batch_verified_counts=counts if sid == 'getty_museum' else zero)
            if sid == 'smk_denmark':
                cursor = source['resume_cursor']; assert cursor['after_artwork_id'] == '02a1f9c0-64e2-4257-bdba-581286514593'
                cursor.update(previous_after_artwork_id=cursor['after_artwork_id'], after_artwork_id=smk['next_cursor'], checked=cursor['checked']+80, latest_checked=80, selected=0, hold_ledger=str((E/'independent-smk-source-verification.json').relative_to(ROOT)), next_step='Rotate sources. On future return, start after the new UUID; do not repeat the 160 unchanged reviewed gaps or relax object-image rights.')
                source.update(status='160_primary_image_gaps_checked_no_eligible_native_public_domain_images', access_status='78 current native object API captures HTTP 200; two creator holds unrequested; zero images downloaded', policy_reference='Original 111-source CSV smk_denmark; docs/ARTLINE_IMAGE_USE.md#general-image-use-policy')
                source['latest_remaining_gaps'] = smk['reason_counts']
                source['remaining_gaps'] = dict(collections.Counter(source['remaining_gaps']) + collections.Counter(smk['reason_counts']))
                evidence = ['independent-smk-source-verification.json', 'bounded-gap-input.json', 'gap-reconciliation.json', 'source-access-holds.json']
            else:
                cursor = source['resume_cursor']['painting_image_gaps']; assert cursor['after_artwork_id'] == 'ea1f74c8-1d54-5aba-94bf-1826c31214d2'
                staged = load(w.E/'bounded-gap-input.json.gz'); checked = [r['id'] for r in staged['rows']]
                assert len(checked) == 16 and set(checked) == set(ids)
                cursor.update(previous_after_artwork_id=cursor['after_artwork_id'], after_artwork_id=checked[-1], selection_sha256=receipt['selection_sha256'], latest_selection_path=str((w.i.folder(w.B)/'selection.json.gz').relative_to(ROOT)), latest_verified_batch=59, next_step='Rotate to NSW WikiArt gaps. Getty painting route resumes after '+checked[-1]+'; prior image and manuscript holds remain unchanged.')
                for key, more in [('inspected_ids', checked), ('delivered_ids', ids)]: cursor[key] = list(dict.fromkeys(cursor[key]+more))
                source['programme_verified_counts'] = {k: source['programme_verified_counts'][k]+counts[k] for k in counts}
                source.update(status='thirty_four_existing_painting_gaps_illustrated_previous_image_holds_preserved', verified_counts=counts, access_status='16 exact native painting, Linked Art and digital-media records verified; 16 selected CC0 primary reproductions delivered HTTP 200')
                source['remaining_gaps'].append('Batch 59: next 16 existing painting gaps all verified. Later UUID pages and museum-wide coverage remain incomplete; prior two painting-image holds and three manuscript-view holds unchanged.')
                evidence = ['getty/batch-verification-receipt.json', 'getty/independent-production-verification.json', 'getty/independent-source-verification.json', 'getty/independent-file-verification.json', 'getty/independent-public-verification.json', 'getty/actual-visual-review.json', 'getty/independent-resume-verification.json']
            source.setdefault('research_history', []).append(dict(at=now, batch=59, verified_counts=counts if sid == 'getty_museum' else zero, evidence=str((E/evidence[0]).relative_to(ROOT))))
            source['evidence_paths'] = list(dict.fromkeys(source['evidence_paths']+[str((E/f).relative_to(ROOT)) for f in evidence]))
        save('source-queue-after.json', after)
        assert load(qp) == before, 'Concurrent queue change; do not overwrite'
        temp = qp.with_suffix('.batch59.tmp'); temp.write_text(json.dumps(after, ensure_ascii=False, indent=2)+'\n'); os.replace(temp, qp)
left = {x['source_id']: x for x in before['sources']}; right = {x['source_id']: x for x in after['sources']}
assert {k:v for k,v in left.items() if k not in touched} == {k:v for k,v in right.items() if k not in touched}
assert left['getty_museum']['resume_cursor']['next_offset'] == right['getty_museum']['resume_cursor']['next_offset'] == 100
assert left['getty_museum']['resume_cursor']['painting_image_gaps']['held_ids'] == right['getty_museum']['resume_cursor']['painting_image_gaps']['held_ids']
save('independent-queue-verification.json', dict(at=h.now(), changed_sources=sorted(touched), unrelated_entries_preserved=109, source_count=111, before=ref(E/'source-queue-immediately-before-update.json'), after=ref(E/'source-queue-after.json'), historical_holds_preserved=True, getty_byzantine_discovery_cursor_unchanged=True))
registry_path = Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'); registry = list(csv.DictReader(registry_path.open())); assert len(registry) == 111
save('source-register-final.json', dict(at=h.now(), original_registry=ref(registry_path), complete_registry_records=111, sources=[dict(registry=next(r for r in registry if r['source_id']==sid), programme_state=right[sid]) for sid in sorted(touched)], metadata_coverage_is_not_artwork_coverage=True, directory_additions=0))

master = load(E.parent.parent/'CHECKPOINT.json'); assert master['inflight']['batch'] == 59
start = datetime.datetime.fromisoformat(master['inflight']['started_at']); end = datetime.datetime.now(datetime.timezone.utc)
cp = save('CHECKPOINT.json', dict(at=end.isoformat(), started_at=start.isoformat(), elapsed_seconds=(end-start).total_seconds(), batch=59, outcome='progress', stage='sixteen_primary_images_independently_verified_replay_and_queue_verified', verified_counts=counts, researched_existing_image_gaps=96, selected_images=16, prepared_images=16, viewed_images=16, imported_images=16, verified_images=16, new_metadata_records=0, smk_holds=80, next_task=next_task, resume_commands=['/tmp/artline-cyprus-venv/bin/python ops/continuous-getty-000059-verify.py verify', '/tmp/artline-cyprus-venv/bin/python ops/continuous-getty-000059-verify.py replay', '/tmp/artline-cyprus-venv/bin/python ops/continuous-batch-000059-finalize.py'], local_catalogue_connections=0, external_supervisor_unmodified=True))
w.save(R/'CHECKPOINT.json', cp); assert load(R/'CHECKPOINT.json') == cp
save('milestone-report.json', dict(at=end.isoformat(), measured_batch_runtime_seconds=(end-start).total_seconds(), measured_programme_runtime_hours=(end-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()/3600, previous_supervisor_counts=master['totals'], verified_batch_counts=counts, cumulative_receipt_counts={k:master['totals'][k]+counts[k] for k in counts}, count_scope='Sixteen independently verified current increments plus persisted supervisor totals; no whole-catalogue census or re-audit of earlier campaign totals.', hourly_summary_owner='Existing external supervisor; unmodified', hundred_hours_is_not_stop=True, next_task=next_task, failures=ref(E/'failures.json')))
refs = ['batch-verification-receipt.json', 'independent-queue-verification.json', 'independent-smk-source-verification.json', 'prior-batch-live-reconciliation.json', 'getty/independent-production-verification.json', 'getty/independent-source-verification.json', 'getty/independent-file-verification.json', 'getty/independent-audit-history-verification.json', 'getty/independent-storage-verification.json', 'getty/independent-public-verification.json', 'getty/independent-held-objects-verification.json', 'getty/actual-visual-review.json', 'getty/independent-resume-verification.json', 'getty/independent-campaign-stop-verification.json', 'CHECKPOINT.json', 'milestone-report.json', 'source-access-holds.json', 'source-register-final.json']
save('final-checkpoint-verification.json', dict(at=h.now(), references=[ref(E/x) for x in refs], verified_counts=counts, runtime_checkpoint_matches=True, all_references_exist=True, source_queue_111_entries=True, external_supervisor_unmodified=True))
print(json.dumps(dict(outcome='progress', verified_counts=counts, next_task=next_task)))
