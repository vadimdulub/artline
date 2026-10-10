#!/usr/bin/env python3
"""Deliver unresolved major-museum source evidence without accepting holdings."""
import argparse
import importlib.util
from pathlib import Path

s = importlib.util.spec_from_file_location('leads', Path(__file__).with_name('apply-artwork-location-leads-20261005.py'))
l = importlib.util.module_from_spec(s)
s.loader.exec_module(l)
r = l.r
l.WAVE = 'location-leads-review-04'
l.FOLDER = r.RUN / 'delivery' / l.WAVE
WAVES = ['major-prado-louvre-01', 'major-deposit-01', 'major-titles-ng-01', 'major-french-identities-01', 'major-date-review-01', 'major-prado-rijks-01']


def candidates(original):
    delivered, leads = set(), {}
    for path in (r.RUN / 'delivery').glob('location-leads-review-*/plan.json.gz'):
        if path.with_name('verification.json').exists():
            delivered.update((v['artwork_id'], v['source_url']) for v in r.load(path)['leads'])

    def add(aid, url, receipt, provider, location, reason, path, evidence):
        assert aid in original and receipt['status'] == 200
        lead = {'artwork_id': aid, 'provider': provider, 'external_id': url, 'source_url': url,
                'source_receipt': receipt, 'review_state': 'review', 'reported_location': location,
                'source_outcome': reason, 'candidate_evidence_path': str(path.relative_to(r.ROOT)),
                'candidate_record': evidence,
                'limitation': 'Unresolved research evidence only. A search result, group record, duplicate source identity or conflicting inventory cannot establish this artwork\'s museum. No accepted holding, publication, attribution, date replacement, physical presence or current-display claim.'}
        leads.setdefault((aid, url), lead)

    for wave in WAVES:
        path = r.RUN / 'delivery' / wave / 'plan.json.gz'
        data = r.load(path)
        held = {v['artwork_id']: v for v in data['held'] if 'another_artwork' in v['reason'] or v['reason'] == 'multiple_catalogue_rows_match_one_source_object'}
        for provider in data['providers']:
            for c in r.load(r.RUN / 'primary-plans' / (provider + '.json.gz'))['claims']:
                if c['artwork_id'] in held:
                    add(c['artwork_id'], c['source_url'], c['source_receipt'], 'major-museum-duplicate-review-20261005d', c['institution']['name'], held[c['artwork_id']]['reason'], path, c)
    path = r.RUN / 'primary-plans/louvre-authorities-20261005d.json.gz'
    for hold in r.load(path)['holds']:
        if hold.get('source_url') and hold.get('source_receipt'):
            add(hold['artwork_id'], hold['source_url'], hold['source_receipt'], 'louvre-inventory-conflict-review-20261005d', 'Musée du Louvre: object identity unresolved', hold['reason'], path, hold)
    path = r.RUN / 'primary-plans/ng-custody-refined-20261005d.json.gz'
    for hold in r.load(path)['holds']:
        add(hold['artwork_id'], hold['source_url'], hold['source_receipt'], 'ng-group-record-review-20261005d', 'National Gallery: group or research record, not confirmed individual object', hold['reason'], path, hold['record'])
    path = r.RUN / 'primary-plans/ng-current-api-20261005d.json.gz'
    for hold in r.load(path)['holds']:
        captured = r.load(Path(hold['capture_path']))
        receipt = captured['source_receipt']
        add(hold['artwork_id'], receipt['url'], receipt, 'ng-search-identity-review-20261005d', 'National Gallery scoped catalogue search: identity unresolved', hold['reason'], path,
            {'query': captured['query'], 'total': captured['result']['hits']['total'], 'identity_hold': hold, 'capture_path': hold['capture_path'], 'negative_or_ambiguous_result_is_not_a_museum_link': True})
    return sorted((v for key, v in leads.items() if key not in delivered), key=lambda v: (v['artwork_id'], v['source_url']))


l.candidates = candidates
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['plan', 'apply', 'verify'])
    parser.add_argument('--target', choices=['local', 'production'], default='local')
    args = parser.parse_args()
    l.apply(args.target) if args.command == 'apply' else l.verify() if args.command == 'verify' else l.plan()
