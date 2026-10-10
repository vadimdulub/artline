#!/usr/bin/env python3
"""Match selected existing artworks to the museum's room and object catalogues."""
import argparse
import collections
import importlib.util
import re
import time
import uuid
from pathlib import Path
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('m', Path(__file__).with_name('research-artwork-location-bristol-glasgow-20261005c.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
r, p = m.r, m.p


def capture():
    selected = r.load(r.RUN / 'remaining-wikidata-groups-20261005c.json.gz')['Q7381305']
    by_title = collections.defaultdict(list)
    index = p.Index()
    for v in selected:
        row = index.by_id[v['artwork_id']]
        for k in ['title', 'alternate_title']:
            if row['artwork'].get(k):
                by_title[m.title_key(row['artwork'][k], [])].append(v)
    raw, rc = r.capture('https://russellcotes.com/online-collections/', tag='russell-cotes-collections-20261005c', timeout=40)
    assert rc['status'] == 200
    sp = BeautifulSoup(raw, 'html.parser')
    rooms = sorted({a['href'] for a in sp.select('a[href]') if re.fullmatch(r'https://russellcotes.com/collection/[^/]+/', a['href'])})
    assert 1 <= len(rooms) <= 25
    matches = collections.defaultdict(dict)
    for url in rooms:
        raw, receipt = r.capture(url, tag='russell-cotes-selected-rooms-20261005c', timeout=40)
        assert receipt['status'] == 200
        page = BeautifulSoup(raw, 'html.parser')
        for link in page.select('a[href]'):
            if re.fullmatch(r'https://russellcotes.com/collection-piece/[^/]+/', link['href']):
                title = link.get_text(' ', strip=True)
                for v in by_title.get(m.title_key(title, []), []):
                    matches[v['artwork_id']][link['href']] = {'selection': v, 'source_title': title, 'room_receipt': receipt, 'url': link['href']}
        time.sleep(.5)
    r.save_gz(r.RUN / 'russell-cotes-current-title-selection-20261005c.json.gz', {'room_index_receipt': rc, 'matched': dict(matches), 'selected_count': len(selected), 'room_count': len(rooms)})
    for n, (aid, group) in enumerate(matches.items(), 1):
        results = []
        for url, v in group.items():
            raw, receipt = r.capture(url, tag='russell-cotes-selected-objects-20261005c', timeout=40)
            assert receipt['status'] == 200
            page = BeautifulSoup(raw, 'html.parser')
            block = page.select_one('.collectionItemHeader')
            assert block is not None and block.find('h2') and block.find('p')
            obj = {'title': block.find('h2').get_text(' ', strip=True), 'label_lines': list(block.find('p').stripped_strings), 'url': url}
            results.append({'object': obj, 'source_receipt': receipt, 'selection': v})
            time.sleep(.5)
        r.save_gz(r.RUN / 'russell-cotes-selected-objects-20261005c' / (aid + '.json.gz'), {'artwork_id': aid, 'objects': results})
        if n % 20 == 0:
            print('Russell-Cotes selected current records', n, '/', len(matches), flush=True)
    r.save(r.RUN / 'russell-cotes-capture-complete-20261005c.json', {'at': r.now(), 'matched_existing_artworks': len(matches), 'selected_count': len(selected)})


def plan():
    assert (r.RUN / 'russell-cotes-capture-complete-20261005c.json').exists()
    index = p.Index()
    with r.connect('local') as db:
        matches = [v['i'] for v in db.execute("SELECT to_jsonb(i) i FROM institutions i WHERE wikidata_id='Q7381305'")]
    assert len(matches) <= 1
    name = 'Russell-Cotes Art Gallery & Museum'
    museum = matches[0] if matches else {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum-location/authority/Q7381305')), 'slug': 'museum-authority-q7381305', 'name': name, 'normalized_name': r.norm(name), 'kind': 'museum', 'status': 'review', 'wikidata_id': 'Q7381305', 'website_url': 'https://russellcotes.com/', 'description': 'Museum identity and selected holdings documented by the official collection pages. A room catalogue is not a fresh dated observation of public display.'}
    authority = r.load(r.RUN / 'remaining-museum-names-20261005c.json.gz')
    claims, holds = [], []
    for path in (r.RUN / 'russell-cotes-selected-objects-20261005c').glob('*.json.gz'):
        cap = r.load(path)
        row = index.by_id[cap['artwork_id']]
        found = []
        for entry in cap['objects']:
            obj, selected = entry['object'], entry['selection']['selection']
            lines = obj['label_lines']
            inventories = [v for v in lines if re.fullmatch(r':?BORGM[ :]+[A-Za-z0-9.]+', v)]
            if len(inventories) != 1 or len(lines) < 3:
                continue
            inventory = inventories[0]
            maker = re.sub(r'\s*\([^)]*\d{4}[^)]*\)\s*$', '', lines[1]).strip()
            title = obj['title']
            source_date = re.search(r'(?:,\s*|\()((?:c\.?\s*)?\d{4}(?:\s*[-–]\s*\d{4})?)\)?$', lines[0])
            dates = [source_date[1]] if source_date else []
            titles = [title]
            for local in [row['artwork'].get(k) for k in ['title', 'alternate_title'] if row['artwork'].get(k)]:
                if m.title_key(local, dates) == m.title_key(title, dates):
                    titles.append(local)
            basis = index.match(row, 'wikidata', selected['qid'], titles, [maker], inventory, dates)
            if not basis.startswith(('existing_', 'unique_')):
                continue
            flags = []
            date = row['artwork'].get('date_display')
            if not any(m.dn.equivalent(date, d) for d in dates):
                flags.append('date_meaning_unresolved')
            numbers = [n for n in m.h.statements(selected['entity'], 'P217') if isinstance(n, str)]
            if numbers and p.acckey(inventory) not in {p.acckey(n) for n in numbers}:
                flags.append('secondary_inventory_conflict')
            if re.search(r'\b(copy|after|attributed|probably|possibly|school|circle|loan|lent)\b', r.norm(' '.join(lines[:2]))):
                flags.append('attribution_or_custody_qualification')
            c = p.claim(row, 'russell-cotes-object', obj['url'].rstrip('/').rsplit('/', 1)[-1], museum, entry['source_receipt'], obj['url'],
                        {'current_museum_label': obj, 'selected_inventory': inventory, 'primary_date': dates, 'local_date': date, 'selection': selected, 'current_room_catalogue_receipt': entry['selection']['room_receipt'], 'museum_authority': {'entity': authority['entities']['Q7381305'], 'source_receipt': authority['receipt']}, 'qualifications': flags},
                        basis + '; specific museum object label, named artist and BORGM accession; no inferred on-view status')
            if flags:
                c['review_state'] = 'review'
                c['limitation'] = 'Official museum label candidate in review: ' + ', '.join(flags) + '. Source wording retained, with no original metadata, publication or current-display change.'
            found.append(c)
        if not found:
            holds.append({'artwork_id': cap['artwork_id'], 'reason': 'current_title_creator_inventory_not_reconciled', 'capture_path': str(path)})
        else:
            claims.extend(found)
    p.output('russell-cotes-20261005c', claims, holds)
    print('States', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan'])
    globals()[parser.parse_args().command]()
