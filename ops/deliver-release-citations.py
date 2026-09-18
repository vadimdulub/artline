#!/usr/bin/env python3
"""Copy missing, existing source citations; never change catalogue facts/status."""
import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

from psycopg import sql
from psycopg.types.json import Jsonb

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('audit-production-release.py'))
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
FIELDS = {'research_image_policy', 'geography_primary_authority', 'official_object_identity'}
TABLES = {'artist': 'artists', 'artwork': 'artworks', 'institution': 'institutions'}


def plan(root):
    report = json.loads((root / 'citation-review.json').read_text())
    selected = [(json.loads(k), row['id']) for k, rows in report['only_local'].items()
                if json.loads(k)[3] in FIELDS for row in rows]
    assert len(selected) == 35
    rows = []
    with r.connect('local') as source, r.connect('cloud') as dest:
        source.execute("SET LOCAL timezone='UTC'")
        for identity, citation_id in selected:
            kind, slug, source_slug, field, record_id, url, locator = identity
            row = source.execute('SELECT to_jsonb(c) FROM citations c WHERE id=%s', (citation_id,)).fetchone()[0]
            assert row['entity_type'] == kind and row['field_name'] == field and row['source_url'] == url
            entity = dest.execute(sql.SQL("SELECT id::text FROM {} WHERE slug=%s AND status<>'archived'").format(sql.Identifier(TABLES[kind])), (slug,)).fetchall()
            assert len(entity) == 1, 'Unresolved destination entity: ' + slug
            source_id = dest.execute('SELECT id::text FROM sources WHERE slug=%s', (source_slug,)).fetchone()[0]
            row.update(entity_id=entity[0][0], source_id=source_id)
            existing = dest.execute("""SELECT id FROM citations WHERE entity_type=%s AND entity_id=%s
                AND field_name=%s AND source_id=%s AND source_record_id IS NOT DISTINCT FROM %s
                AND source_url=%s AND page_or_locator IS NOT DISTINCT FROM %s""",
                (kind, entity[0][0], field, source_id, record_id, url, locator)).fetchall()
            assert not existing, 'Existing citation must be reviewed, never overwritten'
            rows.append(row)
    return {'scope': '35 missing historical source citations; all original evidence preserved. No artwork/artist/institution or rights status is changed.',
            'rows': sorted(rows, key=lambda row: row['id'])}


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--root', type=Path, required=True)
    p.add_argument('--apply-sha256'); p.add_argument('--backup-id'); a = p.parse_args()
    path = a.root / 'citations-plan.json'; proposed = plan(a.root)
    if not a.apply_sha256:
        r.core.save_new(path, proposed); print(hashlib.sha256(path.read_bytes()).hexdigest()); return
    assert hashlib.sha256(path.read_bytes()).hexdigest() == a.apply_sha256
    assert json.loads(path.read_text()) == proposed
    receipt = a.root / 'citations-delivery.json'; assert not receipt.exists()
    backup = json.loads(subprocess.check_output(['gcloud','sql','backups','describe',a.backup_id,
        '--instance=artline-postgres','--project=artline-508319','--format=json'], text=True))
    assert backup['status'] == 'SUCCESSFUL'
    with r.connect('cloud', readonly=False) as db:
        db.execute("SET LOCAL lock_timeout='3s'"); db.execute("SET LOCAL timezone='UTC'")
        for row in proposed['rows']:
            actual = db.execute('INSERT INTO citations SELECT * FROM jsonb_populate_record(NULL::citations,%s) RETURNING to_jsonb(citations)', (Jsonb(row),)).fetchone()[0]
            assert actual == row
    r.core.save_new(receipt, {'at':r.core.now(),'backup_id':a.backup_id,'plan_sha256':a.apply_sha256,
        'citations_inserted_and_verified':35,'catalogue_facts_or_publication_changes':0})
    print('35 original source citations delivered and verified.')


if __name__ == '__main__': main()
