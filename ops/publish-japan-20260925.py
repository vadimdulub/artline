#!/usr/bin/env python3
"""Publish the exact 36 reviewed Japan artworks locally and in production.

Artwork publication is scoped independently of the full artist-profile workflow.
Existing creator profile fields/statuses are preserved. No application deployment.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import time
from urllib.parse import quote

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import requests

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / 'docs/research/japan-expansion-20260924'
RUN = ROOT / 'docs/research/japan-publication-20260925'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/japan-publication-20260925')
SOURCE = 'japan-cleveland-20260924'
PROJECT = 'artline-508319'
INSTANCE = 'artline-postgres'
BUCKET = 'artline-508319-images'
SITE = 'https://artline-web-lpuqqlugnq-ew.a.run.app'
PORT = 55439
ORDER = ['sources', 'artists', 'artist_countries', 'media_assets', 'media_rights_evidence',
         'artworks', 'artwork_artists', 'artwork_media', 'artwork_location_assertions', 'external_identifiers', 'citations']
PUB_FIELDS = ['status', 'research_candidate', 'published_at', 'revision', 'updated_at', 'updated_by',
              'current_location_text', 'location_checked_at', 'creation_place_unknown_reason']


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def raw(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def save(path, value):
    data = value if isinstance(value, bytes) else raw(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, 'Evidence changed: ' + str(path)
    else:
        path.write_bytes(data)


def load(name):
    return json.loads((RUN / name).read_bytes())


def connection(target, readonly=True):
    dsn = 'postgresql://localhost/artline'
    if target == 'production':
        secret = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', 'latest',
            '--secret=artline-database-url', '--project=' + PROJECT], text=True).strip()
        fields = psycopg.conninfo.conninfo_to_dict(secret)
        fields.update(host='127.0.0.1', port=str(PORT), sslmode='disable', connect_timeout='15')
        dsn = psycopg.conninfo.make_conninfo(**fields)
    return psycopg.connect(dsn, autocommit=True, row_factory=dict_row,
        options='-c timezone=UTC -c statement_timeout=120000' + (' -c default_transaction_read_only=on' if readonly else ''))


def getrows(db, table, where, params):
    return [r['record'] for r in db.execute(sql.SQL('SELECT to_jsonb(t) record FROM {} t WHERE {} ORDER BY to_jsonb(t)::text').format(
        sql.Identifier(table), sql.SQL(where)), params).fetchall()]


def insert(db, table, row):
    names = [r['column_name'] for r in db.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND is_generated='NEVER' ORDER BY ordinal_position", (table,))]
    assert set(row) <= set(names), 'Unexpected source columns: ' + table
    columns = sql.SQL(',').join(map(sql.Identifier, names))
    return db.execute(sql.SQL('INSERT INTO {} ({}) SELECT {} FROM jsonb_populate_record(NULL::{},%s) RETURNING to_jsonb({}) record').format(
        sql.Identifier(table), columns, columns, sql.Identifier(table), sql.Identifier(table)), (Jsonb(row),)).fetchone()['record']


def publication_checks(db, ids, status):
    rows = db.execute("""SELECT a.id::text,a.status,a.published_at,a.research_candidate,
      artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,
      artline_has_selection_evidence(a.id) selected,m.checksum_sha256,m.storage_path,m.byte_size,m.rights_status,
      (SELECT count(*) FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=a.id AND s.is_active AND c.source_url LIKE 'https://%%') citations,
      (SELECT count(*) FROM media_rights_evidence e WHERE e.media_id=m.id) image_evidence,
      (SELECT count(*) FROM artwork_location_assertions la WHERE la.artwork_id=a.id AND la.claim_type='display') display_claims
      FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id""", (ids,)).fetchall()
    assert len(rows) == len(ids)
    for row in rows:
        assert row['status'] == status and row['scope'] == 'eligible' and row['selected']
        assert row['citations'] >= 1 and row['image_evidence'] == 1 and row['display_claims'] == 0
        assert row['rights_status'] == 'cc0' and row['byte_size'] <= 100000
        if status == 'published':
            assert row['published_at'] and not row['research_candidate']
    return rows


def plan():
    prior = json.loads((PREVIOUS / 'plan.json').read_bytes())
    verified = json.loads((PREVIOUS / 'verification.json').read_bytes())
    assert not verified['errors'] and verified['works'] == 36
    ids = [r['artwork_id'] for r in prior['records']]
    artist_ids = list({r['artist_id'] for r in prior['records']})
    with connection('local') as source, connection('production') as dest:
        publication_checks(source, ids, 'review')
        rows = {'artworks': getrows(source, 'artworks', 'id=ANY(%s::uuid[])', (ids,)),
                'artists': getrows(source, 'artists', 'id=ANY(%s::uuid[])', (artist_ids,)),
                'sources': getrows(source, 'sources', 'slug=%s', (SOURCE,))}
        assert len(rows['sources']) == 1
        source_id = rows['sources'][0]['id']
        media = [r['primary_media_id'] for r in rows['artworks']]
        for table, column, values in [('artwork_artists', 'artwork_id', ids), ('artwork_media', 'artwork_id', ids),
            ('artwork_location_assertions', 'artwork_id', ids), ('media_assets', 'id', media), ('media_rights_evidence', 'media_id', media)]:
            rows[table] = getrows(source, table, column + '=ANY(%s::uuid[])', (values,))
        rows['artist_countries'] = getrows(source, 'artist_countries', "artist_id=ANY(%s::uuid[]) AND country_code='JP'", (artist_ids,))
        rows['external_identifiers'] = getrows(source, 'external_identifiers', 'entity_id=ANY(%s::uuid[]) AND source_id=%s', (ids + artist_ids, source_id))
        rows['citations'] = getrows(source, 'citations', 'entity_id=ANY(%s::uuid[]) AND source_id=%s', (ids + artist_ids, source_id))
        inst = getrows(source, 'institutions', 'id=%s', (prior['institution']['id'],))[0]
        target_inst = getrows(dest, 'institutions', 'slug=%s', (inst['slug'],))
        assert len(target_inst) == 1 and target_inst[0]['status'] != 'archived'
        remaps = {inst['id']: target_inst[0]['id']}
        old = {'institutions': target_inst}
        old['sources'] = getrows(dest, 'sources', 'slug=%s', (SOURCE,))
        if old['sources']:
            assert len(old['sources']) == 1
            remaps[source_id] = old['sources'][0]['id']
            rows['sources'] = []
        old['artists'] = getrows(dest, 'artists', 'id=ANY(%s::uuid[]) OR slug=ANY(%s)', (artist_ids, [a['slug'] for a in rows['artists']]))
        existing_artist_ids = set()
        new_artists = []
        for person in rows['artists']:
            matches = [a for a in old['artists'] if a['id'] == person['id'] or a['slug'] == person['slug']]
            if matches:
                assert len(matches) == 1 and matches[0]['status'] != 'archived'
                other = matches[0]
                for key in ['display_name', 'birth_year', 'death_year', 'timeline_start_year', 'timeline_end_year']:
                    assert other[key] == person[key], 'Creator conflict: ' + person['display_name'] + ':' + key
                remaps[person['id']] = other['id']
                existing_artist_ids.add(other['id'])
            else:
                assert not getrows(dest, 'artists', 'normalized_name=%s', (person['normalized_name'],)), 'Creator-name conflict'
                new_artists.append(person)
        rows['artists'] = new_artists
        for group in rows.values():
            for row in group:
                for key in ['source_id', 'artist_id', 'entity_id', 'institution_id', 'current_institution_id']:
                    if row.get(key) in remaps:
                        row[key] = remaps[row[key]]
        old['artist_countries'] = getrows(dest, 'artist_countries', 'artist_id=ANY(%s::uuid[])', (list(existing_artist_ids),))
        keys = {(r['artist_id'], r['country_code'], r['relationship_type']) for r in old['artist_countries']}
        rows['artist_countries'] = [r for r in rows['artist_countries'] if (r['artist_id'], r['country_code'], r['relationship_type']) not in keys]
        assert not getrows(dest, 'artworks', 'id=ANY(%s::uuid[]) OR slug=ANY(%s) OR (current_institution_id=%s AND accession_number=ANY(%s))',
            (ids, [r['slug'] for r in rows['artworks']], target_inst[0]['id'], [r['accession_number'] for r in rows['artworks']])), 'Artwork already exists in target'
        assert not getrows(dest, 'external_identifiers', "entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme=ANY(%s) AND external_id=ANY(%s)))",
            ([c['url'] for c in prior['records']], ['cleveland-object', 'european-cleveland-cleveland-museum-of-art-object'], [c['object_id'] for c in prior['records']])), 'Source object already exists'
        artist_before = getrows(source, 'artists', 'id=ANY(%s::uuid[])', (artist_ids,))
        local_before = getrows(source, 'artworks', 'id=ANY(%s::uuid[])', (ids,))
        publication_time = now()
        holding = {r['artwork_id']: r for r in rows['artwork_location_assertions']}
        for work in rows['artworks']:
            work.update(status='published', research_candidate=False, published_at=publication_time, updated_at=publication_time,
                updated_by='local-european-research', revision=work['revision'] + 1,
                current_location_text=work['current_location_text'] or inst['name'], location_checked_at=holding[work['id']]['checked_at'])
            if not work['creation_place_display'] and not work['creation_place_unknown_reason']:
                work['creation_place_unknown_reason'] = 'The museum records Japanese cultural context but does not establish a specific creation place.'
        export = {'at': publication_time, 'ids': ids, 'rows': rows, 'local_artwork_preimages': local_before,
            'local_artist_preimages': artist_before, 'production_preimages': old,
            'note': 'User explicitly authorized publication of these 36 validated artworks. Artist profiles retain their existing review state; full profile publication requires the separate editorial gate.'}
    save(RUN / 'plan.json', export)
    save(RUN / 'plan-pin.json', {'sha256': sha(raw(export))})
    save(BACKUP / 'plan.json', export)
    print(json.dumps({table: len(group) for table, group in rows.items()}, indent=2))


def pinned():
    assert sha((RUN / 'plan.json').read_bytes()) == load('plan-pin.json')['sha256']
    return load('plan.json')


def backup():
    pinned()
    BACKUP.mkdir(parents=True, exist_ok=True)
    dump = BACKUP / 'local-before-publication.dump'
    if not dump.exists():
        incomplete = dump.with_suffix('.incomplete')
        subprocess.run(['pg_dump', '-h', 'localhost', '-d', 'artline', '-Fc', '-f', str(incomplete)], check=True)
        subprocess.run(['pg_restore', '--list', str(incomplete)], check=True, stdout=subprocess.DEVNULL)
        incomplete.rename(dump)
    subprocess.run(['pg_restore', '--list', str(dump)], check=True, stdout=subprocess.DEVNULL)
    cloud_path = BACKUP / 'production-backup.json'
    if not cloud_path.exists():
        value = subprocess.check_output(['gcloud', 'sql', 'backups', 'create', '--instance=' + INSTANCE, '--project=' + PROJECT,
            '--description=Before publishing 36 Japanese artworks 20260925', '--format=json'])
        save(cloud_path, value)
    cloud = json.loads(cloud_path.read_bytes())
    # gcloud versions return either a backup resource or the completed operation.
    backups = json.loads(subprocess.check_output(['gcloud', 'sql', 'backups', 'list', '--instance=' + INSTANCE,
        '--project=' + PROJECT, '--limit=20', '--format=json']))
    item = next(b for b in backups if b.get('description') == 'Before publishing 36 Japanese artworks 20260925')
    assert item['status'] == 'SUCCESSFUL'
    save(RUN / 'backups.json', {'at': now(), 'local': {'path': str(dump), 'bytes': dump.stat().st_size, 'sha256': sha(dump.read_bytes())}, 'production': item})
    print('Recovery backups verified', item['id'])


def upload():
    plan = pinned()
    assert load('backups.json')['production']['status'] == 'SUCCESSFUL'
    token = subprocess.check_output(['gcloud', 'auth', 'print-access-token'], text=True).strip()
    session = requests.Session()
    session.headers['Authorization'] = 'Bearer ' + token
    checks = []
    for m in plan['rows']['media_assets']:
        data = (ROOT / 'apps/web/public' / m['storage_path'].lstrip('/')).read_bytes()
        assert len(data) == m['byte_size'] <= 100000 and sha(data) == m['checksum_sha256']
        name = m['storage_path'].lstrip('/')
        url = f'https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/' + quote(name, safe='')
        check = session.get(url, timeout=40)
        created = False
        if check.status_code == 404:
            response = session.post(f'https://storage.googleapis.com/upload/storage/v1/b/{BUCKET}/o',
                params={'uploadType': 'media', 'name': name, 'ifGenerationMatch': 0}, data=data,
                headers={'Content-Type': 'image/jpeg'}, timeout=60)
            response.raise_for_status()
            created = True
            check = session.get(url, timeout=40)
        check.raise_for_status()
        obj = check.json()
        assert int(obj['size']) == len(data) and obj['md5Hash'] == base64.b64encode(hashlib.md5(data).digest()).decode()
        checks.append({'path': m['storage_path'], 'sha256': sha(data), 'generation': obj['generation'], 'uploaded': created})
        print('Storage verified', len(checks), flush=True)
    save(RUN / 'storage.json', {'at': now(), 'checks': checks})


def apply():
    plan = pinned()
    assert load('backups.json')['production']['status'] == 'SUCCESSFUL'
    assert len(load('storage.json')['checks']) == 36
    for target in ['production', 'local']:
        receipt = RUN / (target + '-applied.json')
        if receipt.exists():
            continue
        with connection(target, False) as db, db.transaction():
            db.execute("SET LOCAL lock_timeout='10s'")
            db.execute('SELECT pg_advisory_xact_lock(559220260915)')
            db.execute('LOCK TABLE artworks,artists,external_identifiers,artist_countries IN SHARE ROW EXCLUSIVE MODE')
            before = getrows(db, 'artworks', 'id=ANY(%s::uuid[])', (plan['ids'],))
            save(BACKUP / (target + '-locked-before-' + sha(raw(before))[:16] + '.json'), before)
            if target == 'production':
                assert not before
                for table in ORDER:
                    for row in plan['rows'][table]:
                        insert(db, table, row)
            else:
                assert before == plan['local_artwork_preimages'], 'Local artworks changed since planning'
                for work in plan['rows']['artworks']:
                    assignments = sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in PUB_FIELDS)
                    db.execute(sql.SQL('UPDATE artworks SET {} WHERE id=%s').format(assignments), [work[k] for k in PUB_FIELDS] + [work['id']])
            checks = publication_checks(db, plan['ids'], 'published')
            artist_before = plan['local_artist_preimages'] if target == 'local' else plan['production_preimages']['artists']
            assert getrows(db, 'artists', 'id=ANY(%s::uuid[])', ([a['id'] for a in artist_before],)) == artist_before
        save(receipt, {'at': now(), 'target': target, 'published_artworks': 36, 'artist_profiles_published': 0, 'checks': checks})
        print('Published', target, 36, flush=True)


def verify():
    plan = pinned()
    results = {}
    for target in ['local', 'production']:
        with connection(target) as db:
            results[target] = publication_checks(db, plan['ids'], 'published')
    assert results['local'] == results['production']
    public = []
    for work in results['production']:
        response = requests.get(SITE + '/api/backend/v1/atlas/artworks/' + work['id'], timeout=(15, 60))
        response.raise_for_status()
        body = response.json()
        assert body['media_url'] == work['storage_path']
        image = requests.get(SITE + work['storage_path'], timeout=(15, 60))
        image.raise_for_status()
        assert sha(image.content) == work['checksum_sha256']
        public.append({'id': work['id'], 'api_status': 200, 'image_status': 200, 'image_sha256': sha(image.content)})
    save(RUN / 'verification.json', {'at': now(), 'published_artworks': 36, 'databases': results, 'public': public, 'errors': []})
    print('Verified local/production publication and public API/image access:', len(public))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['plan', 'backup', 'upload', 'apply', 'verify'])
    globals()[parser.parse_args().phase]()
