#!/usr/bin/env python3
"""Reconcile current Rijksmuseum makers separately from rejected former attributions.

Signed/inscribed names are source object identity evidence only. Existing creator
relationships, attribution labels and prior review assertions remain untouched.
"""
import collections
import copy
import importlib.util
import json
from pathlib import Path
import re

s = importlib.util.spec_from_file_location('j', Path(__file__).with_name('research-artwork-location-rijks-20261005b.py'))
j = importlib.util.module_from_spec(s)
s.loader.exec_module(j)
p, r = j.p, j.r
QUALIFIED = re.compile(r'\b(attributed|attribution|copy|copies|after|workshop|school|follower|circle|possibly|probably|anonymous|toegeschreven|kopie|naar|atelier|anoniem|rejected|verworpen)\b', re.I)


def current_production(production, oid):
    result = copy.deepcopy(production)
    historical = result.get('assigned_by', [])
    for assignment in historical:
        assert assignment.get('assigned_property') == 'part_of'
        assert assignment.get('assigned')
        for value in assignment['assigned']:
            texts = ' '.join(v.get('content', '') for v in value.get('referred_to_by', []))
            assert re.search(r'rejected attribution|verworpen toeschrijving', texts, re.I)
    result.pop('assigned_by', None)
    parts = result.get('part', [])
    assert len(parts) == 1 and not result.get('carried_out_by')
    part = parts[0]
    assert not QUALIFIED.search(json.dumps(result, ensure_ascii=False))
    direct = part.get('carried_out_by', [])
    if direct:
        assert len(direct) == 1
        assert not any(v.get('assigned_property') == 'carried_out_by' for v in part.get('assigned_by', []))
        return [v['@value'] for v in direct[0].get('notation', []) if v.get('@value')], 'single_current_direct_maker; rejected_historical_alternatives_retained_as_evidence'
    assignments = part.get('assigned_by', [])
    assert len(assignments) == 1
    assignment = assignments[0]
    assert assignment.get('assigned_property') == 'carried_out_by'
    people = assignment.get('assigned', [])
    assert len(people) == 1 and people[0]['type'] == 'Person'
    assert not assignment.get('classified_as'), 'Uncertainty assignment is not a signature identity'
    motivation = assignment.get('motivated_by', [])
    assert len(motivation) == 1
    assert 'https://id.rijksmuseum.nl/' + oid in motivation[0].get('carried_by', [])
    assert {v['id'] for v in motivation[0].get('classified_as', [])} <= {'http://vocab.getty.edu/aat/300028702', 'http://vocab.getty.edu/aat/300028705'}
    assert motivation[0].get('classified_as')
    names = []
    for v in part.get('referred_to_by', []):
        if not any(t.get('id') == 'http://vocab.getty.edu/aat/300435417' for t in v.get('classified_as', [])):
            continue
        match = re.fullmatch(r'(.+?)\s+\((signed by artist|mentioned on object|eigenhandig gesigneerd|vermeld op object)\)', v.get('content', ''))
        if match:
            names.append(match[1])
    assert names
    return names, 'single_current_maker_documented_by_signature_or_name_on_this_object; documentary_qualifier_preserved'


def main():
    index = p.Index()
    old = r.load(r.RUN / 'primary-plans/rijks-20261005b.json.gz')
    claims, holds = [], []
    for previous in old['claims']:
        if previous.get('review_state') != 'review':
            continue
        c = copy.deepcopy(previous)
        aid = c['artwork_id']
        try:
            flags = c['object_evidence']['qualifications']
            assert 'loan_or_custody_qualification' not in flags
            production = c['object_evidence']['produced_by']
            makers, detail = current_production(production, c['external_id'])
            obj = c['object_evidence']
            accessions = {v['content'] for v in obj['identified_by'] if v.get('type') == 'Identifier' and any(t.get('id') == 'http://vocab.getty.edu/aat/300312355' for t in v.get('classified_as', []))}
            assert len(accessions) == 1
            basis = index.match(index.by_id[aid], 'rijks-object', c['external_id'], j.names(obj), makers, next(iter(accessions)), j.names(production['timespan']))
            assert basis.startswith(('existing_', 'unique_')), basis
            c['review_state'] = 'accepted'
            c['identity_basis'] = basis + '; ' + detail + '; current exact accession and EDM Rijksmuseum provider verified'
            c['object_evidence']['prior_review_qualifications'] = flags
            c['object_evidence']['identity_reconciliation'] = {'current_maker_names': makers, 'basis': detail}
            c['object_evidence']['qualifications'] = []
            c['limitation'] = 'Museum collection connection only. Prior attribution history and documentary signature wording remain in source evidence; no creator changes, legal ownership, physical presence or current display asserted.'
            claims.append(c)
        except AssertionError as exc:
            holds.append({'artwork_id': aid, 'reason': 'review_qualification_not_fully_resolved', 'detail': str(exc), 'source_url': c['source_url']})
    p.output('rijks-refined-20261005b', claims, holds)


if __name__ == '__main__':
    main()
