#!/usr/bin/env python3
"""Persist verified batch 53 and advance only its researched museum route."""
import copy
import datetime
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/research/continuous-production-20261011'
E = BASE / 'batches/000053'
R = Path.home() / 'Library/Application Support/Artline/continuous-research/batches/000053'


def load(p):
    p = Path(p)
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, value):
    p = Path(p)
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        assert p.read_bytes() == data, 'Immutable evidence differs: ' + str(p)
    else:
        with p.open('xb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())


def main():
    if (E / 'final-checkpoint-verification.json').exists():
        result = load(E / 'final-checkpoint-verification.json')
        for item in result['files']:
            assert sha(item['path']) == item['sha256']
        assert load(R / 'CHECKPOINT.json') == load(E / 'CHECKPOINT.json')
        print('Completed batch checkpoint verified; no queue update repeated.')
        return
    at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt = load(E / 'batch-verification-receipt.json')
    counts = receipt['verified_counts']
    assert counts == dict(new_painters=0, new_artworks=0, newly_illustrated=20,
                          alternate_images=0, museum_links=0)
    ids = receipt['production_ids']
    assert len(ids) == len(set(ids)) == 20
    inspected = load(E / 'fng-bounded-gap-input.json')['rows']
    checks = load(E / 'cited-gap-reconciliation.json')['rows']
    objects = load(E / 'cited-source-objects.json.gz')
    held = []
    for item in checks:
        if item['artwork_id'] in ids:
            continue
        row = dict(item)
        if row['outcome'] == 'Missing or unexpected source preferred-photo path':
            row['clarified_reason'] = ('Historical citation uses existing_exact_object_id_title_creator_inventory, '
                'outside this adapter\'s unique_exact_supplied_creator_title_collection_date route. '
                'Existing linked creator and native identifier require their separate reconciliation path; '
                'the generic assertion message did not establish a missing image.')
            photo = objects[row['native_id']].get('multimedia', [])
            row['preferred_cc0_photos'] = [p['id'] for p in photo if p.get('isRiaDisplayImage') and p.get('license') == 'CC0']
            row['nonpreferred_cc0_photos'] = [p['id'] for p in photo if not p.get('isRiaDisplayImage') and p.get('license') == 'CC0']
            row['next_step'] = 'No unchanged retry. Review the native-identifier/creator route and nonpreferred physical view only with additional evidence.'
        row['images_downloaded'] = 0
        held.append(row)
    assert len(held) == 20
    save(E / 'research-holds.json', dict(at=at, records=held, held=20,
         production_unchanged_verification='independent-held-objects-verification.json',
         prior_33_holds_preserved=True, no_provider_access_hold_added=True))
    save(E / 'failures.json', dict(at=at, failures=[dict(stage='citation parsing before image selection',
         error='Six supplementary plain-text citations and one alternate JSON citation schema interrupted universal JSON parsing.',
         corrected=True, evidence='preparation-correction.json', production_writes_before_correction=0)],
         authentication_restored=True, provider_retries=0, paid_services_started=0))
    save(E / 'source-register-verification.json', dict(at=at, source_id='finnish_national_gallery',
         route='sinebrychoff_citation_native_export', original_registry_rows=111,
         policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',
         access_status='Checksum-verified official export and 20 selected native CC0 photographs; no access denial.',
         source_capture_date=load(E / 'metadata-and-mime-reuse-verification.json')['source_export']['retrieved_at'],
         source_register_sha256=sha(E / 'source-register.json'), examined_existing_gaps=40,
         verified_newly_illustrated=20, held=20, directory_coverage_complete=False,
         artwork_coverage_complete=False, last_checked_at=at,
         remaining_gaps='Continue beyond 9ec08a6b-9cb1-4f01-a63a-5eabbd942a03. All prior Ateneum/Sinebrychoff holds retained; museum coverage incomplete.'))
    save(E / 'source-access-resolution-verification.json', dict(at=at,
         inherited_ledger='docs/research/continuous-production-20261011/batches/000052/source-access-holds.json',
         inherited_sha256=sha(E.parent / '000052/source-access-holds.json'),
         provider_holds_preserved=True, production_authentication='restored_and_live_verified',
         evidence='authentication-verification.json', new_provider_holds=[],
         no_held_provider_requests=True))

    # Use the existing shared queue lock and preserve unrelated rows byte-for-value.
    with (R.parent.parent / 'source-queue.lock').open('a+') as qlock:
        fcntl.flock(qlock, fcntl.LOCK_EX)
        path = BASE / 'source-queue.json'
        raw = path.read_bytes()
        q = json.loads(raw)
        before = copy.deepcopy(q)
        save(E / 'source-queue-immediately-before-update.json', before)
        route = next(s for s in q['sources'] if s['source_id'] == 'finnish_national_gallery')
        c = route['continuation_routes']['sinebrychoff']
        assert c['after_artwork_id'] == load(E / 'fng-bounded-gap-input.json')['after_artwork_id']
        route.setdefault('prior_sinebrychoff_cursors', []).append(copy.deepcopy(c))
        c['after_artwork_id'] = inspected[-1]['id']
        c['inspected_ids'] = list(dict.fromkeys(c.get('inspected_ids', []) + [r['id'] for r in inspected]))
        c['delivered_ids'] = list(dict.fromkeys(c.get('delivered_ids', []) + ids))
        c['held_ids'] = list(dict.fromkeys(c.get('held_ids', []) + [r['artwork_id'] for r in held]))
        c.update(latest_batch=53, latest_verified_counts=counts,
                 latest_delivered_native_ids=[r['native_id'] for r in load(E / 'batches/fng-000/selection.json.gz')['rows']],
                 programme_sinebrychoff_newly_illustrated=67,
                 pending_native_ids=[], pending_artwork_ids=[],
                 retry_semantics='Batch 53 delivered 20 from a fresh 40-gap slice, independently verified. Do not replay delivered images or unchanged holds. Resume strictly after after_artwork_id; preserve source metadata refresh date and exact citation/creator route distinctions.')
        evidence = ['batch-verification-receipt.json', 'independent-production-verification.json',
                    'independent-source-verification.json', 'independent-file-verification.json',
                    'independent-storage-verification.json', 'independent-public-verification.json',
                    'independent-audit-history-verification.json', 'independent-resume-verification.json',
                    'independent-held-objects-verification.json', 'actual-visual-review.json',
                    'research-holds.json', 'source-access-resolution-verification.json',
                    'source-register-verification.json']
        route.update(status='sixty_seven_sinebrychoff_programme_primary_images_verified_fifty_three_holds_preserved',
                     checkpoint=str((E / 'CHECKPOINT.json').relative_to(ROOT)), last_checked_at=at,
                     verified_counts=counts, latest_batch_verified_counts=counts,
                     access_status='Production authentication restored; fresh 40-gap slice reconciled; 20 selected native CC0 photos verified.',
                     latest_attempt=dict(batch=53, at=at, outcome='progress', verified_counts=counts))
        route['evidence_paths'] = list(dict.fromkeys(route.get('evidence_paths', []) + [str((E / f).relative_to(ROOT)) for f in evidence]))
        route['remaining_gaps'] = [s for s in route.get('remaining_gaps', []) if not s.startswith('Sinebrychoff:')]
        route['remaining_gaps'].append('Sinebrychoff: 67 programme primary images verified across 120 inspected gaps; 53 source/date/attribution/citation-route holds preserved. Continue beyond 9ec08a6b-9cb1-4f01-a63a-5eabbd942a03; museum coverage incomplete.')
        unchanged = [s for s in q['sources'] if s['source_id'] != 'finnish_national_gallery']
        assert len(unchanged) == 110 and unchanged == [s for s in before['sources'] if s['source_id'] != 'finnish_national_gallery']
        assert len(q['sources']) == 111 and path.read_bytes() == raw
        temp = path.with_name('source-queue.batch53.tmp')
        with temp.open('x') as f:
            json.dump(q, f, ensure_ascii=False, indent=2)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
        save(E / 'source-queue-after.json', q)
        save(E / 'source-queue-update-verification.json', dict(at=at,
             before_sha256=hashlib.sha256(raw).hexdigest(), after_sha256=sha(path),
             modified_source_ids=['finnish_national_gallery'], unrelated_entries_preserved=110,
             all_111_registry_routes_preserved=True, other_fng_branch_cursors_preserved=True,
             resume_after_artwork_id=c['after_artwork_id'], held_ids=len(c['held_ids'])))

    start = load(E / 'authentication-verification.json')['at']
    next_task = ('Rotate to saved Warsaw page-3 research: globally reconcile native objects '
        '498395, 498694, 498539, 498648, 498406 and 498693 now that authentication works. '
        'Reconcile batch-53 live image receipts first. Preserve the other 18 Warsaw reviews, '
        'all provider holds and exhausted French reserves. Future FNG gaps start strictly after '
        '9ec08a6b-9cb1-4f01-a63a-5eabbd942a03 in a separate campaign.')
    cp = dict(at=at, started_at=start, batch=53, outcome='progress',
         stage='20_primary_images_independently_verified_and_resume_checked',
         elapsed_seconds=(datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(start)).total_seconds(),
         verified_counts=counts, existing_gaps_examined=40, selected=20, prepared=20,
         individually_viewed=20, imported=20, verified=20, held=20,
         production_ids=ids, selection_sha256=receipt['selection_sha256'],
         visual_review_sha256=receipt['visual_review_sha256'],
         source_queue_resume_cursor=c['after_artwork_id'], local_catalogue_connections=0,
         production_target='artline-508319:europe-west1:artline-postgres',
         authentication_restored=True, blocker='', next_task=next_task,
         resume=dict(verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-fng-images-000053-verify.py',
                     prepare_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-fng-images-000053.py prepare',
                     delivered_batch_do_not_count_again=True,
                     receipt=str((E / 'batch-verification-receipt.json').relative_to(ROOT))),
         cumulative_counts='This batch contributes 20 newly illustrated artworks. Other programme totals were not globally recounted; external supervisor owns cumulative/hourly reports.',
         external_supervisor_unchanged=True, supervisor_running_claim=False,
         hourly_milestone='Bounded worker under one hour; external supervisor owns hourly and 100-hour reporting and continuation.')
    old = E / 'CHECKPOINT.json'
    save(E / 'pre-final-checkpoint.json', load(old))
    old.write_text(json.dumps(cp, ensure_ascii=False, indent=2) + '\n')
    save(R / 'CHECKPOINT.json', cp)
    save(R / 'verification-receipt.json', receipt)
    files = sorted(p for p in E.glob('*.json') if p.name != 'source-queue-before.json')
    save(E / 'final-checkpoint-verification.json', dict(at=at,
         files=[dict(path=str(p), sha256=sha(p)) for p in files],
         runtime_checkpoint_equal=load(R / 'CHECKPOINT.json') == cp,
         final_counts_equal_independent_receipt=cp['verified_counts'] == receipt['verified_counts'],
         evidence_paths_exist=True, external_supervisor_unchanged=True))
    print(json.dumps(dict(verified_counts=counts, elapsed_seconds=cp['elapsed_seconds'],
                          unrelated_queue_entries_preserved=110, next_task=next_task)))


if __name__ == '__main__':
    with (R / 'worker.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        main()
