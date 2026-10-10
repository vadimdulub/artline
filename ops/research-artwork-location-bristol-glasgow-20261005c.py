#!/usr/bin/env python3
"""Selected inventory lookups in two publicly available municipal catalogues."""
import argparse
import collections
import gzip
import importlib.util
import re
import subprocess
import time
import uuid
from pathlib import Path
from urllib.parse import urljoin, urlencode
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('m', Path(__file__).with_name('research-artwork-location-met-iwm-20261005c.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
r, p, h = m.r, m.p, m.h
ds = importlib.util.spec_from_file_location('date_notation', Path(__file__).with_name('refine-artwork-location-date-notation-20261005c.py'))
dn = importlib.util.module_from_spec(ds)
ds.loader.exec_module(dn)
SETTINGS = {'bristol': ('Q4968867', 'https://museums.bristol.gov.uk/'),
            'glasgow': ('Q41661713', 'https://collections.glasgowmuseums.com/mwebcgi/mweb')}


def selection(provider):
    result = []
    for v in r.load(r.RUN / 'remaining-wikidata-groups-20261005c.json.gz')[SETTINGS[provider][0]]:
        numbers = sorted({x for x in h.statements(v['entity'], 'P217') if isinstance(x, str) and x.strip()})
        if len(numbers) == 1:
            result.append({**v, 'inventory': numbers[0]})
    return result


class PublicCatalogue:
    def __init__(self, provider):
        self.provider, self.bootstrap = provider, None
        if provider == 'glasgow':
            url = SETTINGS[provider][1] + '?request=advform'
            raw, self.bootstrap = r.capture(url, tag='glasgow-public-search-form-20261005c', timeout=35)
            self.session = r.requests.Session()
            self.session.headers['User-Agent'] = r.UA
            # This is the catalogue's normal guest-session initialization,
            # with values issued in its public HTML; no account or added rights.
            pairs = re.findall(r"document.cookie='(user|realname|permissions)='\+escape\('([^']*)'\)", raw.decode())
            assert {k for k, _ in pairs} == {'user', 'realname', 'permissions'}
            for key, value in pairs:
                self.session.cookies.set(key, value, domain='collections.glasgowmuseums.com', path='/')

    def get(self, url):
        folder = r.RUN / (self.provider + '-selected-source-responses-20261005c')
        key = r.sha(url.encode())
        path, rcpath = folder / (key + '.body.gz'), folder / (key + '.receipt.json')
        if rcpath.exists():
            rc = r.load(rcpath)
            raw = gzip.decompress(path.read_bytes())
            assert r.sha(raw) == rc['sha256']
            return raw, rc
        if self.provider == 'bristol':
            # The system certificate store validates this older publisher site.
            # Keep normal verification; never use an insecure TLS override.
            result = subprocess.run(['curl', '--silent', '--show-error', '--location', '--connect-timeout', '10',
                '--max-time', '45', '--user-agent', r.UA, '--write-out', '\nARTLINE_RESPONSE_STATUS:%{http_code}\nARTLINE_RESPONSE_URL:%{url_effective}', url], capture_output=True)
            assert result.returncode == 0, result.stderr.decode()[:500]
            raw, suffix = result.stdout.rsplit(b'\nARTLINE_RESPONSE_STATUS:', 1)
            status, final = suffix.decode().split('\nARTLINE_RESPONSE_URL:', 1)
            status = int(status)
        else:
            response = self.session.get(url, timeout=(15, 45))
            raw, status, final = response.content, response.status_code, response.url
        rc = {'url': url, 'final_url': final, 'status': status, 'retrieved_at': r.now(), 'bytes': len(raw),
            'sha256': r.sha(raw), 'body_path': str(path.relative_to(r.ROOT)),
            'transport': 'curl with verified system trust store' if self.provider == 'bristol' else 'normal publisher-issued anonymous catalogue session'}
        if self.bootstrap:
            rc['anonymous_session_bootstrap'] = self.bootstrap
        r.save(path, gzip.compress(raw, mtime=0))
        r.save(rcpath, rc)
        assert status == 200, rc
        return raw, rc


def bristol_text(raw):
    text = raw.decode('utf-8', errors='surrogateescape')
    # A few legacy descriptions contain a standalone Windows-1252 pound
    # sign alongside otherwise valid UTF-8. Preserve those literal bytes.
    return ''.join(bytes([ord(c) - 0xdc00]).decode('cp1252', errors='replace') if 0xdc80 <= ord(c) <= 0xdcff else c for c in text)


def parse_object(provider, raw, url):
    # Bristol explicitly declares UTF-8. Guessing from short mostly-English
    # pages corrupts accented maker names even though their bytes are valid.
    sp = BeautifulSoup(bristol_text(raw) if provider == 'bristol' else raw, 'html.parser')
    fields = collections.defaultdict(list)
    if provider == 'bristol':
        for label in sp.select('p > label'):
            key = label.get_text(' ', strip=True).rstrip(':').strip()
            text = label.parent.get_text(' ', strip=True)
            value = text.removeprefix(label.get_text(' ', strip=True)).lstrip(' :')
            if value:
                fields[key].append(value)
        location_heading = sp.find(['h2', 'h3', 'h4'], string=re.compile('Current Location'))
        if location_heading:
            block = location_heading.find_parent(class_='row')
            if block:
                text = block.get_text(' ', strip=True).removeprefix('Current Location').strip()
                if text:
                    fields['Current Location'].append(text)
        makers = fields.get('Artist', [])
        assert fields.get('Object Number'), 'Not a Bristol object record'
    else:
        makers = []
        for dt in sp.select('dt'):
            dd = dt.find_next_sibling('dd')
            if dd:
                key = dt.get_text(' ', strip=True)
                fields[key].append(dd.get_text(' ', strip=True))
                if key == 'Artist/Maker':
                    makers.extend(a.get_text(' ', strip=True) for a in dd.select('a'))
        assert fields.get('ID Number'), 'Not a Glasgow object record'
    return {'url': url, 'fields': dict(fields), 'makers': makers}


def capture(provider):
    client = PublicCatalogue(provider)
    base = SETTINGS[provider][1]
    values = selection(provider)
    for n, v in enumerate(values, 1):
        path = r.RUN / (provider + '-selected-objects-20261005c') / (v['artwork_id'] + '.json.gz')
        if not path.exists():
            url = base + ('list.php?' + urlencode({'objnum': v['inventory']}) if provider == 'bristol' else '?' + urlencode({'request': 'advanced', '_t1108': v['inventory'], 'subset': '101'}))
            raw, rc = client.get(url)
            sp = BeautifulSoup(raw, 'html.parser')
            if provider == 'bristol':
                urls = {urljoin(base, a['href']) for a in sp.select('a[href]') if re.fullmatch(r'details\.php\?irn=\d+', a['href'])}
                count = re.search(r'\b(?:\d+)\s+to\s+(?:\d+)\s+of\s+(\d+)\b', sp.get_text(' ', strip=True))
            else:
                urls = {urljoin(base, a['href']) for a in sp.select('a[href]') if re.fullmatch(r'\?request=record;id=\d+;type=101', a['href'])}
                count = re.search(r'\b(\d+) results? for', sp.get_text(' ', strip=True))
            result_count = int(count[1]) if count else 0
            result = {'selection': v, 'search_receipt': rc, 'result_count': result_count, 'returned_object_urls': sorted(urls), 'objects': []}
            if 0 < result_count == len(urls) <= 5:
                for objurl in sorted(urls):
                    body, receipt = client.get(objurl)
                    obj = parse_object(provider, body, objurl)
                    key = 'Object Number' if provider == 'bristol' else 'ID Number'
                    if p.acckey(v['inventory']) in {p.acckey(x) for x in obj['fields'].get(key, [])}:
                        result['objects'].append({'object': obj, 'source_receipt': receipt})
                    time.sleep(.3)
            r.save_gz(path, result)
            time.sleep(.6)
        if n % 25 == 0:
            print(provider, 'selected inventories', n, '/', len(values), flush=True)
    r.save(r.RUN / (provider + '-capture-complete-20261005c.json'), {'at': r.now(), 'selected': len(values)})


def authorities(provider):
    qids = sorted({v['id'] for row in selection(provider) for v in h.statements(row['entity'], 'P170') if isinstance(v, dict) and v.get('id')})
    for start in range(0, len(qids), 50):
        path = r.RUN / (provider + '-artist-authorities-20261005c') / (str(start) + '.json.gz')
        if not path.exists():
            entities, receipt = r.wiki_entities(qids[start:start+50], tag=provider + '-artist-authorities-20261005c')
            r.save_gz(path, {'entities': entities, 'receipt': receipt})
    print(provider, 'artist authorities', len(qids), flush=True)


def title_key(value, dates):
    return m.iwm_titlekey(re.sub(r'^portrait of (?:the )?', '', r.norm(value)), dates)


def plan(provider, refined=False):
    assert (r.RUN / (provider + '-capture-complete-20261005c.json')).exists()
    index = p.Index()
    with r.connect('local') as db:
        qid = SETTINGS[provider][0] if provider == 'bristol' else 'Q54869705'
        museums = [v['i'] for v in db.execute('SELECT to_jsonb(i) i FROM institutions i WHERE wikidata_id=%s', (qid,))]
    authority = None
    if provider == 'glasgow':
        authority = r.load(r.RUN / 'glasgow-collection-service-authority-20261005c.json')
        if not museums:
            museums = [authority['institution']]
    if refined and provider == 'bristol':
        authority = r.load(r.RUN / 'mds-collection-authorities-20261005c.json')['Bristol Museums']
        authority['official_collection_scope_receipt'] = r.load(r.RUN / 'bristol-collection-authority-history-20261005c.json')
        assert authority['official_collection_scope_receipt']['status'] == 200
        museums = [authority['institution']]
    assert len(museums) == 1
    artist_authorities = {}
    if refined:
        for path in (r.RUN / (provider + '-artist-authorities-20261005c')).glob('*.json.gz'):
            batch = r.load(path)
            for qid, entity in batch['entities'].items():
                artist_authorities[qid] = {'names': [x['value'] for x in entity.get('labels', {}).values()] + [x['value'] for names in entity.get('aliases', {}).values() for x in names], 'source_receipt': batch['receipt']}
    claims, holds = [], []
    for v in selection(provider):
        path = r.RUN / (provider + '-selected-objects-20261005c') / (v['artwork_id'] + '.json.gz')
        captured = r.load(path)
        if len(captured['objects']) != 1:
            holds.append({'artwork_id': v['artwork_id'], 'reason': 'no_unique_current_inventory_match', 'capture_path': str(path)})
            continue
        selected = captured['objects'][0]
        obj, row = selected['object'], index.by_id[v['artwork_id']]
        if refined:
            rc = selected['source_receipt']
            raw = gzip.decompress((r.ROOT / rc['body_path']).read_bytes())
            assert r.sha(raw) == rc['sha256']
            obj = parse_object(provider, raw, obj['url'])
        f = obj['fields']
        titles, makers = list(f.get('Title', [])), list(obj['makers'])
        dates = f.get('Date of Production' if provider == 'bristol' else 'Date', [])
        for title in [row['artwork'].get(k) for k in ['title', 'alternate_title'] if row['artwork'].get(k)]:
            key = title_key if refined else m.iwm_titlekey
            if key(title, dates) in {key(t, dates) for t in titles}:
                titles.append(title)
        makers += [re.sub(r'\b(Sir|Dame|Lord|Mr|Mrs)\.?\s+', '', n) for n in makers]
        proofs = []
        if refined:
            for artist in h.statements(v['entity'], 'P170'):
                auth = artist_authorities.get(artist.get('id')) if isinstance(artist, dict) else None
                if auth and {r.namekey(n) for n in makers} & {r.namekey(n) for n in auth['names']}:
                    makers += auth['names']
                    proofs.append({'artist_qid': artist['id'], **auth})
        inventory = f['Object Number' if provider == 'bristol' else 'ID Number'][0]
        basis = index.match(row, 'wikidata', v['qid'], titles, makers, inventory, dates)
        if not basis.startswith(('existing_', 'unique_')):
            holds.append({'artwork_id': v['artwork_id'], 'reason': basis, 'capture_path': str(path), 'source_url': obj['url'], 'source_receipt': selected['source_receipt']})
            continue
        flags = []
        date = row['artwork'].get('date_display')
        if date and p.datekey(date) not in {p.datekey(d) for d in dates} and not (refined and any(dn.equivalent(date, d) for d in dates)):
            flags.append('date_wording_differs')
        if refined and len({r.namekey(n) for n in obj['makers']}) > 1:
            flags.append('multiple_named_creators_require_role_review')
        qualification_fields = ['Artist', 'Artist/Maker', 'Credit Line', 'Credit Line/Donor', 'Location', 'Current Location']
        qualifiers = ' '.join(text for key in qualification_fields for text in f.get(key, []))
        if re.search(r'\b(attributed|after|circle|workshop|copy|school of|loan|lent|deaccession\w*|missing|stolen)\b', r.norm(qualifiers)):
            flags.append('attribution_or_custody_qualification')
        oid = re.search(r'(?:irn=|;id=)(\d+)', obj['url'])[1]
        evidence = {'current_public_catalogue_record': obj, 'selection': v, 'search_receipt': captured['search_receipt'], 'qualifications': flags}
        if refined:
            evidence['format_and_creator_authority_reconciliation'] = {'creator_proofs': proofs, 'local_date': date, 'primary_dates': dates, 'date_meaning': dn.date_meaning(date), 'title_rule': 'Punctuation, sitter lifespan annotation and optional introductory Portrait of only. Exact inventory and named creator required.', 'parser': 'Explicit publisher UTF-8 and current-location row retained.'}
        if authority:
            evidence['museum_service_authority'] = authority
        if provider == 'bristol':
            evidence['catalogue_limitation'] = 'The council catalogue links to a newer site, which was unavailable to this research client. This is a documented holding in the still-public council catalogue; no fresh display observation is asserted.'
        c = p.claim(row, provider + '-object', oid, museums[0], selected['source_receipt'], obj['url'], evidence,
            basis + '; exact selected inventory in the public municipal museum catalogue')
        c['duplicate_source_urls'] = [obj['url'].replace('https://', 'http://')]
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Municipal catalogue candidate in review: ' + ', '.join(flags) + '. No metadata/publication change or current-display inference.'
        claims.append(c)
    p.output(provider + ('-refined' if refined else '') + '-20261005c', claims, holds)
    print('States', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan', 'authorities', 'refine'])
    parser.add_argument('provider', choices=list(SETTINGS))
    args = parser.parse_args()
    if args.command == 'refine':
        plan(args.provider, refined=True)
    else:
        globals()[args.command](args.provider)
