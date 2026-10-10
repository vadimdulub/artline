#!/usr/bin/env python3
"""Add the verified Manchester holding reconciliation to the immutable campaign report."""
import argparse
import copy
import csv
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('prior', Path(__file__).with_name('museum-expansion-walker-report-20261007.py'))
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
spec = importlib.util.spec_from_file_location('manchester', Path(__file__).with_name('museum-expansion-manchester-holdings-20261007.py'))
manchester = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manchester)
m = manchester.m


def report(label):
    assert not (m.RUN / ('verification-' + label + '.json')).exists()
    plan, digest = manchester.validate_plan()
    receipt = m.load(manchester.RUN / (manchester.KEY + '-applied.json'))
    assert receipt['plan_sha256'] == digest and receipt['verification']['existing_artworks_linked'] == 200
    with m.connect() as db:
        checked = manchester.verify(db, plan, digest)
    base = label + '-prior-batches'
    if not (m.RUN / ('verification-' + base + '.json')).exists():
        prior.report(base)
    summary = copy.deepcopy(m.load(m.RUN / ('verification-' + base + '.json')))
    assert summary['verified_existing_artworks_linked'] == 338 and summary['verified_new_artworks'] == 3553
    with (m.RUN / ('museum-coverage-' + base + '.csv')).open(newline='') as f:
        coverage = list(csv.DictReader(f))
    target = next(r for r in coverage if r['id'] == manchester.IID)
    assert target['kind'] == 'museum' and target['added_this_campaign'] == target['existing_artworks_linked_this_campaign'] == '0'
    assert (int(target['works']), int(target['eligible_works'])) == (checked['current_counts']['linked'], checked['current_counts']['eligible']) == (200, 200)
    target.update(existing_artworks_linked_this_campaign='200', research_state='existing_holdings_reconciled', campaign_state='target_200_reached_this_campaign')
    with (m.RUN / ('museum-coverage-' + label + '.csv')).open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(coverage[0]))
        writer.writeheader()
        writer.writerows(coverage)
    for record in plan['records']:
        f, decision = record['facts'], record['decision']
        summary['existing_holding_verifications'].append(dict(artwork_id=f['artwork_id'], institution_id=manchester.IID,
            source_url=f['source_url'], verified_existing_metadata_unchanged=True, confidence=decision['confidence'],
            evidence_basis=decision['basis'] + ' ' + decision['version_review'], source_limitation=decision['limitation']))
    assert len({r['artwork_id'] for r in summary['existing_holding_verifications']}) == len(summary['existing_holding_verifications']) == 538
    summary.update(at=m.now(), verified_existing_artworks_linked=538,
                   source_pass_museums=summary['source_pass_museums'] + 1,
                   source_pass_institutions=summary['source_pass_institutions'] + 1,
                   manchester_holding_reconciliation=checked,
                   institutions_with_new_records_or_reconciled_holdings=summary['institutions_with_new_records_or_reconciled_holdings'] + 1)
    summary['verification_components'] += [manchester.reference(m.RUN / ('verification-' + base + '.json')),
                                           manchester.reference(manchester.PLAN), manchester.reference(manchester.RUN / (manchester.KEY + '-applied.json'))]
    with (m.RUN / ('reconciled-artworks-' + label + '.csv')).open('x', newline='') as f:
        keys = ['artwork_id', 'institution_id', 'source_url', 'verified_existing_metadata_unchanged', 'confidence', 'evidence_basis', 'source_limitation']
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(summary['existing_holding_verifications'])
    for source, destination in [(base + '.json', label + '.json'), (base + '.csv', label + '.csv'),
                                ('added-artworks-' + base + '.csv', 'added-artworks-' + label + '.csv')]:
        with (m.RUN / destination).open('xb') as f:
            f.write((m.RUN / source).read_bytes())
    m.save(m.RUN / ('verification-' + label + '.json'), summary)
    print(json.dumps({k: summary[k] for k in ['verified_new_artworks', 'verified_existing_artworks_linked', 'museums_expanded', 'source_pass_museums', 'after']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', default='after-wave-29')
    report(parser.parse_args().label)
