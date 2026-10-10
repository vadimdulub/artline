#!/usr/bin/env python3
"""Read-only verification of every new relationship through the public API."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import json
from pathlib import Path
import time
import requests

spec = importlib.util.spec_from_file_location('round2', Path(__file__).with_name('apply-painter-influences-round2-20261008.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
p, digest = m.checked(m.PLAN)
artists = {v['id']: v for v in p['before']['artists']}
by_target = m.defaultdict(list)
for v in p['inserts']['influence_claims']:
    by_target[v['target_artist_id']].append(v)
by_claim = m.defaultdict(set)
for v in p['inserts']['citations']:
    by_claim[v['entity_id']].add(v['source_url'])


def one(item):
    target, expected = item
    artist = artists[target]
    url = 'https://artlines.org/api/backend/v1/artists/' + artist['slug']
    error = None
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=50)
            response.raise_for_status()
            data = response.json()
            assert data['id'] == target
            actual = {v['id']: v for v in data['influences']}
            for claim in expected:
                value = actual[claim['id']]
                assert value['direction'] == 'incoming'
                assert value['relationship_type'] == claim['relationship_type']
                assert value['evidence_level'] == claim['evidence_level']
                assert value['evidence_note'] == claim['evidence_note']
                assert by_claim[claim['id']] <= {v['source_url'] for v in value['citations']}
            return dict(target_id=target, slug=artist['slug'], display_name=artist['display_name'],
                        painter_status_preserved=artist['status'], url=url, http_status=response.status_code,
                        verified_at=m.d.now(), new_incoming_verified=sorted(v['id'] for v in expected),
                        total_relationships_returned=len(actual), response_sha256=m.hashlib.sha256(response.content).hexdigest())
        except (requests.RequestException, KeyError, ValueError, AssertionError) as exc:
            error = str(exc)
            if attempt < 2:
                time.sleep(2)
    return dict(target_id=target, slug=artist['slug'], url=url, error=error)


if __name__ == '__main__':
    result = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(one, item) for item in sorted(by_target.items())]
        for future in as_completed(futures):
            result.append(future.result())
            if len(result) % 25 == 0:
                print('Public painter pages checked', len(result), '/', len(by_target), flush=True)
    failed = [v for v in result if 'error' in v]
    report = dict(at=m.d.now(), read_only=True, plan_sha256=digest, target_pages=len(result),
                  verified_new_relationships=sum(len(v.get('new_incoming_verified', [])) for v in result),
                  failures=failed, results=sorted(result, key=lambda v: v['slug']))
    path = m.RUN / ('public-api-verification-' + ('failed' if failed else 'passed') + '.json')
    m.d.save_new(path, report)
    print(json.dumps({k: v for k, v in report.items() if k != 'results'}, indent=2))
    assert not failed
    assert report['verified_new_relationships'] == len(p['inserts']['influence_claims'])
