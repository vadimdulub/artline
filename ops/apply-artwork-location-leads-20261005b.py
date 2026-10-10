#!/usr/bin/env python3
"""Continue reviewed location citations without duplicating previously delivered evidence."""
import argparse
import importlib.util
from pathlib import Path

s = importlib.util.spec_from_file_location('leads', Path(__file__).with_name('apply-artwork-location-leads-20261005.py'))
l = importlib.util.module_from_spec(s)
s.loader.exec_module(l)
r = l.r
original_candidates = l.candidates
l.WAVE = 'location-leads-review-02'
l.FOLDER = r.RUN / 'delivery' / l.WAVE


def candidates(original):
    delivered = set()
    for path in (r.RUN / 'delivery').glob('location-leads-review-*/plan.json.gz'):
        if not path.with_name('verification.json').exists():
            continue
        delivered.update((v['artwork_id'], v['source_url']) for v in r.load(path)['leads'])
    leads = {(v['artwork_id'], v['source_url']): v for v in original_candidates(original)}
    path = r.RUN / 'primary-plans/arco-20261005b.json.gz'
    assert path.exists(), 'Finish Italian object reconciliation before citation planning'
    graph_receipts = {}
    for batch_path in (r.RUN / 'arco-object-graphs-v2-20261005b').glob('*.json.gz'):
        batch = r.load(batch_path)
        for uri in batch['requested']:
            graph_receipts[uri] = batch['receipt']
    for h in r.load(path)['holds']:
        work_ids = h.get('work_ids', []) or ([h['work']] if h.get('work') else [])
        for uri in work_ids:
            receipt = graph_receipts.get(uri)
            if not receipt:
                continue
            oid = uri.removeprefix('https://w3id.org/arco/resource/')
            url = 'https://catalogo.cultura.gov.it/detail/' + oid
            aid = h['artwork_id']
            names = h.get('museum_names', [])
            # These are explicitly unresolved leads, including same-title objects.
            lead = {'artwork_id': aid, 'provider': 'arco-unresolved-location-review-20261005b', 'external_id': oid,
                    'source_url': url, 'source_receipt': receipt, 'review_state': 'review',
                    'reported_location': '; '.join(names) + (' — ' + h['city'] if h.get('city') else '') if names else 'Museum/site identity unresolved in Italian catalogue candidate',
                    'source_outcome': h['reason'], 'identity_hold': h,
                    'requires_duplicate_reconciliation': h['reason'] == 'multiple_exact_creator_subject_date_candidates',
                    'candidate_evidence_path': str(path.relative_to(r.ROOT)),
                    'limitation': 'Unresolved official catalogue candidate retained only as review evidence. Exact object identity, institution identity or catalogue location remains unreconciled. Does not establish an accepted holding, creator attribution, current physical presence or display.'}
            leads.setdefault((aid, url), lead)
    # Preserve unresolved direct catalogue candidates from the final focused
    # passes. These citations cannot accept an institution or merge duplicates.
    def retain(aid, url, receipt, provider, location, hold, evidence_path):
        lead = {'artwork_id': aid, 'provider': provider + '-unresolved-review',
                'external_id': url, 'source_url': url, 'source_receipt': receipt,
                'review_state': 'review', 'reported_location': location,
                'source_outcome': hold['reason'], 'identity_hold': hold,
                'candidate_evidence_path': str(evidence_path.relative_to(r.ROOT)),
                'limitation': 'Unresolved direct museum-catalogue candidate retained only as review evidence. Object identity, creator relationship or inventory has not been reconciled. Does not establish an accepted holding, current physical presence or display.'}
        leads.setdefault((aid, url), lead)

    for provider, museum in [('ycba-20261005b', 'Yale Center for British Art'), ('aberdeen-refined-20261005b', 'Aberdeen Archives, Gallery & Museums')]:
        source_path = r.RUN / 'primary-plans' / (provider + '.json.gz')
        assert source_path.exists(), 'Finish final catalogue passes before citation planning'
        for hold in r.load(source_path)['holds']:
            aid = hold['artwork_id']
            if provider.startswith('ycba') and hold.get('source_url'):
                retain(aid, hold['source_url'], hold['source_receipt'], provider, museum, hold, source_path)
            elif provider.startswith('aberdeen'):
                entry_path = r.RUN / 'aberdeen-selected-objects-20261005b' / (aid + '.json.gz')
                for entry in r.load(entry_path)['objects']:
                    retain(aid, entry['object']['url'], entry['source_receipt'], provider, museum, hold, entry_path)

    smk_objects = {}
    for folder in ['smk-titles-20261005b', 'smk-creator-titles-20261005b']:
        for entry_path in (r.RUN / folder).glob('*.json.gz'):
            captured = r.load(entry_path)
            for obj in captured['items']:
                smk_objects.setdefault(obj['object_number'], (obj, captured['source_receipts'][0], entry_path))
    for provider in ['smk-current-20261005b', 'smk-refined-20261005b']:
        for hold in r.load(r.RUN / 'primary-plans' / (provider + '.json.gz'))['holds']:
            for oid in hold.get('source_object_ids', []):
                obj, receipt, entry_path = smk_objects[oid]
                retain(hold['artwork_id'], obj['frontend_url'], receipt, provider, 'Statens Museum for Kunst', hold, entry_path)
    armenia_recheck = r.load(r.RUN / 'armenia-primary-recheck-20261005b.json')
    existing_armenia = set(armenia_recheck['already_has_location_assertion'])
    for value in r.load(r.RUN / 'rmg-armenia-selected-20261005b.json.gz'):
        if value['museum_qid'] != 'Q2087788' or value['artwork_id'] in existing_armenia:
            continue
        aid, qid = value['artwork_id'], value['qid']
        assert any(e['scheme'] == 'wikidata' and e['external_id'] == qid for e in original[aid]['identifiers'])
        assert any(st.get('rank') != 'deprecated' and 'P582' not in st.get('qualifiers', {}) and st.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id') == 'Q2087788' for st in value['entity'].get('claims', {}).get('P195', []))
        url = 'https://www.wikidata.org/wiki/' + qid
        lead = {'artwork_id': aid, 'provider': 'armenia-catalogue-unavailable-review-20261005b',
                'external_id': qid, 'source_url': url, 'source_receipt': value['source_receipt'],
                'review_state': 'review', 'reported_location': 'National Gallery of Armenia',
                'source_outcome': 'secondary_collection_claim_primary_record_unavailable',
                'secondary_identity_and_collection': value, 'primary_recheck': armenia_recheck,
                'limitation': 'Wikidata collection statement retained only as review evidence for the existing exact Wikidata artwork ID. The current museum site returned a loader and the legacy object catalogue an application error. No primary current holding, physical presence, creator attribution or display has been accepted.'}
        # Store the common primary failure receipts, not repeated catalogue-wide IDs.
        lead['primary_recheck'] = {k:v for k,v in armenia_recheck.items() if k not in ['selected_artwork_ids', 'already_has_location_assertion']}
        leads.setdefault((aid, url), lead)
    return sorted((v for key,v in leads.items() if key not in delivered), key=lambda v: (v['artwork_id'], v['source_url']))


l.candidates = candidates

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['plan', 'apply', 'verify'])
    parser.add_argument('--target', choices=['local', 'production'], default='local')
    args = parser.parse_args()
    l.apply(args.target) if args.command == 'apply' else l.verify() if args.command == 'verify' else l.plan()
