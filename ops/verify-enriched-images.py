#!/usr/bin/env python3
"""Read-only verification of local, GCS, and database image receipts."""
import argparse
import base64
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from google.cloud import storage
from PIL import Image

spec = importlib.util.spec_from_file_location('enrichment', Path(__file__).with_name('enrich-artwork-images.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--local-only', action='store_true', help='Audit local files and catalogue only; cloud verification remains outstanding')
    args = parser.parse_args()
    latest = {}
    for line in (args.run / 'events.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row.get('artwork_id'):
            latest[row['artwork_id']] = row
    complete = [r for r in latest.values() if r['outcome'] == 'complete']
    results = collections.Counter()
    errors = []
    media_ids = []
    receipts = {}
    expected_attached_ids = {'local': set(), 'cloud': set()}
    hashes = {}
    total_bytes = 0
    sizes = []
    fresh_dates_checked = 0
    for event in complete:
        path = args.run / 'images' / event['provider'] / (event['artwork_id'] + '.json')
        receipt = json.loads(path.read_text())
        local_path = module.ROOT / 'apps/web/public' / event['path'].lstrip('/')
        data = local_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != event['sha256'] or len(data) != event['bytes'] or len(data) > 100000:
            errors.append({'path': str(local_path), 'error': 'local byte/hash mismatch'})
        with Image.open(local_path) as image:
            image.verify()
        hashes[event['path'].lstrip('/')] = (base64.b64encode(hashlib.md5(data).digest()).decode(), len(data))
        media_ids.append(receipt['media_id'])
        receipts[receipt['media_id']] = receipt
        for target in expected_attached_ids:
            if event.get(target) == 'attached':
                expected_attached_ids[target].add(receipt['media_id'])
        results[event['provider']] += 1
        total_bytes += len(data)
        sizes.append(len(data))
        raw = receipt['raw']
        provider = receipt['provider']
        ends = []
        if provider == 'met':
            ends = [raw.get('objectEndDate')]
        elif provider == 'chicago':
            ends = [raw.get('date_end')]
        elif provider == 'cleveland':
            ends = [raw.get('creation_date_latest')]
        elif provider == 'smk':
            ends = [int(d['end'][:4]) for d in raw.get('production_date', [])
                    if d.get('end') and d['end'][:4].isdigit()]
        elif provider == 'night-fng':
            obj = raw.get('object', {})
            ends = [obj.get('yearTo') or obj.get('yearFrom')]
        elif provider == 'night-commons':
            ends = [receipt.get('creation_year_end')]
        elif provider == 'night-nga-commons':
            value = raw.get('nga_object', {}).get('endyear', '')
            ends = [int(value)] if str(value).isdigit() else []
        elif provider in ('night-rijks', 'night-saam'):
            ends = [receipt.get('scope_evidence', {}).get('source_year_end')]
        known_ends = [y for y in ends if isinstance(y, int) and y != 0]
        if known_ends:
            fresh_dates_checked += 1
        if any(y > 1970 for y in known_ends):
            errors.append({'artwork_id': event['artwork_id'], 'error': 'fresh museum creation date exceeds cutoff', 'end_dates': known_ends})
    if not args.local_only:
        client = storage.Client(project='artline-508319', credentials=module.GcloudCredentials())
        objects = {b.name: b for b in client.list_blobs(module.BUCKET, prefix='assets/artworks/open-museums/')}
        for name, (md5, size) in hashes.items():
            blob = objects.get(name)
            if not blob or blob.md5_hash != md5 or blob.size != size or blob.size > 100000:
                errors.append({'path': name, 'error': 'GCS byte/hash mismatch'})
    databases = {}
    targets = [('local','postgres://localhost/artline')]
    if not args.local_only:
        targets.append(('cloud',module.cloud_dsn()))
    for target, dsn in targets:
        with psycopg.connect(dsn,row_factory=dict_row) as db:
            db.execute('SET TRANSACTION READ ONLY')
            row = db.execute('''SELECT count(DISTINCT m.id) AS media,count(DISTINCT r.media_id) AS rights,
                      count(DISTINCT a.id) AS linked_artworks,
                      count(DISTINCT m.id) FILTER (WHERE m.byte_size>100000) AS oversize
                FROM media_assets m LEFT JOIN media_rights_evidence r ON r.media_id=m.id
                LEFT JOIN artworks a ON a.primary_media_id=m.id WHERE m.id=ANY(%s::uuid[])''',(media_ids,)).fetchone()
            databases[target] = row
            expected = sum(r.get(target) == 'attached' for r in complete)
            row['expected_attached'] = expected
            if row['oversize'] or row['media'] != row['rights'] or row['linked_artworks'] != expected or row['media'] < expected:
                errors.append({'database':target,'error':'missing attachment, missing rights, or oversize media'})
            details = db.execute('''SELECT m.id::text AS media_id,m.storage_path AS path,
                m.checksum_sha256 AS sha256,m.byte_size AS bytes,m.width,m.height,m.rights_status,
                m.license_label,m.license_url AS policy_url,m.source_page_url AS page,
                m.creator_credit AS artist,m.alt_text,m.attribution_text,m.verified_at,m.mime_type,
                r.source_image_url,r.source_record_id AS external_id,r.source_checksum,
                r.policy_url AS evidence_policy_url,r.checked_at,
                a.id::text AS linked_artwork_id,e.scheme AS linked_scheme,e.external_id AS linked_external_id,
                e.source_id::text AS linked_source_id,r.source_id::text AS rights_source_id
                FROM media_assets m LEFT JOIN media_rights_evidence r ON r.media_id=m.id
                LEFT JOIN artworks a ON a.primary_media_id=m.id
                LEFT JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id
                    AND e.scheme=r.evidence_json->>'scheme' AND e.external_id=r.source_record_id
                WHERE m.id=ANY(%s::uuid[])''', (media_ids,)).fetchall()
            seen = set()
            for detail in details:
                seen.add(detail['media_id'])
                receipt = receipts[detail['media_id']]
                # New receipts preserve museum/photographer credits separately
                # from the artwork's attributed artist. Older receipts use artist.
                expected = {**receipt, 'artist': receipt.get('creator_credit', receipt['artist'])}
                mismatches = [field for field in ('path','sha256','bytes','width','height','rights_status',
                    'license_label','policy_url','page','artist','source_image_url','external_id')
                    if detail[field] != expected[field]]
                if detail['source_checksum'] != module.sha(module.encode(receipt['raw'])):
                    mismatches.append('source_checksum')
                if detail['evidence_policy_url'] != receipt['policy_url']:
                    mismatches.append('evidence_policy_url')
                if not detail['verified_at'] or not detail['checked_at'] or detail['mime_type'] != 'image/jpeg':
                    mismatches.append('verification_or_mime_type')
                if not (detail['alt_text'] or '').strip() or not (detail['attribution_text'] or '').strip():
                    mismatches.append('alt_text_or_attribution')
                if detail['media_id'] in expected_attached_ids[target]:
                    if detail['linked_scheme'] != receipt['scheme'] or detail['linked_external_id'] != receipt['external_id']:
                        mismatches.append('linked_museum_identity')
                    if detail['linked_source_id'] != detail['rights_source_id']:
                        mismatches.append('linked_source_provenance')
                    if target == 'local' and detail['linked_artwork_id'] != receipt['artwork_id']:
                        mismatches.append('linked_local_artwork_id')
                if mismatches:
                    errors.append({'database':target,'media_id':detail['media_id'],
                                   'error':'database metadata differs from receipt','fields':mismatches})
            row['metadata_checked'] = len(details)
            missing = expected_attached_ids[target] - seen
            if missing:
                errors.append({'database':target,'error':'expected media IDs absent','media_ids':sorted(missing)})
    report = {'checked_at':module.now(),'verification_scope':'local-only' if args.local_only else 'local-and-cloud',
              'complete_images':len(complete),'bytes':total_bytes,
              'max_bytes':max(sizes, default=0), 'fresh_creation_dates_checked':fresh_dates_checked,
              'by_provider':dict(results),'latest_outcomes':dict(collections.Counter(r['outcome'] for r in latest.values())),
              'databases':databases,'errors':errors}
    module.save_new(args.report,report)
    print(json.dumps(report,indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
