#!/usr/bin/env python3
"""Reconcile selected existing Aberdeen records against the council's catalogue."""
import argparse
import collections
import concurrent.futures
import importlib.util
from pathlib import Path
import re
import time
from urllib.parse import quote, urlsplit
import uuid

from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r
BASE = 'https://emuseum.aberdeencity.gov.uk'
FOLDER = r.RUN / 'aberdeen-selected-objects-20261005b'
AUTHORITY = 'https://sites.aberdeencity.gov.uk/AAGM/museum-from-home/blogs/international-open-access-week-2021'


def selected():
    return r.load(r.RUN / 'aberdeen-selected-20261005b.json.gz')


def fetch(url, tag):
    for attempt in range(3):
        try:
            raw, receipt = r.capture(url, tag=tag + ('-retry' + str(attempt) if attempt else ''), timeout=40)
            assert receipt['status'] == 200
            return raw, receipt
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def parse(raw, url):
    soup = BeautifulSoup(raw, 'html.parser')
    assert 'Aberdeen Art Gallery and Museums Collections' in soup.get_text(' ', strip=True)
    titles = [e.get_text(' ', strip=True) for e in soup.select('.detailField.titleField h1')]
    assert len(titles) == 1
    fields = collections.defaultdict(list)
    actors = []
    for field in soup.select('.detailField'):
        label, value = field.select_one('.detailFieldLabel'), field.select_one('.detailFieldValue')
        if not label or not value:
            continue
        name = label.get_text(' ', strip=True)
        fields[name].append(value.get_text(' ', strip=True))
        if 'peopleField' in field.get('class', []):
            actors.append({'role': name, 'names': [v.get_text(' ', strip=True) for v in value.select('a [itemprop="name"]')], 'text': value.get_text(' ', strip=True)})
    assert len(fields['Object number']) == 1
    oid = re.fullmatch(r'/objects/(\d+)/[^/]+', urlsplit(url).path).group(1)
    return {'object_id': oid, 'titles': titles, 'fields': dict(fields), 'actors': actors, 'inventory': fields['Object number'][0], 'url': url}


def capture_one(value):
    path = FOLDER / (value['artwork_id'] + '.json.gz')
    if path.exists():
        return
    assert len(value['inventories']) == 1
    inventory = value['inventories'][0]
    raw, search_receipt = fetch(BASE + '/search/' + quote(inventory, safe=''), 'aberdeen-inventory-search-20261005b')
    soup = BeautifulSoup(raw, 'html.parser')
    matches = re.findall(r'\b([\d,]+) results\b', soup.get_text(' ', strip=True))
    urls = sorted({BASE + urlsplit(a['href']).path for a in soup.select('a[href^="/objects/"]') if re.fullmatch(r'/objects/\d+/[^/]+', urlsplit(a['href']).path)})
    result = {'artwork_id': value['artwork_id'], 'inventory_query': inventory, 'search_receipt': search_receipt, 'objects': []}
    if len(matches) != 1 or int(matches[0].replace(',', '')) != len(urls) or len(urls) > 12:
        result['reason'] = 'inventory_search_not_complete_or_not_narrow'
    else:
        for url in urls:
            raw, receipt = fetch(url, 'aberdeen-current-objects-20261005b')
            result['objects'].append({'object': parse(raw, url), 'source_receipt': receipt})
            time.sleep(0.3)
    r.save_gz(path, result)
    time.sleep(0.4)


def capture():
    raw, receipt = fetch(AUTHORITY, 'aberdeen-current-council-authority-20261005b')
    assert BASE + '/collections' in raw.decode()
    r.save(r.RUN / 'aberdeen-authority-20261005b.json', {'receipt': receipt})
    values = selected()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, _ in enumerate(pool.map(capture_one, values), 1):
            if n % 50 == 0:
                print('Aberdeen selected inventories', n, '/', len(values), flush=True)
    r.save(r.RUN / 'aberdeen-capture-complete-20261005b.json', {'at': r.now(), 'artworks': len(values)})


def authority_names(row, names, authorities):
    result, proofs = list(names), []
    for artist in row['artists']:
        authority = authorities.get(artist['id'])
        if authority and {r.namekey(n) for n in names} & {r.namekey(n) for n in authority['names']}:
            result.append(artist['name'])
            proofs.append({'local_artist_id': artist['id'], 'local_name': artist['name'], 'primary_names': names, 'authority': authority})
    return result, proofs


def plan(refined=False):
    assert (r.RUN / 'aberdeen-capture-complete-20261005b.json').exists()
    index = p.Index()
    museum = {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum/aberdeen-archives-gallery-museums')),
              'slug': 'aberdeen-archives-gallery-museums', 'name': 'Aberdeen Archives, Gallery & Museums',
              'normalized_name': 'aberdeen archives gallery museums', 'kind': 'museum', 'website_url': BASE + '/collections',
              'wikidata_id': 'Q109893034', 'status': 'review',
              'description': 'Aberdeen City Council museum collection service. Collection association does not imply display at Aberdeen Art Gallery or a particular physical venue.'}
    authority = r.load(r.RUN / 'aberdeen-authority-20261005b.json')['receipt']
    claims, holds = [], []
    values = selected()
    authorities = {}
    if refined:
        ids = {v['artwork_id'] for v in r.load(r.RUN / 'primary-plans/aberdeen-20261005b.json.gz')['holds']}
        values = [v for v in values if v['artwork_id'] in ids]
        entities = {}
        for path in (r.RUN / 'aberdeen-artist-authority-batches-20261005b').glob('*.json.gz'):
            batch = r.load(path)
            for qid, entity in batch['data']['entities'].items():
                if entity.get('missing'):
                    continue
                names = [v['value'] for v in entity.get('labels', {}).values()] + [v['value'] for group in entity.get('aliases', {}).values() for v in group]
                entities[qid] = {'wikidata_id': qid, 'names': names, 'source_receipt': batch['receipt']}
        for value in r.load(r.RUN / 'aberdeen-local-artist-authorities-20261005b.json')['identifiers']:
            if value['external_id'] in entities:
                authorities[value['entity_id']] = entities[value['external_id']]
    for value in values:
        aid, qid = value['artwork_id'], value['qid']
        row = index.by_id[aid]
        captured = r.load(FOLDER / (aid + '.json.gz'))
        found = []
        for entry in captured['objects']:
            obj = entry['object']
            identity_flags = []
            makers = [a for a in obj['actors'] if r.norm(a['role']) in {'artist', 'painter', 'engraver', 'printmaker', 'draughtsman', 'designer', 'sculptor'}]
            names = [n for a in makers for n in a['names']]
            # Honorifics identify the same named person; qualified roles remain held.
            names += [re.sub(r'^(Sir|Dame|Lord)\s+', '', n) for n in names]
            names, creator_proofs = authority_names(row, names, authorities)
            if p.acckey(obj['inventory']) != p.acckey(value['inventories'][0]):
                continue
            # Some supplied Wikimedia labels concatenate the exact creator and
            # museum title. Accept only that explicit combination, not fuzzy text.
            titles = [*obj['titles'], *(name + ' - ' + title for name in names for title in obj['titles'])]
            basis = index.match(row, 'wikidata', qid, titles, names, obj['inventory'], obj['fields'].get('Date', []))
            if not basis.startswith(('existing_', 'unique_')):
                qualified = [a for a in obj['actors'] if re.search(r'\b(attributed|after|school|circle|workshop|copy)\b', r.norm(a['role']))]
                qualified_names = [n for a in qualified for n in a['names']]
                qualified_names, qualified_proofs = authority_names(row, qualified_names, authorities)
                qualified_titles = [*obj['titles'], *(name + ' - ' + title for name in qualified_names for title in obj['titles'])]
                other_basis = index.match(row, 'wikidata', qid, qualified_titles, qualified_names, obj['inventory'], obj['fields'].get('Date', []))
                if other_basis.startswith(('existing_', 'unique_')):
                    basis = other_basis
                    makers = qualified
                    creator_proofs = qualified_proofs
                    identity_flags.append('qualified_creator_role')
            if basis.startswith(('existing_', 'unique_')):
                found.append((entry, basis, makers, identity_flags, creator_proofs))
        if len(found) != 1:
            holds.append({'artwork_id': aid, 'reason': 'multiple_exact_current_objects' if found else captured.get('reason', 'current_identity_not_reconciled'), 'search_receipt': captured['search_receipt'], 'candidate_source_urls': [v['object']['url'] for v in captured['objects']]})
            continue
        entry, basis, makers, identity_flags, creator_proofs = found[0]
        obj = entry['object']
        flags = list(identity_flags)
        if len(makers) != 1 or re.search(r'\b(after|attributed|workshop|school|circle|copy)\b', r.norm(' '.join(a['text'] for a in obj['actors']))):
            flags.append('creator_relationship_requires_review')
        acquisition = ' '.join(obj['fields'].get('Acquisition', []))
        if not acquisition:
            flags.append('acquisition_not_stated')
        status = ' '.join([acquisition, *obj['fields'].get('Location', [])])
        if re.search(r'\b(loan|lent|deposit|deposited|returned|restitution|deaccession|stolen|lost|destroyed)\b', r.norm(status)):
            flags.append('custody_qualification')
        evidence = {'current_museum_record': obj, 'selection': value, 'inventory_search_receipt': captured['search_receipt'], 'council_authority_receipt': authority, 'creator_authority_reconciliation': creator_proofs, 'qualifications': flags}
        c = p.claim(row, 'aberdeen-object', obj['object_id'], museum, entry['source_receipt'], obj['url'], evidence, basis + '; exact council catalogue inventory, title and direct maker')
        c['limitation'] = 'Documented Aberdeen museum-service collection association. Catalogue location text is preserved as evidence; no separate current physical presence, public display or gallery-room claim is made.'
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Official council catalogue candidate retained in review: ' + ', '.join(flags) + '. No current physical presence or public display asserted.'
        claims.append(c)
    p.output('aberdeen-refined-20261005b' if refined else 'aberdeen-20261005b', claims, holds)
    print('Claim states', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan', 'plan-refined'])
    command = parser.parse_args().command
    plan(refined=True) if command == 'plan-refined' else globals()[command]()
