#!/usr/bin/env python3
"""Bounded checks of existing artwork URLs in two current museum catalogues."""
import argparse
import collections
import gzip
import importlib.util
import re
import time
import uuid
from pathlib import Path
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('m', Path(__file__).with_name('research-artwork-location-bristol-glasgow-20261005c.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
r, p, h, dn = m.r, m.p, m.h, m.dn
SETTINGS = {'rmg': ('Q7374509', 'Royal Museums Greenwich', 'https://www.rmg.co.uk/'),
            'auckland': ('Q4819492', 'Auckland Art Gallery Toi o Tāmaki', 'https://www.aucklandartgallery.com/')}


def selection(provider):
    result = []
    for v in r.load(r.RUN / 'remaining-wikidata-groups-20261005c.json.gz')[SETTINGS[provider][0]]:
        urls = set()
        for text in m.m.nested_strings(v['entity']):
            if provider == 'rmg':
                match = re.search(r'rmg\.co\.uk/collections/objects/(?:rmgc-object-)?(\d+)', text)
                if match:
                    urls.add('https://www.rmg.co.uk/collections/objects/rmgc-object-' + match[1])
            elif re.fullmatch(r'https?://www\.aucklandartgallery\.com/explore-art-and-ideas/artwork/\d+/[^/?#]+/?', text):
                urls.add(text.replace('http://', 'https://').rstrip('/'))
        native = {re.search(r'(?:rmgc-object-|/artwork/)(\d+)', u)[1] for u in urls}
        if len(native) == 1:
            result.append({**v, 'url': sorted(urls)[0], 'native_id': native.pop(), 'alternate_source_urls': sorted(urls)})
    return result


def parse(provider, raw, url):
    sp = BeautifulSoup(raw, 'html.parser')
    fields = collections.defaultdict(list)
    if provider == 'rmg':
        for tr in sp.select('.collections-table tr'):
            key, value = tr.find('th'), tr.find('td')
            if key and value:
                label = key.get_text(' ', strip=True).rstrip(':')
                if label == 'Creator' and value.select('a'):
                    fields[label].extend(a.get_text(' ', strip=True) for a in value.select('a'))
                else:
                    fields[label].append(value.get_text(' ', strip=True))
        assert fields.get('ID') and sp.find('h1'), 'Missing current RMG object identity'
        fields['Title'] = [sp.find('h1').get_text(' ', strip=True)]
    else:
        for dt in sp.select('dl dt'):
            dd = dt.find_next_sibling('dd')
            if dd:
                fields[dt.get_text(' ', strip=True)].append(dd.get_text(' ', strip=True))
        assert fields.get('Accession No') and fields.get('Title'), 'Missing current Auckland object identity'
    return {'fields': dict(fields), 'url': url}


def capture(provider):
    values = selection(provider)
    for n, v in enumerate(values, 1):
        path = r.RUN / (provider + '-selected-objects-20261005c') / (v['artwork_id'] + '.json.gz')
        if not path.exists():
            raw, rc = r.capture(v['url'], tag=provider + '-current-primary-20261005c', timeout=45)
            assert rc['status'] not in [403, 429], 'Access limitation; stop this provider'
            result = {'selection': v, 'source_receipt': rc}
            if rc['status'] == 200:
                try:
                    result['object'] = parse(provider, raw, rc['final_url'])
                except AssertionError as exc:
                    result['reason'] = str(exc)
            else:
                result['reason'] = 'http_' + str(rc['status'])
            r.save_gz(path, result)
            time.sleep(.6)
        if n % 20 == 0:
            print(provider, 'current object records', n, '/', len(values), flush=True)
    r.save(r.RUN / (provider + '-capture-complete-20261005c.json'), {'at': r.now(), 'selected': len(values)})


def authorities():
    es, rc = r.wiki_entities([v[0] for v in SETTINGS.values()], tag='rmg-auckland-authorities-20261005c')
    with r.connect('local') as db:
        existing = [v['i'] for v in db.execute('SELECT to_jsonb(i) i FROM institutions i WHERE wikidata_id=ANY(%s)', ([v[0] for v in SETTINGS.values()],))]
    result = {}
    for provider, (qid, name, url) in SETTINGS.items():
        matches = [v for v in existing if v.get('wikidata_id') == qid]
        assert len(matches) <= 1
        institution = matches[0] if matches else {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum-location/authority/' + qid)), 'slug': 'museum-authority-' + qid.lower(), 'name': name, 'normalized_name': r.norm(name), 'kind': 'museum', 'status': 'review', 'wikidata_id': qid, 'website_url': url, 'description': 'Museum collection authority documented by its official collection records. Network-level holdings do not assert a branch or current physical/display location.'}
        result[provider] = {'institution': institution, 'museum_entity': es[qid], 'source_receipt': rc}
    r.save(r.RUN / 'rmg-auckland-authorities-20261005c.json', result)


def plan(provider, refined=False):
    assert (r.RUN / (provider + '-capture-complete-20261005c.json')).exists()
    index = p.Index()
    authority = r.load(r.RUN / 'rmg-auckland-authorities-20261005c.json')[provider]
    artist_authorities = {}
    if refined:
        for folder in ['mds', 'iwm', 'hunterian', 'bristol', 'glasgow']:
            for path in (r.RUN / (folder + '-artist-authorities-20261005c')).glob('*.json.gz'):
                batch = r.load(path)
                for qid, entity in batch['entities'].items():
                    artist_authorities[qid] = {'names': [x['value'] for x in entity.get('labels', {}).values()] + [x['value'] for names in entity.get('aliases', {}).values() for x in names], 'source_receipt': batch['receipt']}
    claims, holds = [], []
    for v in selection(provider):
        path = r.RUN / (provider + '-selected-objects-20261005c') / (v['artwork_id'] + '.json.gz')
        cap = r.load(path)
        if 'object' not in cap:
            holds.append({'artwork_id': v['artwork_id'], 'reason': cap['reason'], 'source_url': v['url'], 'source_receipt': cap['source_receipt']})
            continue
        obj, row = cap['object'], index.by_id[v['artwork_id']]
        if refined:
            raw = gzip.decompress((r.ROOT / cap['source_receipt']['body_path']).read_bytes())
            assert r.sha(raw) == cap['source_receipt']['sha256']
            obj = parse(provider, raw, obj['url'])
        f = obj['fields']
        inv = f['ID' if provider == 'rmg' else 'Accession No'][0]
        dates = f.get('Date made' if provider == 'rmg' else 'Production date', [])
        makers = list(f.get('Creator' if provider == 'rmg' else 'Artist', []))
        titles = list(f['Title'])
        for title in [row['artwork'].get(k) for k in ['title', 'alternate_title'] if row['artwork'].get(k)]:
            if m.title_key(title, dates) in {m.title_key(t, dates) for t in titles}:
                titles.append(title)
        makers += [re.sub(r'\b(Sir|Dame|Lord)\s+', '', n) for n in makers]
        proofs = []
        if refined:
            for artist in h.statements(v['entity'], 'P170'):
                auth = artist_authorities.get(artist.get('id')) if isinstance(artist, dict) else None
                if auth and {r.namekey(n) for n in makers} & {r.namekey(n) for n in auth['names']}:
                    makers += auth['names']
                    proofs.append({'artist_qid': artist['id'], **auth})
        basis = index.match(row, 'wikidata', v['qid'], titles, makers, inv, dates)
        if not basis.startswith(('existing_', 'unique_')):
            holds.append({'artwork_id': v['artwork_id'], 'reason': basis, 'source_url': obj['url'], 'source_receipt': cap['source_receipt'], 'capture_path': str(path)})
            continue
        flags = []
        numbers = [n for n in h.statements(v['entity'], 'P217') if isinstance(n, str)]
        if numbers and p.acckey(inv) not in {p.acckey(n) for n in numbers}:
            flags.append('secondary_inventory_conflict')
        date = row['artwork'].get('date_display')
        if not any(dn.equivalent(date, d) for d in dates):
            flags.append('date_meaning_unresolved')
        credit = ' '.join(f.get('Credit' if provider == 'rmg' else 'Credit line', []))
        source_institution = 'National Maritime Museum' if provider == 'rmg' else 'Auckland Art Gallery'
        if source_institution not in credit:
            flags.append('museum_credit_unconfirmed')
        text = ' '.join(makers + [credit] + f.get('Display location', []))
        if re.search(r'\b(attributed|after|style of|workshop|school|circle of|copy|loan|lent|deaccession\w*|missing|stolen)\b', r.norm(text)):
            flags.append('attribution_or_custody_qualification')
        primary_names = f.get('Creator' if provider == 'rmg' else 'Artist', [])
        if len({r.namekey(n) for n in primary_names}) > 1 and not any({r.namekey(n) for n in primary_names} <= {r.namekey(n) for n in proof['names']} for proof in proofs):
            flags.append('multiple_current_creators_require_review')
        c = p.claim(row, provider + '-object', v['native_id'], authority['institution'], cap['source_receipt'], obj['url'],
                    {'current_public_catalogue_record': obj, 'selection': v, 'collection_authority': authority, 'creator_authority_reconciliation': proofs, 'local_date': date, 'primary_dates': dates, 'date_meaning': dn.date_meaning(date), 'qualifications': flags}, basis + '; current native museum URL, title, named creator, accession and collection credit checked')
        c['duplicate_source_urls'] = sorted(set(v['alternate_source_urls'] + [v['url'], obj['url'].replace('https://', 'http://')]))
        if provider == 'rmg':
            c['duplicate_source_urls'] += ['http://collections.rmg.co.uk/collections/objects/' + v['native_id'] + '.html', 'https://collections.rmg.co.uk/collections/objects/' + v['native_id'] + '.html']
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Current primary museum candidate in review: ' + ', '.join(flags) + '. No original metadata or publication change, physical-location inference or current display assertion.'
        claims.append(c)
    p.output(provider + ('-refined' if refined else '') + '-20261005c', claims, holds)
    print('States', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan', 'authorities', 'refine'])
    parser.add_argument('provider', nargs='?', choices=list(SETTINGS))
    args = parser.parse_args()
    if args.command == 'authorities':
        authorities()
    elif args.command == 'refine':
        plan(args.provider, refined=True)
    else:
        globals()[args.command](args.provider)
