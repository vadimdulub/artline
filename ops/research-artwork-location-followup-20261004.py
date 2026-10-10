#!/usr/bin/env python3
"""Recheck selected identities from preserved museum research against live sources."""
import argparse
import collections
import concurrent.futures
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r
MUSEUMS = {'mia': ('Minneapolis Institute of Art', 'minneapolis-institute-of-art'),
           'walters': ('The Walters Art Museum', 'wikimedia-museum-q210081'),
           'saam': ('Smithsonian American Art Museum', 'smithsonian-american-art-museum'),
           'smk': ('Statens Museum for Kunst (SMK)', 'statens-museum-for-kunst')}


def version(provider):
    return provider + ('-followup-v2' if provider in ['saam', 'walters'] else '-followup')


def select(index, provider):
    path = r.RUN / (version(provider) + '-selection.json.gz')
    if path.exists():
        return r.load(path)
    matches = collections.defaultdict(dict)
    museum = MUSEUMS[provider][0]
    facts = {}
    if provider == 'smk':
        for file in sorted((r.ROOT / 'content/imports/europe-smk-20260910').glob('page-*.json')):
            if file.name.endswith('.snapshot.json'):
                continue
            receipt = r.load(file.with_name(file.name + '.snapshot.json'))
            assert r.sha(file.read_bytes()) == receipt['sha256']
            for o in r.load(file)['items']:
                makers = [' '.join(filter(None, [a.get('creator_forename'), a.get('creator_surname')])) for a in o.get('production', []) if not a.get('creator_qualifier') and not a.get('creator_role')]
                f = {'id': o['object_number'], 'accession': o['object_number'], 'titles': [t['title'] for t in o.get('titles', []) if t.get('title')], 'artists': makers, 'dates': [d.get('period') for d in o.get('production_date', [])], 'selection_receipt': receipt}
                facts[f['id']] = f
    else:
        # These are identity leads only; every accepted result requires a fresh response.
        for n in [3, 5, 6, 9, 14]:
            file = r.ROOT / f'docs/research/expanded-round{n}-20260913/new-source-matches.json'
            digest = r.sha(file.read_bytes())
            for group in r.load(file).values():
                for old in group.values():
                    if old['source'] != provider:
                        continue
                    o = old['object_record']
                    if provider == 'mia':
                        titles, dates = [o['title']], [o.get('dated')]
                    elif provider == 'walters':
                        titles, dates = [o['Title']], [o.get('DateText')]
                    else:
                        titles = [o['descriptiveNonRepeating']['title']['content']]
                        dates = [d['content'] for d in o['freetext'].get('date', []) if d.get('label') == 'Date']
                    f = {'id': str(old['object_id']), 'accession': old['accession'], 'titles': titles, 'artists': [old['painter']['name']], 'dates': dates, 'selection_receipt': {'path': str(file.relative_to(r.ROOT)), 'sha256': digest}}
                    if provider == 'saam':
                        f['artists'].extend(v['content'] for v in o['freetext'].get('name', []) if v.get('label') == 'Artist')
                    facts[f['id']] = f
    for oid, f in facts.items():
        for row in index.find(provider + '-object', oid, f['titles'], f['artists'], [museum]):
            # Native records are covered by the first provider pass.
            if provider != 'smk' and any(e['scheme'] == provider + '-object' for e in row['identifiers']):
                continue
            basis = index.match(row, provider + '-object', oid, f['titles'], f['artists'], f['accession'], f['dates'])
            if basis.startswith(('unique_', 'existing_')):
                matches[row['artwork']['id']][oid] = f
    selected, held = [], []
    for aid, group in matches.items():
        if len(group) == 1:
            selected.append({'artwork_id': aid, **next(iter(group.values()))})
        else:
            held.append({'artwork_id': aid, 'reason': 'multiple_historical_objects', 'object_ids': sorted(group)})
    result = {'at': r.now(), 'provider': provider, 'selected': selected, 'held': held}
    r.save_gz(path, result)
    print(provider, 'unique existing artwork identities', len(selected), 'ambiguous', len(held), flush=True)
    return result


def walters_fields(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    heading = soup.select_one('h1.artwork--title')
    title = heading.get_text(' ', strip=True) if heading else ''
    artists = [n.get_text(' ', strip=True).split(' (', 1)[0].strip() for n in soup.select('.section__author a')]
    stats = {}
    for node in soup.select('.stat'):
        h, val = node.find('h3'), node.find('p', recursive=False)
        if h and val:
            stats[h.get_text(' ', strip=True).split(' In libraries,')[0]] = val.get_text(' ', strip=True)
    date = soup.select_one('.section__date')
    if date:
        stats['Date'] = date.get_text(' ', strip=True)
    return title, artists, stats


def saam_fields(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    stats = {}
    for node in soup.select('dl.tombstone > div'):
        h, val = node.find('dt'), node.find('dd')
        if h and val:
            stats[h.get_text(' ', strip=True)] = val.get_text(' ', strip=True)
    title = soup.select_one('main h1')
    return title.get_text(' ', strip=True) if title else '', stats


def capture(index, provider):
    selected = select(index, provider)
    museum = index.institution(MUSEUMS[provider][1])

    def one(f):
        row = index.by_id[f['artwork_id']]
        dest = r.RUN / (version(provider) + '-results') / (f['artwork_id'] + '.json')
        if dest.exists():
            return r.load(dest)
        result = {'artwork_id': f['artwork_id'], 'reason': 'unprocessed'}
        try:
            if provider == 'mia':
                raw, rc = r.capture('https://search.artsmia.org/id/' + f['id'], tag='mia', timeout=45)
                assert rc['status'] == 200, 'http_' + str(rc['status'])
                o = json.loads(raw)
                assert str(o.get('id')) == f['id'], 'source_identifier_mismatch'
                title, artists, acc, dates = o.get('title'), [re.sub(r'^(?:artist|painter):\s*', '', o.get('artist') or '', flags=re.I).strip()], o.get('accession_number'), [o.get('dated')]
                credit = o.get('creditline') or ''
                url = 'https://collections.artsmia.org/art/' + f['id']
                evidence = {k: o.get(k) for k in ['id', 'title', 'artist', 'dated', 'accession_number', 'creditline', 'room', 'department']}
            elif provider == 'walters':
                assert re.fullmatch(r'[A-Za-z0-9.\-/]+', f['accession']), 'unusable_inventory'
                url = 'https://art.thewalters.org/object/' + f['accession'] + '/'
                raw, rc = r.capture(url, tag='walters', timeout=45)
                assert rc['status'] == 200, 'http_' + str(rc['status'])
                title, artists, stats = walters_fields(raw)
                acc, dates, credit = stats.get('Accession Number'), [stats.get('Date')], stats.get('Credit Line', '')
                evidence = {'title': title, 'artists': artists, 'stats': stats}
            elif provider == 'saam':
                raw, rc = r.capture('https://americanart.si.edu/collections/search/artwork/?id=' + f['id'], tag='saam', timeout=45)
                assert rc['status'] == 200, 'http_' + str(rc['status'])
                assert re.search(r'/artwork/[^/?]+-' + re.escape(f['id']) + r'/?$', rc['final_url']), 'redirected_object_identity_mismatch'
                title, stats = saam_fields(raw)
                artists, acc, dates, credit = [stats.get('Artist')], stats.get('Object Number'), [stats.get('Date')], stats.get('Credit Line', '')
                primary_name = artists[0]
                aliases = [name for name in f['artists'] if ',' in name and r.namekey(name.split(',', 1)[0]) == r.namekey(primary_name) and re.search(r'\b\d{4}\b', name.split(',', 1)[1]) and not re.search(r'attributed|workshop|follower|school|after|possibly', name, re.I)]
                artists.extend(aliases)
                url = rc['final_url']
                evidence = {'title': title, 'stats': stats, 'historical_full_creator_labels_with_exact_primary_name_prefix': aliases}
            else:
                raw, rc = r.capture('https://api.smk.dk/api/v1/art/', {'object_number': f['id'], 'lang': 'en'}, tag='smk', timeout=45)
                assert rc['status'] == 200, 'http_' + str(rc['status'])
                items = json.loads(raw).get('items', [])
                assert len(items) == 1 and items[0].get('object_number') == f['id'], 'exact_unique_inventory_required'
                o = items[0]
                active = [v for v in o.get('production', []) if not v.get('creator_qualifier') and not v.get('creator_role')]
                artists = [' '.join(filter(None, [v.get('creator_forename'), v.get('creator_surname')])) for v in active]
                titles = [t['title'] for t in o.get('titles', []) if t.get('title')]
                title = next((t for t in titles if p.titlekey(t) in {p.titlekey(row['artwork']['title']), p.titlekey(row['artwork'].get('alternate_title'))}), '')
                acc, dates, credit = o['object_number'], [v.get('period') for v in o.get('production_date', [])], o.get('acquisition_information', '')
                assert not o.get('deaccession_date') and o.get('acquisition_date'), 'accession_status_requires_review'
                url = o['frontend_url']
                evidence = {k: o.get(k) for k in ['id', 'object_number', 'titles', 'production', 'production_date', 'acquisition_date', 'acquisition_information', 'on_display', 'current_location', 'modified']}
            basis = index.match(row, provider + '-object', f['id'], [title], artists, acc, dates)
            assert basis.startswith(('unique_', 'existing_')), basis
            assert p.acckey(acc) == p.acckey(f['accession']), 'current_accession_mismatch'
            assert not re.search(r'\b(?:deaccession|on loan|lent by|returned to)\b', credit, re.I), 'holding_qualification'
            evidence['identity_selection'] = f
            c = p.claim(row, provider + '-object', f['id'], museum, rc, url, evidence, basis + '; exact_selected_inventory_rechecked_in_current_primary_catalogue')
            result = {'artwork_id': f['artwork_id'], 'claim': c, 'reason': 'primary_holding_supported'}
        except Exception as exc:
            result['reason'] = str(exc)[:300]
            if 'rc' in locals():
                result['source_receipt'] = rc
            if 'evidence' in locals():
                result['evidence'] = evidence
        r.save(dest, result)
        time.sleep(0.8)
        return result

    claims, holds = [], list(selected['held'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, result in enumerate(pool.map(one, selected['selected']), 1):
            (claims if 'claim' in result else holds).append(result['claim'] if 'claim' in result else result)
            if n % 50 == 0:
                print(provider, 'fresh objects', n, '/', len(selected['selected']), 'supported', len(claims), flush=True)
    p.output(version(provider), claims, holds)


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('provider', choices=sorted(MUSEUMS))
    a.add_argument('--selection-only', action='store_true')
    args = a.parse_args()
    (select if args.selection_only else capture)(p.Index(), args.provider)
