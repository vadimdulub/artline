#!/usr/bin/env python3
"""Refresh evidence for an already attached, reverified image without replacing it.

Requires the existing reviewed-image receipt and a fresh source/rights audit.
Preserves old rows in Artline's external backup directory before the transaction.
No artwork, artist, institution or publication fields are changed.
"""
import argparse
import importlib.util
import json
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]


def validate_existing(im, row, target):
    if row['artwork_id'] != im['target_ids'][target] or row['primary_media_id'] != im['media_id']:
        raise ValueError('Current artwork/image association differs')
    if row['status'] != 'review' or row['published_at'] is not None:
        raise ValueError('Editorial state differs')
    media, rights = row['media'], row['rights']
    for key, expected in {
        'id': im['media_id'], 'storage_path': im['path'], 'checksum_sha256': im['sha256'],
        'byte_size': im['bytes'], 'source_page_url': im['page'], 'license_url': im['policy_url'],
        'license_label': im['license_label'], 'creator_credit': im['creator_credit'],
        'attribution_text': im['attribution_text'], 'rights_status': im['rights_status'],
    }.items():
        if media.get(key) != expected:
            raise ValueError('Existing media differs: ' + key)
    for key, expected in {'media_id': im['media_id'], 'source_record_id': im['external_id'],
                          'source_image_url': im['source_image_url'], 'policy_url': im['policy_url']}.items():
        if rights.get(key) != expected:
            raise ValueError('Existing source evidence differs: ' + key)
    old = rights.get('evidence_json', {})
    if old.get('sha256') != im['sha256'] or old.get('media_id') != im['media_id']:
        raise ValueError('Previous verification is for different image bytes')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--target', choices=['local', 'cloud'], required=True)
    args = parser.parse_args()
    im = json.loads(args.receipt.read_text())
    reviewed = json.loads((args.run / 'reviewed-images.json').read_text())['records']
    if not any(x['artwork_id'] == im['artwork_id'] and x['image_sha256'] == im['sha256'] for x in reviewed):
        raise ValueError('Exact image has no completed visual review')
    spec = importlib.util.spec_from_file_location('image_audit', ROOT / 'ops/audit-overnight-local-images.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    spec = importlib.util.spec_from_file_location('image_provider', ROOT / 'ops' / audit.MODULES[im['provider']])
    provider = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(provider)
    core = provider.core
    audit.validate_source(provider, im)
    if not audit.allowed(im['policy_url']):
        raise ValueError('Unapproved licence')
    image_path = (ROOT / 'apps/web/public' / im['path'].lstrip('/')).resolve()
    if not image_path.is_relative_to(ROOT / 'apps/web/public/assets/artworks'):
        raise ValueError('Image path outside approved assets')
    data = image_path.read_bytes()
    if core.sha(data) != im['sha256'] or len(data) != im['bytes']:
        raise ValueError('Prepared image bytes changed')
    dsn = 'postgres://localhost/artline' if args.target == 'local' else core.cloud_dsn()
    with psycopg.connect(dsn, row_factory=dict_row) as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='2s'")
        rows = db.execute('''SELECT a.id::text artwork_id,a.primary_media_id::text,a.status,a.published_at,
          to_jsonb(m) media,to_jsonb(r) rights FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id
          JOIN media_rights_evidence r ON r.media_id=m.id WHERE a.id=%s FOR UPDATE OF a,m,r''',
          (im['target_ids'][args.target],)).fetchall()
        if len(rows) != 1:
            raise ValueError('Unique current image evidence required')
        row = rows[0]
        validate_existing(im, row, args.target)
        checksum = core.sha(core.encode(im['raw']))
        if row['rights']['source_checksum'] == checksum:
            print(args.target, 'fresh evidence already present')
            return
        backup = Path.home() / 'Library/Application Support/Artline/backups' / args.run.name
        core.save_new(backup / (args.target + '-evidence-refresh-' + im['artwork_id'] + '.json'), row)
        evidence = {k: v for k, v in im.items() if k not in ('artist', 'title')}
        evidence['review_resolution'] = {
            'previous_source_checksum': row['rights']['source_checksum'],
            'at': core.now(),
            'basis': 'Same artwork and exact image bytes independently reverified. Explicit original photographer credit, licence, source identity and completed visual review now pass the source audit. Previous evidence retained in the external backup.',
        }
        db.execute('''UPDATE media_rights_evidence SET source_checksum=%s,adapter_version=%s,checked_at=%s,
          rights_basis=%s,evidence_json=%s WHERE media_id=%s AND source_checksum=%s''',
          (checksum, core.VERSION, im['checked_at'], evidence['review_resolution']['basis'], Jsonb(evidence),
           im['media_id'], row['rights']['source_checksum']))
        db.execute('UPDATE media_assets SET verified_at=%s,verified_by=%s WHERE id=%s',
                   (im['checked_at'], core.ACTOR, im['media_id']))
    print(args.target, 'refreshed verified evidence for one unchanged image')


if __name__ == '__main__':
    main()
