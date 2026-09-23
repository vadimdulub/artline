#!/usr/bin/env python3
"""Classify missing audited files without restoring held or withdrawn images."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--local-only',action='store_true');a=p.parse_args()
    audit=json.loads((a.run/'size-audit.json').read_text())
    paths=sorted({r['path'] for r in audit['file_issues'] if r.get('error')})
    result={'at':core.now(),'database_writes':False,'targets':{}}
    targets=[('local','postgres://localhost/artline')]
    if not a.local_only:targets.append(('cloud',core.cloud_dsn()))
    for target,dsn in targets:
        with psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
            rows=db.execute("""SELECT m.id::text,m.storage_path,m.rights_status,m.verified_at,m.source_page_url,m.byte_size,
                (SELECT count(*) FROM artworks a WHERE a.primary_media_id=m.id) artwork_links,
                (SELECT count(*) FROM artwork_media am WHERE am.media_id=m.id) secondary_links,
                (SELECT count(*) FROM artists p WHERE p.portrait_media_id=m.id) portrait_links,
                (SELECT jsonb_agg(jsonb_build_object('id',a.id,'title',a.title,'status',a.status)) FROM artworks a WHERE a.primary_media_id=m.id) artworks
                FROM media_assets m WHERE m.storage_path=ANY(%s) ORDER BY m.storage_path""",(paths,)).fetchall()
        summary={'missing_media_records':len(rows),'rights':dict(collections.Counter(r['rights_status'] for r in rows)),
            'unlinked':sum(r['artwork_links']==r['secondary_links']==r['portrait_links']==0 for r in rows),
            'linked':sum(r['artwork_links']+r['secondary_links']+r['portrait_links']>0 for r in rows)}
        result['targets'][target]={'summary':summary,'records':rows}
        print(target,json.dumps(summary),flush=True)
    core.save_new(a.run/('missing-file-review-local.json' if a.local_only else 'missing-file-review.json'),result)


if __name__=='__main__':main()
