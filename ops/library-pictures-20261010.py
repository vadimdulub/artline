#!/usr/bin/env python3
"""Catalogue-wide library picture research. Database access is always read-only.

Discovery claims are leads, not accepted pictures. Source/rights and visual
selection are separate stages; existing application manifests are preserved.
"""
import argparse
import collections
import datetime
import gzip
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import re
import time
import unicodedata
import urllib.parse

import requests

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/library-pictures-20261010'
DATA = Path.home() / 'Library/Application Support/Artline'
ORIGINALS = DATA / 'source-images/library-pictures-20261010'
BACKUP = DATA / 'backups/library-pictures-20261010'
RESTORED = Path('/tmp/artline-library-restored')
MANIFESTS = {'books': ROOT / 'apps/server/internal/books/cover-selection.json',
             'events': ROOT / 'apps/server/internal/events/image-selection.json'}
SESSION = requests.Session()
SESSION.headers['User-Agent'] = 'ArtlineLibraryResearch/1.0 (https://artlines.org/about; selected images)'
_image_core = None


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'ops' / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value, immutable=True):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, default=str) + '\n').encode()
    if path.suffix == '.gz':
        raw = gzip.compress(raw, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and immutable:
        assert path.read_bytes() == raw, ('existing immutable evidence', str(path))
    else:
        temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
        temporary.write_bytes(raw)
        temporary.replace(path)


def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def plain(value):
    value = re.sub(r'<(?:style|script)\b[^>]*>.*?</(?:style|script)\s*>', ' ', str(value), flags=re.I | re.S)
    return ' '.join(html.unescape(re.sub('<[^>]*>', ' ', value)).split())


def artist_credit(value):
    if 'messagebox' in str(value) or '<style' in str(value):
        from bs4 import BeautifulSoup
        parsed = BeautifulSoup(str(value), 'html.parser')
        for element in parsed.select('style, script, .messagebox, .licensetpl_wrapper, .licensetpl'):
            element.decompose()
        return plain(str(parsed))
    return plain(value)


def image_core():
    global _image_core
    if _image_core is None:
        _image_core = module('library_image_core', 'enrich-artwork-images.py')
    return _image_core


def inventory():
    align = module('library_align', 'align-catalogues-20261008.py')
    for target in ['local', 'production']:
        path = RUN / (target + '-inventory.json.gz')
        if path.exists():
            continue
        result = {'target': target, 'at': now()}
        with align.connect(target, readonly=True) as db:
            for category, table in [('books', 'book_records'), ('events', 'event_records')]:
                result[category] = db.execute('SELECT id,source_id,status,record,source_checksum FROM ' + table + ' ORDER BY id').fetchall()
        save(path, result)
    for category, path in MANIFESTS.items():
        save(RUN / ('before-' + category + '.json'), load(path))
    rows = {}
    for target in ['production', 'local']:
        source = load(RUN / (target + '-inventory.json.gz'))
        for category in MANIFESTS:
            key = 'bookId' if category == 'books' else 'eventId'
            pictures = {r[key]: r for r in load(RUN / ('before-' + category + '.json'))}
            for row in source[category]:
                if row['status'] == 'archived':
                    continue
                r = row['record']
                record = rows.setdefault((category, row['id']), {
                    'category': category, 'id': row['id'], 'qid': row['source_id'],
                    'title': r['title'], 'author': r.get('author'),
                    'startYear': r.get('startYear'), 'endYear': r.get('endYear'),
                    'top100': r.get('top100', False), 'targets': [],
                    'sourceUrl': r.get('sourceUrl'), 'existing': pictures.get(row['id']),
                    'articleUrl': (r.get('overview') or {}).get('sourceUrl') or (r.get('descriptionSource') or {}).get('url'),
                })
                assert record['qid'] == row['source_id']
                if record['existing']:
                    assert record['existing']['sourceId'] == record['qid']
                record['targets'].append(target)
    save(RUN / 'inventory.json.gz', list(rows.values()))
    print('Inventory', collections.Counter(r['category'] for r in rows.values()), flush=True)


def discovery():
    rows = load(RUN / 'inventory.json.gz')
    wanted = {r['qid'] for r in rows}
    entities = {}
    folders = ['historical-books-20260916', 'historical-events-20260917',
               'library-illustrations-20261001', 'pre1850-books-20261001',
               'pre1850-books-20261002', 'books-5000bce-1850-20261004',
               'byzantine-books-20261001', 'war-books-africa-20261004']
    evidence = []
    for folder in folders:
        directory = ROOT / 'docs/research' / folder
        paths = sorted((directory / 'sources').glob('*.json.gz')) + sorted((directory / 'captures').glob('*.json'))
        if (directory / 'metadata.json').exists():
            paths.append(directory / 'metadata.json')
        for path in paths:
            if path.name.endswith('.receipt.json'):
                continue
            data = load(path)
            batch = data.get('entities', {}) if isinstance(data, dict) else {}
            if path.name == 'metadata.json':
                batch = {k: v['entity'] for k, v in data.items() if isinstance(v, dict) and 'entity' in v}
            matches = {q: e for q, e in batch.items() if q in wanted and 'claims' in e}
            if not matches:
                continue
            proof = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path.read_bytes()), 'fresh': False}
            evidence.append(proof)
            for qid, entity in matches.items():
                old = entities.get(qid)
                if old is None or (entity.get('lastrevid') or 0) > (old['entity'].get('lastrevid') or 0):
                    # Keep only evidence needed for images and work identity.
                    entities[qid] = {'entity': {k: entity.get(k) for k in ['id', 'lastrevid', 'labels', 'sitelinks']} | {
                        'claims': {k: v for k, v in entity['claims'].items() if k in ['P18', 'P996', 'P373', 'P935', 'P50']}}, 'evidence': proof}
    candidates = []
    missing = []
    for row in rows:
        source = entities.get(row['qid'])
        if not source:
            missing.append({'category': row['category'], 'id': row['id'], 'qid': row['qid']})
            continue
        e = source['entity']
        for prop in ['P18', 'P996']:
            for claim in (e.get('claims') or {}).get(prop, []):
                val = claim.get('mainsnak', {}).get('datavalue', {}).get('value')
                if claim.get('rank') == 'deprecated' or not isinstance(val, str):
                    continue
                candidates.append({'category': row['category'], 'id': row['id'], 'qid': row['qid'], 'title': row['title'],
                    'file': val, 'property': prop, 'claimId': claim.get('id'), 'rank': claim.get('rank'),
                    'qualifiers': claim.get('qualifiers'), 'workEvidence': source['evidence'], 'entityRevision': e.get('lastrevid')})
    save(RUN / 'entities.json.gz', entities)
    save(RUN / 'candidates.json.gz', candidates)
    save(RUN / 'missing-entities.json', missing)
    save(RUN / 'discovery-summary.json', {'records': len(rows), 'entityIdentities': len(entities), 'missingEntities': len(missing),
        'candidates': len(candidates), 'candidateFiles': len({r['file'] for r in candidates}),
        'candidateRecords': dict(collections.Counter(category for category, _ in {(r['category'], r['id']) for r in candidates})),
        'basis': 'Retained exact work/event claims. Every candidate still requires source identity, permission and visual review.'})
    print(load(RUN / 'discovery-summary.json'), flush=True)


def capture(params, host='commons.wikimedia.org'):
    params = {'format': 'json', 'formatversion': 2, 'maxlag': 5} | params
    url = 'https://' + host + '/w/api.php?' + urllib.parse.urlencode(params)
    key = sha(url.encode())
    path = RUN / 'captures' / (key + '.json.gz')
    receipt = path.with_name(key + '.receipt.json')
    if path.exists():
        proof = load(receipt)
        assert sha(path.read_bytes()) == proof['archiveSha256']
        return load(path), proof
    hold = RUN / 'access-holds' / (host + '.json')
    if hold.exists():
        raise RuntimeError('Provider held: ' + host)
    for attempt in range(5):
        image_core().provider_rate_slot(host)
        response = SESSION.get(url, timeout=(15, 65))
        if response.status_code in [401, 403, 429]:
            save(hold, {'url': url, 'status': response.status_code, 'at': now(), 'retryAfter': response.headers.get('Retry-After')})
            if response.status_code == 429:
                image_core().provider_rate_slot(host, cooldown=image_core().retry_delay(response.headers.get('Retry-After')))
        response.raise_for_status()
        assert len(response.content) < 20_000_000
        data = response.json()
        error = data.get('error')
        if error and error.get('code') == 'maxlag' and attempt < 4:
            delay = max(30, min(60, image_core().retry_delay(response.headers.get('Retry-After'))))
            print('Provider database lag; respectful retry', host, attempt + 1, 'in', delay, 'seconds', flush=True)
            time.sleep(delay)
            continue
        if error:
            raise RuntimeError(str(error))
        break
    raw = gzip.compress(response.content, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    proof = {'path': str(path.relative_to(ROOT)), 'sha256': sha(response.content), 'archiveSha256': sha(raw),
             'url': response.url, 'retrievedAt': now(), 'fresh': True}
    save(receipt, proof)
    return data, proof


def metadata():
    candidates = all_candidates()
    needed = {r['file'] for r in candidates}
    pages = {}
    old = RESTORED / 'docs/research/book-covers-20260917/commons-index.json'
    if old.exists():
        for filename, entry in load(old).items():
            if filename in needed:
                pages[filename] = entry | {'fresh': False}
    for folder in ['library-illustrations-20261001', 'books-5000bce-1850-20261004']:
        for filename in ['candidates.json', 'image-candidates.json', 'image-followup-candidates.json', 'image-exact-candidates.json']:
            path = ROOT / 'docs/research' / folder / filename
            if not path.exists():
                continue
            for row in load(path):
                if row.get('file') in needed and row.get('page', {}).get('imageinfo'):
                    pages[row['file']] = {k: row[k] for k in ['page', 'source', 'evidenceFile', 'evidenceSha256'] if k in row} | {'fresh': False}
    path = RUN / 'commons-index.json.gz'
    if path.exists():
        pages.update(load(path))
    missing = sorted(needed - pages.keys())
    for offset in range(0, len(missing), 20):
        batch = missing[offset:offset + 20]
        try:
            data, proof = capture({'action': 'query', 'titles': '|'.join('File:' + f for f in batch), 'redirects': 1,
                'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata|sha1', 'iiextmetadatalanguage': 'en', 'iiurlwidth': 640})
            query = data['query']
            bytitle = {p['title']: p for p in query['pages']}
            rename = {r['from']: r['to'] for r in query.get('normalized', []) + query.get('redirects', [])}
            for name in batch:
                title = 'File:' + name
                for _ in range(10):
                    title = rename.get(title, title)
                pages[name] = {'page': bytitle.get(title, {}), 'source': proof, 'fresh': True}
        except Exception as error:
            save(RUN / 'metadata-errors' / (sha('|'.join(batch).encode()) + '.json'), {'files': batch, 'error': str(error), 'at': now()})
            if (RUN / 'access-holds/commons.wikimedia.org.json').exists():
                break
        save(path, pages, immutable=False)
        print('Commons metadata', len(pages), '/', len(needed), flush=True)
    save(path, pages, immutable=False)


def articles():
    rows = load(RUN / 'inventory.json.gz')
    entities = load(RUN / 'entities.json.gz')
    seen = {(r['category'], r['id']) for r in load(RUN / 'candidates.json.gz')}
    wanted, audit, candidates = [], [], []
    for row in rows:
        if row['existing'] or (row['category'], row['id']) in seen:
            continue
        e = entities.get(row['qid'], {}).get('entity', {})
        title = ((e.get('sitelinks') or {}).get('enwiki') or {}).get('title')
        if not title and (row.get('articleUrl') or '').startswith('https://en.wikipedia.org/wiki/'):
            title = urllib.parse.unquote(row['articleUrl'].split('/wiki/', 1)[1]).replace('_', ' ')
        if title:
            wanted.append(row | {'articleTitle': title})
        else:
            audit.append({'id': row['id'], 'category': row['category'], 'decision': 'no-matched-english-article'})
    for offset in range(0, len(wanted), 30):
        batch = wanted[offset:offset + 30]
        try:
            data, proof = capture({'action': 'query', 'titles': '|'.join(r['articleTitle'] for r in batch), 'redirects': 1,
                'prop': 'pageimages|pageprops|revisions', 'piprop': 'name|original', 'pifilter': 'free',
                'pilimit': 30, 'ppprop': 'wikibase_item', 'rvprop': 'ids|timestamp'}, host='en.wikipedia.org')
            query = data['query']
            pages = {p['title']: p for p in query['pages']}
            rename = {r['from']: r['to'] for r in query.get('normalized', []) + query.get('redirects', [])}
            for row in batch:
                title = row['articleTitle']
                for _ in range(10):
                    title = rename.get(title, title)
                page = pages.get(title, {})
                same = page.get('pageprops', {}).get('wikibase_item') == row['qid']
                filename = page.get('pageimage')
                decision = 'identity-mismatch' if not same else ('candidate-found' if filename else 'no-free-lead-image')
                audit.append({'id': row['id'], 'category': row['category'], 'articleTitle': title, 'decision': decision, 'source': proof})
                if same and filename:
                    candidates.append({'category': row['category'], 'id': row['id'], 'qid': row['qid'], 'title': row['title'],
                        'file': filename, 'property': 'matched-article-free-lead', 'workEvidence': proof,
                        'articleTitle': title, 'articleRevision': page.get('revisions'), 'original': page.get('original')})
        except Exception as error:
            save(RUN / 'article-errors' / (str(offset) + '.json'), {'ids': [r['id'] for r in batch], 'error': str(error), 'at': now()})
            if (RUN / 'access-holds/en.wikipedia.org.json').exists():
                break
        save(RUN / 'article-audit.json.gz', audit, immutable=False)
        save(RUN / 'article-candidates.json.gz', candidates, immutable=False)
        print('Matched articles', offset + len(batch), '/', len(wanted), 'candidate pictures', len(candidates), flush=True)
    save(RUN / 'article-audit.json.gz', audit, immutable=False)
    save(RUN / 'article-candidates.json.gz', candidates, immutable=False)


def all_candidates():
    result = load(RUN / 'candidates.json.gz')
    for extra in ['article-candidates.json.gz', 'manual-candidates.json.gz', 'author-candidates.json.gz', 'next-article-candidates.json.gz', 'custom-event-candidates.json.gz']:
        if (RUN / extra).exists():
            result += load(RUN / extra)
    return result


def authors():
    creators = {r['id']: r for r in load(RUN / 'creators.json.gz') if r['record'].get('kind') == 'person'}
    inventory = {r['id']: r for r in load(RUN / 'inventory.json.gz') if r['category'] == 'books' and not r['existing']}
    links = [r for r in load(RUN / 'creator-links.json.gz') if r['book_id'] in inventory and r['creator_id'] in creators and r['position'] == 0]
    wanted = {r['creator_id'] for r in links}
    entities = {}
    directory = ROOT / 'docs/research/book-context-20260922'
    for path in sorted((directory / 'creator-entities').glob('*.json')):
        if path.stem in wanted:
            entities[path.stem] = load(path)
    for folder in [directory / 'sources', ROOT / 'docs/research/historical-books-20260916/sources']:
        for path in sorted(folder.glob('*.json.gz')):
            data = load(path)
            for qid, e in data.get('entities', {}).items():
                if qid in wanted and 'claims' in e and (qid not in entities or (e.get('lastrevid') or 0) > (entities[qid]['entity'].get('lastrevid') or 0)):
                    entities[qid] = {'entity': e, 'receipt': {'path': str(path.relative_to(ROOT)), 'sha256': sha(path.read_bytes()), 'fresh': False}}
    result = []
    for link in links:
        qid = link['creator_id']
        row, creator = inventory[link['book_id']], creators[qid]
        source = entities.get(qid)
        if not source:
            continue
        for claim in source['entity'].get('claims', {}).get('P18', []):
            filename = claim.get('mainsnak', {}).get('datavalue', {}).get('value')
            if claim.get('rank') == 'deprecated' or not isinstance(filename, str):
                continue
            result.append({'category': 'books', 'id': row['id'], 'qid': row['qid'], 'title': row['title'],
                'file': filename, 'property': 'author-portrait', 'claimId': claim.get('id'),
                'creatorId': qid, 'creatorName': creator['name'], 'creatorLink': link,
                'workEvidence': {'inventory': 'production-inventory.json.gz', 'links': 'creator-links.json.gz', 'creatorSourceChecksum': creator['source_checksum']},
                'portraitEvidence': source.get('receipt'), 'entityRevision': source['entity'].get('lastrevid')})
    save(RUN / 'author-candidates.json.gz', result)
    save(RUN / 'author-discovery-summary.json', {'authorIdentities': len(entities), 'wantedAuthors': len(wanted), 'bookCandidates': len(result),
        'uniqueFiles': len({r['file'] for r in result}), 'books': len({r['id'] for r in result}),
        'scope': 'Last fallback only: a clearly labelled portrait of the already linked first credited creator, never represented as a book cover.'})
    print(load(RUN / 'author-discovery-summary.json'), flush=True)


def source_review(row, entry):
    """Permission/format triage only; never substitutes for identity/visual QA."""
    info = entry.get('page', {}).get('imageinfo', [{}])[0]
    meta = info.get('extmetadata', {})
    val = lambda key: plain(meta.get(key, {}).get('value', ''))
    if not meta:
        return None, 'source-metadata-unavailable'
    cats, origin = val('Categories'), val('Credit')
    if re.search(r'child sexual abuse|erotic activities involving children|sexual exploitation of children', cats, re.I):
        return None, 'excluded-sexual-content-involving-minors'
    if re.search(r'AI-generated|AI generated|generated by (?:an? )?(?:AI|neural network)|created by (?:an? )?neural network|Stable Diffusion|Midjourney', cats + ' ' + val('ImageDescription'), re.I):
        return None, 'synthetic-image-needs-explicit-context-review'
    if val('Restrictions') or re.search(r'disputed copyright|copyright violations?|copyright claims|deletion requests?|missing permission|no permission|possibly unfree|fair use|de minimis|freedom of panorama|unfree|permission pending|license review needed|license review failed', cats, re.I):
        return None, 'rights-warning-or-restriction'
    if not origin or re.fullmatch(r'(?:unknown(?: source)?\s*)+', origin, re.I):
        return None, 'reproduction-origin-not-established'
    origin_raw = str(meta.get('Credit', {}).get('value', ''))
    if not re.search(r'href\s*=', origin_raw, re.I) and re.fullmatch(r'(?:public domain|internet|google)[.\s]*', origin, re.I):
        return None, 'reproduction-origin-not-established'
    if re.search(r'gallica|bnf\.fr|Biblioth[eè]que nationale de France', origin_raw, re.I):
        return None, 'bnf-commercial-reuse-needs-clearance'
    custodian_evidence = origin_raw + ' ' + val('ImageDescription') + ' ' + cats
    if re.search(r'Biblioteca (?:Nazionale|Medicea|Angelica|Casanatense|Braidense)|Library Medicea Laurentiana|Laurentian(?: Medici)? Library|Museo (?:archeologico nazionale|Nazionale del Risorgimento|del Risorgimento \(Milan\))|Palazzo Vecchio|Palazzo Pubblico \(Siena\)|Musei Capitolini|Palazzo Altemps|beniculturali\.it|cultura\.gov\.it|museogalileo|gutenberg\.beic\.it', custodian_evidence, re.I):
        return None, 'italian-custodian-permission-needs-review'
    if re.search(r'non[ -]?commercial|personal use only|study only', origin, re.I):
        return None, 'source-use-needs-review'
    license_name, license_url = val('LicenseShortName'), val('LicenseUrl')
    agency_evidence = origin + ' ' + val('Artist') + ' ' + val('ImageDescription')
    if license_name != 'Public domain' and not re.search(r'VRTS permission confirmed|OTRS permission', cats, re.I) and re.search(r'Getty Images|Agence France.Presse|\bReuters\b|\bEPA[ -]+(?:ELTA|EFE|PHOTO)', agency_evidence, re.I):
        return None, 'agency-image-permission-not-established'
    if license_name == 'Public domain':
        license_url = 'https://creativecommons.org/publicdomain/mark/1.0/'
        us_formality = re.search(r'PD[ -]US[^|]*(?:no notice|defective notice|not renewed|only)', cats, re.I)
        other_term = re.search(r'PD[ -]old(?! missing)|PD-anon-expired|PD-(?:South-Africa|SouthAfrica|UK|Canada|Australia|Russia|Germany|France)|PD US Government', cats, re.I)
        if us_formality and not other_term:
            return None, 'public-domain-only-us-needs-territorial-review'
        if re.search(r'PD Italy \(20 years after creation\)', cats) and not re.search(r'PD-1996|PD-old-(?:[7-9]\d|\d{3}|auto)|Author died more than (?:70|100) years', cats, re.I):
            return None, 'italian-20-year-photo-term-needs-territorial-review'
        if re.search(r'PD-old-[0-6]\d(?:-|\b)', cats) and not re.search(r'PD-old-(?:[7-9]\d|\d{3})(?:-|\b)', cats):
            return None, 'creator-term-under-70-years-needs-territorial-review'
        if re.search(r'author died less than (?:50|70) years ago', cats, re.I):
            return None, 'creator-term-under-70-years-needs-territorial-review'
    elif license_name == 'CC0':
        license_url = 'https://creativecommons.org/publicdomain/zero/1.0/'
    elif not re.fullmatch(r'CC BY(?:-SA)? (?:[1-4]\.0|2\.5)(?: [a-z]{2,3})?', license_name):
        return None, 'unsupported-or-unresolved-license'
    license_url = license_url.replace('http://', 'https://', 1)
    if not license_url.startswith('https://creativecommons.org/'):
        return None, 'missing-license-link'
    credit = val('Attribution') or artist_credit(meta.get('Artist', {}).get('value', ''))
    if not credit or re.fullmatch(r'(?:unknown(?: author| illustrator)?\s*)+', credit, re.I):
        if license_name == 'Public domain' and val('AttributionRequired').lower() == 'false':
            credit = 'Creator not identified in the source'
        else:
            return None, 'credit-needs-review'
    if row['category'] == 'books' and row.get('property') != 'author-portrait':
        text_design = re.search(r'PD[ -](?:text(?:logo)?|ineligible)(?:[ |(]|$)', cats, re.I)
        old_design = re.search(r'PD[ -]Old(?! missing)(?:[ |(]|$)|PD-old-(?:[7-9]\d|\d{3}|auto)|Author died more than (?:70|100) years|PD-anon-expired', cats, re.I)
        date_years = [int(y) for y in re.findall(r'(?<!\d)(1\d{3}|20\d{2})(?!\d)', val('DateTimeOriginal').split('date QS:', 1)[0])]
        old_publication = bool(date_years and max(date_years) <= 1930)
        expired = bool(re.search(r'PD-old-(?:[7-9]\d|\d{3}|auto)-expired|PD-anon-expired|PD US expired', cats))
        if not text_design and not (old_design and (old_publication or expired)):
            return None, 'underlying-book-design-rights-not-established'
    mime = info.get('mime', '')
    if mime not in ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/tiff', 'image/svg+xml', 'image/vnd.djvu', 'application/pdf']:
        return None, 'unsupported-format'
    url = info.get('thumburl') or info.get('url', '')
    if mime in ['image/svg+xml', 'image/vnd.djvu', 'application/pdf'] and not info.get('thumburl'):
        return None, 'no-raster-preview'
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ['upload.wikimedia.org', 'thumb.wikimedia.org']:
        return None, 'unsupported-image-host'
    source_url = info.get('descriptionurl', '')
    if not source_url.startswith('https://commons.wikimedia.org/wiki/File:'):
        return None, 'missing-source-page'
    return {'license': license_name, 'licenseUrl': license_url, 'credit': credit, 'sourceUrl': source_url,
            'sourceImageUrl': url, 'description': val('ImageDescription'), 'date': val('DateTimeOriginal'),
            'categories': cats, 'origin': origin, 'mime': mime, 'fileSha1': info.get('sha1'),
            'fresh': entry.get('fresh', False)}, 'eligible-for-identity-review'


def triage():
    inventory = {(r['category'], r['id']): r for r in load(RUN / 'inventory.json.gz')}
    pages = load(RUN / 'commons-index.json.gz')
    decisions = []
    for i, candidate in enumerate(all_candidates()):
        if inventory[candidate['category'], candidate['id']]['existing']:
            decision, reviewed = 'existing-picture-preserved', None
        else:
            reviewed, decision = source_review(candidate, pages.get(candidate['file'], {}))
        decisions.append(candidate | {'candidateIndex': i, 'decision': decision, 'reviewed': reviewed})
    save(RUN / 'triage.json.gz', decisions, immutable=False)
    for cat in MANIFESTS:
        group = [r for r in decisions if r['category'] == cat]
        print(cat, dict(collections.Counter(r['decision'] for r in group)), flush=True)
        print('eligible records', len({r['id'] for r in group if r['reviewed']}), flush=True)


STOPWORDS = set('the and for from with book history edition first second volume novel tale story collected works selected poems of in de la le les der die das des und ein eine von del el los las il lo gli di un una du des sur et to at on a an by as or'.split())


def words(text):
    value = ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))
    return {w for w in re.findall(r'[^\W_]+', value) if len(w) >= 4 and not w.isdigit() and w not in STOPWORDS}


def propose():
    rows = load(RUN / 'triage.json.gz')
    entities = load(RUN / 'entities.json.gz')
    inventory = {(r['category'], r['id']): r for r in load(RUN / 'inventory.json.gz')}
    groups = collections.defaultdict(list)
    for r in rows:
        if not r['reviewed']:
            continue
        meta = r['reviewed']
        entity = entities.get(r['qid'], {}).get('entity', {})
        names = [r['title']] + [v['value'] for v in (entity.get('labels') or {}).values()]
        if r.get('property') == 'author-portrait':
            names = [r['creatorName']]
        text = r['file'] + ' ' + meta['description']
        common = max((len(words(name) & words(text)) for name in names), default=0)
        # This ranks candidates for review, never confers approval.
        cover = bool(re.search(r'cover|title.?page|titelblatt|portada|frontespizio|обложк|титульн', r['file'] + ' ' + meta['description'][:120], re.I))
        document = meta['mime'] in ['image/vnd.djvu', 'application/pdf']
        rank = min(common, 5) * 10 + (8 if cover else 0) + (2 if r['property'] == 'P18' else 0) - (10 if document else 0)
        if r.get('property') == 'author-portrait':
            rank -= 1000
        groups[r['category'], r['id']].append(r | {'identityWordMatches': common, 'rankScore': rank})
    proposals = []
    for key, values in sorted(groups.items()):
        ordered = sorted(values, key=lambda r: (-r['rankScore'], r['file']))
        best = ordered[0]
        meta = best['reviewed']
        text = best['file'] + ' ' + meta['description'][:300]
        if best.get('property') == 'author-portrait':
            label = 'Author portrait: ' + best['creatorName']
        elif best['category'] == 'books':
            if re.search(r'title.?page|titelblatt|frontespizio|титульн', text, re.I):
                label = 'Title page'
            elif re.search(r'cover|couverture|portada|обложк|dust.?jacket', text, re.I):
                label = 'Edition cover'
            elif re.search(r'manuscript|codex|papyrus|papyri|handwritten|manuscri|рукопис', text, re.I):
                label = 'Manuscript page'
            elif re.search(r'illustrat|engraving|woodcut|drawing|painting|gemalde|иллюстрац', text, re.I):
                label = 'Associated illustration'
            else:
                label = 'Associated image'
        else:
            label = 'Map' if re.search(r'\b(?:maps?|cartes?|karten?)\b|地図|地圖|\bкарта\b', text, re.I) else 'Associated image'
            if label != 'Map' and re.search(r'photograph|photo\b|фотограф', text, re.I):
                label = 'Photograph'
        source_title = re.sub(r'\.(?:jpe?g|png|gif|svg|tiff?|pdf|djvu|webp)$', '', best['file'], flags=re.I).replace('_', ' ')
        date = meta['date'].split('date QS:', 1)[0].strip()
        best['proposedLabel'] = label + (' · ' + date if re.fullmatch(r'(?:circa |c\. )?\d{3,4}', date) else '')
        best['sourceTitle'] = source_title
        best['alternatives'] = [r['file'] for r in ordered[1:]]
        best['visualReview'] = 'pending'
        best['identityReview'] = 'pending'
        proposals.append(best)
    save(RUN / 'proposals.json.gz', proposals, immutable=False)
    print('Proposed for review', dict(collections.Counter(r['category'] for r in proposals)), flush=True)
    for cat in MANIFESTS:
        group = [r for r in proposals if r['category'] == cat]
        print(cat, 'no matching title words', sum(r['identityWordMatches'] == 0 for r in group), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['inventory', 'discovery', 'metadata', 'articles', 'triage', 'propose', 'authors'])
    args = parser.parse_args()
    globals()[args.phase]()
