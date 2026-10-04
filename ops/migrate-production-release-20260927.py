#!/usr/bin/env python3
"""Install the widening type constraint with a short exclusive lock.

Migrations 0028 and 0029 only expand the same allowed-type set. Install their
final superset with NOT VALID, commit, then validate under PostgreSQL's weaker
lock before recording either migration. This preserves reads during the scan
and avoids the API's 30-second startup migration deadline.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('r', Path(__file__).with_name('audit-production-release.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
BACKUP = '1790509197914'
NAMES = ['0028_decorative_art_types.sql', '0029_textile_photograph_types.sql']


def main():
    backup = json.loads(subprocess.check_output([
        '/Users/vadimdulub/Documents/google-cloud-sdk/bin/gcloud', 'sql', 'backups', 'describe', BACKUP,
        '--instance=artline-postgres', '--project=artline-508319', '--format=json'], text=True))
    assert backup['status'] == 'SUCCESSFUL'
    bodies = {name: (r.ROOT / 'apps/server/db/migrations' / name).read_text() for name in NAMES}
    with r.connect('cloud', readonly=False) as db:
        db.autocommit = True
        db.execute('SELECT pg_advisory_lock(20250907001)')
        try:
            applied = {row[0] for row in db.execute('SELECT filename FROM schema_migrations')}
            if not set(NAMES) <= applied:
                assert NAMES[-1] not in applied, 'Unexpected partial migration order'
                db.execute("SET lock_timeout='5s'")
                body = bodies[NAMES[-1]].rstrip().removesuffix(';') + ' NOT VALID;'
                with db.transaction():
                    db.execute(body)
                print('Final widened constraint installed; exclusive lock released', flush=True)
                db.execute('ALTER TABLE artworks VALIDATE CONSTRAINT artworks_work_type_check')
                with db.transaction():
                    for name in NAMES:
                        if name not in applied:
                            db.execute('INSERT INTO schema_migrations(filename) VALUES(%s)', (name,))
            assert db.execute("SELECT convalidated FROM pg_constraint WHERE conrelid='artworks'::regclass AND conname='artworks_work_type_check'").fetchone()[0]
        finally:
            db.execute('SELECT pg_advisory_unlock(20250907001)')
    r.core.save_new(r.ROOT / 'docs/research/production-release-20260927/schema-delivery.json', {
        'at': r.core.now(), 'backup_id': BACKUP, 'validated': True,
        'migrations': {name: hashlib.sha256(body.encode()).hexdigest() for name, body in bodies.items()},
        'method': 'Install the final widening superset without a validation scan under the exclusive lock; commit; validate with a weaker lock; record both equivalent schema extensions.'})
    print('Both schema extensions validated and recorded', flush=True)


if __name__ == '__main__':
    main()
