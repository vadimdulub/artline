#!/usr/bin/env python3
"""Narrow ambiguous common SMK titles by the supplied creator, then verify identity."""
import argparse
import concurrent.futures
import importlib.util
import json
from pathlib import Path
import re
import time

s = importlib.util.spec_from_file_location('smk', Path(__file__).with_name('research-artwork-location-smk-20261005b.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
r = m.r
FOLDER = r.RUN / 'smk-creator-titles-20261005b'


def selected():
    ids = {v['artwork_id'] for v in r.load(r.RUN / 'primary-plans/smk-current-20261005b.json.gz')['holds'] if v['reason'] == 'title_search_requires_further_scope'}
    return [v for v in m.selected() if v['artwork']['id'] in ids]


def capture_one(row):
    path = FOLDER / (row['artwork']['id'] + '.json.gz')
    if path.exists():
        return
    title = row['artwork']['title']
    # Query simplification only. Exact identity checking retains qualifications.
    creators = sorted({re.sub(r'\s*\([^()]*\)\s*$', '', c[0]).strip() for c in row['supplied'] or []})
    objects, receipts, too_broad = {}, [], False
    for creator in creators:
        params = {'keys': json.dumps(title, ensure_ascii=False), 'qfields': 'titles', 'filters': '[creator:' + creator + ']', 'lang': 'da', 'rows': 100, 'offset': 0}
        for attempt in range(3):
            try:
                raw, receipt = r.capture('https://api.smk.dk/api/v1/art/search', params, tag='smk-creator-refinement-20261005b' + ('-retry' + str(attempt) if attempt else ''), timeout=45)
                assert receipt['status'] == 200
                data = json.loads(raw)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(5 * (attempt + 1))
        receipts.append(receipt)
        if data['found'] > 100:
            too_broad = True
        else:
            assert len(data['items']) == data['found']
            for obj in data['items']:
                objects[obj['object_number']] = obj
        time.sleep(0.4)
    value = {'title': title, 'creator_queries': creators, 'items': [] if too_broad else list(objects.values()), 'source_receipts': receipts, 'total': len(objects)}
    if too_broad:
        value['reason'] = 'title_creator_search_requires_further_scope'
    r.save_gz(path, value)


def capture():
    rows = selected()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, _ in enumerate(pool.map(capture_one, rows), 1):
            if n % 25 == 0:
                print('SMK narrow searches', n, '/', len(rows), flush=True)
    r.save(r.RUN / 'smk-refinement-complete-20261005b.json', {'at': r.now(), 'artworks': len(rows)})


def plan():
    assert (r.RUN / 'smk-refinement-complete-20261005b.json').exists()
    m.plan(selected(), lambda row: r.load(FOLDER / (row['artwork']['id'] + '.json.gz')), 'smk-refined-20261005b')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan'])
    globals()[parser.parse_args().command]()
