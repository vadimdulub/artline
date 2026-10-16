#!/usr/bin/env python3
"""Nationwide directory research; no database writes or image downloads.

Switzerland precedes India. Directory entries are research leads, never invented
artworks. Source responses are immutable; each museum retains its own gaps.
"""
import argparse
import collections
import concurrent.futures
import csv
import importlib.util
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

spec = importlib.util.spec_from_file_location('base', Path(__file__).with_name('cesi-top100-20261010.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
OP = 'switzerland-india-museums-20261011'
RUN = m.ROOT / 'docs/research' / OP
m.RUN = RUN
DIRECTORY = 'https://www.museums.ch/de/museumsbesuch/museen/museen-1852.html'


def source(url):
    if url.startswith('http://'):
        url = 'https://' + url[len('http://'):]
    raw, receipt = m.capture(url)
    assert receipt['status'] == 200, (url, receipt['status'])
    return BeautifulSoup(raw, 'html.parser'), receipt


def directory():
    page, receipt = source(DIRECTORY)
    script = next(s.get_text() for s in page.select('script') if 'const ___fumanClasses = ' in s.get_text())
    classes = json.JSONDecoder().raw_decode(script.split('const ___fumanClasses = ', 1)[1])[0]
    options = next(c['options'] for c in classes if '/organisationlist/' in c['path'])
    entries = options['mapArray']
    text = (page.find('main') or page).get_text(' ', strip=True)
    match = re.search(r'(\d+) von (\d+) Museen', text)
    assert match and int(match[1]) == int(match[2]) == len(entries)
    assert len({x['id'] for x in entries}) == len(entries)
    records = []
    for entry in entries:
        records.append({
            'directory_id': str(entry['id']), 'name': entry['title'].strip(),
            'locality': entry.get('locality'), 'primary_category': entry.get('category'),
            'category_ids': entry.get('categoryIds') or [],
            'directory_url': urljoin(DIRECTORY, entry['uri']),
            'latitude_source': entry.get('lat'), 'longitude_source': entry.get('lng'),
            'country_status': 'national-directory lead; individual country reconciliation required',
            'evidence': receipt, 'object_coverage': 'not yet assessed in this campaign',
        })
    m.save(RUN/'CH/directory.json.gz', {'source': receipt, 'reported_total': int(match[2]), 'records': records})
    print(json.dumps({'directory_entries': len(records), 'art_tagged': sum('57' in r['category_ids'] for r in records),
                      'primary_categories': dict(collections.Counter(r['primary_category'] for r in records))}), flush=True)


def detail(record):
    target = RUN/'CH/directory-details'/(record['directory_id']+'.json.gz')
    if target.exists():
        return m.load(target)
    try:
        page, receipt = source(record['directory_url'])
        main = page.find('main') or page
        h1 = main.find('h1')
        assert h1 and m.norm(h1.get_text(' ', strip=True)) == m.norm(record['name']), 'Directory identity mismatch'
        links = []
        for a in main.select('a[href]'):
            href = urljoin(record['directory_url'], a['href'])
            host = urlsplit(href).hostname or ''
            if href.startswith(('http://', 'https://')) and host != 'www.museums.ch':
                links.append({'label': a.get_text(' ', strip=True), 'url': href})
        for node in main.select('script,style'):
            node.decompose()
        text = main.get_text('\n', strip=True)
        value = {'directory_id': record['directory_id'], 'name': record['name'],
                 'evidence': receipt, 'source_text': text, 'external_links': links,
                 'result': 'directory identity and native-site leads captured',
                 'object_coverage': 'individual collection evidence required'}
        m.save(target, value)
        time.sleep(.15)
        return value
    except Exception as error:
        value = {'directory_id': record['directory_id'], 'name': record['name'], 'url': record['directory_url'],
                 'result': 'source gap', 'error': type(error).__name__ + ': ' + str(error)[:500]}
        m.save(RUN/'CH/directory-gaps'/(record['directory_id']+'.json'), value)
        return value


def details(limit):
    rows = m.load(RUN/'CH/directory.json.gz')['records']
    rows.sort(key=lambda r: ('57' not in r['category_ids'], r['name'].casefold()))
    if limit:
        rows = rows[:limit]
    counts = collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for index, result in enumerate(pool.map(detail, rows), 1):
            counts[result['result']] += 1
            if index % 25 == 0:
                print(json.dumps({'checked': index, 'selected': len(rows), 'results': dict(counts)}), flush=True)
    print(json.dumps({'checked': len(rows), 'results': dict(counts)}), flush=True)


def ledger():
    rows = m.load(RUN/'CH/directory.json.gz')['records']
    institutions = m.load(RUN/'production-baseline.json.gz')['institutions']
    output = []
    for row in rows:
        target = RUN/'CH/directory-details'/(row['directory_id']+'.json.gz')
        item = m.load(target) if target.exists() else {}
        native_links = item.get('external_links', [])
        websites = [x['url'] for x in native_links if x['label'].startswith(('www.', 'http')) or len(native_links) == 1]
        hosts = {(urlsplit(u).hostname or '').removeprefix('www.') for u in websites}
        candidates = [i for i in institutions if m.norm(i['name']) == m.norm(row['name']) or
                      (i.get('website_url') and (urlsplit(i['website_url']).hostname or '').removeprefix('www.') in hosts)]
        output.append({'directory_id': row['directory_id'], 'name': row['name'], 'locality': row['locality'],
                       'primary_category': row['primary_category'], 'art_category': '57' in row['category_ids'],
                       'directory_url': row['directory_url'], 'native_websites': ' | '.join(websites),
                       'directory_checked': bool(item), 'catalogue_identity_candidates': ' | '.join(i['id'] for i in candidates),
                       'object_coverage': 'individual research required',
                       'country_status': row['country_status']})
    path = RUN/'CH/directory-coverage.csv'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    print(json.dumps({'entries': len(output), 'directory_checked': sum(r['directory_checked'] for r in output),
                      'identity_candidates': sum(bool(r['catalogue_identity_candidates']) for r in output)}), flush=True)


def native_homes(limit):
    rows = m.load(RUN/'CH/directory.json.gz')['records']
    rows.sort(key=lambda r: ('57' not in r['category_ids'], r['name'].casefold()))
    if limit:
        rows = rows[:limit]

    def one(row):
        target = RUN/'CH/native-sites'/(row['directory_id']+'.json.gz')
        if target.exists():
            return m.load(target)
        detail_path = RUN/'CH/directory-details'/(row['directory_id']+'.json.gz')
        if not detail_path.exists():
            return {'result': 'directory detail pending'}
        d = m.load(detail_path)
        links = [x for x in d['external_links'] if x['label'].startswith(('www.', 'http')) or len(d['external_links']) == 1]
        if len(links) != 1:
            value = {'directory_id': row['directory_id'], 'name': row['name'],
                     'result': 'native website requires manual selection', 'links': d['external_links']}
            m.save(target, value)
            return value
        url = links[0]['url']
        try:
            page, receipt = source(url)
            source_links = [{'label': a.get_text(' ', strip=True), 'url': urljoin(receipt['final_url'], a['href'])}
                            for a in page.select('a[href]')]
            collection_links = [x for x in source_links if re.search(
                r'samml|collection|collezion|best[aä]nd|catalog|katalog|werke|oeuvres|œuvres|objekt|objets|highlights',
                x['label']+' '+x['url'], re.I)]
            for node in page.select('script,style,noscript'):
                node.decompose()
            value = {'directory_id': row['directory_id'], 'name': row['name'], 'website': url,
                     'evidence': receipt, 'title': page.title.get_text(' ', strip=True) if page.title else None,
                     'text': page.get_text('\n', strip=True)[:100000],
                     'collection_links': list({x['url']: x for x in collection_links}.values()),
                     'result': 'native site checked; object evidence pending'}
        except Exception as error:
            value = {'directory_id': row['directory_id'], 'name': row['name'], 'website': url,
                     'result': 'native source gap', 'error': type(error).__name__+': '+str(error)[:500]}
        m.save(target, value)
        return value

    counts = collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for index, result in enumerate(pool.map(one, rows), 1):
            counts[result['result']] += 1
            if index % 25 == 0:
                print(json.dumps({'native_checked': index, 'selected': len(rows), 'results': dict(counts)}), flush=True)
    print(json.dumps({'native_checked': len(rows), 'results': dict(counts)}), flush=True)


def collection_leads(limit):
    """Bounded metadata discovery, at most two collection pages per art institution."""
    rows = m.load(RUN/'CH/directory.json.gz')['records']
    tasks = collections.defaultdict(list)
    for row in rows:
        if '57' not in row['category_ids']:
            continue
        native = RUN/'CH/native-sites'/(row['directory_id']+'.json.gz')
        if not native.exists():
            continue
        item = m.load(native)
        choices = []
        for link in item.get('collection_links', []):
            url = link['url'].split('#')[0]
            if not url.startswith(('https://', 'http://')) or len(url)>250:
                continue
            if re.search(r'\.pdf(?:$|\?)|shop|facebook|twitter|instagram|linkedin|cataloghi|veranstalt|agenda|veranstaltung|sammlung-auf-reisen', url, re.I):
                continue
            label = link['label']
            score = 0 if re.search(r'highlights|online|en ligne|opere|objekte|werke|catalogue|katalog', label, re.I) else 1
            choices.append((score, len(label), url))
        seen = set()
        for _, _, url in sorted(choices):
            if url in seen:
                continue
            seen.add(url)
            tasks[url].append({'directory_id':row['directory_id'], 'name':row['name']})
            if len(seen)==2:
                break
    work = list(tasks.items())[:limit or None]

    def one(task):
        url, museums = task
        path = RUN/'CH/collection-discovery'/(m.sha(url.encode())+'.json.gz')
        if path.exists():
            return m.load(path)
        try:
            page, receipt = source(url)
            body = page.find('main') or page
            captions = [x.get_text(' ', strip=True) for x in body.select('figcaption,.caption')]
            links = [{'label':a.get_text(' ',strip=True), 'url':urljoin(receipt['final_url'],a['href'])}
                     for a in body.select('a[href]')]
            images = [{'alt':a.get('alt'), 'src':a.get('src')} for a in body.select('img')]
            for node in body.select('script,style,noscript'):
                node.decompose()
            value = dict(url=url, museums=museums, evidence=receipt, source_text=body.get_text('\n',strip=True),
                         captions=captions, links=links, image_metadata=images,
                         result='collection page captured; individual object selection pending')
        except Exception as error:
            value = dict(url=url,museums=museums,result='collection source gap',error=type(error).__name__+': '+str(error)[:500])
        m.save(path,value)
        return value

    counts = collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for index, result in enumerate(pool.map(one, work),1):
            counts[result['result']]+=1
            if index%20==0:
                print(json.dumps(dict(collection_pages=index,selected=len(work),results=dict(counts))),flush=True)
    print(json.dumps(dict(collection_pages=len(work),results=dict(counts))),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['directory', 'details', 'ledger', 'native_homes', 'collection_leads'])
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()
    globals()[args.action](args.limit) if args.action in ['details', 'native_homes', 'collection_leads'] else globals()[args.action]()
