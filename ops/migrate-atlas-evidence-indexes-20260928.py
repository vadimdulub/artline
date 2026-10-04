#!/usr/bin/env python3
"""Install two covering/existence indexes concurrently, without rewriting data."""
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('audit-production-release.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
name = '0032_atlas_image_evidence_indexes.sql'
body = (r.ROOT / 'apps/server/db/migrations' / name).read_text()
backup = json.loads(subprocess.check_output([
    '/Users/vadimdulub/Documents/google-cloud-sdk/bin/gcloud', 'sql', 'backups', 'describe',
    '1790597235330', '--instance=artline-postgres', '--project=artline-508319', '--format=json']))
assert backup['status'] == 'SUCCESSFUL'
indexes = ['media_assets_atlas_deliverable_idx', 'artwork_atlas_holding_evidence_idx']
sql_body = '\n'.join(line for line in body.splitlines() if not line.lstrip().startswith('--'))
statements = [v.strip() for v in sql_body.split(';') if 'CREATE INDEX ' in v]
assert len(statements) == len(indexes)
out = {'at': r.core.now(), 'backup_id': backup['id'],
       'migration_sha256': hashlib.sha256(body.encode()).hexdigest(), 'targets': {}}
for target in ['local', 'cloud']:
    with r.connect(target, readonly=False) as db:
        db.autocommit = True
        db.execute('SELECT pg_advisory_lock(20250907001)')
        try:
            db.execute("SET lock_timeout='5s'")
            db.execute("SET statement_timeout='10min'")
            rows = []
            for index, statement in zip(indexes, statements):
                existing = db.execute('SELECT indisvalid FROM pg_index WHERE indexrelid=to_regclass(%s)', (index,)).fetchone()
                if not existing:
                    db.execute(statement.replace('CREATE INDEX ', 'CREATE INDEX CONCURRENTLY ', 1))
                row = db.execute('SELECT indisvalid,pg_get_indexdef(indexrelid),pg_relation_size(indexrelid) FROM pg_index WHERE indexrelid=to_regclass(%s)', (index,)).fetchone()
                assert row and row[0], ('invalid index', target, index)
                rows.append({'name': index, 'valid': row[0], 'definition': row[1], 'bytes': row[2]})
                print(target, index, row[2], 'bytes', flush=True)
            if target == 'cloud':
                assert [v['definition'] for v in rows] == [v['definition'] for v in out['targets']['local']]
            db.execute('INSERT INTO schema_migrations(filename) VALUES(%s) ON CONFLICT DO NOTHING', (name,))
            out['targets'][target] = rows
        finally:
            db.execute('SELECT pg_advisory_unlock(20250907001)')
r.core.save_new(r.ROOT / 'docs/research/production-starting-points-20260928/atlas-evidence-indexes.json', out)
