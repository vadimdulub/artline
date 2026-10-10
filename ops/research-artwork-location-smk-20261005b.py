#!/usr/bin/env python3
"""Search current SMK Danish titles for already selected unresolved records."""
import argparse
import collections
import concurrent.futures
import importlib.util
import json
from pathlib import Path
import re
import time

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def selected():
    return [v for v in r.load(r.RUN / 'remaining-snapshot-20261005c.json.gz') if any(c[3] == 'Statens Museum for Kunst (SMK)' for c in v['supplied'] or [])]


def capture_title(title):
    path = r.RUN / 'smk-titles-20261005b' / (r.sha(title.encode()) + '.json.gz')
    if path.exists():
        return
    items, receipts, total = [], [], None
    for page in range(3):
        for attempt in range(3):
            try:
                raw, receipt = r.capture('https://api.smk.dk/api/v1/art/search', {'keys': json.dumps(title, ensure_ascii=False), 'qfields': 'titles', 'lang': 'da', 'rows': 100, 'offset': page * 100}, tag='smk-current-title-20261005b' + (('-retry' + str(attempt)) if attempt else ''), timeout=45)
                assert receipt['status'] == 200
                data = json.loads(raw)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(5 * (attempt + 1))
        receipts.append(receipt)
        total = data['found'] if total is None else total
        assert total == data['found']
        if total > 100:
            r.save_gz(path, {'title': title, 'items': [], 'source_receipts': receipts, 'reason': 'title_search_requires_further_scope', 'total': total})
            return
        items.extend(data['items'])
        assert len(items) == total
        break
    r.save_gz(path, {'title': title, 'items': items, 'source_receipts': receipts, 'total': total})
    time.sleep(0.4)


def capture():
    titles = sorted({v['artwork']['title'] for v in selected()})
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, _ in enumerate(pool.map(capture_title, titles), 1):
            if n % 50 == 0:
                print('SMK current titles', n, '/', len(titles), flush=True)
    r.save(r.RUN / 'smk-capture-complete-20261005b.json', {'at': r.now(), 'titles': len(titles)})


def maker_labels(maker):
    names = {maker.get('creator') or '', ' '.join(filter(None, [maker.get('creator_forename'), maker.get('creator_surname')]))}
    for qualifier in [maker.get('creator_qualifier'), maker.get('creator_role')]:
        if qualifier:
            names.update(n + ' (' + qualifier + ')' for n in list(names) if n)
    return {n for n in names if n}


def plan(rows=None, captured_for=None, provider='smk-current-20261005b'):
    assert (r.RUN / 'smk-capture-complete-20261005b.json').exists()
    index = p.Index()
    museum = index.institution('statens-museum-for-kunst')
    claims, holds = [], []
    for row in selected() if rows is None else rows:
        aid, title = row['artwork']['id'], row['artwork']['title']
        captured = captured_for(row) if captured_for else r.load(r.RUN / 'smk-titles-20261005b' / (r.sha(title.encode()) + '.json.gz'))
        found = {}
        for obj in captured['items']:
            names = set().union(*(maker_labels(m) for m in obj.get('production', [])))
            basis = index.match(row, 'smk-object', obj['object_number'], [v['title'] for v in obj.get('titles', []) if v.get('title')], names, obj['object_number'], [v.get('period') for v in obj.get('production_date', [])])
            if basis.startswith(('existing_', 'unique_')):
                found[obj['object_number']] = (obj, basis)
        if len(found) != 1:
            holds.append({'artwork_id': aid, 'reason': 'multiple_exact_source_objects' if found else captured.get('reason', 'no_exact_current_identity'), 'source_object_ids': sorted(found), 'source_receipts': captured['source_receipts']})
            continue
        obj, basis = next(iter(found.values()))
        flags = []
        makers = obj.get('production', [])
        if len(makers) != 1 or any(m.get('creator_role') or m.get('creator_qualifier') for m in makers):
            flags.append('qualified_or_multiple_creator_relationships')
        if not obj.get('acquisition_date') or obj.get('deaccession_date'):
            flags.append('accession_status_requires_review')
        custody = json.dumps({k:obj.get(k) for k in ['acquisition_information', 'current_location', 'current_location_name', 'credit_line', 'work_status']}, ensure_ascii=False)
        if re.search(r'\b(udlant|udlaant|deponeret|bortkommet|forsvundet|brændt|braendt|tilbageleveret|deaccession|loan|lent|returned|lost|destroyed|stolen)\b', r.norm(custody)):
            flags.append('custody_or_object_status_requires_review')
        if obj.get('part_of'):
            flags.append('component_identity_requires_review')
        evidence = {'object': {k:v for k,v in obj.items() if not re.search(r'image|iiif|thumbnail|3d', k, re.I)}, 'qualifications': flags}
        c = p.claim(row, 'smk-object', obj['object_number'], museum, captured['source_receipts'][0], obj['frontend_url'], evidence, basis + '; current Danish-language museum record and exact inventory')
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Official museum candidate retained in review: ' + ', '.join(flags) + '. No current display or physical presence asserted.'
        claims.append(c)
    p.output(provider, claims, holds)
    print('Claim states', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan'])
    globals()[parser.parse_args().command]()
