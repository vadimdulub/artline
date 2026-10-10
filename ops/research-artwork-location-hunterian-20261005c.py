#!/usr/bin/env python3
"""Selected Hunterian catalogue metadata only; no image retrieval."""
import argparse
import collections
import concurrent.futures
import copy
import importlib.util
import json
import re
import time
from pathlib import Path
from urllib.parse import unquote

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r
BASE = 'https://frontdoor.spa.gla.ac.uk/gdc'
FOLDER = r.RUN / 'hunterian-objects-20261005c'


def unquote_title(value):
    text = (value or '').strip()
    if len(text) > 1 and (text[0], text[-1]) in [('"', '"'), ('“', '”')]:
        return text[1:-1].strip()
    return text


def statements(entity, prop):
    return [v['mainsnak']['datavalue']['value'] for v in entity.get('claims', {}).get(prop, []) if v.get('rank') != 'deprecated' and not v.get('qualifiers', {}).get('P582') and 'datavalue' in v['mainsnak']]


def selection():
    values = r.load(r.RUN / 'remaining-wikidata-groups-20261005c.json.gz')['Q1465387']
    for v in values:
        inventories = set(statements(v['entity'], 'P217'))
        for url in statements(v['entity'], 'P973'):
            inventories.update(re.findall(r'GLAHA[:\s]?(\d+)', unquote(url)))
        v['inventory_numbers'] = sorted({re.sub(r'\D', '', x) for x in inventories if re.search(r'\d', x)})
    return values


def fetch(url, params=None):
    for attempt in range(3):
        try:
            raw, receipt = r.capture(url, params, tag='hunterian-catalogue-20261005c' + ('-retry' + str(attempt) if attempt else ''), timeout=40)
            assert receipt['status'] == 200, str(receipt)
            return json.loads(raw), receipt
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 + attempt)


def capture_one(value):
    path = FOLDER / (value['artwork_id'] + '.json.gz')
    if path.exists():
        return
    numbers = value['inventory_numbers']
    query = 'GLAHA:' + numbers[0] if len(numbers) == 1 else value['title']
    rows, receipt = fetch(BASE + '/search/advanced', {'advancedText': query, 'startingRecord': 0, 'collection': 'Art'})
    assert isinstance(rows, list)
    candidates = [v for v in rows if v.get('catType') == 'C' and v.get('collection') == 'Art' and
                  ((numbers and re.sub(r'\D', '', v.get('objectNumber') or '') in numbers) or p.titlekey(unquote_title(v.get('title'))) == p.titlekey(unquote_title(value['title'])))]
    result = {'artwork_id': value['artwork_id'], 'query': query, 'search_receipt': receipt,
              'result_count': rows[0]['counter'] if rows else 0, 'returned_count': len(rows), 'objects': []}
    if len(candidates) <= 5:
        for v in candidates:
            try:
                obj, rc = fetch(BASE + '/manifest/C/' + str(v['irn']))
            except Exception as exc:
                result.setdefault('object_errors', []).append({'object_id': str(v['irn']), 'reason': str(exc)[:1800]})
                continue
            fields = {x['label']: x['value'] for x in obj['metadata']}
            assert fields.get('Department') == 'Hunterian' and fields.get('Collection') == 'Art'
            assert obj['@id'] == BASE + '/manifest/C/' + str(v['irn'])
            result['objects'].append({'object_id': str(v['irn']), 'fields': fields, 'source_receipt': rc})
            time.sleep(.2)
    else:
        result['reason'] = 'too_many_title_candidates'
    r.save_gz(path, result)
    time.sleep(.3)


def capture():
    values = selection()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, _ in enumerate(pool.map(capture_one, values), 1):
            if n % 50 == 0:
                print('Hunterian selected searches', n, '/', len(values), flush=True)
    r.save(r.RUN / 'hunterian-capture-complete-20261005c.json', {'at': r.now(), 'selected': len(values)})


def plan(refined=False):
    assert (r.RUN / 'hunterian-capture-complete-20261005c.json').exists()
    index = p.Index()
    museum = next(x['v'] for x in r.load(r.RUN / 'glasgow-kunstsammlung-institution-check-20261005c.json') if x['v'].get('wikidata_id') == 'Q1465387')
    claims, holds = [], []
    authorities = {}
    if refined:
        for path in (r.RUN / 'hunterian-artist-authorities-20261005c').glob('*.json.gz'):
            batch = r.load(path)
            for qid, entity in batch['entities'].items():
                names = [x['value'] for x in entity.get('labels', {}).values()] + [x['value'] for values in entity.get('aliases', {}).values() for x in values]
                authorities[qid] = {'names': names, 'source_receipt': batch['receipt']}
    for value in selection():
        row = index.by_id[value['artwork_id']]
        captured = r.load(FOLDER / (value['artwork_id'] + '.json.gz'))
        found = []
        for obj in captured['objects']:
            f = obj['fields']
            makers = [re.split(r';|\bCreated by\b', x)[0].strip() for x in f.get('Producers', '').split('|')]
            titles = [f.get('Title', '')]
            proofs = []
            inventory_for_match = f.get('Object Number')
            if refined:
                titles += [unquote_title(t) for t in titles]
                makers += [re.sub(r'\b(Sir|Dame|Lord)\s+', '', n) for n in makers]
                for artist in statements(value['entity'], 'P170'):
                    auth = authorities.get(artist.get('id')) if isinstance(artist, dict) else None
                    if auth and {r.namekey(n) for n in makers} & {r.namekey(n) for n in auth['names']}:
                        makers += auth['names']
                        proofs.append({'artist_qid': artist['id'], **auth})
                local_inventory = row['artwork'].get('accession_number') or ''
                if re.fullmatch(r'GLAHA_\d+', local_inventory) and local_inventory.replace('_', ':') == inventory_for_match:
                    inventory_for_match = local_inventory
                    proofs.append({'inventory_format_alias': [local_inventory, f.get('Object Number')]})
            basis = index.match(row, 'wikidata', value['qid'], titles, makers, inventory_for_match, [f.get('Production Dates', '')])
            if not basis.startswith(('existing_', 'unique_')):
                continue
            flags = []
            if captured['result_count'] > captured['returned_count'] and not value['inventory_numbers']:
                flags.append('title_search_not_exhausted')
            text = ' '.join(f.get(k, '') for k in ['Producers', 'Description', 'Acquisition', 'Provenance'])
            if re.search(r'\b(after|attributed|school of|copy of|copy after|circle of|workshop|collaboration|loan|lent|deaccession|stolen|lost)\b', r.norm(text)):
                flags.append('attribution_or_custody_qualification')
            date = row['artwork'].get('date_display')
            source_date = f.get('Production Dates', '')
            if refined and (match := re.fullmatch(r'(\d{4})\s*-\s*\1', source_date)):
                source_date = match[1]
            if date and p.datekey(date) != p.datekey(source_date):
                flags.append('creation_date_wording_differs')
            inventory = re.sub(r'\D', '', f.get('Object Number', ''))
            if value['inventory_numbers'] and inventory not in value['inventory_numbers']:
                flags.append('secondary_inventory_changed')
            c = p.claim(row, 'hunterian-object', obj['object_id'], museum, obj['source_receipt'],
                        'https://www.gla.ac.uk/collections/#/details?catType=C&irn=' + obj['object_id'],
                        {'catalogue_metadata': f, 'identity_selection': value, 'search_receipt': captured['search_receipt'], 'qualifications': flags, 'format_and_creator_authority_proofs': proofs},
                        basis + '; current Hunterian department and Art collection; exact title, named creator and inventory checks')
            c['duplicate_source_urls'] = statements(value['entity'], 'P973') + [obj['source_receipt']['url']]
            if flags:
                c['review_state'] = 'review'
                c['limitation'] = 'Primary museum candidate in review: ' + ', '.join(flags) + '. No new attribution, date or current display asserted.'
            found.append(c)
        if found:
            claims.extend(found)
        else:
            holds.append({'artwork_id': value['artwork_id'], 'reason': 'primary_object_identity_not_reconciled', 'capture_path': str(FOLDER / (value['artwork_id'] + '.json.gz'))})
    p.output('hunterian-refined-20261005c' if refined else 'hunterian-20261005c', claims, holds)
    print('States', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


def refine():
    global FOLDER
    old_folder = FOLDER
    FOLDER = r.RUN / 'hunterian-objects-refined-20261005c'
    for value in selection():
        old = r.load(old_folder / (value['artwork_id'] + '.json.gz'))
        if old['objects']:
            r.save_gz(FOLDER / (value['artwork_id'] + '.json.gz'), old)
        else:
            capture_one(value)
    plan(refined=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan', 'refine'])
    globals()[parser.parse_args().command]()
