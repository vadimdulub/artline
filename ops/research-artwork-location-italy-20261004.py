#!/usr/bin/env python3
"""Recheck selected Lombardia catalogue identities and present collection fields."""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time

spec = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
r = p.r


def dates(o):
    a = ' '.join(filter(None, [o.get('dtsv'), o.get('dtsi')]))
    b = ' '.join(filter(None, [o.get('dtsl'), o.get('dtsf')]))
    return {a + '-' + b, a} if a and a == b else {a + '-' + b} if a and b else {a or b or ' '.join(filter(None, [o.get('dtzg'), o.get('dtzs')]))}


def museums(o):
    name, part = o.get('ldcm') or '', o.get('ldci') or ''
    return {name, *[name + sep + part for sep in ['. ', ' - ', ' — ']]} if part else {name}


def selection(index):
    dest = r.RUN / 'italy-selection.json.gz'
    if dest.exists():
        return r.load(dest)
    path = r.ROOT / 'content/imports/campaign-lombardia-20260910/objects.json'
    rc = r.load(path.with_name(path.name + '.snapshot.json'))
    raw = path.read_bytes()
    assert r.sha(raw) == rc['sha256']
    found = collections.defaultdict(dict)
    for o in json.loads(raw):
        for row in index.find('lombardia-object', o['idk'], [o.get('sgtt'), o.get('sgti')], [o.get('autn')], museums(o)):
            basis = index.match(row, 'lombardia-object', o['idk'], [o.get('sgtt'), o.get('sgti')], [o.get('autn')], '', dates(o))
            if not basis.startswith(('existing_', 'unique_')):
                continue
            found[row['artwork']['id']][o['idk']] = {'artwork_id': row['artwork']['id'], 'object_id': o['idk'], 'source_record': {k: v for k, v in o.items() if not k.startswith('urlimg')}, 'identity_basis': basis}
    unique = [next(iter(group.values())) for group in found.values() if len(group) == 1]
    ambiguous = [{'artwork_id': aid, 'object_ids': sorted(group)} for aid, group in found.items() if len(group) != 1]
    result = {'at': r.now(), 'historical_receipt': rc, 'unique': unique, 'ambiguous': ambiguous}
    r.save_gz(dest, result)
    print('Lombardia selected identities', len(unique), 'ambiguous', len(ambiguous), flush=True)
    return result


def capture(index):
    chosen = selection(index)
    ids = sorted({v['object_id'] for v in chosen['unique']})
    for offset in range(0, len(ids), 100):
        dest = r.RUN / 'italy-batches' / f'{offset//100:04d}.json.gz'
        if dest.exists():
            continue
        group = ids[offset:offset+100]
        assert all(re.fullmatch(r'[A-Za-z0-9-]+', oid) for oid in group)
        where = 'idk in (' + ','.join("'" + oid + "'" for oid in group) + ')'
        raw, rc = r.capture('https://www.dati.lombardia.it/resource/ay8b-p38f.json', {'$where': where, '$limit': 100, '$order': 'idk'}, tag='lombardia')
        assert rc['status'] == 200, rc['status']
        data = json.loads(raw)
        assert all(o['idk'] in group for o in data)
        r.save_gz(dest, {'requested': group, 'receipt': rc, 'data': data})
        print('Lombardia fresh selected IDs', min(offset+100, len(ids)), '/', len(ids), flush=True)
        time.sleep(0.6)


def plan(index):
    chosen = selection(index)
    current = {}
    for path in sorted((r.RUN / 'italy-batches').glob('*.json.gz')):
        batch = r.load(path)
        for o in batch['data']:
            assert o['idk'] not in current
            current[o['idk']] = (o, batch['receipt'])
    with r.connect() as db:
        places = {str(row['id']): row['city'] for row in db.execute('SELECT i.id,p.name city FROM institutions i LEFT JOIN places p ON p.id=i.place_id').fetchall()}
    claims, holds = [], []
    for v in chosen['unique']:
        aid, oid = v['artwork_id'], v['object_id']
        row = index.by_id[aid]
        if oid not in current:
            holds.append({'artwork_id': aid, 'reason': 'current_source_not_retrieved', 'object_id': oid})
            continue
        o, rc = current[oid]
        prior = v['source_record']
        reason = None
        if any(p.titlekey(o.get(k)) != p.titlekey(prior.get(k)) for k in ['autn', 'sgtt', 'sgti']):
            reason = 'current_source_identity_changed'
        elif any(p.titlekey(o.get(k)) != p.titlekey(prior.get(k)) for k in ['ldcm', 'ldci', 'pvcc']):
            reason = 'current_collection_changed_requires_review'
        elif not o.get('ldcm') or not o.get('pvcc'):
            reason = 'no_named_present_collection'
        # Match both museum and city: generic Italian museum names are ambiguous.
        names = {p.titlekey(n) for n in museums(o)}
        institutions = [i for i in index.institutions if p.titlekey(i['name']) in names and p.titlekey(places.get(i['id'])) == p.titlekey(o.get('pvcc'))]
        if len(institutions) != 1:
            reason = 'museum_and_city_identity_requires_review'
        if reason:
            holds.append({'artwork_id': aid, 'reason': reason, 'object_id': oid, 'museum': o.get('ldcm'), 'city': o.get('pvcc'), 'source_receipt': rc})
            continue
        url = (o.get('url') or '').replace('http://', 'https://', 1)
        if not url.startswith('https://www.lombardiabeniculturali.it/opere-arte/schede/') or url.rstrip('/').split('/')[-1] != oid:
            holds.append({'artwork_id': aid, 'reason': 'source_object_url_identity_review', 'object_id': oid})
            continue
        evidence = {k: v for k, v in o.items() if not k.startswith('urlimg') and k not in ['nsc', 'deso', 'dess']}
        claims.append(p.claim(row, 'lombardia-object', oid, institutions[0], rc, url, evidence, v['identity_basis'] + '; current_exact_regional_object_id_and_collection_city_rechecked'))
    p.output('lombardia', claims, holds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['selection', 'capture', 'plan'])
    args = parser.parse_args()
    globals()[args.command](p.Index())
