"""Validate source integrity and preserve wave 114 research without claiming writes."""
import ast
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('review', Path(__file__).with_name('museum-expansion-kilkis-review-20261010.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
m, RUN, PROOF = r.m, r.RUN, r.PROOF


def checked(pin):
    p = Path(pin['path'])
    if not p.is_absolute():
        p = m.ROOT / p
    assert p.is_file(), str(p)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == pin['sha256'], str(p)


def main():
    previous = m.RUN / 'native/kazantzakis-more-20261009/research-checkpoint-001.json'
    assert r.ref(previous)['sha256'] == '69cf8a71a80abe2efd3e9d94cf6da1cd2d723225aa6ebbe19313a7a5c83178ff'
    prior = m.load(previous)
    for pin in prior['artifacts'] + prior['external_artifacts']:
        checked(pin)
    last_production = m.ROOT / prior['last_successful_production_checkpoint']['path']
    checked(prior['last_successful_production_checkpoint'])
    prod = m.load(last_production)
    assert r.ref(last_production)['sha256'] == '21973a04eb7411fec1875f49baa8f0ac9f426e5de3effd5da24ca028b22b891a'

    native = m.load(r.OLD / 'candidate-facts-001.json.gz')['rows'] + m.load(RUN / 'decorative-candidate-facts-001.json.gz')['rows']
    decisions = m.load(RUN / 'editorial-decisions-001.json.gz')['rows']
    native_decisions = {v['source_id']: v for v in decisions if v.get('source_id')}
    receipts = {}
    for row in native:
        result = native_decisions[row['source_id']]
        for key in ['inventory_literal', 'title', 'creator_label', 'date_display', 'first', 'last', 'native_description', 'native_fields', 'aggregator_literal', 'aggregator_enrichment']:
            assert result[key] == row[key], (row['source_id'], key)
        for key in ['source_receipt', 'native_receipt']:
            receipt = row[key]
            assert receipt['status'] == 200
            raw = gzip.decompress((m.ROOT / receipt['body_path']).read_bytes())
            assert len(raw) == receipt['bytes']
            assert hashlib.sha256(raw).hexdigest() == receipt['sha256']
            receipts[receipt['body_path']] = receipt
    assert len(receipts) == 58
    assert len(decisions) == len({v['lead_key'] for v in decisions}) == 32
    assert all(not v['ready_to_apply'] and not v['new_production_record'] and not v['current_display_verified'] for v in decisions)
    assert all(v['first'] is None and v['last'] is None and v['creator_label'] is None for v in decisions)
    assert all(v['proposed_status'] == 'review' for v in decisions)
    assert {v['number'] for v in decisions if v['decision'] == 'hold'} == {6, 10, 13, 14, 15, 'book-05'}
    assert sum(v['decision'] == 'candidate_pending_live_identity' for v in decisions) == 26
    book = m.load(RUN / 'publication-object-review-001.json')
    assert len(book['entries']) == 5 and sum(v['complete_entry'] for v in book['entries']) == 4
    assert [v['accession'] for v in book['entries']] == ['201', '11', '331', '2046', '134']
    assert all(v['artwork_creator'] is None and v['numeric_creation_start'] is None and v['numeric_creation_end'] is None for v in book['entries'])
    image_refs = m.load(RUN / 'visual-references-001.json')
    assert len(image_refs['rows']) == 33
    for pin in image_refs['rows'] + image_refs['sheets']:
        checked(pin)
    for name in ['native-3-image-capture-001.json', 'catalogue-excerpt-capture-001.json', 'catalogue-contents-capture-001.json']:
        checked(m.load(RUN / name))
    pending = m.RUN / 'native/kazantzakis-more-20261009/pending-delivery-001.json'
    assert m.load(pending)['actual_additions'] == 0
    for p in (m.ROOT / 'ops').glob('museum-expansion-kilkis*20261010.py'):
        ast.parse(p.read_text(), filename=str(p))
    m.save(RUN / 'checks-001.json', dict(
        at=m.now(), previous_research_checkpoint=r.ref(previous), previous_artifacts_verified=len(prior['artifacts']),
        previous_external_artifacts_verified=len(prior['external_artifacts']), original_page_bodies_verified=len(receipts),
        internal_image_files_verified=34, contact_sheets_verified=2, pdf_files_verified=2,
        reviewed_objects=32, pending_identity=26, held_leads=6, unchanged_native_fields_verified=True,
        numeric_creation_dates_invented=0, new_creator_assignments=0, production_records_added=0,
        local_database_writes=0, production_images_attached=0, live_identity_check_performed=False,
        validation='Source body lengths/digests, all original native fields, selected physical-unit holds, distinct lead keys, unknown dates/creators, image/PDF digests, preceding wave pins and Python syntax verified. Research-only assertions; no database fixtures, performance claim or mutation test.',
        script_reference=r.ref(Path(__file__).resolve())))

    paths = {p for p in RUN.rglob('*') if p.is_file()}
    paths |= set((m.ROOT / 'ops').glob('museum-expansion-kilkis*20261010.py'))
    paths |= {previous, last_production}
    pins = [r.ref(p) for p in sorted(paths)]
    external = [r.ref(p) for p in sorted(PROOF.rglob('*')) if p.is_file()]
    checkpoint = RUN / 'research-checkpoint-001.json'
    m.save(checkpoint, dict(
        at=m.now(), wave=114, previous_goal_turn='progress', goal_complete=False, goal_status='active',
        previous_research_checkpoint=r.ref(previous), last_successful_production_checkpoint=r.ref(last_production),
        production_apply_attempted=False, actual_new_records=0, proposed_kilkis_candidates=26, kilkis_holds=6,
        kazantzakis_pending_candidates=105, kazantzakis_pending_reference=r.ref(pending),
        production_campaign_totals_unchanged=prod['production_campaign_totals'],
        production_register_reference_unchanged=prod['production_institution_register_reference'],
        priority_queue_reference_unchanged=prod['priority_museum_queue_reference'],
        initial_full_historical_verification_reference=prod['initial_full_historical_verification_reference'],
        prior_artifact_pins_inherited=len(prior['artifacts']), prior_external_pins_inherited=len(prior['external_artifacts']),
        artifacts=pins, external_artifacts=external, checks_reference=r.ref(RUN / 'checks-001.json'),
        auth_requirement='Second continuation with failed Google Cloud token refresh. User must restore gcloud auth login before production reads/writes. Meaningful independent research continued; full goal is not at a no-progress impasse.',
        kilkis_remaining_reference=r.ref(RUN / 'remaining-research-001.json'),
        next_work='After authentication restoration, complete Kazantzakis comparator snapshot and exact-plan preflight (105 candidates, conditional 223/217; actual last verified 118/112). Preserve CP112 and 921 prior protected records. Kilkis has 32 reviewed leads: 24 native plus two book candidates await live accession/source/title reconciliation, six held. Fresh baseline and all mutation safeguards required before adding. Last Kilkis register remains 18/0 from 9 October. Unknown numeric dates persist. Full 87-sculpture book unavailable beyond public excerpt. Accessions 2/3 have reciprocal image/description contradictions; no silent swap. Parent objects for 1593–1595 and 5859/5862 unresolved. Entry 134 truncated. Native CC BY-NC-ND images internal only. Continue primary-source research at other museums while gaps persist. Next priority institutions from previous queue include Theocharakis (18/12), Zongolopoulos (18/18), Chania (18/0), not freshly counted. No commits, deployment, local DB mutation, fixtures or subagents. All historical provider holds remain, plus ejournals.epublishing.ekt.gr HTTP403 in this wave. Do not rerun immutable writers; create versioned reconciliation if state changes.'))
    for pin in pins + external:
        checked(pin)
    m.save(RUN / 'research-checkpoint-verification-001.json', dict(
        at=m.now(), checkpoint=r.ref(checkpoint), new_artifact_pins_verified=len(pins),
        new_external_pins_verified=len(external), previous_checkpoint_verified=r.ref(previous),
        production_delivery=False, goal_complete=False))
    print(json.dumps(dict(checkpoint=r.ref(checkpoint), artifacts=len(pins), external=len(external), candidates=26, held=6, actual_added=0)), flush=True)


if __name__ == '__main__':
    main()
