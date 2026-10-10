#!/usr/bin/env python3
"""Deliver unresolved current catalogue and historical book evidence as citations."""
import argparse
import importlib.util
from pathlib import Path

s = importlib.util.spec_from_file_location('leads', Path(__file__).with_name('apply-artwork-location-leads-20261005.py'))
l = importlib.util.module_from_spec(s)
s.loader.exec_module(l)
r = l.r
original_candidates = l.candidates
l.WAVE = 'location-leads-review-03'
l.FOLDER = r.RUN / 'delivery' / l.WAVE
PROVIDERS = {
    'louvre-refined-20261005c': 'Musée du Louvre',
    'met-20261005c': 'The Metropolitan Museum of Art',
    'iwm-refined-20261005c': 'Imperial War Museums',
    'hunterian-refined-20261005c': 'The Hunterian, University of Glasgow',
    'whistler-20261005c': 'Collection identity requires review',
    'bristol-refined-20261005c': 'Bristol Museums',
    'glasgow-refined-20261005c': 'Glasgow Museums',
    'rmg-refined-20261005c': 'Royal Museums Greenwich',
    'auckland-refined-20261005c': 'Auckland Art Gallery Toi o Tāmaki',
    'russell-cotes-20261005c': 'Russell-Cotes Art Gallery & Museum',
    'mds-refined-20261005c': 'Contributing museum collection named in the source record',
}


def candidates(original):
    delivered = set()
    for path in (r.RUN / 'delivery').glob('location-leads-review-*/plan.json.gz'):
        if path.with_name('verification.json').exists():
            delivered.update((v['artwork_id'], v['source_url']) for v in r.load(path)['leads'])
    leads = {(v['artwork_id'], v['source_url']): v for v in original_candidates(original)}

    def retain(aid, url, receipt, provider, location, hold, path, evidence=None):
        if not url or not receipt or receipt.get('status') != 200:
            return
        lead = {'artwork_id': aid, 'provider': provider + '-unresolved-review', 'external_id': url,
                'source_url': url, 'source_receipt': receipt, 'review_state': 'review',
                'reported_location': location, 'source_outcome': hold['reason'], 'identity_hold': hold,
                'candidate_evidence_path': str(path.relative_to(r.ROOT)),
                'limitation': 'Unresolved source candidate retained only as review evidence. Title, creator, accession, attribution or collection identity has not been fully reconciled. No accepted museum link, metadata replacement, publication, current physical presence or display assertion.'}
        if evidence:
            lead['candidate_record'] = evidence
        leads.setdefault((aid, url), lead)

    for provider, location in PROVIDERS.items():
        path = r.RUN / 'primary-plans' / (provider + '.json.gz')
        assert path.exists(), 'Finish all current museum plans before citation delivery: ' + provider
        for hold in r.load(path)['holds']:
            aid = hold['artwork_id']
            if hold.get('source_url') and hold.get('source_receipt'):
                retain(aid, hold['source_url'], hold['source_receipt'], provider, location, hold, path)
            elif provider.startswith('louvre') and hold.get('source_receipt'):
                rc = hold['source_receipt']
                retain(aid, rc['url'].removesuffix('.json'), rc, provider, location, hold, path)
            if hold.get('capture_path'):
                capture_path = Path(hold['capture_path'])
                cap = r.load(capture_path)
                for entry in cap.get('objects', []):
                    obj = entry.get('object', entry)
                    url = obj.get('url')
                    rc = entry.get('source_receipt') or cap.get('source_receipt')
                    if provider.startswith('hunterian') and obj.get('object_id'):
                        url = 'https://www.gla.ac.uk/collections/#/details?catType=C&irn=' + obj['object_id']
                    named_location = '; '.join(obj.get('fields', {}).get('Collection', [])) if provider.startswith('mds') else location
                    retain(aid, url, rc, provider, named_location or location, hold, capture_path, obj)
    whistler_holds = {v['artwork_id']: v for v in r.load(r.RUN / 'primary-plans/whistler-20261005c.json.gz')['holds'] if v['reason'] == 'repeated_title_requires_inventory'}
    for name in ['whistler-painting-candidates-20261005c.json.gz', 'whistler-paper-candidates-20261005c.json.gz']:
        path = r.RUN / name
        for candidate in r.load(path):
            aid = candidate['row']['artwork']['id']
            if aid in whistler_holds:
                for hit in candidate['hits']:
                    retain(aid, hit['url'], hit['receipt'], 'whistler-title-index', 'Collection identity requires review', whistler_holds[aid], path,
                           {'title_index_hit': hit, 'limitation': 'Repeated title in scholarly catalogue index; this evidence does not identify which catalogue object matches the local artwork or establish its holding museum.'})
    # A 1982 illustration index is useful historical provenance, not evidence
    # that an artwork is presently held by or on display at the museum.
    path = r.RUN / 'primary-plans/armenia-book-20261005c.json.gz'
    for c in r.load(path)['claims']:
        assert c['review_state'] == 'review'
        lead = {'artwork_id': c['artwork_id'], 'provider': 'armenia-museum-book-1982-review',
                'external_id': c['external_id'], 'source_url': c['source_url'], 'source_receipt': c['source_receipt'],
                'review_state': 'review', 'reported_location': c['institution']['name'],
                'source_class': 'historical_museum_book', 'source_outcome': 'historical_book_identity_and_current_holding_require_review',
                'candidate_evidence_path': str(path.relative_to(r.ROOT)), 'book_evidence': c['object_evidence'], 'limitation': c['limitation']}
        leads.setdefault((c['artwork_id'], c['source_url']), lead)
    return sorted((v for key, v in leads.items() if key not in delivered), key=lambda v: (v['artwork_id'], v['source_url']))


l.candidates = candidates

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['plan', 'apply', 'verify'])
    parser.add_argument('--target', choices=['local', 'production'], default='local')
    args = parser.parse_args()
    l.apply(args.target) if args.command == 'apply' else l.verify() if args.command == 'verify' else l.plan()
