#!/usr/bin/env python3
"""Validate a holding for an exact undated object; keep the artwork in review.

An unknown creation date is not a contradictory museum identity. This pass
requires matching accession/title/creator and a current primary record. It
does not classify eligibility, assign a year, or publish the artwork.
"""
import collections
import argparse
import copy
import importlib.util
from pathlib import Path

s = importlib.util.spec_from_file_location('dn', Path(__file__).with_name('refine-artwork-location-date-notation-20261005c.py'))
dn = importlib.util.module_from_spec(s)
s.loader.exec_module(dn)
r, p = dn.r, dn.p
DATE_FLAGS = {'date_wording_differs', 'creation_date_wording_differs', 'source_date_wording_changed', 'date_meaning_unresolved'}


def source(c):
    e, scheme = c['object_evidence'], c['scheme']
    if scheme == 'ycba-object':
        o = e['current_lido_record']
        return o['inventory'], o['dates']
    if scheme == 'hunterian-object':
        o = e['catalogue_metadata']
        return o.get('Object Number'), [o.get('Production Dates')]
    if scheme == 'met-object':
        o = e['current_museum_record']
        return o['accessionNumber'], [o.get('objectDate')]
    if scheme in ['bristol-object', 'glasgow-object', 'auckland-object']:
        o = e['current_public_catalogue_record']['fields']
        inventory, dates = {'bristol-object': ('Object Number', 'Date of Production'), 'glasgow-object': ('ID Number', 'Date'), 'auckland-object': ('Accession No', 'Production date')}[scheme]
        return o[inventory][0], o.get(dates, [])
    if scheme == 'mds-object':
        o = e['museum_supplied_record']['fields']
        dates = list(e['date_reconciliation']['primary_dates'])
        # The source may hold additional dates in mapped fields or free text.
        # An empty preferred display date must not conceal those values.
        dates += [v for k in ['Object production date', 'Object production note', 'Date - earliest / single', 'Date - latest', 'Associated date'] for v in o.get(k, [])]
        return o['Object number'][0], dates
    raise AssertionError(scheme)


def undated_identity(row, c):
    a = row['artwork']
    if a['status'] != 'review' or a.get('date_display') != 'Creation date under review' or a.get('creation_year_start') is not None or a.get('creation_year_end') is not None:
        return None
    flags = set(c['object_evidence'].get('qualifications', []))
    if c.get('review_state') != 'review' or not flags or not flags <= DATE_FLAGS:
        return None
    inventory, dates = source(c)
    if not all(r.norm(v) in ['', 'undated', 'date unknown', 'unknown date', 'unknown'] for v in dates):
        return None
    local_inventory = a.get('accession_number')
    if not local_inventory or p.acckey(local_inventory.replace('_', ':')) != p.acckey(inventory):
        return None
    if c['scheme'] == 'ycba-object':
        qids = {v['external_id'] for v in row['identifiers'] if v['scheme'] == 'wikidata'}
        if not any('https://www.wikidata.org/wiki/' + q in c['object_evidence']['current_lido_record']['object_wikidata'] for q in qids):
            return None
    return {'local_inventory': local_inventory, 'primary_inventory': inventory, 'primary_date_wording': dates, 'original_date_review_flags': sorted(flags), 'creation_years_remain_null': True, 'artwork_publication_remains_review': True, 'eligibility_not_determined': True, 'basis': 'Current primary title, creator and exact museum accession identify the same undated object; its holding can be evidenced while creation date and eligibility remain in editorial review.'}


def main(mds_only=False):
    index = p.Index()
    baseline = set(r.load(r.RUN / 'publication-pass-baseline-20261005c.json')['ids'])
    providers = ['ycba-20261005b', 'hunterian-refined-20261005c', 'met-20261005c', 'bristol-refined-20261005c', 'glasgow-refined-20261005c', 'auckland-refined-20261005c']
    if mds_only:
        providers = ['mds-refined-20261005c']
    claims = []
    for provider in providers:
        for original in r.load(r.RUN / 'primary-plans' / (provider + '.json.gz'))['claims']:
            if original['artwork_id'] not in baseline:
                continue
            proof = undated_identity(index.by_id[original['artwork_id']], original)
            if not proof:
                continue
            c = copy.deepcopy(original)
            c['review_state'] = 'accepted'
            c['object_evidence']['qualifications'] = []
            c['object_evidence']['undated_object_holding_reconciliation'] = proof
            c['object_evidence']['creation_date_and_eligibility_require_editorial_review'] = True
            c['identity_basis'] += '; exact undated museum object, with date and publication review retained'
            c['limitation'] = 'Accepted museum holding only. Artwork and unknown creation date remain in editorial review; no eligibility decision, invented year, publication, current physical presence or display claim.'
            claims.append(c)
    p.output('mds-undated-refined-20261005c' if mds_only else 'undated-identities-20261005c', claims, [])
    print('Providers', collections.Counter(c['scheme'] for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mds-only', action='store_true')
    main(parser.parse_args().mds_only)
