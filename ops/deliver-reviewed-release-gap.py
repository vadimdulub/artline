#!/usr/bin/env python3
"""Deliver two existing sourced review records without resolving their creators.

An immutable, hash-pinned plan and successful Cloud SQL backup are required.
Existing target records are never updated; archived and withdrawn rows are out
of scope. Selected image bytes already in GCS must match the local evidence.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

from psycopg import sql
from psycopg.types.json import Jsonb

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('audit-production-release.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
SLUGS = ['wikimedia-artwork-q28026294', 'wikimedia-artwork-q28038359']
ORDER = ['media_assets', 'media_rights_evidence', 'artworks', 'artwork_media',
         'artwork_location_assertions', 'external_identifiers', 'citations']


def make_plan(port):
    with r.connect('local', port) as source, r.connect('cloud', port) as dest:
        source.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        source.execute("SET LOCAL timezone='UTC'")
        works = [v[0] for v in source.execute('SELECT to_jsonb(a) FROM artworks a WHERE slug=ANY(%s) ORDER BY slug', (SLUGS,))]
        assert len(works) == 2
        assert all(w['status'] == 'review' and w['published_at'] is None and w['creation_year_end'] <= 1970
                   and w['unlinked_creator_label'] == 'Richard Caton Woodville Jr.' for w in works)
        ids = [w['id'] for w in works]; media_ids = [w['primary_media_id'] for w in works]
        assert not source.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])', (ids,)).fetchone()
        rows = {'artworks': works}
        for table, column, values in [('media_assets', 'id', media_ids), ('media_rights_evidence', 'media_id', media_ids),
                                     ('artwork_media', 'artwork_id', ids), ('artwork_location_assertions', 'artwork_id', ids),
                                     ('external_identifiers', 'entity_id', ids), ('citations', 'entity_id', ids)]:
            query = sql.SQL('SELECT to_jsonb(t) FROM {} t WHERE {}=ANY(%s::uuid[]) ORDER BY to_jsonb(t)::text').format(sql.Identifier(table), sql.Identifier(column))
            rows[table] = [v[0] for v in source.execute(query, (values,))]
        assert len(rows['media_assets']) == len(rows['media_rights_evidence']) == 2
        assert all(m['rights_status'] == 'public_domain' and m['verified_at'] for m in rows['media_assets'])
        assert all(x['claim_type'] == 'holding' and x['venue_id'] is None and x['superseded_by'] is None
                   and x['display_state'] is None for x in rows['artwork_location_assertions'])
        assert {x['entity_id'] for x in rows['citations'] if x['field_name'] == 'primary_creator_review'
                and x['source_url'].startswith('https://www.rct.uk/collection/')} == set(ids)
        remaps = {}
        for table, fields in [('sources', ['source_id']), ('institutions', ['institution_id', 'current_institution_id'])]:
            requested = {row[field] for group in rows.values() for row in group for field in fields if row.get(field)}
            for old_id, slug in source.execute(sql.SQL('SELECT id::text,slug FROM {} WHERE id=ANY(%s::uuid[])').format(sql.Identifier(table)), (sorted(requested),)):
                found = dest.execute(sql.SQL('SELECT id::text FROM {} WHERE slug=%s').format(sql.Identifier(table)), (slug,)).fetchall()
                assert len(found) == 1
                remaps[old_id] = found[0][0]
        for group in rows.values():
            for row in group:
                for field in ['source_id', 'institution_id', 'current_institution_id']:
                    if row.get(field): row[field] = remaps[row[field]]
        assert not dest.execute('SELECT 1 FROM artworks WHERE slug=ANY(%s) OR id=ANY(%s::uuid[])', (SLUGS, ids)).fetchone()
        for work in works:
            assert not dest.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number=%s',
                                    (work['current_institution_id'], work['accession_number'])).fetchone()
        return {'scope': SLUGS, 'rows': rows, 'identity_note': 'Named object-level creator labels retained; no artist person, biography or life dates inferred.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--port', type=int, default=55434)
    p.add_argument('--apply-sha256')
    p.add_argument('--backup-id')
    p.add_argument('--receipt', type=Path)
    a = p.parse_args()
    plan = make_plan(a.port)
    if not a.apply_sha256:
        r.core.save_new(a.plan, plan)
        print(hashlib.sha256(a.plan.read_bytes()).hexdigest(), {k: len(v) for k, v in plan['rows'].items()}); return
    assert hashlib.sha256(a.plan.read_bytes()).hexdigest() == a.apply_sha256
    assert json.loads(a.plan.read_text()) == plan, 'Reviewed source or target identities changed'
    assert a.receipt and not a.receipt.exists()
    backup = json.loads(subprocess.check_output(['gcloud', 'sql', 'backups', 'describe', a.backup_id,
        '--instance=artline-postgres', '--project=artline-508319', '--format=json'], text=True))
    assert backup['status'] == 'SUCCESSFUL'
    bucket = r.core.storage.Client(project='artline-508319', credentials=r.core.GcloudCredentials()).bucket(r.core.BUCKET)
    for media in plan['rows']['media_assets']:
        data = (r.ROOT / 'apps/web/public' / media['storage_path'].lstrip('/')).read_bytes()
        assert len(data) == media['byte_size'] <= 100000 and hashlib.sha256(data).hexdigest() == media['checksum_sha256']
        blob = bucket.get_blob(media['storage_path'].lstrip('/'))
        assert blob and blob.size == len(data) and blob.md5_hash == base64.b64encode(hashlib.md5(data).digest()).decode()
    with r.connect('cloud', a.port, readonly=False) as db:
        db.execute("SET LOCAL lock_timeout='3s'")
        db.execute("SET LOCAL timezone='UTC'")
        for table in ORDER:
            columns = [v[0] for v in db.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND is_generated='NEVER' ORDER BY ordinal_position", (table,))]
            names = sql.SQL(',').join(map(sql.Identifier, columns))
            insert = sql.SQL('INSERT INTO {} ({}) SELECT {} FROM jsonb_populate_record(NULL::{},%s) RETURNING to_jsonb({})').format(
                sql.Identifier(table), names, names, sql.Identifier(table), sql.Identifier(table))
            for row in plan['rows'][table]:
                actual = db.execute(insert, (Jsonb(row),)).fetchone()[0]
                assert actual == row, 'Copied record differs: ' + table
    r.core.save_new(a.receipt, {'at': r.core.now(), 'plan_sha256': a.apply_sha256,
        'backup_id': a.backup_id, 'verified_rows': {t: len(v) for t, v in plan['rows'].items()},
        'images_verified_existing_in_storage': 2, 'published': 0, 'inferred_creator_links': 0})
    print('Two sourced review artworks and their selected media delivered and verified.')


if __name__ == '__main__': main()
