#!/usr/bin/env python3
"""Follow exact existing Wikidata references to current AGSA object pages."""
import collections
import concurrent.futures
import importlib.util
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def main():
    index = p.Index()
    museum = index.institution('wikimedia-museum-q705557')
    wanted = set()
    for path in (r.RUN / 'wikidata-batches').glob('*.json'):
        for qid, entity in r.load(path)['entities'].items():
            for statements in entity.get('claims', {}).values():
                for statement in statements:
                    for ref in statement.get('references', []):
                        for snak in ref.get('snaks', {}).get('P854', []):
                            url = snak.get('datavalue', {}).get('value')
                            if isinstance(url, str) and urlsplit(url).hostname == 'www.agsa.sa.gov.au' and '/collection/works/' in url:
                                wanted.add((qid, url))
    def one(item):
        qid, url = item
        yes, no = [], []
        try:
            raw, receipt = r.capture(url, tag='agsa', timeout=45)
        except Exception as exc:
            return [], [{'artwork_id': row['artwork']['id'], 'source_url': url, 'reason': 'source_error', 'error': str(exc)[:300]} for row in index.external.get(('wikidata', qid), [])]
        soup = BeautifulSoup(raw, 'html.parser')
        h = soup.select_one('h1.page-header__title')
        title = h.get_text(' ', strip=True) if h else ''
        artists = [x.get_text(' ', strip=True) for x in soup.select('.collection-detail-work-details__creator-link')]
        fields = {dt.get_text(' ', strip=True): dt.find_next_sibling('dd').get_text(' ', strip=True) for dt in soup.select('dl.collection-detail-data dt') if dt.find_next_sibling('dd')}
        for row in index.external.get(('wikidata', qid), []):
            basis = index.match(row, 'wikidata', qid, [title], artists, fields.get('Accession number'), [])
            if receipt['status'] != 200 or not basis.startswith('existing_') or not fields.get('Accession number') or re.search(r'deaccession|on loan|lent by|returned to', fields.get('Credit line', ''), re.I):
                no.append({'artwork_id': row['artwork']['id'], 'reason': 'primary_identity_or_holding_review', 'match': basis, 'fields': fields, 'source_receipt': receipt})
            else:
                oid = url.rstrip('/').rsplit('/', 1)[-1]
                yes.append(p.claim(row, 'agsa-object', oid, museum, receipt, url, {'qid': qid, 'title': title, 'artists': artists, 'fields': fields}, basis + '; exact Wikidata reference to current museum catalogue with title, creator and inventory corroboration'))
        time.sleep(0.8)
        return yes, no
    claims, holds = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, (yes, no) in enumerate(pool.map(one, sorted(wanted)), 1):
            claims.extend(yes)
            holds.extend(no)
            if n % 20 == 0:
                print('AGSA primary references checked', n, '/', len(wanted), flush=True)
    p.output('agsa', claims, holds)


if __name__ == '__main__':
    main()
