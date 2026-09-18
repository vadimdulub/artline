#!/usr/bin/env python3
"""Archive only this campaign's unattached, rejected local derivatives."""
import argparse
import importlib.util
import time
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from google.cloud import storage

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('campaign', ROOT/'ops/italy-image-campaign.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def main(move=False):
    candidates, active_paths = {}, set()
    for run in c.RUN.glob('round-*'):
        latest = c.core.latest_events(run)
        reviews = {r['artwork_id']: r for r in c.load(run/'visual-review.json')['images']} if (run/'visual-review.json').exists() else {}
        for receipt in (run/'images').glob('*/*.json'):
            im = c.load(receipt)
            event = latest.get(im['artwork_id'], {})
            if event.get('outcome') == 'complete':
                active_paths.add(im['path'])
                continue
            source = (ROOT/'apps/web/public'/im['path'].lstrip('/')).resolve()
            if not source.exists():
                continue
            if event.get('outcome') != 'prepared' or reviews.get(im['artwork_id'], {}).get('outcome') != 'held':
                raise ValueError('Every remaining local image requires an explicit visual hold before archival')
            if not source.is_relative_to((ROOT/'apps/web/public/assets/artworks/open-museums').resolve()):
                raise ValueError('Derivative lies outside approved artwork asset directory')
            if c.core.sha(source.read_bytes()) != im['sha256']:
                raise ValueError('Local file differs from exact campaign receipt')
            candidates[im['path']] = (run, im, reviews[im['artwork_id']], receipt, source)
    if active_paths & set(candidates):
        raise ValueError('A completed image shares a candidate path; preserve it')
    paths = list(candidates)
    checks = {}
    for target, dsn in [('local','postgres://127.0.0.1/artline'), ('cloud',c.core.cloud_dsn())]:
        with psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
            rows = db.execute('SELECT id::text,storage_path FROM media_assets WHERE storage_path=ANY(%s::text[])', (paths,)).fetchall()
            readonly = db.execute("SELECT current_setting('transaction_read_only') AS value").fetchone()['value']
        if rows:
            raise ValueError('A derivative has a database media record; separate review required')
        checks[target] = {'transaction_read_only':readonly, 'candidate_media_records':0}
    bucket = storage.Client(project='artline-508319',credentials=c.core.GcloudCredentials()).bucket(c.core.BUCKET)
    for path in paths:
        if bucket.get_blob(path.lstrip('/')):
            raise ValueError('A derivative already exists in cloud storage; separate review required')
    records = []
    for path, (run, im, review, receipt, source) in candidates.items():
        destination = c.BACKUP/'held-derivatives'/run.name/source.name
        if move:
            c.save(destination, source.read_bytes())
            if c.core.sha(destination.read_bytes()) != im['sha256'] or c.core.sha(source.read_bytes()) != im['sha256']:
                raise ValueError('Verified private copy required before removing local public path')
            source.unlink()
            c.core.event(run, {'provider':im['provider'],'artwork_id':im['artwork_id'],'external_id':im['external_id'],
                'outcome':'manual_review','reason':review['note'],'held_derivative_archive':str(destination),
                'sha256':im['sha256'],'source_receipt':str(receipt.relative_to(c.RUN))})
        records.append({'artwork_id':im['artwork_id'],'round':run.name,'sha256':im['sha256'],
            'original_path':path,'private_archive':str(destination),'reason':review['note'],
            'database_media_record_absent_in_both':True,'gcs_object_absent':True,
            'local_public_copy_removed':move and not source.exists()})
    result = {'checked_at':c.core.now(),'mode':'archived' if move else 'verified_dry_run',
              'database_writes':0,'targets':checks,'count':len(records),'records':records}
    c.save(c.RUN/('held-derivative-archive-'+str(time.time_ns())+'.json'),result)
    print(result['mode'],len(records),'exact campaign files; both databases read-only; no cloud deletions')


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--move',action='store_true')
    main(parser.parse_args().move)
