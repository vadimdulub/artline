#!/usr/bin/env python3
"""Accept exact museum identities while preserving separate date editorial review."""
import collections
import copy
import importlib.util
from pathlib import Path

s = importlib.util.spec_from_file_location('u', Path(__file__).with_name('refine-artwork-location-undated-identities-20261005c.py'))
u = importlib.util.module_from_spec(s)
s.loader.exec_module(u)
r, p = u.r, u.p
FLAGS = {'date_wording_differs', 'creation_date_wording_differs', 'source_date_wording_changed', 'date_meaning_unresolved', 'conflicting_explicit_production_dates', 'creation_date_requires_review', 'creation_date_conflict'}
PROVIDERS = ['ycba-20261005b', 'hunterian-refined-20261005c', 'met-20261005c', 'bristol-refined-20261005c', 'glasgow-refined-20261005c', 'auckland-refined-20261005c', 'mds-refined-20261005c', 'louvre-authorities-20261005d']


def proof(row, c):
    a, e = row['artwork'], c['object_evidence']
    flags = set(e.get('qualifications', []))
    if a['status'] != 'review' or c.get('review_state') != 'review' or not flags or not flags <= FLAGS:
        return None
    if c['source_receipt']['status'] != 200 or c['checked_at'][:10] < '2026-10-04': return None
    if c['scheme'] == 'louvre-object':
        # The prior exact Joconde object and fresh Louvre object independently
        # share inventory, and the identifier crosswalk pins the Louvre ARK.
        old = e['prior_joconde_candidate']
        prior = old['object_evidence']
        inventories = {p.acckey(v['value']) for v in e['current_louvre_record']['objectNumber']}
        original = {p.acckey(v.strip()) for v in (prior.get('Numero_inventaire') or '').split(';') if v.strip()}
        if not inventories & original or old['artwork_id'] != a['id']: return None
        if e['external_identifier_crosswalk']['joconde'] != old['external_id']: return None
        if c['external_id'] != 'cl' + e['external_identifier_crosswalk']['ark']: return None
        identity = {'prior_exact_object_reference': old['external_id'], 'prior_inventory': prior['Numero_inventaire'], 'current_inventory': e['current_louvre_record']['objectNumber'], 'current_native_id': c['external_id']}
        dates = e['current_louvre_record'].get('dateCreated', [])
    else:
        inventory, dates = u.source(c)
        local = a.get('accession_number')
        if not local or not inventory or p.acckey(local.replace('_', ':')) != p.acckey(inventory): return None
        identity = {'local_inventory': local, 'current_primary_inventory': inventory, 'current_native_id': c['external_id']}
        if c['scheme'] == 'ycba-object':
            qids = {v['external_id'] for v in row['identifiers'] if v['scheme'] == 'wikidata'}
            if not any('https://www.wikidata.org/wiki/' + q in e['current_lido_record']['object_wikidata'] for q in qids): return None
    return {'identity': identity, 'original_date_review_flags': sorted(flags), 'original_date_display': a.get('date_display'),
            'original_creation_year_start': a.get('creation_year_start'), 'original_creation_year_end': a.get('creation_year_end'),
            'current_source_creation_dates': dates, 'creation_date_and_eligibility_require_editorial_review': True,
            'artwork_publication_remains_review': True,
            'basis': 'Current source title and named creator identify the exact museum object through matching inventory and native identifier. Date uncertainty or disagreement is retained for editorial review and does not negate the documented collection association. No creation date or eligibility is inferred.'}


def main():
    index = p.Index()
    ids = set(r.load(r.RUN / 'major-museums-baseline-20261005d.json')['ids'])
    claims, holds = [], []
    for provider in PROVIDERS:
        for old in r.load(r.RUN / 'primary-plans' / (provider + '.json.gz'))['claims']:
            if old['artwork_id'] not in ids: continue
            decision = proof(index.by_id[old['artwork_id']], old)
            if not decision: continue
            c = copy.deepcopy(old)
            c['review_state'] = 'accepted'
            # Keep the date flags, rather than making the discrepancy vanish.
            c['object_evidence']['holding_identity_with_date_review'] = decision
            c['identity_basis'] += '; exact museum inventory/native identity with creation-date and eligibility review explicitly retained'
            c['limitation'] = 'Accepted museum holding only. Original creation dates and source date discrepancies remain in editorial review; no eligibility, publication, ownership transfer, present physical verification or current-display claim. Artwork titles, dates, creators and publication state are preserved.'
            claims.append(c)
    p.output('exact-holdings-date-review-20261005d', claims, holds)
    print(collections.Counter(c['scheme'] for c in claims), flush=True)


if __name__ == '__main__': main()
