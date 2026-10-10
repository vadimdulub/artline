#!/usr/bin/env python3
"""Resolve selected Joconde candidates using the Louvre's public JSON records."""
import argparse
import collections
import concurrent.futures
import copy
import importlib.util
import json
import re
import time
from pathlib import Path

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r
FOLDER = r.RUN / 'louvre-objects-20261005c'


def selection():
    return r.load(r.RUN / 'louvre-selected-candidates-20261005c.json.gz')


def crosswalk():
    values = sorted({c['external_id'] for c in selection()})
    for start in range(0, len(values), 50):
        path = r.RUN / 'louvre-joconde-crosswalk-20261005c' / (str(start) + '.json.gz')
        if path.exists():
            continue
        query = 'SELECT ?item ?joconde ?ark WHERE { VALUES ?joconde { ' + ' '.join(json.dumps(v) for v in values[start:start+50]) + ' } ?item wdt:P347 ?joconde . OPTIONAL { ?item wdt:P9394 ?ark } }'
        raw, receipt = r.capture('https://query.wikidata.org/sparql', {'query': query, 'format': 'json'}, tag='louvre-joconde-crosswalk-20261005c', timeout=70)
        assert receipt['status'] == 200, receipt['status']
        data = json.loads(raw)['results']['bindings']
        r.save_gz(path, {'receipt': receipt, 'data': [{k: v['value'] for k, v in row.items()} for row in data]})
        print('Selected Louvre crosswalk', min(start + 50, len(values)), '/', len(values), flush=True)
        time.sleep(1)


def mapped():
    result = collections.defaultdict(list)
    for path in (r.RUN / 'louvre-joconde-crosswalk-20261005c').glob('*.json.gz'):
        batch = r.load(path)
        for value in batch['data']:
            if value.get('ark') and re.fullmatch(r'\d{9}', value['ark']):
                result[value['joconde']].append({**value, 'source_receipt': batch['receipt']})
    return result


def capture_one(ark):
    path = FOLDER / (ark + '.json.gz')
    if path.exists():
        return
    url = 'https://collections.louvre.fr/en/ark:/53355/cl' + ark + '.json'
    raw, receipt = r.capture(url, tag='louvre-selected-json-20261005c', timeout=45)
    if receipt['status'] == 404:
        r.save_gz(path, {'reason': 'current_primary_record_not_found', 'source_receipt': receipt})
        return
    # Do not retry or evade an anti-bot response.
    assert receipt['status'] == 200, str(receipt)
    obj = json.loads(raw)
    assert obj['arkId'] == 'cl' + ark and obj['url'] == 'https://collections.louvre.fr/ark:/53355/cl' + ark
    r.save_gz(path, {'object': {k: v for k, v in obj.items() if k not in ['image', 'images']}, 'source_receipt': receipt})
    time.sleep(.5)


def capture():
    crosswalk()
    ids = sorted({v['ark'] for group in mapped().values() for v in group})
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, _ in enumerate(pool.map(capture_one, ids), 1):
            if n % 100 == 0:
                print('Louvre selected records', n, '/', len(ids), flush=True)
    r.save(r.RUN / 'louvre-capture-complete-20261005c.json', {'at': r.now(), 'objects': len(ids)})


def title_variants(value, refined=False):
    values = {p.titlekey(re.sub(r'\s*\((?:ancien titre|titre attribué|titre principal|traduction)\)\s*$', '', s, flags=re.I)) for s in (value or '').split(';')}
    # The Louvre systematically punctuates titles with a final full stop.
    # Preserve every word, date, numeral and internal punctuation mark.
    return {v.rstrip('.').strip() for v in values} if refined else values


def plan(refined=False):
    assert (r.RUN / 'louvre-capture-complete-20261005c.json').exists()
    index = p.Index()
    mapping = mapped()
    claims, holds = [], []
    for old in selection():
        aid = old['artwork_id']
        row = index.by_id[aid]
        matches = mapping.get(old['external_id'], [])
        if len({v['ark'] for v in matches}) != 1:
            holds.append({'artwork_id': aid, 'reason': 'no_unique_primary_ark_crosswalk'})
            continue
        match = matches[0]
        captured = r.load(FOLDER / (match['ark'] + '.json.gz'))
        if not captured.get('object'):
            holds.append({'artwork_id': aid, **captured})
            continue
        obj = captured['object']
        inventories = {p.acckey(v['value']) for v in obj.get('objectNumber', [])}
        prior_inventory = {p.acckey(v.strip()) for v in (old['object_evidence'].get('Numero_inventaire') or '').split(';')}
        if not inventories & prior_inventory:
            holds.append({'artwork_id': aid, 'reason': 'current_inventory_conflict', 'source_receipt': captured['source_receipt']})
            continue
        titles = set().union(*(title_variants(t, refined) for t in [obj.get('title', ''), *[x['value'] for x in obj.get('denominationTitle', [])]]))
        local_titles = title_variants(row['artwork']['title'], refined)
        if refined and row['artwork'].get('alternate_title'):
            local_titles |= title_variants(row['artwork']['alternate_title'], refined)
        if not local_titles & titles:
            holds.append({'artwork_id': aid, 'reason': 'current_title_not_reconciled', 'source_receipt': captured['source_receipt']})
            continue
        local_names = {r.namekey(v['name']) for v in row['artists']} | {r.namekey(c[0]) for c in row['supplied'] or []}
        if row['artwork'].get('unlinked_creator_label'):
            local_names.add(r.namekey(row['artwork']['unlinked_creator_label']))
        current = [v for v in obj.get('creator', []) if v.get('attributionLevel') == 'Attribution actuelle' and r.namekey(v['label']) in local_names]
        if not current:
            holds.append({'artwork_id': aid, 'reason': 'current_artist_not_reconciled', 'source_receipt': captured['source_receipt']})
            continue
        flags = []
        if any(v.get(k) for v in current for k in ['linkType', 'authenticationType', 'doubt']):
            flags.append('qualified_current_attribution')
        if obj.get('heldBy') != 'Musée du Louvre, Département des Peintures':
            flags.append('current_keeper_changed')
        if obj.get('isMuseesNationauxRecuperation') or obj.get('longTermLoanTo') or obj.get('ownedBy') != 'Etat':
            flags.append('ownership_or_long_term_loan_qualification')
        if re.search(r'\b(disparu|manquant|vole|restitue|detrui\w*)\b', r.norm(obj.get('currentLocation', ''))):
            flags.append('current_location_status_requires_review')
        if refined and not (r.norm(obj.get('currentLocation', '')) == 'non expose' or obj.get('currentLocation', '').startswith(('Sully,', 'Denon,', 'Richelieu,', 'Louvre-Lens,'))):
            flags.append('external_or_unresolved_current_location')
        a = row['artwork']
        years = [int(v[k]) for v in obj.get('dateCreated', []) for k in ['startYear', 'endYear'] if str(v.get(k, '')).isdigit()]
        if years and a.get('creation_year_start') and a.get('creation_year_end') and (max(years) < a['creation_year_start'] or min(years) > a['creation_year_end']):
            flags.append('creation_date_conflict')
        evidence = {'current_louvre_record': obj, 'prior_joconde_candidate': old, 'external_identifier_crosswalk': match,
                    'qualifications': flags, 'bibliography_limitation': 'Bibliography references are supplied by the Louvre record; the referenced books were not all independently opened.',
                    'location_limitation': 'The museum warns that rooms and catalogue content may lag collection changes. No current display observation is created.'}
        c = p.claim(row, 'louvre-object', 'cl' + match['ark'], old['institution'], captured['source_receipt'], obj['url'], evidence,
                    'Exact Joconde crosswalk, current Louvre inventory, title and current artist attribution; heldBy and ownership fields checked')
        c['duplicate_source_urls'] = [obj['url'].replace('/ark:', '/en/ark:'), old['source_url']]
        c['duplicate_native_ids'] = [match['ark']]
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Current Louvre candidate remains review: ' + ', '.join(flags) + '. Previous evidence and original metadata retained.'
        claims.append(c)
    p.output(('louvre-refined' if refined else 'louvre') + '-20261005c', claims, holds)
    print('States', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan', 'refine'])
    command = parser.parse_args().command
    plan(True) if command == 'refine' else globals()[command]()
