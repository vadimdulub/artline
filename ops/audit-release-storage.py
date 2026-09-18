#!/usr/bin/env python3
"""Inventory every stored catalogue image without downloading museum collections."""
import argparse
import base64
import concurrent.futures
import hashlib
import importlib.util
import json
from pathlib import Path

from psycopg.rows import dict_row

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('audit-production-release.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
core = release.core


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--port', type=int, default=55434)
    args = p.parse_args()
    bucket = core.storage.Client(project='artline-508319', credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    result = {'at': core.now(), 'scope': 'Every media_assets storage_path in both databases; '
              'compare database SHA256/size, local file SHA256 and GCS MD5/size. Remote on-demand book covers are separate.',
              'targets': {}, 'objects': {}}
    def objects():
        out = {}
        for b in bucket.list_blobs(prefix='assets/'):
            out[b.name] = {'bytes': b.size, 'md5': b.md5_hash, 'generation': b.generation, 'metadata': b.metadata}
        return out
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        inventory = pool.submit(objects)
        for target in ('local', 'cloud'):
            with release.connect(target, args.port) as db:
                db.row_factory = dict_row
                rows = db.execute("""WITH art AS MATERIALIZED (
                    SELECT DISTINCT primary_media_id id FROM artworks WHERE primary_media_id IS NOT NULL AND status<>'archived'
                    ), portraits AS MATERIALIZED (
                    SELECT DISTINCT portrait_media_id id FROM artists WHERE portrait_media_id IS NOT NULL AND status<>'archived'
                    ) SELECT m.id::text,m.storage_kind,m.storage_path,m.checksum_sha256,m.byte_size,
                    m.rights_status,m.verified_at IS NOT NULL verified,e.rights_basis,e.adapter_version,
                    art.id IS NOT NULL artwork_primary,portraits.id IS NOT NULL portrait
                    FROM media_assets m LEFT JOIN media_rights_evidence e ON e.media_id=m.id
                    LEFT JOIN art ON art.id=m.id LEFT JOIN portraits ON portraits.id=m.id
                    WHERE m.storage_path IS NOT NULL ORDER BY m.storage_path""").fetchall()
                result['targets'][target] = rows
                print(target, 'stored media records', len(rows), flush=True)
        result['objects'] = inventory.result()
    paths = {r['storage_path'] for rows in result['targets'].values() for r in rows}
    def inspect(path):
        relative = path.lstrip('/')
        assert relative.startswith('assets/') and '..' not in Path(relative).parts
        f = release.ROOT / 'apps/web/public' / relative
        if not f.is_file():
            return path, {'missing': True}
        data = f.read_bytes()
        return path, {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                      'md5': base64.b64encode(hashlib.md5(data).digest()).decode()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        local_files = dict(pool.map(inspect, sorted(paths)))
    result['local_files'] = local_files
    issues = []
    for target, rows in result['targets'].items():
        for row in rows:
            path = row['storage_path']; f = local_files[path]; b = result['objects'].get(path.lstrip('/'))
            reasons = []
            if f.get('missing'): reasons.append('local_file_missing')
            else:
                if row['checksum_sha256'] and row['checksum_sha256'].strip() != f['sha256']: reasons.append('database_local_sha_mismatch')
                if row['byte_size'] is not None and row['byte_size'] != f['bytes']: reasons.append('database_local_size_mismatch')
                if b and (f['md5'] != b['md5'] or f['bytes'] != b['bytes']): reasons.append('cloud_object_differs')
            if not b: reasons.append('cloud_object_missing')
            if reasons: issues.append({'target': target, 'media': row, 'reasons': reasons})
    result['issues'] = issues
    core.save_new(args.output, result)
    print('Storage objects', len(result['objects']), 'catalogue paths', len(paths), 'issues', len(issues), flush=True)
    from collections import Counter
    print(dict(Counter(reason for issue in issues for reason in issue['reasons'])), flush=True)


if __name__ == '__main__':
    main()
