#!/usr/bin/env python3
"""Evidence-led Cyprus collection review. Local catalogue only; no publication."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import time
from urllib.parse import urlsplit, urljoin, urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed

from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row
import requests

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/cyprus-collections-20260921'
BACKUP = Path.home() / 'Library/Application Support/Artline/backups/cyprus-collections-20260921'
DSN = 'postgres://localhost/artline'


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = data if isinstance(data, bytes) else (json.dumps(data, ensure_ascii=False, indent=2, default=str) + '\n').encode()
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('Existing evidence differs: ' + str(path))
        return
    path.write_bytes(raw)


def capture(url):
    key = hashlib.sha256(url.encode()).hexdigest()[:24]
    path = RUN / 'captures' / (key + '.html')
    receipt = path.with_suffix('.json')
    if receipt.exists():
        meta = json.loads(receipt.read_text())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == meta['sha256']
        return path, meta
    response = requests.get(url, headers={'User-Agent': 'Artline/1.0 (Cyprus collection metadata research)'}, timeout=(15, 40))
    response.raise_for_status()
    assert len(response.content) < 20_000_000, 'Metadata capture exceeds bound'
    meta = {'url': url, 'final_url': response.url, 'retrieved_at': now(), 'status': response.status_code,
            'sha256': hashlib.sha256(response.content).hexdigest(), 'bytes': len(response.content),
            'path': str(path.relative_to(ROOT))}
    save(path, response.content)
    save(receipt, meta)
    soup = BeautifulSoup(response.content, 'html.parser')
    for node in soup(['script', 'style', 'noscript']):
        node.decompose()
    save(path.with_suffix('.txt'), soup.get_text('\n', strip=True).encode())
    time.sleep(0.5)
    return path, meta


def audit():
    destination = RUN / 'baseline.json'
    if destination.exists():
        print('Baseline preserved')
        return
    with psycopg.connect(DSN, options='-c default_transaction_read_only=on -c statement_timeout=15000', row_factory=dict_row) as db:
        artists = db.execute("""SELECT a.*, (SELECT jsonb_agg(to_jsonb(ac)) FROM artist_countries ac WHERE ac.artist_id=a.id) countries,
          (SELECT jsonb_agg(alias) FROM artist_aliases al WHERE al.artist_id=a.id) aliases,
          (SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id) identifiers
          FROM artists a WHERE EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=a.id AND ac.country_code='CY') ORDER BY a.display_name""").fetchall()
        works = db.execute("""SELECT a.*,
          (SELECT jsonb_agg(to_jsonb(aa)) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creators,
          (SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers,
          (SELECT jsonb_agg(to_jsonb(c)) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id) citations,
          (SELECT jsonb_agg(to_jsonb(ci)) FROM curated_collection_items ci WHERE ci.artwork_id=a.id) selections
          FROM artworks a WHERE EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_countries ac ON ac.artist_id=aa.artist_id
            WHERE aa.artwork_id=a.id AND ac.country_code='CY')
          OR a.cultural_context ILIKE '%cypr%' OR a.current_location_text ILIKE '%cypr%'
          OR EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id
            AND (c.source_url LIKE '%visitcyprus.com/%' OR c.source_url LIKE '%apsida.cut.ac.cy/%' OR c.source_url LIKE '%xeniartspace.com/%'))
          ORDER BY a.id""").fetchall()
        institutions = db.execute('SELECT * FROM institutions ORDER BY name').fetchall()
        schema = db.execute("""SELECT table_name,column_name,data_type,column_default,is_nullable FROM information_schema.columns
          WHERE table_name IN ('artists','artist_countries','artworks','artwork_artists','curated_collection_items',
            'curated_collections','artwork_location_assertions','citations','sources','external_identifiers','places')
          ORDER BY table_name,ordinal_position""").fetchall()
        constraints = db.execute("""SELECT conrelid::regclass::text table_name,conname,pg_get_constraintdef(oid) definition
          FROM pg_constraint WHERE conrelid IN ('artists'::regclass,'artworks'::regclass,'artist_countries'::regclass,
            'artwork_location_assertions'::regclass,'curated_collection_items'::regclass)""").fetchall()
        owner = db.execute("SELECT * FROM curated_collections WHERE institution_id IS NULL AND curator_kind='owner'").fetchone()
    save(destination, {'at': now(), 'artists': artists, 'works': works, 'institutions': institutions,
                       'schema': schema, 'constraints': constraints, 'owner_collection': owner})
    print(json.dumps({'painters': len(artists), 'related_works': len(works), 'institutions': len(institutions)}))


def archive_inventory():
    """Bounded metadata-only discovery; Dublin Core Date/Creator are not artwork facts."""
    tags = ['Icons--Byzantine--Cyprus', 'Icons--post-Byzantine--Cyprus',
            'Mural painting and decoration--Cyprus', 'Mural painting and decoration--Byzantine--Cyprus',
            'Mural painting and decoration--Byzantine--Cyprus--Paphos',
            'Mural painting and decoration--post-Byzantine--Cyprus--Paphos']
    discovered = {}
    indexes = []
    for tag in tags:
        url = 'https://apsida.cut.ac.cy/items/browse?' + urlencode({'tags': tag})
        visited = set()
        while url:
            assert url not in visited and len(visited) < 60, 'Unexpected pagination'
            visited.add(url)
            path, receipt = capture(url)
            soup = BeautifulSoup(path.read_bytes(), 'html.parser')
            ids = sorted({int(m.group(1)) for a in soup.select('a[href]')
                          if (m := re.search(r'/items/show/(\d+)', a['href']))})
            for ident in ids:
                discovered.setdefault(ident, set()).add(tag)
            indexes.append({'tag': tag, 'ids': ids, 'capture': receipt})
            nxt = soup.select_one('a[rel="next"], li.pagination_next a, .pagination-next a')
            url = urljoin(url, nxt['href']) if nxt else None
        print(tag, len(visited), 'pages;', len(discovered), 'unique archive records', flush=True)
    save(RUN / 'archive-indexes.json', indexes)
    assert len(discovered) <= 1000, 'Review batch exceeds planned bound'
    def fetch(ident):
        path, receipt = capture(f'https://apsida.cut.ac.cy/api/items/{ident}')
        obj = json.loads(path.read_bytes())
        assert obj['id'] == ident and obj['public']
        fields = {}
        for element in obj['element_texts']:
            fields.setdefault(element['element']['name'], []).append(BeautifulSoup(element['text'], 'html.parser').get_text(' ', strip=True))
        return {'id': ident, 'fields': fields, 'tags': sorted(discovered[ident]), 'capture': receipt}
    rows, errors = [], []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(fetch, ident): ident for ident in sorted(discovered)}
        for future in as_completed(futures):
            try:
                rows.append(future.result())
            except Exception as exc:
                errors.append({'id': futures[future], 'error': str(exc)})
            if (len(rows) + len(errors)) % 25 == 0:
                print('Captured', len(rows), 'metadata records;', len(errors), 'errors', flush=True)
    save(RUN / 'archive-inventory.json', {'records': sorted(rows, key=lambda r: r['id']), 'errors': errors})
    print('Inventory complete:', len(rows), 'records,', len(errors), 'errors', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['audit', 'capture', 'inventory'])
    parser.add_argument('urls', nargs='*')
    args = parser.parse_args()
    if args.stage == 'audit':
        audit()
    elif args.stage == 'inventory':
        archive_inventory()
    else:
        for url in args.urls:
            path, receipt = capture(url)
            soup = BeautifulSoup(path.read_bytes(), 'html.parser')
            print(json.dumps({'url': url, 'path': str(path), 'frames': [i.get('src') for i in soup.select('iframe')],
                              'links': sorted({a.get('href') for a in soup.select('a[href]') if a.get('href') and not a.get('href').startswith(('#', 'tel:', 'mailto:'))})}, ensure_ascii=False))
