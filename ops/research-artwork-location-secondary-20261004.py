#!/usr/bin/env python3
"""Capture secondary location leads; do not promote name-only location claims."""
import argparse
import collections
import concurrent.futures
import html
import importlib.util
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

spec = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
r = p.r


def wikiart(workers=4, deadline=None, summary_name='wikiart-summary.json', retry_errors=False, results_folder='wikiart-leads'):
    index = p.Index()
    with r.connect() as db:
        priority = {str(v['id']) for v in db.execute("""SELECT DISTINCT a.id FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id JOIN artist_countries ac ON ac.artist_id=aa.artist_id WHERE a.current_institution_id IS NULL AND a.status<>'archived' AND ac.country_code IN ('RU','GR','CY','AM','GE')""").fetchall()}
    wanted = [(row, e) for row in index.rows for e in row['identifiers'] if e['scheme'] == 'wikiart-artwork']
    assert Path(results_folder).name == results_folder
    if retry_errors:
        assert results_folder != 'wikiart-leads', 'Preserve failed first-attempt evidence'
        wanted = [(row, e) for row, e in wanted if (r.RUN / 'wikiart-leads' / (row['artwork']['id'] + '.json')).exists() and r.load(r.RUN / 'wikiart-leads' / (row['artwork']['id'] + '.json'))['outcome'] == 'source_error']
    wanted.sort(key=lambda x: (x[0]['artwork']['id'] not in priority, x[0]['artwork']['id']))
    counts = collections.Counter()

    def one(item):
        row, e = item
        dest = r.RUN / results_folder / (row['artwork']['id'] + '.json')
        if dest.exists():
            return r.load(dest)['outcome']
        if deadline and time.time() >= deadline:
            return 'deadline_not_researched'
        url = e['canonical_url']
        assert urlsplit(url).hostname == 'www.wikiart.org'
        result = {'artwork_id': row['artwork']['id'], 'title': row['artwork']['title'], 'external_id': e['external_id'], 'source_url': url}
        try:
            raw, rc = r.capture(url, tag='wikiart', timeout=45)
            result['source_receipt'] = rc
            result['outcome'] = 'http_' + str(rc['status'])
            if rc['status'] == 200:
                soup = BeautifulSoup(raw, 'html.parser')
                info = soup.select_one('.wiki-layout-artwork-info')
                canon = soup.find('link', rel='canonical')
                result['canonical'] = canon.get('href') if canon else None
                title = info.select_one('h1').get_text(' ', strip=True) if info and info.select_one('h1') else ''
                fields = {}
                if info:
                    for li in info.select('article > ul > li'):
                        label = li.find('s')
                        if label:
                            key = label.get_text(' ', strip=True).rstrip(':')
                            label.extract()
                            fields[key] = li.get_text(' ', strip=True)
                result['source_title'] = title
                result['fields'] = fields
                result['source_artist'] = info.select_one('h2').get_text(' ', strip=True) if info and info.select_one('h2') else None
                identity = bool(info and any(e['external_id'] in a.get('ng-init', '') for a in info.select('[ng-init]')))
                if not identity or p.titlekey(html.unescape(title)) != p.titlekey(row['artwork']['title']) or (canon and canon.get('href', '').rstrip('/') != url.rstrip('/')):
                    result['outcome'] = 'source_identity_review'
                elif not fields.get('Location'):
                    result['outcome'] = 'no_location_stated'
                elif re.search(r'private collection|unknown|lost|destroyed|stolen', fields['Location'], re.I):
                    result['outcome'] = 'non_museum_or_unknown_location'
                else:
                    result['outcome'] = 'museum_lead_requires_corroboration'
                result['review_note'] = 'Secondary source lead only. Exact page identity checked; museum name is not an accepted holding or current-display claim.'
        except Exception as exc:
            result['outcome'] = 'source_error'
            result['error'] = type(exc).__name__ + ': ' + str(exc)[:400]
            if 'NameResolutionError' in result['error']:
                time.sleep(10)
        r.save(dest, result)
        time.sleep(1)
        return result['outcome']

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for n, outcome in enumerate(pool.map(one, wanted), 1):
            counts[outcome] += 1
            if n % 100 == 0:
                print('WikiArt selected pages', n, '/', len(wanted), dict(counts), flush=True)
    assert Path(summary_name).name == summary_name and summary_name.endswith('.json')
    r.save(r.RUN / summary_name, {'at': r.now(), 'pages': len(wanted), 'counts': counts})


def value(statement):
    v = statement.get('mainsnak', {}).get('datavalue', {}).get('value')
    return v.get('id') if isinstance(v, dict) else v


def current_statements(entity, prop):
    statements = [s for s in entity.get('claims', {}).get(prop, []) if s.get('rank') != 'deprecated' and 'P582' not in s.get('qualifiers', {})]
    preferred = [s for s in statements if s.get('rank') == 'preferred']
    return preferred or statements


def wikidata_plan():
    index = p.Index()
    existing = {i['wikidata_id']: i for i in index.institutions if i.get('wikidata_id')}
    claims, holds = [], []
    for path in sorted((r.RUN / 'wikidata-batches').glob('*.json')):
        batch = r.load(path)
        for qid, entity in batch['entities'].items():
            for row in index.external.get(('wikidata', qid), []):
                a = row['artwork']
                collections_ = current_statements(entity, 'P195')
                locations = current_statements(entity, 'P276')
                cq = {value(s) for s in collections_}
                lq = {value(s) for s in locations}
                titles = [x['value'] for x in entity.get('labels', {}).values()] + [x['value'] for group in entity.get('aliases', {}).values() for x in group]
                inventories = {p.acckey(value(s)) for s in current_statements(entity, 'P217') if isinstance(value(s), str)}
                reason = None
                if len(cq) != 1 or not next(iter(cq), None):
                    reason = 'no_unique_current_collection_statement'
                elif cq != lq:
                    reason = 'collection_and_location_not_identical'
                elif next(iter(cq)) not in existing:
                    reason = 'institution_identity_requires_research'
                elif not {p.titlekey(a[k]) for k in ['title', 'alternate_title'] if a.get(k)} & {p.titlekey(t) for t in titles}:
                    reason = 'current_entity_title_conflict'
                elif a['accession_number'] and inventories and p.acckey(a['accession_number']) not in inventories:
                    reason = 'current_entity_inventory_conflict'
                elif not all(s.get('references') for s in collections_):
                    reason = 'collection_statement_has_no_reference'
                elif any(set(s.get('qualifiers', {})) - {'P580', 'P585'} for s in collections_ + locations):
                    reason = 'qualified_collection_or_location_statement'
                if reason:
                    holds.append({'artwork_id': a['id'], 'qid': qid, 'reason': reason, 'collections': sorted(q for q in cq if q), 'locations': sorted(q for q in lq if q)})
                    continue
                institution = existing[next(iter(cq))]
                evidence = {'id': qid, 'lastrevid': entity.get('lastrevid'), 'modified': entity.get('modified'), 'labels': entity.get('labels'), 'collection_statements': collections_, 'location_statements': locations, 'inventory_statements': current_statements(entity, 'P217'), 'creator_statements': current_statements(entity, 'P170')}
                c = p.claim(row, 'wikidata', qid, institution, batch['receipt'], 'https://www.wikidata.org/wiki/' + qid, evidence, 'existing_exact_wikidata_object_id_title_and_available_inventory; uniquely_matching_referenced_current_collection_and_location_statements')
                c['source_class'] = 'referenced_secondary_catalogue'
                c['review_state'] = 'review'
                c['limitation'] = 'Freshly retrieved secondary catalogue assertion, not independently confirmed by the museum; retained for review. No current-display claim.'
                claims.append(c)
    p.output('wikidata-review', claims, holds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['wikiart', 'wikidata_plan'])
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--deadline', type=float)
    parser.add_argument('--summary-name', default='wikiart-summary.json')
    parser.add_argument('--retry-errors', action='store_true')
    parser.add_argument('--results-folder', default='wikiart-leads')
    args = parser.parse_args()
    if args.command == 'wikiart':
        wikiart(args.workers, args.deadline, args.summary_name, args.retry_errors, args.results_folder)
    else:
        wikidata_plan()
