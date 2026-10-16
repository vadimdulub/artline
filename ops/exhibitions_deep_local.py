#!/usr/bin/env python3
"""Bounded, resumable source research. Writes local evidence only; no DB mutations.

Selects historical-artist exhibitions from the existing canonical catalogue.
Completeness means all public provider-list entries, never a certified checklist.
"""
import argparse
import json
import time
from pathlib import Path

import exhibitions_common as c

DATA = Path.home() / 'Library/Application Support/Artline/source-metadata/exhibitions-deep-local-20261011'
FIELDS = '''internalID slug name startAt endAt status description pressRelease pressReleaseUrl
artists { internalID slug name birthday deathday nationality }
artistsWithoutArtworks { internalID slug name }
artworksConnection(first:100) { totalCount pageInfo { hasNextPage endCursor }
edges { node { internalID slug title date artistNames medium imageRights
image { url(version:"large") } artists { internalID slug name } } } }'''


def eligible(show):
    works = show.get('artworksConnection') or {}
    entries = [edge['node'] for edge in works.get('edges') or []]
    return (show.get('status') == 'closed' and len(entries) >= 3
            and len(entries) == works.get('totalCount')
            and len({e['internalID'] for e in entries}) == len(entries)
            and not (works.get('pageInfo') or {}).get('hasNextPage')
            and len((show.get('description') or show.get('pressRelease') or '').split()) >= 20
            and bool(show.get('artists')))


def collect(target):
    candidates = json.loads((DATA / 'candidates.json').read_text())
    accepted = []
    for start in range(0, len(candidates), 5):
        batch = candidates[start:start+5]
        missing = [r for r in batch if not (DATA/'shows'/f"{r['native']}.json").exists()]
        if missing:
            query = 'query ArtlineLocalDeepReview { ' + ' '.join(
                f's{i}: show(id:{json.dumps(r["native"])}) {{ {FIELDS} }}'
                for i, r in enumerate(missing)) + ' }'
            raw, receipt = c.capture('https://metaphysics-cdn.artsy.net/v2', {'query':query})
            response = json.loads(raw)
            for i, row in enumerate(missing):
                show = (response.get('data') or {}).get(f's{i}')
                errors = [e for e in response.get('errors',[]) if not e.get('path') or e['path'][0] == f's{i}']
                c.save(DATA/'shows'/f"{row['native']}.json", dict(candidate=row,show=show,errors=errors,receipt=receipt))
            time.sleep(.4)
        for row in batch:
            saved = c.load(DATA/'shows'/f"{row['native']}.json")
            if not saved['errors'] and saved['show'] and eligible(saved['show']):
                accepted.append(row['native'])
        print(json.dumps(dict(examined=start+len(batch),accepted=len(accepted))),flush=True)
        if len(accepted) >= target:
            break
    (DATA/'accepted.json').write_text(json.dumps(accepted[:target]))
    if len(accepted) < target:
        raise RuntimeError(f'Only {len(accepted)} complete public lists with source descriptions')


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--target',type=int,default=600)
    collect(p.parse_args().target)
