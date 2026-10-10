#!/usr/bin/env python3
"""Resolve only existing IWM candidates through exact public inventory searches."""
import argparse
import concurrent.futures
import importlib.util
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('m', Path(__file__).with_name('research-artwork-location-met-iwm-20261005c.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
r, p, h = m.r, m.p, m.h
FOLDER = r.RUN / 'iwm-inventory-resolution-20261005c'
COMPLETE = r.RUN / 'iwm-inventory-capture-complete-20261005c.json'


def selected():
    return r.load(r.RUN / 'remaining-wikidata-groups-20261005c.json.gz')['Q23315190']


def inventories(v):
    return sorted({x for x in h.statements(v['entity'], 'P217') if isinstance(x, str) and re.fullmatch(r'(?:Art\.)?IWM\s+ART\s+[\d.]+', x)})


def search_one(v):
    path = FOLDER / (v['artwork_id'] + '.json.gz')
    if path.exists():
        return
    numbers = inventories(v)
    result = {'selection': v, 'inventories': numbers, 'candidates': []}
    if len(numbers) != 1:
        result['reason'] = 'no_unique_art_inventory'
    else:
        raw, receipt = r.capture('https://www.iwm.org.uk/collections/search', {'query': numbers[0]}, tag='iwm-inventory-search-20261005c', timeout=45)
        result['search_receipt'] = receipt
        assert receipt['status'] == 200, receipt
        sp = BeautifulSoup(raw, 'html.parser')
        for card in sp.select('.teaser-list-collections__content-wrapper'):
            number = card.select_one('.teaser-list-collections__id-number')
            a = card.select_one('a[href^="/collections/item/object/"]')
            if number and a and m.inventory_key('iwm', number.get_text(' ', strip=True)) == m.inventory_key('iwm', numbers[0]):
                result['candidates'].append({'native_id': a['href'].rstrip('/').split('/')[-1], 'inventory': number.get_text(' ', strip=True), 'text': card.get_text(' ', strip=True)})
        if len({x['native_id'] for x in result['candidates']}) != 1:
            result['reason'] = 'no_unique_exact_inventory_result'
    r.save_gz(path, result)
    time.sleep(.5)


def combined():
    direct = {v['artwork_id']: v for v in m.selection('iwm')}
    for v in selected():
        if v['artwork_id'] in direct:
            continue
        path = FOLDER / (v['artwork_id'] + '.json.gz')
        if not path.exists():
            continue
        obj = r.load(path)
        if not obj.get('reason') and obj['candidates']:
            direct[v['artwork_id']] = {**v, 'native_id': obj['candidates'][0]['native_id'], 'inventory_resolution': obj}
    return list(direct.values())


def capture():
    direct = {v['artwork_id'] for v in m.selection('iwm')}
    values = [v for v in selected() if v['artwork_id'] not in direct]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, _ in enumerate(pool.map(search_one, values), 1):
            if n % 25 == 0:
                print('IWM selected inventory searches', n, '/', len(values), flush=True)
    values = combined()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, _ in enumerate(pool.map(m.capture_one, [('iwm', v) for v in values]), 1):
            if n % 25 == 0:
                print('IWM selected object records', n, '/', len(values), flush=True)
    artist_ids = sorted({a['id'] for v in values for a in h.statements(v['entity'], 'P170') if isinstance(a, dict) and a.get('id')})
    for start in range(0, len(artist_ids), 50):
        path = r.RUN / 'iwm-artist-authorities-20261005c' / (str(start) + '.json.gz')
        if not path.exists():
            entities, receipt = r.wiki_entities(artist_ids[start:start+50], tag='iwm-artist-authorities-20261005c')
            r.save_gz(path, {'entities': entities, 'receipt': receipt})
    r.save(COMPLETE, {'at': r.now(), 'original_candidates': len(selected()), 'resolved_objects': len(values)})


def plan(refined=False):
    assert COMPLETE.exists()
    values = combined()
    m.selection = lambda provider: values
    m.completion_file = lambda provider: COMPLETE
    m.plan('iwm', refined)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan', 'refine'])
    command = parser.parse_args().command
    plan(True) if command == 'refine' else globals()[command]()
