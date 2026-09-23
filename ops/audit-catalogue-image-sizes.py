#!/usr/bin/env python3
"""Read-only whole-catalogue image-byte audit and painter-level gap inventory."""
import argparse
import base64
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from PIL import Image
import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('core', ROOT/'ops/enrich-artwork-images.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
LIMIT = 100_000
PUBLIC = ROOT/'apps/web/public'


def snapshot(dsn, run, target):
    with psycopg.connect(dsn, row_factory=dict_row,
                         options='-c default_transaction_read_only=on -c statement_timeout=180000') as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        at = db.execute('SELECT now()::text at').fetchone()['at']
        rows = db.execute("""SELECT id::text,storage_path,byte_size,checksum_sha256,
            mime_type,width,height,rights_status,license_url,verified_at
            FROM media_assets WHERE mime_type LIKE 'image/%%' OR mime_type IS NULL
            ORDER BY id""").fetchall()
        summary = db.execute("""SELECT count(*) all_media,
            count(*) FILTER(WHERE mime_type LIKE 'image/%%' OR mime_type IS NULL) audited_media,
            max(byte_size) FILTER(WHERE mime_type LIKE 'image/%%' OR mime_type IS NULL) largest_recorded_image,
            count(*) FILTER(WHERE (mime_type LIKE 'image/%%' OR mime_type IS NULL) AND byte_size>100000) recorded_oversize
            FROM media_assets""").fetchone()
        counts = db.execute("""SELECT count(*) artworks,count(primary_media_id) with_image
            FROM artworks WHERE status<>'archived'""").fetchone()
        if target == 'local':
            inventory = db.execute("""WITH counts AS (
                SELECT aa.artist_id,count(*) artworks,count(a.primary_media_id) with_image,
                count(*) FILTER(WHERE a.primary_media_id IS NULL) missing_images,
                count(*) FILTER(WHERE a.primary_media_id IS NULL AND
                  artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible') eligible_date_gaps
                FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
                WHERE a.status<>'archived' GROUP BY aa.artist_id)
                SELECT p.id::text,p.slug,p.display_name,p.birth_year,p.death_year,
                coalesce(c.artworks,0) artworks,coalesce(c.with_image,0) with_image,
                coalesce(c.missing_images,0) missing_images,coalesce(c.eligible_date_gaps,0) eligible_date_gaps,
                EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=p.id AND d.is_popular) popular,
                EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=p.id AND ac.country_code IN ('RU','GR')) priority,
                (SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=p.id AND e.scheme='wikidata') qid
                FROM artists p LEFT JOIN counts c ON c.artist_id=p.id WHERE p.status<>'archived'
                ORDER BY priority DESC,popular DESC,eligible_date_gaps DESC,p.slug""").fetchall()
            core.save_new(run/'painter-inventory.json', {'at': at, 'painters': inventory,
                'note': 'Complete active-artist coverage inventory; date-eligible gaps still require selection evidence, identity and image rights. Multi-creator artworks can appear for multiple artists.'})
    core.save_new(run/(target+'-media-snapshot.json'), {'at': at, 'summary': summary, 'artworks': counts, 'images': rows})
    print(target, 'snapshot', summary, counts, flush=True)
    return rows, dict(summary, snapshot_at=at, artworks=counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--local-only', action='store_true')
    args = parser.parse_args()
    args.run.mkdir(parents=True, exist_ok=True)
    start = time.time()
    targets = {}
    connections=[('local', 'postgres://localhost/artline')]
    if not args.local_only:connections.append(('cloud',core.cloud_dsn()))
    for target, dsn in connections:
        targets[target] = snapshot(dsn, args.run, target)
    bypath = collections.defaultdict(list)
    for target, (rows, summary) in targets.items():
        for row in rows:
            bypath[row['storage_path']].append((target, row))
    checked, file_errors = {}, []
    for n, (path, entries) in enumerate(bypath.items(), 1):
        try:
            if not path or not path.startswith('/assets/'):
                raise ValueError('Non-local or unexpected image storage path')
            local = (PUBLIC/path.lstrip('/')).resolve()
            if not local.is_relative_to(PUBLIC):
                raise ValueError('Storage path leaves public directory')
            data = local.read_bytes()
            info = {'bytes': len(data), 'sha256': core.sha(data),
                    'md5': base64.b64encode(hashlib.md5(data).digest()).decode()}
            if not path.lower().endswith('.svg'):
                with Image.open(local) as im:
                    info.update(width=im.width, height=im.height, format=im.format)
                    im.verify()
            checked[path] = info
            for target, row in entries:
                mismatches = []
                if len(data)>LIMIT: mismatches.append('actual_file_over_100000_bytes')
                if row['byte_size']!=len(data): mismatches.append('recorded_size_differs')
                if row['checksum_sha256']!=info['sha256']: mismatches.append('checksum_differs_or_absent')
                if 'width' in info and (row['width'],row['height'])!=(info['width'],info['height']): mismatches.append('dimensions_differ')
                if mismatches: file_errors.append({'target': target, 'media_id': row['id'], 'path': path, 'actual_bytes': len(data), 'problems': mismatches})
        except Exception as error:
            file_errors.append({'path': path, 'targets': [t for t,_ in entries], 'error': str(error)[:400]})
        if n%2000==0: print('Local files inspected', n, 'of', len(bypath), 'issues', len(file_errors), flush=True)
    core.save_new(args.run/'local-file-verification.json', {'unique_paths': len(bypath), 'verified_files': len(checked),
        'max_bytes': max((i['bytes'] for i in checked.values()),default=0), 'files': checked, 'issues': file_errors})
    cloud_rows = targets.get('cloud', ([], {}))[0]
    wanted = collections.defaultdict(list)
    for row in cloud_rows:
        if row['storage_path'] and row['storage_path'].startswith('/assets/'):
            wanted[row['storage_path'].lstrip('/')].append(row)
    found, storage_errors = set(), []
    sizes, listed = [], 0
    client = None if args.local_only else core.storage.Client(project='artline-508319', credentials=core.GcloudCredentials())
    blobs = [] if args.local_only else client.list_blobs(core.BUCKET, prefix='assets/', page_size=1000, timeout=60)
    for blob in blobs:
        listed+=1
        if blob.name not in wanted: continue
        found.add(blob.name)
        sizes.append(blob.size)
        for row in wanted[blob.name]:
            issues=[]
            if blob.size>LIMIT: issues.append('stored_file_over_100000_bytes')
            if blob.size!=row['byte_size']: issues.append('storage_size_differs_from_db')
            info=checked.get('/'+blob.name)
            if info and blob.md5_hash!=info['md5']: issues.append('storage_md5_differs_from_local')
            if blob.content_type!=row['mime_type']: issues.append('storage_mime_differs_from_db')
            if issues: storage_errors.append({'media_id':row['id'],'path':row['storage_path'],'bytes':blob.size,'generation':blob.generation,'problems':issues})
        if len(found)%2000==0: print('Cloud image objects inspected',len(found),'of',len(wanted),'issues',len(storage_errors),flush=True)
    for name in wanted.keys()-found:
        storage_errors.append({'path':'/'+name,'error':'Database-referenced image absent in cloud storage'})
    result = {'at': core.now(), 'limit_bytes': LIMIT, 'database_writes': False, 'local_only': args.local_only,
        'scope': 'Every image media row (including unlinked/archived media) in the selected database snapshots; actual local files. Production-referenced storage objects checked only when local_only is false. Source-image archives are not app media. Concurrent imports after snapshot are not included.',
        'databases':{t:s for t,(_,s) in targets.items()},
        'unique_file_paths':len(bypath),'local_files_read':len(checked),
        'local_max_bytes':max((i['bytes'] for i in checked.values()),default=0),
        'local_actual_oversize':sum(i['bytes']>LIMIT for i in checked.values()),
        'storage_objects_listed':listed,'production_image_paths':len(wanted),'production_images_found':len(found),
        'storage_max_bytes':max(sizes,default=0),'storage_actual_oversize':sum(s>LIMIT for s in sizes),
        'file_issues':file_errors,'storage_issues':storage_errors,'elapsed_seconds':round(time.time()-start,2)}
    core.save_new(args.run/'size-audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('file_issues','storage_issues')},indent=2),flush=True)
    print('File issues',len(file_errors),'storage issues',len(storage_errors),flush=True)


if __name__=='__main__': main()
