#!/usr/bin/env python3
"""Audit direct Wikidata book-image candidates; cache Commons rights metadata.

Metadata only. No database writes, publication, or image downloads. A Commons
image is not automatically a cover and a photographer's license does not clear
the underlying design. Selection is a separate, reviewed step.
"""
import datetime
import gzip
import hashlib
import json
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/research/book-covers-20260917'
SOURCE = ROOT / 'docs/research/historical-books-20260916'


def main():
    books = json.loads((SOURCE / 'books.json').read_text())
    wanted = {b['sourceId'] for b in books}
    entities, evidence = {}, {}
    for path in sorted((SOURCE / 'sources').glob('*.json.gz')):
        raw = path.read_bytes()
        for key, entity in json.loads(gzip.decompress(raw)).get('entities', {}).items():
            if key in wanted:
                entities[key] = entity
                evidence[key] = {'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(raw).hexdigest(), 'revision': entity.get('lastrevid')}
    candidates = []
    for book in books:
        for claim in entities.get(book['sourceId'], {}).get('claims', {}).get('P18', []):
            if claim.get('rank') != 'deprecated' and claim['mainsnak'].get('datavalue'):
                candidates.append({'bookId': book['id'], 'title': book['title'], 'sourceId': book['sourceId'],
                                   'file': claim['mainsnak']['datavalue']['value'], 'claimId': claim.get('id'),
                                   'qualifiers': claim.get('qualifiers'), 'workEvidence': evidence[book['sourceId']]})
    OUT.mkdir(exist_ok=True)
    (OUT / 'sources').mkdir(exist_ok=True)
    extra = OUT / 'additional-candidates.json'
    if extra.exists():
        candidates.extend(json.loads(extra.read_text()))
    (OUT / 'candidates.json').write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + '\n')
    filenames = sorted({c['file'] for c in candidates})
    existing_index = OUT / 'commons-index.json'
    pages = json.loads(existing_index.read_text()) if existing_index.exists() else {}
    failures = []
    batches, batch, encoded_length = [], [], 0
    for name in filenames:
        if name in pages:
            continue
        length = len(urllib.parse.quote('File:' + name, safe='')) + 3
        if batch and (len(batch) >= 20 or encoded_length + length > 5000):
            batches.append(batch)
            batch, encoded_length = [], 0
        batch.append(name)
        encoded_length += length
    if batch:
        batches.append(batch)
    for batch in batches:
        key = hashlib.sha256(json.dumps(batch).encode()).hexdigest()[:20]
        path = OUT / 'sources' / f'commons-{key}.json.gz'
        data = None
        if path.exists():
            data = json.loads(gzip.decompress(path.read_bytes()))
        else:
            params = {'action': 'query', 'format': 'json', 'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata|sha1',
                      'iiextmetadatalanguage': 'en', 'iiurlwidth': 600, 'titles': '|'.join('File:' + name for name in batch), 'redirects': 1, 'maxlag': 5}
            url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
            for attempt in range(4):
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'ArtlineBookCoverResearch/1.0 (source and reuse-rights audit; metadata only)'})
                    raw = urllib.request.urlopen(req, timeout=45).read()
                    data = json.loads(raw)
                    if 'error' in data:
                        if data['error'].get('code') == 'urlparamnormal' and 'iiurlwidth' in params:
                            # Some document files cannot render a thumbnail;
                            # retain their metadata without requesting a preview.
                            params.pop('iiurlwidth')
                            url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
                        raise ValueError(str(data['error']))
                    path.write_bytes(gzip.compress(raw))
                    break
                except Exception as exc:
                    if attempt == 3:
                        failures.append({'files': batch, 'error': str(exc)})
                        print(f'Batch failed: {exc}', flush=True)
                    else:
                        retry_after = int(exc.headers.get('Retry-After', '30')) if getattr(exc, 'code', None) == 429 else 2 ** attempt
                        time.sleep(min(120, retry_after))
            time.sleep(1)
        if data and data.get('query'):
            query = data['query']
            by_title = {p['title']: p for p in query.get('pages', {}).values()}
            renames = {x['from']: x['to'] for x in query.get('normalized', []) + query.get('redirects', [])}
            for name in batch:
                title = 'File:' + name
                seen = set()
                while title in renames and title not in seen:
                    seen.add(title)
                    title = renames[title]
                page = by_title.get(title)
                if page:
                    pages[name] = {'page': page, 'evidenceFile': str(path.relative_to(ROOT)), 'evidenceSha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        print(f'Commons metadata {len(pages)}/{len(filenames)}; failures {len(failures)}', flush=True)
    (OUT / 'commons-index.json').write_text(json.dumps(pages, ensure_ascii=False) + '\n')
    by_book = {}
    for candidate in candidates:
        by_book.setdefault(candidate['bookId'], []).append(candidate['file'])
    audit = [{'bookId': b['id'], 'sourceId': b['sourceId'], 'title': b['title'], 'candidates': by_book.get(b['id'], []),
              'status': 'pending-cover-and-rights-review' if b['id'] in by_book else 'no-direct-image-in-retained-source',
              'fallback': 'original-artline-typography'} for b in books]
    (OUT / 'book-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    summary = {'checkedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'booksAudited': len(books),
               'booksWithDirectImage': len(by_book), 'uniqueFiles': len(filenames), 'filesFetched': len(pages), 'failures': failures,
               'scope': 'Direct image claims from all 10,000 retained work records. Not an exhaustive search of all editions.'}
    (OUT / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
