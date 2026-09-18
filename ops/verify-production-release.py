#!/usr/bin/env python3
"""Read-only post-delivery verification against immutable reviewed release plans."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path

from psycopg import sql

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('audit-production-release.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    gap = json.loads((args.root / 'woodville-plan.json').read_text())
    citations = json.loads((args.root / 'citations-plan.json').read_text())
    storage = json.loads((args.root / 'storage-before.json').read_text())
    result = {'at': r.core.now(), 'read_only': True, 'copied_rows': {}, 'counts': {}}
    with r.connect('cloud') as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        db.execute("SET LOCAL timezone='UTC'")
        for table, rows in gap['rows'].items():
            key = {'media_rights_evidence': 'media_id', 'artwork_media': 'artwork_id'}.get(table, 'id')
            actual = [v[0] for v in db.execute(sql.SQL(
                'SELECT to_jsonb(t) FROM {} t WHERE {}=ANY(%s::uuid[])'
            ).format(sql.Identifier(table), sql.Identifier(key)), ([row[key] for row in rows],))]
            assert sorted(actual, key=lambda row: row[key]) == sorted(rows, key=lambda row: row[key]), table
            result['copied_rows'][table] = len(rows)
        rows = citations['rows']
        actual = [v[0] for v in db.execute(
            'SELECT to_jsonb(t) FROM citations t WHERE id=ANY(%s::uuid[])', ([row['id'] for row in rows],))]
        assert sorted(actual, key=lambda row: row['id']) == rows
        result['additional_original_citations'] = len(rows)
        for table in ['artists', 'artworks', 'institutions', 'media_assets', 'book_records', 'event_records', 'schema_migrations']:
            result['counts'][table] = db.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table))).fetchone()[0]
        active = db.execute("""WITH ids AS MATERIALIZED (
            SELECT primary_media_id id FROM artworks WHERE status<>'archived' AND primary_media_id IS NOT NULL
            UNION SELECT portrait_media_id FROM artists WHERE status<>'archived' AND portrait_media_id IS NOT NULL
            ) SELECT DISTINCT m.storage_path,m.checksum_sha256,m.byte_size FROM ids JOIN media_assets m ON m.id=ids.id
            WHERE m.storage_path IS NOT NULL""").fetchall()
        additions = []
        bucket = None
        for path, sha256, byte_size in active:
            local = storage['local_files'].get(path, {})
            cloud = storage['objects'].get(path.lstrip('/'), {})
            if path not in storage['local_files']:
                # Another authorized image workflow may complete after the
                # original inventory. Verify its actual bytes, never waive it.
                relative = path.lstrip('/')
                assert relative.startswith('assets/') and '..' not in Path(relative).parts
                data = (r.ROOT / 'apps/web/public' / relative).read_bytes()
                assert len(data) <= 100000
                local = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                         'md5': base64.b64encode(hashlib.md5(data).digest()).decode()}
                if bucket is None:
                    bucket = r.core.storage.Client(project='artline-508319', credentials=r.core.GcloudCredentials()).bucket(r.core.BUCKET)
                blob = bucket.get_blob(relative)
                assert blob, path
                cloud = {'bytes': blob.size, 'md5': blob.md5_hash, 'generation': blob.generation}
                additions.append({'path': path, 'local': local, 'cloud': cloud})
            assert not local.get('missing') and local.get('md5') and local['md5'] == cloud.get('md5'), path
            assert local['bytes'] == cloud['bytes'], path
            assert not sha256 or sha256.strip() == local['sha256'], path
            assert byte_size is None or byte_size == local['bytes'], path
        result['active_image_paths_matching_storage_audit'] = len(active)
        result['storage_inventory_at'] = storage['at']
        result['additional_images_verified_since_inventory'] = additions
        result['storage_note'] = 'Fresh active DB references matched the checksum-verified storage inventory; newly observed paths received fresh local/GCS checksum checks. Not a second full storage listing. Remote book covers are separate.'
    r.core.save_new(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
