#!/usr/bin/env python3
"""Evidence-preserving location research on existing catalogue records only.

Research commands are read-only. Applying reviewed, pinned claims is separate.
No image downloads, artwork creation, publication, or inferred display claims.
"""
import argparse
import collections
import concurrent.futures
import csv
import gzip
import hashlib
import json
import re
import subprocess
import threading
import time
import unicodedata
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
import requests

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/artwork-locations-20261004'
BACKUP = Path.home() / 'Library/Application Support/Artline/backups/artwork-locations-20261004'
PORT = 55441
UA = 'ArtlineCatalogueResearch/1.0 (selected existing artwork location verification)'


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path = Path(path)
    raw = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, 'Preserve existing evidence: ' + str(path)
    else:
        temp = path.with_name(path.name + '.partial')
        temp.write_bytes(raw)
        temp.rename(path)


def load(path):
    path = Path(path)
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes())


def save_gz(path, value):
    save(path, gzip.compress(json.dumps(value, ensure_ascii=False, default=str).encode(), mtime=0))


def norm(value):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', value or '').casefold() if not unicodedata.combining(c)).split())


def namekey(value):
    value = re.sub(r'\(\d{4}[^)]*\)', '', value or '')
    return ' '.join(sorted(re.findall(r'[^\W_]+', norm(value))))


def connect(target='local', readonly=True):
    fields = psycopg.conninfo.conninfo_to_dict('postgresql://localhost/artline')
    if target == 'production':
        secret = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', 'latest', '--secret=artline-database-url', '--project=artline-508319'], text=True).strip()
        fields = psycopg.conninfo.conninfo_to_dict(secret)
        fields.update(host='127.0.0.1', port=str(PORT), sslmode='disable', connect_timeout='20')
    return psycopg.connect(**fields, autocommit=True, row_factory=dict_row,
        options='-c timezone=UTC -c statement_timeout=180000' + (' -c default_transaction_read_only=on' if readonly else ''))


def audit(target):
    dest = RUN / (target + '-baseline.json')
    if dest.exists():
        print('Existing audit preserved', target, flush=True)
        return
    with connect(target) as db:
        totals = db.execute('SELECT status,count(*) artworks,count(current_institution_id) with_institution FROM artworks GROUP BY status ORDER BY status').fetchall()
        institutions = db.execute('SELECT to_jsonb(i) row FROM institutions i ORDER BY id').fetchall()
        holdings = db.execute("SELECT claim_type,review_state,count(*) FROM artwork_location_assertions GROUP BY 1,2 ORDER BY 1,2").fetchall()
        if target == 'local':
            records = []
            cursor = None
            while True:
                batch = db.execute('''SELECT to_jsonb(a) artwork,
                  COALESCE((SELECT jsonb_agg(to_jsonb(e) ORDER BY e.scheme,e.external_id) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers,
                  COALESCE((SELECT jsonb_agg(jsonb_build_object('id',ar.id,'name',ar.display_name,'slug',ar.slug,'role',aa.attribution_role) ORDER BY ar.id) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artists,
                  (SELECT jsonb_agg(r.raw_json #> '{csv,cells}') FROM research_artwork_links l JOIN research_records r ON (r.snapshot_id,r.source_key,r.record_kind,r.source_record_id)=(l.snapshot_id,l.source_key,l.record_kind,l.research_record_id) WHERE l.artwork_id=a.id) supplied,
                  COALESCE((SELECT jsonb_agg(to_jsonb(h) ORDER BY h.id) FROM artwork_location_assertions h WHERE h.artwork_id=a.id),'[]') assertions
                  FROM artworks a WHERE a.status<>'archived' AND a.current_institution_id IS NULL AND (%s::uuid IS NULL OR a.id>%s::uuid) ORDER BY a.id LIMIT 2000''', (cursor, cursor)).fetchall()
                if not batch:
                    break
                records.extend(batch)
                cursor = batch[-1]['artwork']['id']
                if len(records) % 20000 == 0:
                    print('Audited missing location records', len(records), flush=True)
            save_gz(RUN / 'missing-locations.json.gz', records)
            schemes = collections.Counter(e['scheme'] for r in records for e in r['identifiers'])
            supplied = collections.Counter(cells[3] for r in records for cells in (r['supplied'] or []))
            save(RUN / 'gap-distribution.json', {'schemes': dict(schemes), 'supplied_museums': dict(supplied)})
            with (RUN / 'catalogue-location-coverage.csv').open('w') as file:
                with db.cursor().copy("COPY (SELECT a.id,a.slug,a.title,a.status,a.current_institution_id,i.name institution,a.current_location_text,a.current_location_unknown_reason,a.location_checked_at FROM artworks a LEFT JOIN institutions i ON i.id=a.current_institution_id WHERE a.status<>'archived' ORDER BY a.id) TO STDOUT WITH CSV HEADER") as cp:
                    for chunk in cp:
                        file.write(bytes(chunk).decode())
        save(RUN / (target + '-institutions.json'), [r['row'] for r in institutions])
        save(dest, {'at': now(), 'totals': totals, 'assertions': holdings, 'institution_count': len(institutions), 'read_only': True})
        print(json.dumps(load(dest)), flush=True)


def capture(url, params=None, tag='sources', timeout=90):
    prepared = requests.Request('GET', url, params=params).prepare().url
    key = sha(prepared.encode())
    folder = RUN / tag
    receipt_path = folder / (key + '.receipt.json')
    body_path = folder / (key + '.body.gz')
    if receipt_path.exists():
        rc = load(receipt_path)
        raw = gzip.decompress(body_path.read_bytes())
        assert sha(raw) == rc['sha256']
        return raw, rc
    response = requests.get(prepared, headers={'User-Agent': UA}, timeout=(15, timeout))
    raw = response.content
    rc = {'url': prepared, 'final_url': response.url, 'status': response.status_code, 'retrieved_at': now(), 'bytes': len(raw), 'sha256': sha(raw), 'body_path': str(body_path.relative_to(ROOT)), 'content_type': response.headers.get('Content-Type'), 'last_modified': response.headers.get('Last-Modified'), 'etag': response.headers.get('ETag'), 'retry_after': response.headers.get('Retry-After')}
    save(body_path, gzip.compress(raw, mtime=0))
    save(receipt_path, rc)
    return raw, rc


def wiki_entities(ids, tag='wikidata'):
    for attempt in range(4):
        raw, rc = capture('https://www.wikidata.org/w/api.php', {'action': 'wbgetentities', 'ids': '|'.join(ids), 'props': 'labels|aliases|claims|sitelinks', 'format': 'json'}, tag if attempt == 0 else tag + '-retry-' + str(attempt))
        if rc['status'] == 200:
            data = json.loads(raw)
            if 'entities' in data:
                return data['entities'], rc
        wait = max(60, int(rc.get('retry_after') or 60))
        print('Source rate limit/server error; waiting', wait, 'seconds', rc['status'], flush=True)
        time.sleep(wait)
    raise RuntimeError('Wikidata source unavailable after spaced retries')


def wikidata():
    rows = load(RUN / 'missing-locations.json.gz')
    qids = sorted({e['external_id'] for r in rows for e in r['identifiers'] if e['scheme'] == 'wikidata' and re.fullmatch(r'Q[1-9][0-9]*', e['external_id'])})
    for offset in range(0, len(qids), 40):
        dest = RUN / 'wikidata-batches' / f'{offset//40:04d}.json'
        if dest.exists():
            continue
        entities, rc = wiki_entities(qids[offset:offset+40])
        save(dest, {'entities': entities, 'receipt': rc})
        print('Wikidata existing artworks', min(offset+40, len(qids)), '/', len(qids), flush=True)
        time.sleep(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['audit', 'wikidata'])
    parser.add_argument('--target', choices=['local', 'production'], default='local')
    args = parser.parse_args()
    if args.command == 'audit':
        audit(args.target)
    else:
        wikidata()
