#!/usr/bin/env python3
"""Persist batch 75 evidence and update only its researched Athens source route."""
import copy, datetime, fcntl, importlib.util, json, os, sys
from pathlib import Path

s = importlib.util.spec_from_file_location('b75', Path(__file__).with_name('continuous-greek-batch-000075.py'))
b = importlib.util.module_from_spec(s); s.loader.exec_module(b)
h, i = b.h, b.i
if (b.E / 'final-checkpoint-verification.json').exists():
    final = h.load(b.E / 'final-checkpoint-verification.json')
    for item in final['files']:
        assert h.sha((b.ROOT / item['path']).read_bytes()) == item['sha256']
    print('Completed immutable checkpoint verified; no queue changes.')
    sys.exit(0)
receipt = h.load(b.E / 'batch-verification-receipt.json')
replay = h.load(b.E / 'independent-resume-verification.json')
assert replay['unchanged_snapshot'] and not any(replay['replay_increments'].values())
p, pin = h.pinned(b.PHASE)
counts = receipt['verified_counts']
at = h.now()
first = h.load(b.E / 'global-identity-reconciliation.json')['records']
second = h.load(b.E / 'parthenis-global-identity-reconciliation.json')['records']
assert len(first) == 22 and len(second) == 24
assert sum(bool(x['existing']) for x in first + second) == 35
selected = {r['source_id'] for r in p['records']}
review = h.load(b.E / 'editorial-selection-review.json')
with h.connect() as db, db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    heldids = [x['record'].get('artwork_id') or h.uid('artwork/athens/' + x['record']['source_id']) for x in p['held']]
    assert not h.snapshot(db, heldids)
    citations = db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s", (b.FIELD,)).fetchall()
    assert len(citations) == 5 and all(x['pin'] == pin for x in citations)
    for phase in ['greek-objects', 'greek-objects-v2']:
        assert not (b.E / phase / 'applied.json').exists()
b.save('independent-superseded-plan-verification.json', dict(at=at, final_plan_sha256=pin, final_plan_persisted_citations=5, held_proposed_ids_absent=heldids, superseded_plans_never_applied=True))

cursor = dict(
    route='official_parthenis_artist_index_and_exact_inventory_pages',
    artist_index='https://www.nationalgallery.gr/en/artist/parthenis-konstantinos/',
    processed_page=1,
    next_page=2,
    documented_next_request=dict(method='POST', url='https://www.nationalgallery.gr/wp-admin/admin-ajax.php', form=dict(artist_id='91', lang='en', page=2, action='get_artist_artworks'), evidence='parthenis-konstantinos-capture.json', executed=False),
    processed_urls=[x['url'] for x in first + second],
    completed_creator_indexes=['flora-karavia-thaleia', 'laskaridou-sofia'],
    parthenis_source_reported_total=115,
    parthenis_notices_reviewed=24,
    verified_source_ids=sorted(selected),
    verified_artwork_ids=receipt['production_ids'],
    held_versions=review['version_holds'],
    held_date_source_ids=['lamentation-7882'],
    next_step='Rotate to ColBase Japan for regional diversity. Athens can resume documented native page 2 without replaying these 46 notices; resolve five version holds and the open date separately.'
)
next_task = 'Research ColBase Japan through the original registry after checking provider holds; reconcile exact institution/native object IDs and image terms. Preserve Athens page-2 cursor, five Parthenis version holds, one date hold, and all NGV holds.'
b.save('source-access-holds.json', dict(at=at, inherited_ledger='docs/research/continuous-production-20261011/batches/000074/source-access-holds.json', inherited_sha256=h.sha((b.ROOT / 'docs/research/continuous-production-20261011/batches/000074/source-access-holds.json').read_bytes()), selected_route='national_gallery_athens', selected_route_access='Three artist indexes, 46 object pages, terms and five selected image URLs returned HTTP 200', new_access_holds=[], previously_held_creator_urls_unretried=True, version_and_date_holds=review, other_provider_holds_preserved=True))
registry = h.load(b.E / 'required-input-verification.json')['registry_rows']
assert len(registry) == 111
registry_path = Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
b.save('source-register-final.json', dict(at=at, source_id='national_gallery_athens', provider='National Gallery - Alexandros Soutsos Museum', original_registry_path=str(registry_path), original_registry_sha256=h.sha(registry_path.read_bytes()), original_registry_rows=111, registry_entry=next(x for x in registry if x['source_id']=='national_gallery_athens'), policy_reference='docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026', access_status='HTTP 200; no new provider hold', last_checked_at=at, discovered_object_urls=46, selected_objects=5, prepared_images=5, imported_objects=5, verified_objects=5, verified_primary_images=5, existing_objects_excluded=35, version_holds=5, open_date_holds=1, directory_coverage_claimed=False, nationwide_or_complete_institution_coverage_claimed=False, resume_cursor=cursor))
b.save('failures.json', dict(at=at, production_failures=[], source_access_failures=[], local_tool_failures=[dict(action='Parse captured index with system python3', error='bs4 unavailable in system interpreter', resolution='Used established /tmp/artline-cyprus-venv/bin/python; succeeded without additional provider request')]))

essential = ['batch-verification-receipt.json', 'independent-source-verification.json', 'independent-production-verification.json', 'independent-audit-history-verification.json', 'independent-file-verification.json', 'independent-storage-verification.json', 'independent-public-verification.json', 'independent-existing-preservation-verification.json', 'independent-resume-verification.json', 'independent-superseded-plan-verification.json', 'actual-visual-review.json', 'actual-existing-composition-review.json', 'source-register-final.json', 'source-access-holds.json', 'local-recovery-verification.json']
paths = [str((b.E / x).relative_to(b.ROOT)) for x in essential]
queue_path = b.ROOT / 'docs/research/continuous-production-20261011/source-queue.json'
with (b.R / 'source-queue-update.lock').open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    before_bytes = queue_path.read_bytes(); queue = json.loads(before_bytes)
    before = copy.deepcopy(queue); sources = queue['sources']
    assert len(sources) == 111
    row = next(x for x in sources if x['source_id'] == 'national_gallery_athens')
    row.setdefault('prior_resume_cursors', []).append(copy.deepcopy(row['resume_cursor']))
    row.update(status='five_new_parthenis_works_holdings_and_primary_images_verified', last_checked_at=at, access_status='Three artist indexes, 46 exact notices, terms and five selected images HTTP 200', checkpoint=str((b.E / 'CHECKPOINT.json').relative_to(b.ROOT)), resume_cursor=cursor)
    row.setdefault('verified_count_history', []).append(dict(checkpoint=next(x for x in before['sources'] if x['source_id']=='national_gallery_athens').get('checkpoint'), verified_counts=copy.deepcopy(row.get('verified_counts')), scope='Previously recorded batch counts, not cumulative route totals'))
    row['verified_counts'] = counts
    row['latest_batch_verified_counts'] = counts
    row.setdefault('research_history', []).append(dict(batch=75, at=at, evidence_path=str((b.E / 'source-register-final.json').relative_to(b.ROOT)), finding='46 exact object notices reconciled; five new Parthenis inventories and primary images verified; 35 existing objects excluded; five versions and one date held.'))
    row['evidence_paths'] = list(dict.fromkeys(row.get('evidence_paths', []) + paths + [str((b.E / 'CHECKPOINT.json').relative_to(b.ROOT))]))
    old_other = {x['source_id']:x for x in before['sources'] if x['source_id'] != 'national_gallery_athens'}
    new_other = {x['source_id']:x for x in sources if x['source_id'] != 'national_gallery_athens'}
    assert old_other == new_other and len(new_other) == 110
    part = queue_path.with_name('source-queue.batch-000075.tmp')
    part.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + '\n')
    assert queue_path.read_bytes() == before_bytes
    os.replace(part, queue_path)
    actual = json.loads(queue_path.read_bytes())
    assert {x['source_id']:x for x in actual['sources'] if x['source_id'] != 'national_gallery_athens'} == old_other
b.save('source-queue-update-verification.json', dict(at=at, before_sha256=h.sha(before_bytes), after_sha256=h.sha(queue_path.read_bytes()), entries=111, changed_source_ids=['national_gallery_athens'], unrelated_entries_preserved=110, prior_athens_cursor_preserved=True))

start = h.load(b.E / 'batch-start.json')['at']
elapsed = (datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(start)).total_seconds()
checkpoint = dict(at=at, batch=75, stage='independently_verified_complete', outcome='progress', started_at=start, elapsed_seconds=elapsed, verified_counts=counts, discovered_objects=46, selected_objects=5, prepared_images=5, imported_objects=5, verified_objects=5, verified_primary_images=5, existing_objects_excluded=35, version_holds=5, date_holds=1, production_ids=receipt['production_ids'], metadata_plan_sha256=pin, image_selection_sha256=receipt['image_selection_sha256'], resume_cursor=cursor, next_task=next_task, resume_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-greek-000075-resume.py', verify_command='/tmp/artline-cyprus-venv/bin/python ops/continuous-greek-000075-verify.py', evidence_paths=paths, external_supervisor_unchanged=True, no_local_catalogue_connections=True)
b.save('CHECKPOINT.json', checkpoint); h.save(b.R / 'CHECKPOINT.json', checkpoint)
parent = h.load(b.ROOT / 'docs/research/continuous-production-20261011/CHECKPOINT.json')
assert parent['next_batch'] == 75
runtime = (datetime.datetime.fromisoformat(at)-datetime.datetime.fromisoformat(parent['started_at'])).total_seconds()
b.save('milestone-report.json', dict(at=at, batch=75, batch_elapsed_seconds=elapsed, programme_measured_elapsed_seconds=runtime, prior_supervisor_verified_totals=parent['totals'], batch_verified_increments=counts, reconciled_programme_totals_including_this_batch={k:parent['totals'][k]+counts[k] for k in counts}, totals_scope='Programme-attributed receipts only; not whole-catalogue live totals. Supervisor retains ownership of cumulative state and scheduling.', next_task=next_task, continue_after_100_hours=True))
(b.E / 'README.md').write_text('''# Batch 75: National Gallery, Athens

Verified five new review paintings by the existing Konstantinos Parthenis artist,
five primary images and five documented holdings. No new painters or alternate
images. All five original museum inventories and source labels are retained.

The batch researched 46 object notices: all 22 Flora-Karavia/Laskaridou entries
and 13 of the first 24 Parthenis entries already existed. Five Parthenis title or
version candidates and one open date remain held. The next native Parthenis
request is saved as page 2, artist 91, in CHECKPOINT.json. Institution and national
coverage remain incomplete. The next proposed source is ColBase Japan.

Every delivered derivative was individually viewed, fully decoded, hashed and
verified below 100,000 bytes in storage and public delivery. Originals remain
outside Documents. Thirty-nine existing Parthenis compositions were viewed in
three contact sheets; seventeen unillustrated records were not visually viewed.
Actual museum rights remain restricted, with the Greek source approval recorded
separately from copyright-holder permission.

Production attribution is established by empty locked metadata preimages,
persisted plan/source checksums, insertion audits, null image preimages and
matching rights-plan checksums. Replaying delivery changed no rows, audit counts
or storage generations. Superseded plans were not applied. Source queue changes
are limited to Athens; all other 110 entries remain equal. The real local
catalogue and external supervisor configuration were not changed.

See batch-verification-receipt.json, independent-production-verification.json,
independent-public-verification.json, independent-resume-verification.json and
final-checkpoint-verification.json for verified evidence. Exact run duration and
programme receipt totals are in milestone-report.json. Local recovery schema,
plans and affected-row snapshots are referenced by local-recovery-verification.json.
''')
manifest = []
for name in essential + ['source-queue-update-verification.json', 'CHECKPOINT.json', 'milestone-report.json', 'README.md']:
    path = b.E / name; manifest.append(dict(path=str(path.relative_to(b.ROOT)), sha256=h.sha(path.read_bytes()), bytes=path.stat().st_size))
for path in sorted((b.ROOT / 'ops').glob('*000075*.py')):
    manifest.append(dict(path=str(path.relative_to(b.ROOT)), sha256=h.sha(path.read_bytes()), bytes=path.stat().st_size))
b.save('final-checkpoint-verification.json', dict(at=h.now(), files=manifest, evidence_files_exist=True, runtime_checkpoint_equal=h.load(b.R/'CHECKPOINT.json')==checkpoint, verified_counts=counts, source_queue_other_110_unchanged=True, supervisor_configuration_unchanged=True))
print(json.dumps(dict(verified_counts=counts, elapsed_seconds=elapsed, unrelated_source_entries_preserved=110)))
