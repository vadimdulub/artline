#!/usr/bin/env python3
"""Recognise current named NG custody separately from ownership of loans."""
import collections
import copy
import importlib.util
import re
from pathlib import Path

s = importlib.util.spec_from_file_location('ng', Path(__file__).with_name('research-artwork-location-national-gallery-20261005d.py'))
ng = importlib.util.module_from_spec(s)
s.loader.exec_module(ng)
r, p = ng.r, ng.p


def custody_proof(o, checked_at):
    if o.get('legal', {}).get('status') != 'Long Loan' or o['@datatype'].get('virtual'):
        return None
    current = o.get('location', {}).get('current', {})
    link = current.get('@link', {})
    custodian = link.get('custodian', {})
    if custodian.get('@admin', {}).get('uid') != '0P5X-0001-0000-0000' or custodian.get('summary', {}).get('title') != 'The National Gallery (London)':
        return None
    dates = link.get('date', [])
    if len(dates) != 1: return None
    start, end = dates[0].get('from', ''), dates[0].get('to', '')
    if not re.match(r'^\d{4}-\d{2}-\d{2}', start): return None
    if start[:10] > checked_at[:10]: return None
    if end and (not re.match(r'^\d{4}-\d{2}-\d{2}', end) or end[:10] < checked_at[:10]): return None
    return {'current_named_custodian': custodian, 'catalogue_custody_interval': dates,
            'source_location': current, 'source_legal_status': o['legal']['status'],
            'source_lender_credit': o['legal'].get('credit'), 'retrieved_at': checked_at,
            'basis': 'Current public catalogue names the National Gallery as custodian with an effective start and no recorded past end; Long Loan is distinct from ownership. Absent ends and the 9999 sentinel remain open, not an invented end date or guarantee of future custody.'}


def main():
    claims, holds = [], []
    for old in r.load(r.RUN / 'primary-plans/ng-current-api-20261005d.json.gz')['claims']:
        c = copy.deepcopy(old)
        e = c['object_evidence']
        o = e['current_gallery_api_record']
        if o.get('legal', {}).get('status') in {'Virtual Object', 'Research Object'}:
            holds.append({'artwork_id': c['artwork_id'], 'reason': 'group_or_research_record_not_a_physical_collection_object', 'source_url': c['source_url'], 'source_receipt': c['source_receipt'], 'record': o})
            continue
        proof = custody_proof(o, c['checked_at'])
        flags = set(e['qualifications'])
        if proof and flags <= {'non_accessioned_collection_object', 'credit_ownership_qualification'}:
            c['review_state'] = 'accepted'
            e['qualifications'] = []
            e['documented_loan_custody'] = proof
            c['identity_basis'] = 'Unique exact title, creator, source object number and creation date; fresh official record explicitly identifies current National Gallery custodian for a documented long loan'
            c['limitation'] = 'Accepted museum holding through a documented long loan; ownership remains with the credited lender. Catalogue custody information is preserved without making an on-view claim or guaranteeing future loan duration. Publication and artwork metadata are unchanged.'
        else:
            c['identity_basis'] = 'Current source candidate with exact title and named creator; loan custody, attribution or creation-date details remain in review'
        claims.append(c)
    p.output('ng-custody-refined-20261005d', claims, holds)
    print(collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__': main()
