#!/usr/bin/env python3
"""Research exact museum records without mutating catalogue data."""
import argparse
import collections
import concurrent.futures
import csv
import gzip
import importlib.util
import io
import json
import re
import time
import uuid
from pathlib import Path

from bs4 import BeautifulSoup

spec = importlib.util.spec_from_file_location('locations', Path(__file__).with_name('research-artwork-locations-20261004.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def datekey(value):
    return re.sub(r'\s+', '', r.norm(value).replace('–', '-').replace('—', '-'))


def titlekey(value):
    return r.norm(value).replace('’', "'").replace("''", "'")


def acckey(value):
    return re.sub(r'[^\w]', '', r.norm(value))


def source(url):
    for path in (r.RUN / 'primary').glob('*.receipt.json'):
        rc = r.load(path)
        if rc['url'] == url and rc['status'] == 200:
            raw = gzip.decompress((r.ROOT / rc['body_path']).read_bytes())
            assert r.sha(raw) == rc['sha256']
            return raw, rc
    raw, rc = r.capture(url, tag='primary', timeout=180)
    assert rc['status'] == 200
    return raw, rc


class Index:
    def __init__(self):
        self.rows = r.load(r.RUN / 'missing-locations.json.gz')
        self.institutions = r.load(r.RUN / 'local-institutions.json')
        self.by_id = {x['artwork']['id']: x for x in self.rows}
        self.external = collections.defaultdict(list)
        self.supplied = collections.defaultdict(list)
        for row in self.rows:
            for e in row['identifiers']:
                self.external[(e['scheme'], e['external_id'])].append(row)
            for cells in row['supplied'] or []:
                self.supplied[(r.namekey(cells[0]), titlekey(cells[1]), titlekey(cells[3]))].append(row)

    def institution(self, slug):
        return next(i for i in self.institutions if i['slug'] == slug)

    def find(self, scheme, oid, titles, artists, museum_names):
        candidates = {x['artwork']['id']: x for x in self.external.get((scheme, str(oid)), [])}
        for name in artists:
            for title in titles:
                for museum in museum_names:
                    for row in self.supplied.get((r.namekey(name), titlekey(title), titlekey(museum)), []):
                        candidates[row['artwork']['id']] = row
        return list(candidates.values())

    def match(self, row, scheme, oid, titles, artists, accession, dates):
        a = row['artwork']
        if not {titlekey(a[k]) for k in ('title', 'alternate_title') if a.get(k)} & {titlekey(t) for t in titles if t}:
            return 'title_mismatch'
        names = {r.namekey(x['name']) for x in row['artists']} | {r.namekey(c[0]) for c in row['supplied'] or []}
        if a.get('unlinked_creator_label'):
            names.add(r.namekey(a['unlinked_creator_label']))
        if not names & {r.namekey(x) for x in artists}:
            return 'creator_mismatch'
        if a['accession_number'] and acckey(a['accession_number']) != acckey(accession):
            return 'inventory_mismatch'
        exact_id = any(e['scheme'] == scheme and e['external_id'] == str(oid) for e in row['identifiers'])
        if not exact_id:
            original_dates = {datekey(c[2]) for c in row['supplied'] or []}
            if not original_dates & {datekey(d) for d in dates}:
                return 'supplied_date_wording_mismatch'
        return 'existing_exact_object_id_title_creator_inventory' if exact_id else 'unique_exact_supplied_creator_title_collection_date'


def claim(row, scheme, oid, institution, rc, url, obj, basis, location=None):
    return {'artwork_id': row['artwork']['id'], 'title': row['artwork']['title'], 'scheme': scheme,
            'external_id': str(oid), 'institution': institution, 'source_url': url,
            'checked_at': rc['retrieved_at'], 'location_text': location or institution['name'],
            'identity_basis': basis, 'source_class': 'primary_museum_catalogue',
            'source_receipt': rc, 'object_evidence': obj, 'claim_type': 'holding',
            'limitation': 'Documented museum collection; no current display, room, loan destination or legal ownership is asserted.'}


def output(name, claims, holds):
    # A candidate matching several source objects stays unresolved.
    by_work = collections.defaultdict(list)
    for c in claims:
        by_work[c['artwork_id']].append(c)
    selected = []
    for aid, group in by_work.items():
        identities = {(c['scheme'], c['external_id']) for c in group}
        if len(identities) != 1:
            holds.append({'artwork_id': aid, 'reason': 'multiple_source_objects', 'identities': sorted(identities)})
        else:
            selected.append(group[0])
    r.save_gz(r.RUN / 'primary-plans' / (name + '.json.gz'), {'at': r.now(), 'claims': selected, 'holds': holds})
    print(name, 'supported candidates', len(selected), 'holds', len(holds), collections.Counter(h['reason'] for h in holds), flush=True)


def moma(index):
    raw, rc = source('https://media.githubusercontent.com/media/MuseumofModernArt/collection/main/Artworks.csv')
    museum = index.institution('wikimedia-museum-q188740')
    claims, holds = [], []
    for o in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        oid = o['ObjectID']
        rows = index.find('moma-object', oid, [o['Title']], [o['Artist']], ['Museum of Modern Art (MoMA)'])
        for row in rows:
            basis = index.match(row, 'moma-object', oid, [o['Title']], [o['Artist']], o['AccessionNumber'], [o['Date']])
            reason = None
            if o['Cataloged'] != 'Y':
                reason = 'museum_record_not_catalogued'
            elif re.search(r'\b(?:deaccession|on loan|lent by)\b', o['CreditLine'], re.I):
                reason = 'holding_qualification'
            elif not basis.startswith(('existing_', 'unique_')):
                reason = basis
            if reason:
                holds.append({'artwork_id': row['artwork']['id'], 'reason': reason, 'object_id': oid})
                continue
            evidence = {k: o[k] for k in ['ObjectID', 'Title', 'Artist', 'ConstituentID', 'Date', 'CreditLine', 'AccessionNumber', 'Classification', 'Department', 'Cataloged', 'URL']}
            claims.append(claim(row, 'moma-object', oid, museum, rc, o['URL'], evidence, basis))
    output('moma', claims, holds)


def fng(index):
    raw, rc = source('https://kokoelma.kansallisgalleria.fi/api/v1/objects')
    institutions = {
        'Kansallisgalleria / Ateneumin taidemuseo': ('ateneum-art-museum', 'Ateneum Art Museum', 'https://ateneum.fi/en/', 'Finnish National Gallery — Ateneum Art Museum'),
        'Kansallisgalleria / Sinebrychoffin taidemuseo': ('sinebrychoff-art-museum', 'Sinebrychoff Art Museum', 'https://sinebrychoffintaidemuseo.fi/en/', 'Finnish National Gallery — Sinebrychoff Art Museum'),
        'Kansallisgalleria / Nykytaiteen museo Kiasma': ('kiasma-museum-contemporary-art', 'Museum of Contemporary Art Kiasma', 'https://kiasma.fi/en/', 'Finnish National Gallery — Museum of Contemporary Art Kiasma'),
    }
    institutions['Kansallisgalleria / Nykytaiteen museo Kiasma, Helsinki'] = institutions['Kansallisgalleria / Nykytaiteen museo Kiasma']
    claims, holds = [], []
    for o in json.loads(raw):
        org = o.get('responsibleOrganisation')
        museum_info = institutions.get(org)
        artists = [' '.join(filter(None, [p.get('firstName'), p.get('familyName')])) for p in o.get('people', []) if p.get('role', {}).get('en') == 'Artist']
        titles = list((o.get('title') or {}).values())
        rows = index.find('fng-object', o['objectId'], titles, artists, [museum_info[3]] if museum_info else [])
        for row in rows:
            first, last = o.get('yearFrom'), o.get('yearTo') or o.get('yearFrom')
            date = '' if first is None else str(first) if first == last else f'{first}–{last}'
            prefix = (o.get('datePrefix') or {}).get('en', '')
            if prefix:
                date = prefix + ' ' + date
            basis = index.match(row, 'fng-object', o['objectId'], titles, artists, o.get('inventoryNumber'), [date])
            reason = None
            if not museum_info:
                reason = 'non_museum_or_unspecified_responsible_organization'
            elif o.get('category', {}).get('categoryId') != 'artwork':
                reason = 'record_is_not_whole_artwork'
            elif not basis.startswith(('existing_', 'unique_')):
                reason = basis
            if reason:
                holds.append({'artwork_id': row['artwork']['id'], 'reason': reason, 'object_id': o['objectId'], 'responsibleOrganisation': org})
                continue
            slug, name, website, supplied = museum_info
            institution = {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum-location/' + slug)), 'slug': slug, 'name': name, 'normalized_name': r.norm(name), 'website_url': website, 'kind': 'museum', 'status': 'review', 'wikidata_id': None, 'description': 'A constituent museum of the Finnish National Gallery. Object-to-museum assignments are documented by the official collection API responsibleOrganisation field. Collection membership does not establish present display.'}
            existing = [i for i in index.institutions if i['slug'] == slug]
            if existing:
                institution = existing[0]
            evidence = {k: o.get(k) for k in ['objectId', 'title', 'people', 'inventoryNumber', 'responsibleOrganisation', 'collection', 'owner', 'category', 'acquisitionDate', 'acquisitionYear', 'yearFrom', 'yearTo', 'datePrefix']}
            claims.append(claim(row, 'fng-object', o['objectId'], institution, rc, 'https://kokoelma.kansallisgalleria.fi/en/object/' + str(o['objectId']), evidence, basis))
    output('fng', claims, holds)


def mia(index):
    claims, holds = [], []
    wanted = [(key[1], rows) for key, rows in index.external.items() if key[0] == 'mia-object']
    museum = index.institution('minneapolis-institute-of-art')

    def one(item):
        oid, rows = item
        raw, rc = r.capture('https://search.artsmia.org/id/' + oid, tag='mia')
        if rc['status'] != 200:
            return [], [{'artwork_id': row['artwork']['id'], 'reason': 'source_http_' + str(rc['status'])} for row in rows]
        o = json.loads(raw)
        artists = [re.sub(r'^(?:artist|painter):\s*', '', o.get('artist') or '', flags=re.I).strip()]
        yes, no = [], []
        for row in rows:
            basis = index.match(row, 'mia-object', oid, [o.get('title')], artists, o.get('accession_number'), [o.get('dated')])
            if str(o.get('id')) != oid or not basis.startswith(('existing_', 'unique_')) or re.search(r'\b(?:deaccession|on loan|lent by)\b', o.get('creditline') or '', re.I):
                no.append({'artwork_id': row['artwork']['id'], 'reason': 'identity_or_holding_review', 'match': basis, 'source_id': o.get('id')})
                continue
            evidence = {k: o.get(k) for k in ['id', 'title', 'artist', 'dated', 'accession_number', 'creditline', 'department', 'room', 'classification', 'life_date']}
            yes.append(claim(row, 'mia-object', oid, museum, rc, 'https://collections.artsmia.org/art/' + oid, evidence, basis))
        time.sleep(0.4)
        return yes, no

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, (yes, no) in enumerate(pool.map(one, wanted), 1):
            claims.extend(yes)
            holds.extend(no)
            if n % 50 == 0:
                print('Mia museum objects checked', n, '/', len(wanted), flush=True)
    output('mia', claims, holds)


def walters(index):
    museum = index.institution('wikimedia-museum-q210081')
    wanted = [(row, e) for row in index.rows for e in row['identifiers'] if e['scheme'] == 'walters-object']
    claims, holds = [], []

    def one(item):
        row, e = item
        a = row['artwork']
        acc = a.get('accession_number') or ''
        if not re.fullmatch(r'[A-Za-z0-9.\-/]+', acc):
            return None, {'artwork_id': a['id'], 'reason': 'no_usable_museum_inventory'}
        url = 'https://art.thewalters.org/object/' + acc + '/'
        try:
            raw, rc = r.capture(url, tag='walters', timeout=45)
            if rc['status'] != 200:
                return None, {'artwork_id': a['id'], 'reason': 'http_' + str(rc['status'])}
            soup = BeautifulSoup(raw, 'html.parser')
            heading = soup.select_one('h1.artwork--title')
            title = heading.get_text(' ', strip=True) if heading else ''
            artists = [n.get_text(' ', strip=True).split(' (', 1)[0].strip() for n in soup.select('.section__author a')]
            stats = {}
            for node in soup.select('.stat'):
                h, value = node.find('h3'), node.find('p', recursive=False)
                if h and value:
                    key = h.get_text(' ', strip=True)
                    stats[key.split(' In libraries,')[0]] = value.get_text(' ', strip=True)
            inv = stats.get('Accession Number')
            basis = index.match(row, 'walters-object', e['external_id'], [title], artists, inv, [])
            if not basis.startswith('existing_') or re.search(r'deaccession|on loan|lent by', stats.get('Credit Line', ''), re.I):
                return None, {'artwork_id': a['id'], 'reason': 'primary_identity_or_holding_review', 'match': basis, 'source_title': title, 'artists': artists, 'stats': stats, 'source_receipt': rc}
            evidence = {'title': title, 'artists': artists, 'inventory': inv, 'stats': stats, 'original_external_id': e['external_id'], 'original_canonical_url': e['canonical_url']}
            return claim(row, 'walters-object', e['external_id'], museum, rc, url, evidence, 'existing_native_object_link_then_current_title_creator_and_exact_accession_on_official_collection_page'), None
        except Exception as exc:
            return None, {'artwork_id': a['id'], 'reason': 'source_error', 'error': type(exc).__name__ + ': ' + str(exc)[:200]}
        finally:
            time.sleep(0.5)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, (yes, no) in enumerate(pool.map(one, wanted), 1):
            if yes:
                claims.append(yes)
            if no:
                holds.append(no)
            if n % 50 == 0:
                print('Walters current object pages', n, '/', len(wanted), flush=True)
    output('walters-current', claims, holds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', choices=['moma', 'fng', 'mia', 'walters'])
    args = parser.parse_args()
    globals()[args.source](Index())
