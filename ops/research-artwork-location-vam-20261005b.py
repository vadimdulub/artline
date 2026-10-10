#!/usr/bin/env python3
"""Exact existing V&A candidates from current, bounded public metadata queries."""
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


def qualify(c, authority=None):
    obj = c['object_evidence']
    qualifications = json.dumps(obj.get('artistMakerPerson', []), ensure_ascii=False) + ' ' + (obj.get('creditLine') or '')
    location = obj.get('current_location_observation') or {}
    flags = []
    if re.search(r'\b(attributed|after|copy|workshop|school|circle|possibly|probably|loan|lent|returned|deaccession|restitut)\w*\b', qualifications, re.I):
        flags.append('attribution_or_credit_qualification')
    if re.search(r'\b(returned to|deaccessioned|restituted|on loan to|lost|stolen)\b', obj.get('objectHistory') or '', re.I):
        flags.append('qualified_object_history')
    if re.search(r'loan|deposit|lost|missing', json.dumps(location), re.I):
        flags.append('current_loan_or_other_location_qualification')
    if location.get('site') not in ['VA', 'ES', None, '']:
        flags.append('museum_branch_identity_requires_review')
    if location.get('site') == 'ES':
        assert authority and authority['status'] == 200
        obj['museum_storage_authority_receipt'] = authority
    obj['qualifications'] = flags
    if flags:
        c['review_state'] = 'review'
        c['limitation'] = 'Exact V&A collection candidate remains in review: ' + ', '.join(flags) + '. No accepted current custody, ownership or display claim.'
    else:
        c.pop('review_state', None)
        c['limitation'] = 'Documented V&A collection holding. No present building, room, public display, loan destination or legal ownership asserted.'
    return c


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refine', action='store_true')
    args = parser.parse_args()
    authority = None
    if args.refine:
        _, authority = r.capture('https://www.vam.ac.uk/articles/about-va-east-storehouse', tag='vam-authority-20261005b', timeout=40)
        assert authority['status'] == 200
    index = p.Index()
    museums = [i for i in r.load(r.RUN / 'local-institutions-20261005b.json') if 'vam.ac.uk' in (i.get('website_url') or '')]
    assert len(museums) == 1, [(i['slug'], i['name']) for i in museums]
    museum = museums[0]
    rows = [x for x in r.load(r.RUN / 'remaining-snapshot-20261005b.json.gz')
            if any(c[3] == 'Victoria and Albert Museum' for c in x['supplied'] or [])]

    def one(row):
        aid = row['artwork']['id']
        old_dest = r.RUN / 'vam-results-20261005b' / (aid + '.json.gz')
        dest = r.RUN / ('vam-results-refined-20261005b' if args.refine else 'vam-results-20261005b') / (aid + '.json.gz')
        if dest.exists():
            return r.load(dest)
        if args.refine and old_dest.exists():
            old = r.load(old_dest)
            if old['reason'] not in ["'name'", 'search_http_422']:
                old['claims'] = [qualify(c, authority) for c in old['claims']]
                r.save_gz(dest, old)
                return old
        result = {'artwork_id': aid, 'claims': [], 'search_receipts': []}
        try:
            cells = next(c for c in row['supplied'] if c[3] == 'Victoria and Albert Museum')
            query_title = cells[1].replace('"', ' ')
            if len(query_title) > 115:
                query_title = query_title[:115].rsplit(' ', 1)[0]
            phrase = '"' + query_title + '"'
            raw, rc = r.capture('https://api.vam.ac.uk/v2/objects/search', {'q': phrase, 'page_size': 100}, tag='vam-20261005b', timeout=35)
            result['search_receipts'].append(rc)
            assert rc['status'] == 200, 'search_http_' + str(rc['status'])
            search = json.loads(raw)
            if search['info']['record_count'] > 100:
                raw, rc = r.capture('https://api.vam.ac.uk/v2/objects/search',
                                    {'q': (phrase + ' ' + r.norm(cells[0]))[:128], 'page_size': 100}, tag='vam-20261005b', timeout=35)
                result['search_receipts'].append(rc)
                assert rc['status'] == 200, 'narrow_search_unavailable'
                search = json.loads(raw)
            assert search['info']['record_count_exact'] and search['info']['record_count'] <= 100, 'search_not_bounded'
            assert len(search['records']) == search['info']['record_count'], 'search_incomplete'
            matches = []
            for brief in search['records']:
                basis = index.match(row, 'vam-object', brief['systemNumber'], [brief['_primaryTitle']],
                                    [(brief.get('_primaryMaker') or {}).get('name', '')], brief['accessionNumber'], [brief['_primaryDate']])
                if basis.startswith(('existing_', 'unique_')):
                    matches.append(brief)
            assert len(matches) == 1, 'multiple_exact_candidates' if matches else 'no_exact_creator_title_date_match'
            brief = matches[0]
            raw, receipt = r.capture('https://api.vam.ac.uk/v2/museumobject/' + brief['systemNumber'], tag='vam-20261005b', timeout=35)
            result['source_receipt'] = receipt
            assert receipt['status'] == 200, 'object_unavailable'
            full = json.loads(raw)
            obj = full['record']
            assert obj['systemNumber'] == brief['systemNumber'] and obj['accessionNumber'] == brief['accessionNumber'], 'source_identity_changed'
            makers = obj.get('artistMakerPerson', [])
            titles = [v['title'] for v in obj.get('titles', [])]
            artists = [v['name']['text'] for v in makers]
            dates = [v['date']['text'] for v in obj.get('productionDates', [])]
            basis = index.match(row, 'vam-object', obj['systemNumber'], titles, artists, obj['accessionNumber'], dates)
            assert basis.startswith(('existing_', 'unique_')), basis
            url = full['meta']['_links']['collection_page']['href']
            assert url == 'https://collections.vam.ac.uk/item/' + obj['systemNumber'] + '/', 'collection_url_conflict'
            evidence = {k: obj.get(k) for k in ['systemNumber', 'accessionNumber', 'titles', 'artistMakerPerson', 'productionDates', 'collectionCode', 'creditLine', 'objectHistory', 'galleryLocations', 'recordModificationDate']}
            evidence['search_receipts'] = result['search_receipts']
            evidence['current_location_observation'] = brief.get('_currentLocation')
            c = p.claim(row, 'vam-object', obj['systemNumber'], museum, receipt, url, evidence, basis + '; exact current V&A object and accession rechecked')
            qualifications = json.dumps(makers, ensure_ascii=False) + ' ' + (obj.get('creditLine') or '')
            history = obj.get('objectHistory') or ''
            location = brief.get('_currentLocation') or {}
            if (re.search(r'\b(attributed|after|copy|workshop|school|circle|possibly|probably|loan|lent|returned|deaccession|restitut)\w*\b', qualifications, re.I)
                    or re.search(r'\b(returned to|deaccessioned|restituted|on loan to|lost|stolen)\b', history, re.I)
                    or location.get('site') not in ['VA', 'VAE', 'VAM', None, '']):
                c['review_state'] = 'review'
                c['limitation'] = 'Exact V&A collection candidate with attribution, loan or location qualification; preserve source wording in review. No accepted current custody, ownership or display claim.'
            if args.refine:
                c = qualify(c, authority)
            result['claims'] = [c]
            result['reason'] = 'current_museum_candidate'
        except Exception as exc:
            result['reason'] = str(exc)[:300]
        r.save_gz(dest, result)
        time.sleep(0.5)
        return result

    claims, holds = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, result in enumerate(pool.map(one, rows), 1):
            if result['claims']:
                claims.extend(result['claims'])
            else:
                holds.append(result)
            if n % 100 == 0:
                print('V&A existing identities researched', n, '/', len(rows), flush=True)
    p.output('vam-refined-20261005b' if args.refine else 'vam-20261005b', claims, holds)


if __name__ == '__main__':
    main()
