#!/usr/bin/env python3
"""Read-only, streamed catalogue/storage inventory for an explicit release.

This reports differences; it never treats the local DB as authority to overwrite
production. IDs, row revisions and ingestion clocks are not content equivalence.
Raw receipts remain ignored research evidence, not application bundle contents.
"""
import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
from pathlib import Path

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('image_core', ROOT / 'ops/enrich-artwork-images.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
OPERATIONAL = {'audit_log', 'editor_accounts', 'schema_migrations'}
CLOCKS = ['created_at', 'updated_at', 'retrieved_at', 'verified_at', 'checked_at',
          'imported_at', 'applied_at', 'revision', 'published_at']


def connect(target, port=55434, readonly=True):
    dsn = 'postgres://localhost/artline'
    if target == 'cloud':
        fields = psycopg.conninfo.conninfo_to_dict(core.cloud_dsn())
        fields['port'] = str(port)
        dsn = psycopg.conninfo.make_conninfo(**fields)
    return psycopg.connect(dsn, options='-c statement_timeout=180000' +
                           (' -c default_transaction_read_only=on' if readonly else ''))


def snapshot(target, port, output):
    result = {'at': core.now(), 'tables': {}, 'migrations': []}
    with connect(target, port) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        result['migrations'] = [r[0] for r in db.execute('SELECT filename FROM schema_migrations ORDER BY filename')]
        tables = db.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall()
        for (table,) in tables:
            cols = db.execute("""SELECT column_name,data_type,is_generated FROM information_schema.columns
                WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position""", (table,)).fetchall()
            pk = [r[0] for r in db.execute("""SELECT a.attname FROM pg_index i
                JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=ANY(i.indkey)
                WHERE i.indrelid=%s::regclass AND i.indisprimary ORDER BY array_position(i.indkey,a.attnum)""", (table,))]
            entry = {'columns': cols, 'primary_key': pk}
            if table in OPERATIONAL:
                entry['count'] = db.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table))).fetchone()[0]
            else:
                assert pk, 'Table lacks an auditable primary key: ' + table
                key = sql.SQL('jsonb_build_array({})::text').format(sql.SQL(',').join(map(sql.Identifier, pk)))
                query = sql.SQL('SELECT {}, md5((to_jsonb(t)-%s::text[])::text) FROM {} t').format(key, sql.Identifier(table))
                rows = {}
                with db.cursor(name='release_rows') as cursor:
                    cursor.itersize = 2000
                    cursor.execute(query, (CLOCKS,))
                    for k, digest in cursor:
                        rows[k] = digest
                entry['count'] = len(rows)
                entry['rows'] = rows
                entry['digest'] = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
            result['tables'][table] = entry
            print(target, table, entry['count'], flush=True)
    core.save_new(output / (target + '-snapshot.json'), result)
    return result


def compare(output):
    snapshots = {t: json.loads((output / (t + '-snapshot.json')).read_text()) for t in ('local', 'cloud')}
    report = {'at': core.now(), 'scope': 'Whole public-schema inventory; streamed repeatable-read snapshots. '
              'Row PK fingerprints exclude ingestion clocks/revision; differences require semantic review, not blind synchronization.',
              'excluded_fingerprint_fields': CLOCKS, 'tables': {}}
    for table in sorted(snapshots['local']['tables'].keys() | snapshots['cloud']['tables'].keys()):
        a, b = (snapshots[t]['tables'].get(table, {}) for t in ('local', 'cloud'))
        x, y = a.get('rows', {}), b.get('rows', {})
        report['tables'][table] = {'local': a.get('count', 0), 'cloud': b.get('count', 0),
            'only_local': sorted(x.keys() - y.keys()), 'only_cloud': sorted(y.keys() - x.keys()),
            'changed': sorted(k for k in x.keys() & y.keys() if x[k] != y[k]),
            'schema_matches': a.get('columns') == b.get('columns'), 'operational': table in OPERATIONAL}
    core.save_new(output / 'comparison.json', report)
    for table, r in report['tables'].items():
        print(table, 'local/cloud', r['local'], r['cloud'], 'local-only/cloud-only/changed',
              len(r['only_local']), len(r['only_cloud']), len(r['changed']), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--port', type=int, default=55434)
    p.add_argument('--reuse', action='store_true')
    args = p.parse_args()
    if not args.reuse:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda t: snapshot(t, args.port, args.output), ('local', 'cloud')))
    compare(args.output)


if __name__ == '__main__':
    main()
