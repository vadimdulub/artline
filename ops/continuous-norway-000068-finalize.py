#!/usr/bin/env python3
"""Read-only replay verification and durable batch-68 handoff; no supervisor edits."""
import copy, csv, datetime, fcntl, importlib.util, json, os
from pathlib import Path

spec = importlib.util.spec_from_file_location('batch68', Path(__file__).with_name('continuous-norway-images-000068.py'))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
h = b.h; i = b.i; E = b.E.parent; R = b.RUNTIME; load = b.load

def save(name, value): return b.save(E/name, value)
def rel(p): return str(Path(p).relative_to(b.ROOT))
def ref(p):
    p = Path(p)
    return dict(path=rel(p) if p.is_relative_to(b.ROOT) else str(p), sha256=h.sha(p.read_bytes()), bytes=p.stat().st_size)

def main():
    receipt = load(b.E/'batch-verification-receipt.json'); counts = receipt['verified_counts']
    assert counts == dict(new_painters=0, new_artworks=0, newly_illustrated=8, alternate_images=0, museum_links=0)
    images, audit, review = i.accepted(b.B); ids = receipt['production_ids']
    staged = load(b.E/'oslo-bounded-gap-input.json.gz'); allids = [r['id'] for r in staged['rows']]
    holds = load(b.E/'research-holds.json')['records']
    assert len(images) == len(ids) == len(review['decisions']) == 8
    assert all(r['viewed_individually'] for r in review['decisions'])
    assert len(allids) == 12 and len(holds) == 4

    def state():
        with b.connect() as db:
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            snapshots = h.snapshot(db, allids)
            events = [dict(r) for r in db.execute('SELECT entity_type,entity_id::text,action,count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[]) GROUP BY entity_type,entity_id,action ORDER BY entity_type,entity_id,action', (ids,))]
            rights = [dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s', (i.OP,))]
            assert {r['media_id'] for r in rights} == {im['media_id'] for im in images}
            for r in rights:
                ev = json.loads(r['evidence_json']) if isinstance(r['evidence_json'], str) else r['evidence_json']
                assert ev['selection_sha256'] == receipt['selection_sha256']
                assert ev['batch_visual_review_sha256'] == receipt['visual_review_sha256']
            verified = load(b.E/'independent-production-verification.json')['after']
            assert all(snapshots[aid] == verified[aid] for aid in ids)
            assert all(snapshots[aid] == staged['states'][aid] for aid in set(allids)-set(ids))
            return snapshots, events, rights

    before = state()
    artifacts = [p for p in (b.E/'batches').rglob('*') if p.is_file()]
    hashes = {str(p): h.sha(p.read_bytes()) for p in artifacts}
    calls = []
    def forbidden(*args, **kwargs):
        calls.append('Unexpected network or database request during completed-receipt replay')
        raise AssertionError(calls[-1])
    old_connect, old_session = i.m.m.connect, i.session
    try:
        i.m.m.connect = forbidden; i.session = forbidden
        b.finish(); i.apply(b.B)
    finally:
        i.m.m.connect = old_connect; i.session = old_session
    after = state()
    assert before == after and not calls
    assert hashes == {p: h.sha(Path(p).read_bytes()) for p in hashes}
    stops = load(E/'completed-campaign-stop-preservation.json')
    for r in stops['files']: assert h.sha(Path(r['path']).read_bytes()) == r['sha256']
    save('independent-resume-verification.json', dict(at=h.now(), steps=['prepare finish', 'transaction apply'], unchanged_snapshot=True, unchanged_audit_counts=True, unchanged_rights_evidence=True, pinned_files_unchanged=True, unexpected_requests=0, replay_increments={k: 0 for k in counts}, completed_campaign_stops_unchanged=True, separate_campaign=i.OP, limitation='Completed-receipt replay verified; external supervisor was not changed or restarted.'))
    save('independent-final-production-reconciliation.json', dict(at=h.now(), production_ids=ids, operation_rights_rows=8, selection_sha256=receipt['selection_sha256'], visual_review_sha256=receipt['visual_review_sha256'], live_snapshot_matches=True, prior_delivery_counts_excluded=True, held_objects_unchanged=4))
    save('batch-verification-receipt.json', dict(receipt, detailed_receipt=ref(b.E/'batch-verification-receipt.json')))

    at = h.now()
    next_task = 'Rotate to the undercovered National Gallery of Iceland registry route: audit existing primary-image gaps and exact native reuse evidence, with approved WikiArt alternatives where justified. If no eligible objects, resume the saved Ateneum native export after UUID 034cfdbc-08ad-4973-8e7d-1c565d5c2ea9. Norway resumes after 1254dc72-2c88-5258-b4ee-64a17d686797; retain its four new holds. French reserves are exhausted.'
    qp = E.parents[1]/'source-queue.json'; sid = 'nasjonalmuseet_norway'
    with qp.with_suffix('.lock').open('a+') as qlock:
        fcntl.flock(qlock, fcntl.LOCK_EX)
        if (E/'source-queue-after.json').exists():
            qbefore = load(E/'source-queue-immediately-before-update.json'); qafter = load(E/'source-queue-after.json')
            current = next(r for r in load(qp)['sources'] if r['source_id'] == sid)
            assert current == next(r for r in qafter['sources'] if r['source_id'] == sid)
        else:
            qbefore = load(qp); qafter = copy.deepcopy(qbefore)
            save('source-queue-immediately-before-update.json', qbefore)
            route = next(r for r in qafter['sources'] if r['source_id'] == sid)
            original = next(r for r in load(E/'source-queue-before.json')['sources'] if r['source_id'] == sid)
            assert route == original, 'Researched source changed concurrently; reconcile before queue update'
            old = copy.deepcopy(route['resume_cursor']); route.setdefault('prior_resume_cursors', []).append(old)
            c = route['resume_cursor']; assert c['after_artwork_id'] == staged['after_artwork_id']
            c.update(previous_after_artwork_id=c['after_artwork_id'], after_artwork_id=allids[-1], latest_frozen_input=rel(b.E/'oslo-bounded-gap-input.json.gz'), selection_sha256=receipt['selection_sha256'], latest_verified_batch=68, latest_hold_ledger=rel(b.E/'research-holds.json'), visual_hold_ledger=rel(b.E/'actual-visual-review.json'), latest_visual_hold_ids=[], no_repeat_of_unchanged_holds=True, next_step=next_task)
            for key, more in [('inspected_ids', allids), ('delivered_ids', ids), ('held_ids', [r['artwork_id'] for r in holds])]:
                c[key] = list(dict.fromkeys(c.get(key, []) + more))
            c.update(latest_rights_hold_ids=[r['artwork_id'] for r in holds if r['reason'] == 'Object-specific copyright restriction'], latest_source_404_hold_ids=[r['artwork_id'] for r in holds if r['reason'] == 'Native page HTTP 404'], latest_identity_hold_ids=[])
            route['programme_verified_counts'] = {k: route['programme_verified_counts'][k]+counts[k] for k in counts}
            route.update(last_checked_at=at, checkpoint=rel(E/'CHECKPOINT.json'), status='fifty_programme_primary_images_verified_eight_new_CC_BY_images', verified_counts=counts, latest_batch_verified_counts=counts, policy_reference='Original GLOBAL_MUSEUM_SOURCE_REGISTRY.csv nasjonalmuseet_norway; docs/ARTLINE_IMAGE_USE.md#general-image-use-policy; current official CC BY photo policy', access_status='12 exact native object routes researched: 11 HTTP 200, one HTTP 404; 8 selected native photos verified in production and public delivery. No host access denial.')
            route.setdefault('remaining_gaps', []).append('Batch 68: eight existing gaps illustrated; three object copyright labels and one canonical-page 404 held unchanged. Museum-wide coverage remains incomplete. No directory or metadata additions.')
            route.setdefault('research_history', []).append(dict(batch=68, at=at, researched=12, selected=8, prepared=8, individually_viewed=8, verified_counts=counts, evidence=rel(E/'batch-verification-receipt.json')))
            refs = ['batch-verification-receipt.json', 'norway/independent-production-verification.json', 'norway/independent-source-verification.json', 'norway/independent-file-verification.json', 'norway/independent-public-verification.json', 'norway/research-holds.json', 'norway/actual-visual-review.json', 'independent-resume-verification.json', 'source-access-hold-reconciliation.json']
            route['evidence_paths'] = list(dict.fromkeys(route.get('evidence_paths', []) + [rel(E/f) for f in refs]))
            save('source-queue-after.json', qafter); assert load(qp) == qbefore
            temp = qp.with_suffix('.batch68.tmp'); temp.write_text(json.dumps(qafter, ensure_ascii=False, indent=2)+'\n'); os.replace(temp, qp)
    left = {r['source_id']: r for r in qbefore['sources']}; right = {r['source_id']: r for r in qafter['sources']}
    assert len(left) == len(right) == 111
    assert {k: v for k, v in left.items() if k != sid} == {k: v for k, v in right.items() if k != sid}
    assert set(left[sid]['resume_cursor']['held_ids']) <= set(right[sid]['resume_cursor']['held_ids'])
    save('independent-queue-verification.json', dict(at=h.now(), modified_source_ids=[sid], unrelated_entries_preserved=110, all_111_registry_routes_preserved=True, prior_object_and_provider_holds_preserved=True, before=ref(E/'source-queue-immediately-before-update.json'), after=ref(E/'source-queue-after.json'), after_artwork_id=allids[-1]))
    registry_path = Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
    registry = list(csv.DictReader(registry_path.open()))
    save('source-register-final.json', dict(at=at, registry_path=str(registry_path), registry_sha256=h.sha(registry_path.read_bytes()), registry_records=111, researched_source=dict(registry=next(r for r in registry if r['source_id'] == sid), programme_state=right[sid]), directory_additions=0, directory_coverage_complete=False, artwork_coverage_complete=False))
    prev = E.parent/'000067/source-access-holds.json'
    save('source-access-holds.json', dict(at=at, inherited_ledger=rel(prev), inherited_sha256=h.sha(prev.read_bytes()), provider_holds_preserved=True, held_provider_requests=0, new_provider_access_holds=0, new_object_holds=ref(b.E/'research-holds.json'), active_route_host_reconciliation=ref(E/'source-access-hold-reconciliation.json')))
    master = load(E.parents[1]/'CHECKPOINT.json'); assert master['inflight']['batch'] == 68
    start = datetime.datetime.fromisoformat(master['inflight']['started_at']); end = datetime.datetime.now(datetime.timezone.utc)
    cp = save('CHECKPOINT.json', dict(at=end.isoformat(), started_at=start.isoformat(), elapsed_seconds=(end-start).total_seconds(), batch=68, stage='independently_verified_complete', outcome='progress', verified_counts=counts, researched=12, selected=8, prepared=8, individually_viewed=8, imported=8, verified=8, production_ids=ids, selection_sha256=receipt['selection_sha256'], visual_review_sha256=receipt['visual_review_sha256'], holds=dict(object_copyright=3, canonical_page_404=1), next_task=next_task, blocker='', resume_commands=['/tmp/artline-cyprus-venv/bin/python ops/continuous-norway-images-000068-verify.py', '/tmp/artline-cyprus-venv/bin/python ops/continuous-norway-000068-finalize.py'], local_catalogue_connections=0, external_supervisor_unmodified=True, supervisor_running_claim=False, reporting='Existing external supervisor owns continuation and hourly reports; one bounded worker batch completed.', limitations=['Scoped recovery contains full schema and exact affected rows, not a full database backup.', 'Eight prepared images individually viewed; originals decoded and hashed but not separately viewed.', 'No museum-wide coverage claim.']))
    b.save(R/'CHECKPOINT.json', cp); assert load(R/'CHECKPOINT.json') == cp
    save('milestone-report.json', dict(at=cp['at'], measured_batch_runtime_seconds=cp['elapsed_seconds'], measured_programme_runtime_hours=(datetime.datetime.fromisoformat(cp['at'])-datetime.datetime.fromisoformat(master['started_at'])).total_seconds()/3600, previous_supervisor_counts=master['totals'], verified_batch_counts=counts, cumulative_receipt_counts={k: master['totals'][k]+counts[k] for k in counts}, count_scope='Current batch independently verified; earlier supervisor totals retained, not recounted as current delivery. No whole-catalogue census.', hourly_summary_owner='Existing external supervisor; unmodified', hundred_hours_is_not_stop=True, failures=ref(E/'failures.json'), next_task=next_task))
    refs = ['batch-verification-receipt.json', 'independent-resume-verification.json', 'independent-queue-verification.json', 'independent-final-production-reconciliation.json', 'prior-write-reconciliation.json', 'norway/independent-production-verification.json', 'norway/independent-source-verification.json', 'norway/independent-file-verification.json', 'norway/independent-storage-verification.json', 'norway/independent-public-verification.json', 'norway/independent-audit-history-verification.json', 'norway/independent-held-objects-verification.json', 'norway/actual-visual-review.json', 'norway/local-recovery-verification.json', 'norway/research-holds.json', 'source-register-final.json', 'source-access-holds.json', 'CHECKPOINT.json', 'milestone-report.json']
    save('independent-final-handoff-verification.json', dict(at=h.now(), verified_counts=counts, references=[ref(E/f) for f in refs], all_references_exist=True, runtime_checkpoint_matches=True, source_count=111, unrelated_routes_preserved=110, completed_campaign_stops_unchanged=True, local_catalogue_connections=0, external_supervisor_unmodified=True))
    print(json.dumps(dict(outcome='progress', verified_counts=counts, next_task=next_task)))

if __name__ == '__main__':
    with (R/'worker.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); main()
