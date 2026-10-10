#!/usr/bin/env python3
"""Verify the exact publication through bounded anonymous production API reads."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--api-root', default='https://artlines.org/api/backend/v1')
parser.add_argument('--receipt', required=True)
args = parser.parse_args()
plan = json.loads((ROOT / 'docs/research/war-books-africa-20261004/plan.json').read_text())


def get(path):
    request = urllib.request.Request(args.api_root + path, headers={'User-Agent': 'ArtlineSelectedPublicationVerification/1.0'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def verify(change):
    book = get('/books/' + change['id'])
    assert book['status'] == 'published', (change['id'], 'status')
    for field in ['id', 'sourceId', 'title', 'author', 'years', 'startYear', 'endYear', 'approximate', 'theme', 'description', 'dateBasis', 'dateSources', 'selectionBasis']:
        assert book[field] == change['record'][field], (change['id'], field)
    assert [c['id'] for c in book['creators']] == [link['creator_id'] for link in change['links']]
    return {'id': book['id'], 'title': book['title'], 'year': book['startYear'], 'status': book['status']}


with ThreadPoolExecutor(max_workers=3) as pool:
    books = list(pool.map(verify, plan['changes']))
queries = [('Thebes at War', ['wd-q12234985']), ('Wole Soyinka', ['wd-q6728296', 'wd-q23307171', 'wd-q42192613', 'wd-q42195571']), ('Hosties noires', ['wd-q115286382'])]
searches = []
for query, ids in queries:
    data = get('/books?' + urllib.parse.urlencode({'q': query, 'top100': 'false'}))
    assert len(data['items']) <= 100
    assert set(ids) <= {b['id'] for b in data['items']}
    searches.append({'query': query, 'total': data['total'], 'expectedIdsPresent': ids})
session = get('/auth/session')
assert not session.get('local_debug') and not session.get('all_features')
receipt = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'apiRoot': args.api_root,
           'verifiedPublishedBooks': len(books), 'books': books, 'boundedSearches': searches,
           'productionDebugAccessDisabled': True}
Path(args.receipt).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'verifiedPublishedBooks': len(books), 'searches': len(searches), 'productionDebugAccessDisabled': True, 'apiRoot': args.api_root}))
