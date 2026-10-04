#!/usr/bin/env python3
"""Apply a hash-pinned reviewed catalogue plan after a successful cloud backup.

No deletes, publication, conflict-upserts, fixture records or local DB writes.
Exact target preimages and absences are verified inside one data transaction;
all catalogue content is checked again before commit. Schema extensions use
the application's migration advisory lock and preserve the existing ledger.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

from psycopg import sql
from psycopg.types.json import Jsonb

spec = importlib.util.spec_from_file_location('planner', Path(__file__).with_name('plan-production-release-20260927.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
r = p.r
GCLOUD = '/Users/vadimdulub/Documents/google-cloud-sdk/bin/gcloud'


def ordered_tables(plan):
    remaining = {t for t, rows in plan['inserts'].items() if rows} | {t for t, rows in plan['updates'].items() if rows}
    order = []
    while remaining:
        ready = sorted(t for t in remaining if not any(child == t and parent != t and parent in remaining
                       for child, _, parent, _ in plan['foreign']))
        assert ready, 'Unresolved foreign-key cycle'
        order.extend(ready)
        remaining.difference_update(ready)
    return order


def content(row):
    return {k: v for k, v in row.items() if k not in p.IGNORE}


def invalidated_book_ids(plan):
    # The existing source-checksum trigger removes stale discovery projections.
    # Recreate exactly those pinned, preimage-checked projections after updating
    # their source records; do not disable invalidation or use conflict-upserts.
    assert not plan['updates'].get('book_creators'), 'Creator invalidation needs a separate plan'
    changed = {u['source']['id']: u['source']['source_checksum']
               for u in plan['updates'].get('book_records', []) if 'source_checksum' in u['changes']}
    projections = {u['source']['book_id']: u['source'] for u in plan['updates'].get('book_discovery', [])}
    assert changed.keys() <= projections.keys()
    assert all(projections[k]['book_checksum'] == checksum for k, checksum in changed.items())
    return set(changed)


def verify(db, plan):
    result = {}
    for table in ordered_tables(plan):
        expected = plan['inserts'].get(table, []) + [row['source'] for row in plan['updates'].get(table, [])]
        actual = {p.keys(row, plan['metadata'][table]): row for row in p.fetch(db, table, plan['metadata'][table], expected)}
        assert len(actual) == len(expected), ('verification count', table)
        for row in expected:
            found = actual[p.keys(row, plan['metadata'][table])]
            assert content(found) == content(row), ('post-write content mismatch', table, p.keys(row, plan['metadata'][table]))
        result[table] = len(actual)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--backup-id', required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    assert hashlib.sha256(args.plan.read_bytes()).hexdigest() == args.sha256
    plan = json.loads(args.plan.read_text())
    rebuilt_books = invalidated_book_ids(plan)
    if args.verify_only:
        with r.connect('cloud') as db:
            db.execute("SET LOCAL timezone='UTC'")
            result = verify(db, plan)
        r.core.save_new(args.receipt, {'at': r.core.now(), 'read_only': True, 'verified': result, 'plan_sha256': args.sha256})
        print('Post-commit verification passed', result)
        return
    assert not args.receipt.exists()
    backup = json.loads(subprocess.check_output([GCLOUD, 'sql', 'backups', 'describe', args.backup_id,
        '--instance=artline-postgres', '--project=artline-508319', '--format=json'], text=True))
    assert backup['status'] == 'SUCCESSFUL'
    for table in ('artists', 'artworks', 'institutions', 'curated_collections'):
        assert all(row.get('status') != 'published' for row in plan['inserts'].get(table, [])), ('new publication', table)
        assert all('status' not in row['changes'] for row in plan['updates'].get(table, [])), ('publication-state change', table)
    migrations = []
    with r.connect('cloud', readonly=False) as db:
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('SELECT pg_advisory_xact_lock(20250907001)')
        applied = {row[0] for row in db.execute('SELECT filename FROM schema_migrations')}
        for name in ('0028_decorative_art_types.sql', '0029_textile_photograph_types.sql', '0031_archive_institutions.sql'):
            if name not in applied:
                body = (r.ROOT / 'apps/server/db/migrations' / name).read_bytes()
                db.execute(body.decode())
                db.execute('INSERT INTO schema_migrations(filename) VALUES(%s)', (name,))
                migrations.append({'name': name, 'sha256': hashlib.sha256(body).hexdigest()})
    print('Required schema extensions applied', [m['name'] for m in migrations], flush=True)
    with r.connect('cloud', readonly=False) as db:
        db.execute("SET LOCAL timezone='UTC'")
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute("SET LOCAL application_name='artline-release-20260927'")
        db.execute('SELECT pg_advisory_xact_lock(20260927001)')
        # Lock only the exact rows being updated, then verify the entire pinned
        # preimage. Other production-only records are outside this operation.
        for table in ordered_tables(plan):
            meta = plan['metadata'][table]
            updates = plan['updates'].get(table, [])
            for offset in range(0, len(updates), 400):
                batch = updates[offset:offset + 400]
                query = sql.SQL('SELECT to_jsonb(t) FROM {} t JOIN jsonb_populate_recordset(NULL::{},%s) k ON {} FOR UPDATE OF t').format(
                    sql.Identifier(table), sql.Identifier(table), sql.SQL(' AND ').join(
                        sql.SQL('t.{}=k.{}').format(sql.Identifier(k), sql.Identifier(k)) for k in meta['primary_key']))
                actual = {p.keys(row[0], meta): row[0] for row in db.execute(query, (Jsonb([u['before'] for u in batch]),))}
                for u in batch:
                    assert actual.get(p.keys(u['before'], meta)) == u['before'], ('preimage changed', table)
            assert not p.fetch(db, table, meta, plan['inserts'].get(table, [])), ('insert key already exists', table)
        for table in ordered_tables(plan):
            meta = plan['metadata'][table]
            columns = [column for column, _, generated in meta['columns'] if generated == 'NEVER']
            names = sql.SQL(',').join(map(sql.Identifier, columns))
            insert = sql.SQL('INSERT INTO {} ({}) SELECT {} FROM jsonb_populate_recordset(NULL::{},%s)').format(
                sql.Identifier(table), names, names, sql.Identifier(table))
            rows = plan['inserts'].get(table, [])
            for offset in range(0, len(rows), 300):
                batch = rows[offset:offset + 300]
                assert db.execute(insert, (Jsonb(batch),)).rowcount == len(batch), ('insert count', table)
            print('Inserted', table, len(rows), flush=True)
        for table in ordered_tables(plan):
            meta = plan['metadata'][table]
            groups = collections.defaultdict(list)
            if table == 'book_discovery' and rebuilt_books:
                rebuilt = [u['source'] for u in plan['updates'][table] if u['source']['book_id'] in rebuilt_books]
                assert not p.fetch(db, table, meta, rebuilt), 'Expected source-trigger invalidation'
                columns = [column for column, _, generated in meta['columns'] if generated == 'NEVER']
                names = sql.SQL(',').join(map(sql.Identifier, columns))
                insert = sql.SQL('INSERT INTO {} ({}) SELECT {} FROM jsonb_populate_recordset(NULL::{},%s)').format(
                    sql.Identifier(table), names, names, sql.Identifier(table))
                assert db.execute(insert, (Jsonb(rebuilt),)).rowcount == len(rebuilt)
                print('Rebuilt invalidated book projections', len(rebuilt), flush=True)
            for update in plan['updates'].get(table, []):
                if table == 'book_discovery' and update['source']['book_id'] in rebuilt_books:
                    continue
                groups[tuple(sorted(update['changes']))].append(update)
            for fields, updates in groups.items():
                assignments = [sql.SQL('{}=s.{}').format(sql.Identifier(f), sql.Identifier(f)) for f in fields]
                columns = {c[0] for c in meta['columns']}
                if 'revision' in columns:
                    assignments.append(sql.SQL('revision=t.revision+1'))
                if 'updated_at' in columns:
                    assignments.append(sql.SQL('updated_at=now()'))
                query = sql.SQL('UPDATE {} t SET {} FROM jsonb_populate_recordset(NULL::{},%s) s WHERE {}').format(
                    sql.Identifier(table), sql.SQL(',').join(assignments), sql.Identifier(table),
                    sql.SQL(' AND ').join(sql.SQL('t.{}=s.{}').format(sql.Identifier(k), sql.Identifier(k)) for k in meta['primary_key']))
                for offset in range(0, len(updates), 300):
                    batch = updates[offset:offset + 300]
                    assert db.execute(query, (Jsonb([u['source'] for u in batch]),)).rowcount == len(batch), ('update count', table)
            if groups:
                print('Updated', table, sum(map(len, groups.values())), flush=True)
        result = verify(db, plan)
        print('All proposed catalogue content verified before commit', flush=True)
    r.core.save_new(args.receipt, {'at': r.core.now(), 'plan_sha256': args.sha256, 'backup_id': args.backup_id,
        'migrations': migrations, 'inserted': {t: len(v) for t, v in plan['inserts'].items() if v},
        'updated': {t: len(v) for t, v in plan['updates'].items() if v}, 'verified': result,
        'rebuilt_invalidated_book_projections': len(rebuilt_books), 'deletes': 0, 'publications': 0})


if __name__ == '__main__':
    main()
