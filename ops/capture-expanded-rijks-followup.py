#!/usr/bin/env python3
"""Capture bounded official metadata for previously unsearched named creators."""
import argparse
import collections
import concurrent.futures
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('capture', ROOT / 'ops/capture-expanded-rijks.py')
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def main(number, limit):
    src = ROOT / f'content/imports/expanded-round{number}-20260913'
    src.mkdir(parents=True, exist_ok=True)
    capture.SRC = src
    rows = json.loads((ROOT / f'docs/research/expanded-round{number}-20260913/unlinked.json').read_text())
    previously_searched = set()
    for path in (ROOT / 'content/imports').glob('expanded-round*-20260913/selection.json'):
        if path.parent == src:
            continue
        selection = json.loads(path.read_text())
        previously_searched.update(r['creator'] for r in selection if 'creator' in r)
    counts = collections.Counter(r['cells'][0] for r in rows if r['source'] is None and r['cells'][3] == 'Rijksmuseum')
    chosen = [(name, count) for name, count in counts.most_common() if name not in previously_searched][:limit]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        selection = list(pool.map(capture.search, chosen))
    (src / 'selection.json').write_text(json.dumps(selection, indent=2, ensure_ascii=False) + '\n')
    ids = sorted({uri for item in selection for uri in item['ids']})
    print(f'Selected {len(chosen)} new creator groups, {len(ids)} object identifiers', flush=True)

    def fetch_object(uri):
        key = uri.rsplit('/', 1)[1]
        return capture.fetch(f'https://data.rijksmuseum.nl/{key}?_profile=la-framed', f'object-{key}.json')

    people = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i, obj in enumerate(pool.map(fetch_object, ids), 1):
            for part in obj.get('produced_by', {}).get('part', []):
                people.update(a['id'] for a in part.get('carried_out_by', []) if a.get('type') == 'Person' and a.get('id', '').startswith('https://id.rijksmuseum.nl/'))
            if i % 100 == 0:
                print(f'Object metadata {i}/{len(ids)}', flush=True)

    def fetch_person(uri):
        key = uri.rsplit('/', 1)[1]
        return capture.fetch(f'https://data.rijksmuseum.nl/{key}?_profile=la-framed', f'person-{key}.json')

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch_person, sorted(people)))
    print(f'Capture complete: {len(ids)} objects, {len(people)} creator authorities; no images downloaded', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--round', type=int, required=True)
    parser.add_argument('--limit', type=int, default=80)
    args = parser.parse_args()
    assert 1 <= args.limit <= 100
    main(args.round, args.limit)
