#!/usr/bin/env python3
"""Recover failed database attachments from already uploaded image receipts.

No museum requests, image downloads, or uploads. Run only for historical failed
items that the main importer has already passed, or after the importer stops.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from google.cloud import storage

spec = importlib.util.spec_from_file_location('enrichment', Path(__file__).with_name('enrich-artwork-images.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    latest = {}
    for line in (args.run / 'events.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row.get('artwork_id'):
            latest[row['artwork_id']] = row
    candidates = []
    for row in latest.values():
        path = args.run / 'images' / row['provider'] / (row['artwork_id'] + '.json')
        if row['outcome'] == 'failed' and path.exists():
            candidates.append(json.loads(path.read_text()))
    if not candidates:
        print('No failed attachments with saved image receipts.')
        return
    bucket = storage.Client(project='artline-508319', credentials=module.GcloudCredentials()).bucket(module.BUCKET)
    with psycopg.connect('postgres://localhost/artline', autocommit=True, row_factory=dict_row) as local, \
            psycopg.connect(module.cloud_dsn(), autocommit=True, row_factory=dict_row) as remote:
        for image in candidates:
            data = (module.ROOT / 'apps/web/public' / image['path'].lstrip('/')).read_bytes()
            if len(data) > 100000 or len(data) != image['bytes'] or module.sha(data) != image['sha256']:
                raise ValueError('Saved image byte/hash mismatch')
            blob = bucket.blob(image['path'].lstrip('/'))
            blob.reload(timeout=30)
            if blob.size != len(data) or blob.md5_hash != base64.b64encode(hashlib.md5(data).digest()).decode():
                raise ValueError('Uploaded image byte/hash mismatch')
            local_result = module.attach(local, image, 'local')
            cloud_result = module.attach(remote, image, 'cloud')
            module.event(args.run, {k:image[k] for k in ('provider','artwork_id','external_id','path','sha256','bytes')} |
                         {'outcome':'complete','local':local_result,'cloud':cloud_result,
                          'generation':blob.generation,'recovery':'verified_existing_upload'})
            print(image['provider'], image['external_id'], local_result, cloud_result, flush=True)


if __name__ == '__main__':
    main()
