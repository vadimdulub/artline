#!/usr/bin/env python3
"""Bounded exact-title searches and selected object metadata; no images or writes."""
import concurrent.futures
import importlib.util
import json
from pathlib import Path
import time

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def main():
    rows = [x for x in r.load(r.RUN / 'remaining-snapshot-20261005b.json.gz')
            if any(c[3] == 'Rijksmuseum' for c in x['supplied'] or [])]

    def one(row):
        dest = r.RUN / 'rijks-discovery-20261005b' / (row['artwork']['id'] + '.json.gz')
        if dest.exists():
            return r.load(dest).get('reason')
        result = {'artwork_id': row['artwork']['id'], 'objects': []}
        try:
            ids = {e['external_id'] for e in row['identifiers'] if e['scheme'] == 'rijks-object'}
            if not ids:
                cells = next(c for c in row['supplied'] if c[3] == 'Rijksmuseum')
                raw, rc = r.capture('https://data.rijksmuseum.nl/search/collection',
                                    {'title': cells[1], 'creator': cells[0]},
                                    tag='rijks-discovery-20261005b', timeout=35)
                result['search_receipt'] = rc
                assert rc['status'] == 200, 'search_http_' + str(rc['status'])
                data = json.loads(raw)
                total = data['partOf']['totalItems']
                result['total'] = total
                assert total <= 20 and not data.get('next'), 'search_not_bounded'
                ids = {v['id'].removeprefix('https://id.rijksmuseum.nl/') for v in data.get('orderedItems', [])}
                assert len(ids) == total, 'search_incomplete'
            assert len(ids) <= 20 and all(v.isdigit() for v in ids), 'unexpected_native_ids'
            for oid in sorted(ids):
                raw, rc = r.capture('https://data.rijksmuseum.nl/' + oid, {'_profile': 'la-framed'}, tag='rijks-discovery-20261005b', timeout=35)
                record = {'id': oid, 'source_receipt': rc}
                if rc['status'] == 200:
                    obj = json.loads(raw)
                    assert obj['id'] == 'https://id.rijksmuseum.nl/' + oid, 'object_id_mismatch'
                    record['object'] = obj
                    # EDM proves the actual collection provider for selected exact titles.
                    titles = {p.titlekey(v.get('content')) for v in obj.get('identified_by', []) if v.get('type') == 'Name'}
                    if p.titlekey(row['artwork']['title']) in titles:
                        _, edm = r.capture('https://data.rijksmuseum.nl/' + oid, {'_profile': 'edm'}, tag='rijks-discovery-20261005b', timeout=35)
                        record['provider_receipt'] = edm
                result['objects'].append(record)
            result['reason'] = 'captured' if ids else 'no_search_result'
        except Exception as exc:
            result['reason'] = str(exc)[:300]
        r.save_gz(dest, result)
        time.sleep(0.5)
        return result['reason']

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for n, reason in enumerate(pool.map(one, rows), 1):
            if n % 100 == 0:
                print('Rijks remaining identities searched', n, '/', len(rows), flush=True)


if __name__ == '__main__':
    main()
