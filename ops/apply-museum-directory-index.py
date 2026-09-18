"""Deploy only the additive museum-card index, never unrelated migrations.

Uses CONCURRENTLY so ordinary catalogue writes remain available. A failed or
different existing index is reported for review; it is never dropped/replaced.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
from datetime import datetime, timezone

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row

ROOT = pathlib.Path(__file__).resolve().parents[1]
NAME = '0023_museum_directory_covering_index.sql'
INDEX = 'artworks_museum_card_covering_idx'
OUT = ROOT / 'docs/research/api-museum-directory-deploy-20260917'
parser = argparse.ArgumentParser()
parser.add_argument('target', choices=('local', 'cloud'))
parser.add_argument('--apply', action='store_true')
parser.add_argument('--vacuum', action='store_true', help='refresh artwork visibility map with ordinary VACUUM ANALYZE, never FULL')
args = parser.parse_args()
assert not args.vacuum or args.apply
dsn = 'postgres://localhost/artline'
if args.target == 'cloud':
    secret = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', 'latest',
        '--secret=artline-database-url', '--project=artline-508319'], text=True).strip()
    config = conninfo_to_dict(secret)
    config.update(host='127.0.0.1', port='55433', sslmode='disable', connect_timeout='15')
    dsn = make_conninfo(**config)

body = (ROOT / 'apps/server/db/migrations' / NAME).read_text()
sql = '\n'.join(line for line in body.splitlines() if not line.lstrip().startswith('--'))
assert sql.strip().startswith('CREATE INDEX IF NOT EXISTS ' + INDEX)
assert sql.count(';') == 1
inspect_sql = '''SELECT indexrelid::regclass::text AS name,indisvalid,indisready,
 pg_get_indexdef(indexrelid) AS definition,pg_relation_size(indexrelid) AS bytes
 FROM pg_index WHERE indexrelid=to_regclass(%s)'''
expected_fragment = '(current_institution_id, status, id) INCLUDE (title, creation_year_start, primary_media_id, unlinked_creator_label)'

def validate(row):
    assert row and row['indisvalid'] and row['indisready'], 'missing/invalid index; manual review required'
    assert expected_fragment in row['definition'], 'existing index definition differs'
    assert "WHERE (status <> 'archived'::text)" in row['definition'], 'existing predicate differs'

with psycopg.connect(dsn, autocommit=True, row_factory=dict_row) as conn:
    conn.execute("SET statement_timeout='20min'")
    conn.execute("SET lock_timeout='5s'")
    if not args.apply:
        conn.execute('SET default_transaction_read_only=on')
    max_bytes = conn.execute("SELECT max(octet_length(title)+coalesce(octet_length(unlinked_creator_label),0)) AS n FROM artworks WHERE status<>'archived'").fetchone()['n']
    assert max_bytes < 2300, 'index tuple-size preflight failed'
    before = conn.execute(inspect_sql, (INDEX,)).fetchone()
    if before:
        validate(before)
    applied = False
    if args.apply:
        locked = conn.execute('SELECT pg_try_advisory_lock(20250907001) AS locked').fetchone()['locked']
        assert locked, 'another migration is active; retry later'
        try:
            if not before:
                conn.execute(sql.replace('CREATE INDEX IF NOT EXISTS', 'CREATE INDEX CONCURRENTLY IF NOT EXISTS', 1))
            after = conn.execute(inspect_sql, (INDEX,)).fetchone()
            validate(after)
            conn.execute('INSERT INTO schema_migrations(filename) VALUES(%s) ON CONFLICT(filename) DO NOTHING', (NAME,))
            applied = True
        finally:
            conn.execute('SELECT pg_advisory_unlock(20250907001)')
        if args.vacuum:
            # Recently imported rows may not yet be all-visible. A normal
            # non-FULL vacuum enables true index-only scans without table locks.
            conn.execute('VACUUM (ANALYZE) public.artworks')
    else:
        after = before

OUT.mkdir(parents=True, exist_ok=True)
result = {'at':datetime.now(timezone.utc).isoformat(), 'target':args.target, 'applied':applied,
          'migration':NAME, 'migration_sha256':hashlib.sha256(body.encode()).hexdigest(),
          'max_existing_text_bytes':max_bytes, 'before':before, 'after':after,
          'catalogue_rows_modified':False, 'unrelated_migrations_applied':False}
result['artworks_vacuum_analyze'] = args.vacuum
(OUT / f'index-{args.target}-{"applied" if args.apply else "preflight"}.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))
