#!/usr/bin/env python3
"""Resumable read-only semantic audit using short, indexed keyset batches.

Each page is an immutable receipt. Connections are rotated between pages so a
long-lived proxy connection cannot discard an entire table's completed audit.
These are page snapshots, not one global snapshot; delivery separately checks
every exact target preimage and key absence under locks before any writes.
"""
import importlib.util
import json
from pathlib import Path
import time

import psycopg

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit-release-content.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
OUT = a.r.ROOT / 'docs/research/production-release-20260927/content'
SIZE = 5000


def main():
    base = json.loads((OUT.parent / 'before/local-snapshot.json').read_text())['tables']
    with a.r.connect('cloud') as db:
        # Keep credentials in memory; never write or print the DSN.
        connection_fields = psycopg.conninfo.conninfo_to_dict(a.r.core.cloud_dsn())
        connection_fields.update(port='55434', options='-c default_transaction_read_only=on -c statement_timeout=180000')
        connection = psycopg.conninfo.make_conninfo(**connection_fields)
        foreign = db.execute("""SELECT conrelid::regclass::text,a.attname,confrelid::regclass::text,b.attname
            FROM pg_constraint c JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=c.conkey[1]
            JOIN pg_attribute b ON b.attrelid=c.confrelid AND b.attnum=c.confkey[1]
            WHERE contype='f' AND cardinality(conkey)=1""").fetchall()
    for table, meta in base.items():
        if table in a.SKIP or (OUT / ('cloud-' + table + '.json')).exists():
            continue
        rows, after, number, done = {}, None, 0, False
        while not done:
            receipt = OUT / (table + '-pages') / f'{number:05}.json'
            if receipt.exists():
                page = json.loads(receipt.read_text())
                assert page['previous'] == after
            else:
                query = a.statement(table, meta, [(col, parent, pc) for t, col, parent, pc in foreign if t == table], SIZE, after)
                for attempt in range(3):
                    try:
                        with psycopg.connect(connection) as db:
                            db.execute('SET TRANSACTION READ ONLY')
                            db.execute("SET LOCAL timezone='UTC'")
                            db.execute('SET LOCAL jit=off')
                            db.execute('SET LOCAL max_parallel_workers_per_gather=0')
                            db.execute("SET LOCAL work_mem='1MB'")
                            values = []
                            with db.cursor().copy('COPY (' + query + ') TO STDOUT') as copy:
                                values.extend(copy.rows())
                        page = {'at': a.r.core.now(), 'previous': after, 'rows': values}
                        a.r.core.save_new(receipt, page)
                        break
                    except psycopg.OperationalError:
                        if attempt == 2:
                            raise
                        time.sleep(2)
            for key, digest, primary in page['rows']:
                rows.setdefault(key, []).append([digest, primary])
                after = primary
            number += 1
            done = len(page['rows']) < SIZE
            print(table, 'page', number, 'rows', sum(map(len, rows.values())), flush=True)
        for records in rows.values():
            records.sort()
        with psycopg.connect(connection) as db:
            count = db.execute('SELECT count(*) FROM ' + psycopg.sql.Identifier(table).as_string()).fetchone()[0]
            assert count == sum(map(len, rows.values())), ('table membership changed during audit', table)
        a.r.core.save_new(OUT / ('cloud-' + table + '.json'), rows)
    a.compare(OUT)


if __name__ == '__main__':
    main()
