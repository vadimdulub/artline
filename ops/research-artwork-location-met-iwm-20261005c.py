#!/usr/bin/env python3
"""Read only selected existing artworks from two current museum catalogues."""
import argparse
import collections
import concurrent.futures
import importlib.util
import json
import re
import time
import uuid
from pathlib import Path
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('h', Path(__file__).with_name('research-artwork-location-hunterian-20261005c.py'))
h = importlib.util.module_from_spec(s)
s.loader.exec_module(h)
p, r = h.p, h.r
SETTINGS = {'met': ('Q160236', 'P3634'), 'iwm': ('Q23315190', None)}


def completion_file(provider):
    # Preserve the first zero-selection IWM discovery receipt.
    return r.RUN / (provider + '-capture-complete-' + ('20261005d' if provider == 'iwm' else '20261005c') + '.json')


def nested_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from nested_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from nested_strings(v)


def selection(provider):
    qid, prop = SETTINGS[provider]
    values = r.load(r.RUN / 'remaining-wikidata-groups-20261005c.json.gz').get(qid, [])
    result = []
    for v in values:
        ids = h.statements(v['entity'], prop) if prop else sorted({m[1] for text in nested_strings(v['entity']) if (m := re.fullmatch(r'https?://(?:www\.)?iwm\.org\.uk/collections/item/object/(\d+)/?', text))})
        if len(set(ids)) == 1 and re.fullmatch(r'\d+', str(ids[0])):
            result.append({**v, 'native_id': str(ids[0])})
    return result


def capture_one(job):
    provider, v = job
    oid = v['native_id']
    path = r.RUN / (provider + '-selected-objects-20261005c') / (oid + '.json.gz')
    if path.exists():
        return
    url = ('https://collectionapi.metmuseum.org/public/collection/v1/objects/' if provider == 'met' else 'https://www.iwm.org.uk/collections/item/object/') + oid
    raw, receipt = r.capture(url, tag=provider + '-selected-catalogue-20261005c', timeout=45)
    result = {'source_receipt': receipt}
    if receipt['status'] != 200:
        result['reason'] = 'source_http_' + str(receipt['status'])
    elif provider == 'met':
        obj = json.loads(raw)
        assert str(obj['objectID']) == oid
        result['object'] = {k: v for k, v in obj.items() if k not in ['primaryImage', 'primaryImageSmall', 'additionalImages']}
    else:
        sp = BeautifulSoup(raw, 'html.parser')
        fields = collections.defaultdict(list)
        for node in sp.select('dt'):
            value = node.find_next_sibling('dd')
            if value:
                fields[node.get_text(' ', strip=True)].append(value.get_text(' ', strip=True))
        if not sp.h1 or not fields.get('Catalogue number') or 'Imperial War Museums' not in sp.get_text(' ', strip=True):
            result['reason'] = 'museum_object_content_not_present'
        else:
            result['object'] = {'title': sp.h1.get_text(' ', strip=True), 'fields': dict(fields), 'url': url}
    r.save_gz(path, result)
    time.sleep(.4)


def capture(provider):
    values = selection(provider)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, _ in enumerate(pool.map(capture_one, [(provider, v) for v in values]), 1):
            if n % 50 == 0:
                print(provider, 'selected museum records', n, '/', len(values), flush=True)
    r.save(completion_file(provider), {'at': r.now(), 'selected': len(values)})


def inventory_key(provider, value):
    value = value or ''
    if provider == 'iwm':
        value = re.sub(r'^Art\.', '', value)
    return p.acckey(value)


def iwm_titlekey(value, dates=()):
    text = value or ''
    # Art UK adds sitter lifespan annotations to titles in the supplied data.
    # Object inventory and named creator must still match the museum record.
    text = re.sub(r'\s*\(\d{4}\s*[–-]\s*\d{4}\)', '', text)
    for date in dates:
        if re.fullmatch(r'\d{4}', date or ''):
            text = re.sub(r',?\s+' + re.escape(date) + r'\s*$', '', text)
    return re.sub(r'[^\w]', '', r.norm(text))


def plan(provider, refined=False):
    assert completion_file(provider).exists()
    index = p.Index()
    with r.connect('local') as db:
        museums = [v['i'] for v in db.execute('SELECT to_jsonb(i) i FROM institutions i WHERE wikidata_id=%s OR slug=%s', (SETTINGS[provider][0], 'the-met' if provider == 'met' else 'imperial-war-museums')).fetchall()]
    museum_authority = None
    if provider == 'iwm':
        museum_authority = r.load(r.RUN / 'iwm-museum-authority-20261005c.json')
        assert museum_authority['museum_receipt']['status'] == 200
        assert museum_authority['entities']['Q23315190']['labels']['en']['value'] == 'Imperial War Museums'
        assert "IWM’s collection" in museum_authority['museum_text']
        if not museums:
            museums = [{'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum-location/authority/Q23315190')),
                'slug': 'imperial-war-museums', 'name': 'Imperial War Museums',
                'normalized_name': 'imperial war museums', 'wikidata_id': 'Q23315190',
                'website_url': 'https://www.iwm.org.uk/collections', 'kind': 'museum', 'status': 'review',
                'description': 'Imperial War Museums collection authority. A holding does not assign an artwork to IWM London, IWM North or any specific branch, and does not establish current display.'}]
    assert len(museums) == 1, museums
    museum = museums[0]
    claims, holds = [], []
    authorities = {}
    if provider == 'iwm':
        for path in (r.RUN / 'iwm-artist-authorities-20261005c').glob('*.json.gz'):
            batch = r.load(path)
            for qid, entity in batch['entities'].items():
                names = [x['value'] for x in entity.get('labels', {}).values()] + [x['value'] for group in entity.get('aliases', {}).values() for x in group]
                authorities[qid] = {'names': names, 'source_receipt': batch['receipt']}
    for v in selection(provider):
        row = index.by_id[v['artwork_id']]
        captured = r.load(r.RUN / (provider + '-selected-objects-20261005c') / (v['native_id'] + '.json.gz'))
        obj = captured.get('object')
        if not obj:
            holds.append({'artwork_id': v['artwork_id'], **captured})
            continue
        flags, proofs = [], []
        if provider == 'met':
            titles, makers, inventory, dates = [obj['title']], [obj['artistDisplayName']], obj['accessionNumber'], [obj.get('objectDate', '')]
            url = obj.get('objectURL') or 'https://www.metmuseum.org/art/collection/search/' + v['native_id']
            if re.search(r'\b(after|attributed|school|circle|workshop|style|copy|follower)\b', r.norm(' '.join(obj.get(k, '') or '' for k in ['artistRole', 'artistPrefix', 'artistDisplayName']))):
                flags.append('qualified_creator')
            if re.search(r'\b(loan|lent|deaccession|returned)\b', r.norm(obj.get('creditLine', ''))):
                flags.append('custody_qualification')
        else:
            f = obj['fields']
            titles, makers, dates = [obj['title']], f.get('Creator', []), f.get('Production date', [])
            inventory = f['Catalogue number'][0]
            url = obj['url']
            if re.search(r'\b(attributed|after|school|circle|workshop|copy)\b', r.norm(' '.join(makers))):
                flags.append('qualified_creator')
            for artist in h.statements(v['entity'], 'P170'):
                auth = authorities.get(artist.get('id')) if isinstance(artist, dict) else None
                if auth and {r.namekey(n) for n in makers} & {r.namekey(n) for n in auth['names']}:
                    makers += auth['names']
                    proofs.append({'artist_qid': artist['id'], **auth})
            source_inventories = h.statements(v['entity'], 'P217')
            if source_inventories and inventory_key(provider, inventory) not in {inventory_key(provider, n) for n in source_inventories if isinstance(n, str)}:
                flags.append('secondary_inventory_changed')
        titles += [h.unquote_title(t) for t in titles]
        makers += [re.sub(r'\b(Sir|Dame|Lord)\s+', '', m) for m in makers]
        if provider == 'iwm' and refined:
            local_titles = [row['artwork'].get(k) for k in ['title', 'alternate_title'] if row['artwork'].get(k)]
            for title in local_titles:
                if iwm_titlekey(title, dates) in {iwm_titlekey(t, dates) for t in titles}:
                    proofs.append({'title_format_comparison': [title, titles[0]], 'normalization': 'Punctuation, sitter lifespan annotation, and explicitly recorded creation year suffix only; inventory and creator remain mandatory.'})
                    titles.append(title)
        local_inv = row['artwork'].get('accession_number')
        comparison_inv = local_inv if local_inv and inventory_key(provider, local_inv) == inventory_key(provider, inventory) else inventory
        basis = index.match(row, 'wikidata', v['qid'], titles, makers, comparison_inv, dates)
        if not basis.startswith(('existing_', 'unique_')):
            holds.append({'artwork_id': v['artwork_id'], 'reason': basis, 'source_url': url, 'source_receipt': captured['source_receipt']})
            continue
        date = row['artwork'].get('date_display')
        if date and p.datekey(date) not in {p.datekey(d) for d in dates}:
            flags.append('date_wording_differs')
        c = p.claim(row, provider + '-object', v['native_id'], museum, captured['source_receipt'], url,
                    {'current_museum_record': obj, 'identity_selection': v, 'qualifications': flags, 'inventory_format_comparison': [local_inv, inventory], 'creator_authority_proofs': proofs},
                    basis + '; exact selected museum native ID and current catalogue metadata')
        if museum_authority:
            c['object_evidence']['museum_collection_service_authority'] = museum_authority
        if provider == 'met':
            c['duplicate_source_urls'] = ['https://www.metmuseum.org/art/collection/search/' + v['native_id'], 'http://www.metmuseum.org/art/collection/search/' + v['native_id']]
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Current museum candidate in review: ' + ', '.join(flags) + '. No changed date, attribution or current display assertion.'
        claims.append(c)
    p.output(provider + ('-refined' if refined else '') + '-20261005c', claims, holds)
    print('States', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan'])
    parser.add_argument('provider', choices=list(SETTINGS))
    args = parser.parse_args()
    globals()[args.command](args.provider)
