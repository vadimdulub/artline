#!/usr/bin/env python3
"""Compare explicit year/range notation without inventing or broadening dates."""
import collections
import copy
import importlib.util
from pathlib import Path
import re

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def date_meaning(value):
    text = r.norm(value or '').replace('–', '-').replace('—', '-')
    qualifier = 'exact'
    match = re.match(r'^(?:circa|ca\.?|c\.?)\s*(?=\d)', text)
    if match:
        qualifier, text = 'circa', text[match.end():]
    match = re.fullmatch(r'(\d{4})', text)
    if match:
        return qualifier, int(match[1]), int(match[1])
    match = re.fullmatch(r'(\d{4})\s*(?:-|to)\s*(\d{4})', text)
    if not match:
        match = re.fullmatch(r'between (\d{4}) and (\d{4})', text)
    if match and int(match[1]) <= int(match[2]):
        return qualifier, int(match[1]), int(match[2])
    return None


def equivalent(local, source):
    a, b = date_meaning(local), date_meaning(source)
    return a is not None and a == b and a[2] <= 1970


def source_dates(c):
    e, scheme = c['object_evidence'], c['scheme']
    if scheme == 'ycba-object':
        return e['current_lido_record']['dates']
    if scheme == 'hunterian-object':
        return [e['catalogue_metadata'].get('Production Dates', '')]
    if scheme == 'met-object':
        return [e['current_museum_record'].get('objectDate', '')]
    if scheme == 'iwm-object':
        return e['current_museum_record']['fields'].get('Production date', [])
    raise AssertionError(scheme)


def main():
    index = p.Index()
    baseline = set(r.load(r.RUN / 'publication-pass-baseline-20261005c.json')['ids'])
    providers = ['ycba-20261005b', 'hunterian-refined-20261005c', 'met-20261005c', 'iwm-refined-20261005c']
    allowed = {'date_wording_differs', 'creation_date_wording_differs', 'source_date_wording_changed'}
    claims, holds = [], []
    for name in providers:
        for original in r.load(r.RUN / 'primary-plans' / (name + '.json.gz'))['claims']:
            if original['artwork_id'] not in baseline or original.get('review_state') != 'review':
                continue
            flags = set(original['object_evidence'].get('qualifications', []))
            if not flags or not flags <= allowed:
                continue
            date = index.by_id[original['artwork_id']]['artwork'].get('date_display')
            dates = source_dates(original)
            matching = [d for d in dates if equivalent(date, d)]
            if not matching:
                holds.append({'artwork_id': original['artwork_id'], 'reason': 'date_meaning_unresolved', 'provider': name, 'local_date': date, 'source_dates': dates})
                continue
            c = copy.deepcopy(original)
            c['review_state'] = 'accepted'
            c['object_evidence']['qualifications'] = []
            c['object_evidence']['date_notation_reconciliation'] = {'original_provider': name, 'original_qualifications': sorted(flags), 'local_date': date, 'primary_dates': dates, 'same_meaning': date_meaning(date), 'rule': 'Only spelled-out circa abbreviations and explicit full-year range notation. Unknown, uncertain, open-ended and different dates stay unresolved; original date fields are not changed.'}
            c['identity_basis'] += '; equivalent explicit date notation with uncertainty and range preserved'
            c['limitation'] = 'Documented museum holding; equivalent date notation reconciled for identity only. No date, publication, creator, physical presence or current-display change.'
            claims.append(c)
    p.output('date-notation-20261005c', claims, holds)
    print('Providers', collections.Counter(c['scheme'] for c in claims), flush=True)


if __name__ == '__main__':
    main()
