#!/usr/bin/env python3
"""Build auditable book filter projections from retained source responses.

prepare reads the catalogue in a read-only transaction. apply is explicit,
local-only, checks preconditions, and never changes base records or visibility.
Requires psycopg 3. Source refresh and editorial changes require a new reviewed
projection; conflicting existing projections are not silently overwritten.
"""
import argparse
import collections
import datetime
import gzip
import hashlib
import importlib.util
import json
import pathlib

import psycopg
from psycopg.types.json import Jsonb

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/research/historical-books-20260916'
BACKUP = pathlib.Path('/Users/vadimdulub/Library/Application Support/Artline/backups/books-discovery-20260917')
DSN = 'postgres://127.0.0.1/artline?sslmode=disable'
spec = importlib.util.spec_from_file_location('research', ROOT / 'ops/research-historical-books.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def prepare():
    books = json.loads((OUT / 'books.json').read_text())
    top = json.loads((OUT / 'top-100-editorial.json').read_text())
    selected = {x['bookId']: x for x in top['items']}
    assert len(selected) == 100 and selected.keys() <= {b['id'] for b in books}
    wanted = {b['sourceId'] for b in books} | {c['id'] for b in books for c in b['creators']}
    entities, sources = {}, {}
    for path in sorted((OUT / 'sources').glob('*.json.gz')):
        raw = path.read_bytes()
        for key, entity in json.loads(gzip.decompress(raw)).get('entities', {}).items():
            if key in wanted:
                entities[key] = entity
                sources[key] = {'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(raw).hexdigest(), 'revision': entity.get('lastrevid')}
    terms = json.loads((OUT / 'discovery-terms.json').read_text())
    un = json.loads((OUT / 'un-m49.json').read_text())
    un_by_iso = {row['ISO-alpha2 Code']: row for row in un['rows']}
    term_rows, regions_by_country = {}, {}
    for b in books:
        for kind, prop in [('language', 'P407'), ('country', 'P495')]:
            for qid in r.ids(entities[b['sourceId']], prop):
                entity = terms[qid]
                # A missing English label is retained as an explicit source ID.
                term_rows[(kind, qid)] = {'kind': kind, 'key': qid, 'name': r.name(entity) or qid, 'evidence': {'sourceUrl': 'https://www.wikidata.org/wiki/' + qid, 'revision': entity.get('lastrevid')}}
                if kind != 'country':
                    continue
                # Only direct current ISO matches. Do not turn historical states
                # into modern countries or infer a region from the author.
                regions_by_country[qid] = []
                for iso in r.values(entity, 'P297'):
                    row = un_by_iso.get(iso)
                    if not row:
                        continue
                    label = row['Intermediate Region Name'] or row['Sub-region Name']
                    if not label:
                        continue
                    key = label.lower().replace(' ', '-')
                    regions_by_country[qid].append(key)
                    term_rows[('region', key)] = {'kind': 'region', 'key': key, 'name': label, 'evidence': {'sourceUrl': un['url'], 'sha256': un['sha256']}}
                    term_rows[(kind, qid)]['evidence'].update(iso=iso, region=key, regionBasis='Direct Wikidata P297 to UN M49 ISO-alpha2 match.')
    with psycopg.connect(DSN, options='-c default_transaction_read_only=on') as db:
        base = {row[0]: (row[1], row[2]) for row in db.execute('SELECT id,source_id,source_checksum FROM book_records')}
        # Shared taxonomy must agree wherever ArtWorks already has the country.
        for iso, region in db.execute('SELECT trim(code),region_code FROM countries'):
            row = un_by_iso[iso]
            assert region == (row['Intermediate Region Name'] or row['Sub-region Name']).lower().replace(' ', '-')
    rows = []
    for b in books:
        entity = entities[b['sourceId']]
        languages, countries = r.ids(entity, 'P407'), r.ids(entity, 'P495')
        gender_evidence, women = [], []
        for creator in b['creators']:
            source = entities.get(creator['id'], {})
            gender_ids = r.ids(source, 'P21')
            if set(gender_ids) & {'Q6581072', 'Q1052281'}:  # female, transgender female
                women.append(creator['id'])
            gender_evidence.append({'creatorId': creator['id'], 'property': 'P21', 'values': gender_ids, 'source': sources.get(creator['id'])})
        assert base[b['id']][0] == b['sourceId']
        row = {'bookId': b['id'], 'bookChecksum': base[b['id']][1], 'womanAuthorIds': sorted(set(women)), 'top100': b['id'] in selected,
               'languages': sorted(languages), 'countries': sorted(countries), 'regions': sorted({key for q in countries for key in regions_by_country.get(q, [])}),
               'checkedAt': '2026-09-17T00:00:00Z',
               'evidence': {'work': {'sourceId': b['sourceId'], 'source': sources[b['sourceId']], 'languageProperty': 'P407', 'countryProperty': 'P495'}, 'creators': gender_evidence,
                            'editorial': {'version': top['version'], 'basis': selected[b['id']]['basis']} if b['id'] in selected else None,
                            'regionBasis': 'Direct country ISO code to UN M49; historical or unmatched origins remain unclassified.'}}
        row['projectionChecksum'] = digest(row)
        rows.append(row)
    data = {'version': 'book-discovery-v1', 'terms': list(term_rows.values()), 'books': rows}
    (OUT / 'discovery.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    counts = {key: sum(bool(row[key]) for row in rows) for key in ['womanAuthorIds', 'top100', 'languages', 'countries', 'regions']}
    summary = {'bookCount': len(rows), 'coverage': counts, 'termCounts': dict(collections.Counter(x['kind'] for x in term_rows.values())), 'projectionSha256': hashlib.sha256((OUT / 'discovery.json').read_bytes()).hexdigest(), 'basis': top['basis']}
    summary['termSources'] = [{'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted((OUT / 'sources').glob('discovery-terms-*.json.gz'))]
    summary['vocabularySha256'] = hashlib.sha256((OUT / 'discovery-terms.json').read_bytes()).hexdigest()
    summary['regionSourceSha256'] = un['sha256']
    (OUT / 'discovery-manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


def apply():
    data = json.loads((OUT / 'discovery.json').read_text())
    rows = data['books']
    assert len(rows) == 10000 and len({x['bookId'] for x in rows}) == 10000
    assert sum(x['top100'] for x in rows) == 100
    for row in rows:
        assert digest({k: v for k, v in row.items() if k != 'projectionChecksum'}) == row['projectionChecksum']
    with psycopg.connect(DSN) as db, db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(202609170021)')
        db.execute('LOCK TABLE book_records,book_creators,book_creator_links IN SHARE MODE')
        base = dict(db.execute('SELECT id,source_checksum FROM book_records'))
        assert all(base.get(row['bookId']) == row['bookChecksum'] for row in rows), 'Base records changed; rebuild research.'
        existing = dict(db.execute('SELECT book_id,projection_checksum FROM book_discovery'))
        assert all(existing.get(row['bookId'], row['projectionChecksum']) == row['projectionChecksum'] for row in rows), 'Conflicting projection requires explicit reconciliation.'
        terms = {(kind, key): (name, evidence) for kind, key, name, evidence in db.execute('SELECT kind,key,name,evidence FROM book_discovery_terms')}
        assert all((t['kind'], t['key']) not in terms or terms[(t['kind'], t['key'])] == (t['name'], t['evidence']) for t in data['terms'])
        BACKUP.mkdir(parents=True, exist_ok=True)
        snapshot = BACKUP / 'before-projection.json'
        if not snapshot.exists():
            snapshot.write_text(json.dumps({'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'existing': existing, 'bookChecksums': base}, indent=2) + '\n')
        for term in data['terms']:
            db.execute('INSERT INTO book_discovery_terms(kind,key,name,evidence) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING', (term['kind'], term['key'], term['name'], Jsonb(term['evidence'])))
        new = [row for row in rows if row['bookId'] not in existing]
        with db.cursor().copy('COPY book_discovery(book_id,book_checksum,woman_author_ids,top100,languages,countries,regions,evidence,checked_at,projection_checksum) FROM STDIN') as copy:
            for row in new:
                copy.write_row((row['bookId'], row['bookChecksum'], row['womanAuthorIds'], row['top100'], row['languages'], row['countries'], row['regions'], Jsonb(row['evidence']), row['checkedAt'], row['projectionChecksum']))
        assert db.execute('SELECT count(*) FROM book_discovery WHERE top100').fetchone()[0] == 100
    print(f'Added {len(new)} discovery projections. Base records and publication status unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'apply'])
    args = parser.parse_args()
    prepare() if args.command == 'prepare' else apply()
