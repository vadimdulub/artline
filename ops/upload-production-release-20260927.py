#!/usr/bin/env python3
"""Create missing, verified catalogue objects from the immutable storage audit.

Never download source images, replace objects, change rights, or attach media.
Each uploaded object is checked against both the DB receipt and local bytes.
"""
import base64
import concurrent.futures
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('audit-production-release.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
OUT = r.ROOT / 'docs/research/production-release-20260927'


def main():
    audit = json.loads((OUT / 'storage-before.json').read_text())
    selected = [i['media'] for i in audit['issues'] if i['target'] == 'local'
                and i['reasons'] == ['cloud_object_missing']]
    assert len(selected) == 255
    assert all(m['verified'] and m['rights_status'] in ('cc0', 'public_domain') for m in selected)
    ids = [m['id'] for m in selected]
    with r.connect('local') as db:
        rows = {row['id']: row for (row,) in db.execute(
            'SELECT to_jsonb(m) FROM media_assets m WHERE id=ANY(%s::uuid[])', (ids,))}
    bucket = r.core.storage.Client(project='artline-508319', credentials=r.core.GcloudCredentials()).bucket(r.core.BUCKET)

    def upload(m):
        path = m['storage_path'].lstrip('/')
        assert path.startswith('assets/') and '..' not in Path(path).parts
        data = (r.ROOT / 'apps/web/public' / path).read_bytes()
        checksum = hashlib.sha256(data).hexdigest()
        md5 = base64.b64encode(hashlib.md5(data).digest()).decode()
        assert len(data) == m['byte_size'] and checksum == m['checksum_sha256'].strip()
        row = rows[m['id']]
        assert row['storage_path'] == m['storage_path'] and row['checksum_sha256'].strip() == checksum
        blob = bucket.get_blob(path)
        created = blob is None
        if created:
            blob = bucket.blob(path)
            blob.metadata = {'sha256': checksum, 'license': row.get('license_label') or m['rights_status'],
                             'source': row.get('source_page_url') or '', 'release': '20260927'}
            blob.cache_control = 'public,max-age=31536000,immutable'
            blob.upload_from_string(data, content_type=row.get('mime_type') or 'image/jpeg', if_generation_match=0)
            blob.reload()
        assert blob.size == len(data) and blob.md5_hash == md5, 'Stored bytes differ: ' + path
        return {'media_id': m['id'], 'path': path, 'sha256': checksum, 'bytes': len(data),
                'generation': blob.generation, 'created': created}

    receipt = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for item in pool.map(upload, selected):
            receipt.append(item)
            print(len(receipt), item['path'], flush=True)
    r.core.save_new(OUT / 'storage-delivery.json', {'at': r.core.now(), 'objects': receipt,
        'audit_sha256': hashlib.sha256((OUT / 'storage-before.json').read_bytes()).hexdigest(),
        'historical_unreferenced_missing_media_preserved': 590})


if __name__ == '__main__':
    main()
