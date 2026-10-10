#!/usr/bin/env python3
"""Resolve storage-only catalogue qualifications without asserting current display."""
import collections
import copy
import importlib.util
import re
from pathlib import Path

s = importlib.util.spec_from_file_location('a', Path(__file__).with_name('research-artwork-location-arco-plan-20261005b.py'))
a = importlib.util.module_from_spec(s)
s.loader.exec_module(a)
p, r = a.p, a.r
SPEC = 'https://w3id.org/arco/ontology/core/specifications'
PUBLIC = {'proprieta stato', 'proprieta ente pubblico territoriale', 'proprieta ente pubblico non territoriale'}
WARNING = r'\b(deposito|prestito|rubat\w*|furt\w*|dispers\w*|restitu\w*|privat\w*)\b'


def storage_only(rights, descriptions, specifications, other_location):
    if not rights or not all(r.norm(v) in PUBLIC for v in rights):
        return False
    # A loan/deposit narrative outside LDCS cannot be reinterpreted as a room.
    if re.search(WARNING, r.norm(' '.join(descriptions + other_location))):
        return False
    if not specifications:
        return False
    for value in specifications:
        text = r.norm(value)
        if not re.search(r'\bdeposito\b', text):
            return False
        if re.search(r'\b(in deposito|presso|estern\w*|privat\w*|prest\w*|rubat\w*|furt\w*|dispers\w*|restitu\w*|sindaco|ufficio|uffici|temporane\w*)\b', text):
            return False
        if not re.match(r'^(deposito\b|luogo di deposito\b|(?:\w+\s+)?piano\b|(?:i{1,3}|[1-3]°?) piano\b|pinacoteca, deposito\b|palazzo barberini\s*/\s*deposito\b|lazio/ rm/ roma/ palazzo barberini/ deposito\b)', text):
            return False
    return True


def main():
    ids = set(r.load(r.RUN / 'publication-pass-baseline-20261005c.json')['ids'])
    standard = r.load(r.RUN / 'iccd-location-standard-20261005c.json')['receipt']
    assert standard['status'] == 200 and standard['content_type'].startswith('application/pdf')
    claims, holds = [], []
    old = r.load(r.RUN / 'primary-plans/arco-20261005b.json.gz')
    for original in old['claims']:
        if original['artwork_id'] not in ids or original['object_evidence']['qualifications'] != ['custody_or_legal_qualification']:
            continue
        c = copy.deepcopy(original)
        e = c['object_evidence']
        root = 'https://w3id.org/arco/resource/' + c['external_id']
        rights, descriptions, specs, other = [], [], [], []
        for t in e['object_graph']:
            if t['s'] == root and t['p'] == a.DC + 'rights':
                rights.append(t['o'])
            if t['s'] == root and t['p'] == a.DC + 'description':
                descriptions.append(t['o'])
            if t['s'] == e['current_location']:
                (specs if t['p'] == SPEC else other).append(t['o'])
        if not storage_only(rights, descriptions, specs, other):
            holds.append({'artwork_id': c['artwork_id'], 'reason': 'custody_not_proven_storage_only', 'source_url': c['source_url'], 'external_id': c['external_id']})
            continue
        c['review_state'] = 'accepted'
        e['previous_qualifications'] = e.pop('qualifications')
        e['qualifications'] = []
        e['storage_resolution'] = {
            'basis': 'Public ownership and the only qualification is an internal physical-placement storage specification; exact object, creator, date, museum and city checks from the original plan remain required.',
            'specifications': specs, 'rights': rights,
            'field_definition_receipt': standard, 'pdf_page': 70, 'printed_page': 69,
            'field': 'LDCS - Specifiche',
            'field_definition_summary': 'ICCD defines LDCS as physical placement, including location codes inside the conservation structure. This is distinct from legal ownership and loan/deposit narratives.',
            'prior_review_preserved': True,
        }
        c['limitation'] = 'Museum connection supported by the current Italian national catalogue, with an internal storage specification and public ownership. Catalogue location is not a fresh observation of physical custody or public display. Prior review evidence is preserved.'
        c['identity_basis'] = c.get('identity_basis', '') + '; storage qualification resolved against ICCD LDCS field definition'
        claims.append(c)
    p.output('arco-storage-20261005c', claims, holds)
    print('Storage-only resolved', len(claims), 'Still custody review', len(holds), flush=True)
    print('Museums', collections.Counter(c['institution']['name'] for c in claims).most_common(12), flush=True)


if __name__ == '__main__':
    main()
