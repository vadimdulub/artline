#!/usr/bin/env python3
"""Corroborate existing exact Wikidata object references with the Irish museum."""
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
    museum = index.institution('national-gallery-ireland')
    wanted = set()
    for path in (r.RUN / 'wikidata-batches').glob('*.json'):
        for qid, entity in r.load(path)['entities'].items():
            for statements in entity.get('claims', {}).values():
                for statement in statements:
                    for ref in statement.get('references', []):
                        for snak in ref.get('snaks', {}).get('P854', []):
                            url = snak.get('datavalue', {}).get('value')
                            if isinstance(url, str) and urlsplit(url).hostname == 'onlinecollection.nationalgallery.ie' and re.match(r'/objects/[0-9]+/', urlsplit(url).path):
                                wanted.add((qid, url.replace('http://', 'https://')))

    def one(item):
        qid, url = item
        dest = r.RUN / 'ireland-results-20261005' / (r.sha((qid + url).encode()) + '.json')
        if dest.exists():
            return r.load(dest)
        result = {'claims': [], 'holds': []}
        try:
            raw, receipt = r.capture(url, tag='ireland-20261005', timeout=35)
            soup = BeautifulSoup(raw, 'html.parser')
            fields = {}
            for el in soup.select('#detailView .detailField'):
                label, value = el.select_one('.detailFieldLabel'), el.select_one('.detailFieldValue')
                if label and value:
                    fields[label.get_text(' ', strip=True)] = value.get_text(' ', strip=True)
            artists = [el.get_text(' ', strip=True) for el in soup.select('#detailView .peopleField [itemprop=name]')]
            oid = urlsplit(url).path.split('/')[2]
            for row in index.external.get(('wikidata', qid), []):
                basis = index.match(row, 'wikidata', qid, [fields.get('Title')], artists, fields.get('Object number'), [])
                if receipt['status'] != 200 or urlsplit(receipt['final_url']).hostname != 'onlinecollection.nationalgallery.ie' or not re.match('/objects/' + oid + r'(?:/|$)', urlsplit(receipt['final_url']).path) or not basis.startswith('existing_') or not fields.get('Object number') or re.search(r'deaccession|on loan|lent by|returned to', fields.get('Credit Line', ''), re.I):
                    result['holds'].append({'artwork_id': row['artwork']['id'], 'reason': 'primary_identity_or_holding_review', 'match': basis, 'fields': fields, 'source_receipt': receipt})
                else:
                    result['claims'].append(p.claim(row, 'ngi-object', oid, museum, receipt, receipt['final_url'], {'qid': qid, 'fields': fields, 'artists': artists}, basis + '; exact Wikidata reference corroborated by current National Gallery of Ireland object page, named creator and inventory'))
        except Exception as exc:
            result['holds'] = [{'artwork_id': row['artwork']['id'], 'reason': 'source_error', 'source_url': url, 'error': str(exc)[:300]} for row in index.external.get(('wikidata', qid), [])]
        r.save(dest, result)
        time.sleep(0.7)
        return result

    claims, holds = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, result in enumerate(pool.map(one, sorted(wanted)), 1):
            claims.extend(result['claims'])
            holds.extend(result['holds'])
            if n % 20 == 0:
                print('Irish museum object pages', n, '/', len(wanted), flush=True)
    p.output('ireland-20261005', claims, holds)


if __name__ == '__main__':
    main()
