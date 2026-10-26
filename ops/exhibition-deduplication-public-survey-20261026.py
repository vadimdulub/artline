"""Bounded public exhibition discovery while owner SQL authentication is held.

This is an observational API inventory, not a transaction-consistent database
snapshot or approval to merge events with similar names.
"""
import collections
import gzip
import json
import shutil
import time
from pathlib import Path
import requests
import exhibitions_common as c

E = c.ROOT / 'docs/research/catalogue-deduplication-20261026'
D = Path.home() / 'Library/Application Support/Artline/source-metadata/catalogue-deduplication-20261026'
ORIGIN = 'https://artline-api-lpuqqlugnq-ew.a.run.app'


def run():
    directory = D / 'public-exhibition-survey'
    directory.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers['User-Agent'] = 'ArtlineOwnerVerification/1.0'
    after, rows, receipts = None, [], []
    for page in range(1, 301):
        assert shutil.disk_usage(D).free > 15 * 1024**3
        path = directory / (str(page).zfill(3) + '.json.gz')
        if path.exists():
            saved = c.load(path)
            assert saved['requested_after'] == after
        else:
            params = dict(limit=100)
            if after:
                params['after'] = after
            response = session.get(ORIGIN + '/api/v1/exhibitions', params=params, timeout=(8, 35), allow_redirects=False)
            assert response.status_code == 200, ('Owner service-origin API status', response.status_code)
            raw = response.content
            saved = dict(at=c.now(), url=response.url, status=response.status_code,
                         bytes=len(raw), sha256=c.sha(raw), requested_after=after, response=response.json())
            c.save(path, saved)
            time.sleep(0.6)
        body = saved['response']
        rows.extend(body['items'])
        receipts.append({k: v for k, v in saved.items() if k != 'response'})
        if page % 10 == 0:
            print('Public exhibition discovery', len(rows), '/', body['total'], flush=True)
        if not body['hasMore']:
            break
        assert body.get('nextCursor') and body['nextCursor'] != after
        after = body['nextCursor']
    else:
        raise RuntimeError('Finite page cap reached; do not claim complete inventory')
    assert len({r['id'] for r in rows}) == len(rows)
    by_title_dates, by_title = collections.defaultdict(list), collections.defaultdict(list)
    for row in rows:
        by_title_dates[(c.norm(row['title']), row['startDate'], row['endDate'], row['startYear'], row['endYear'])].append(row)
        by_title[(c.norm(row['title']), row['startYear'], row['endYear'])].append(row)
    exact = [v for v in by_title_dates.values() if len(v) > 1]
    broad = [v for v in by_title.values() if len(v) > 1]
    candidates = dict(at=c.now(), rows=rows, exact_title_date_groups=exact, same_title_year_leads=broad,
                      observational_api_not_repeatable_read=True,
                      merges_require_complete_source_venue_tour_section_review=True)
    c.save(D / 'public-exhibition-deduplication-candidates.json.gz', candidates)
    summary = dict(at=c.now(), complete_pagination=True, distinct_exhibitions=len(rows), pages=len(receipts),
                   observed_totals=sorted({c.load(directory / (str(i).zfill(3) + '.json.gz'))['response']['total'] for i in range(1, len(receipts) + 1)}),
                   exact_title_date_groups=len(exact), same_title_year_leads=len(broad),
                   receipts=receipts, SQL_authentication_still_required_before_changes=True,
                   real_local_catalogue_connections=0, production_writes=0)
    c.save(E / 'public-exhibition-discovery-receipt.json', summary)
    print(json.dumps({k: v for k, v in summary.items() if k != 'receipts'}), flush=True)


if __name__ == '__main__':
    run()
