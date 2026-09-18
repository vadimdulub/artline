#!/usr/bin/env python3
"""Withdraw only exact reviewed image receipts from this Italy campaign.

Keep artwork records, all metadata, source evidence and backed-up image bytes.
Exact IDs, original preimages and storage generation/checksums constrain changes.
"""
import importlib.util
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from google.cloud import storage
import requests

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('campaign',ROOT/'ops/italy-image-campaign.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--policy',required=True,choices=['carrara','brescia','tadini','gam','castello','brera','venice','borghese','pavia','monza','poldi','khm','scotland','vienna-academy','commercial-use-20260917'])
args=parser.parse_args()
POLICY_PATH=c.RUN/'institution-rights-holds'/(args.policy+'.json')
POLICY=c.load(POLICY_PATH)
EXPECTED_RECEIPTS={r['artwork_id']:r for r in c.load(c.RUN/(args.policy+'-rights-hold')/'affected-images.json')}
EXPECTED=set(EXPECTED_RECEIPTS)
if EXPECTED!=set(POLICY['affected_campaign_artworks']) or not EXPECTED:
    raise ValueError('Exact reviewed policy/affected receipt identity required')

def main():
    policy_path=POLICY_PATH
    if not policy_path.exists():c.save(policy_path,dict(POLICY,checked_at=c.core.now()))
    policy=c.load(policy_path);images=[]
    for run in c.RUN.glob('round-*'):
        for path in (run/'images').glob('*/*.json'):
            im=c.load(path)
            if im['artwork_id'] in EXPECTED and im['media_id']==EXPECTED_RECEIPTS[im['artwork_id']]['media_id'] and im['sha256']==EXPECTED_RECEIPTS[im['artwork_id']]['sha256']:
                images.append((run,im))
    if {im['artwork_id'] for _,im in images}!=EXPECTED or len(images)!=len(EXPECTED):
        raise ValueError('Exact campaign image receipts required')
    backup=c.BACKUP/(args.policy+'-rights-hold');out=c.RUN/(args.policy+'-rights-hold')
    for run,im in images:
        local=ROOT/'apps/web/public'/im['path'].lstrip('/')
        destination=backup/'derivatives'/local.name
        if local.exists():
            if c.core.sha(local.read_bytes())!=im['sha256']:raise ValueError('Own derivative checksum differs')
            c.save(destination,local.read_bytes())
        if not destination.exists() or c.core.sha(destination.read_bytes())!=im['sha256']:
            raise ValueError('Verified private backup required before withdrawal')
    for target,dsn in [('local','postgres://127.0.0.1/artline'),('cloud',c.core.cloud_dsn())]:
        with psycopg.connect(dsn,row_factory=dict_row) as db:
            rows=[]
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='2s'")
                for run,im in images:
                    expected=next(r for r in c.load(run/(target+'-before.json')) if r['local_id']==im['artwork_id'])
                    row=db.execute('''SELECT a.id::text,a.primary_media_id::text,
                      to_jsonb(a) artwork,to_jsonb(m) media,to_jsonb(e) evidence,
                      to_jsonb(a)-ARRAY['primary_media_id','revision','updated_at','updated_by'] metadata,
                      coalesce((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id,aa.attribution_role)
                       FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]'::jsonb) creators
                      FROM artworks a JOIN media_assets m ON m.id=%s
                      JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=%s FOR UPDATE OF a,m,e''',
                      (im['media_id'],expected['target_id'])).fetchone()
                    if not row or row['metadata']!=expected['metadata'] or row['creators']!=expected['creators']:
                        raise ValueError('Artwork metadata/creators changed; withdrawal needs review')
                    if row['media']['checksum_sha256']!=im['sha256'] or row['media']['storage_path']!=im['path']:
                        raise ValueError('Media is no longer this campaign image')
                    if row['primary_media_id'] not in (None,im['media_id']):
                        raise ValueError('Another primary image must be preserved')
                    rows.append(row)
                path=backup/(target+'-before-withdrawal.json')
                if not path.exists():c.save(path,rows)
                for run,im in images:
                    db.execute('''UPDATE artworks SET primary_media_id=NULL,revision=revision+1,
                        updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id=%s''',
                        (c.core.ACTOR,im['target_ids'][target],im['media_id']))
                    db.execute('UPDATE media_assets SET rights_status=%s,verified_at=NULL,verified_by=NULL,updated_at=now() WHERE id=%s',
                        ('unknown',im['media_id']))
                    db.execute('''UPDATE media_rights_evidence SET rights_basis=%s,checked_at=now(),
                        evidence_json=evidence_json || %s::jsonb WHERE media_id=%s''',
                        (policy.get('rights_basis','HOLD: newly found museum redistribution terms conflict with the earlier Commons-based clearance; source evidence retained pending explicit authorization.'),Jsonb({'subsequent_rights_hold':policy}),im['media_id']))
        print(target,len(images),'own image links withdrawn; artwork metadata retained',flush=True)
    bucket=storage.Client(project='artline-508319',credentials=c.core.GcloudCredentials()).bucket(c.core.BUCKET)
    for run,im in images:
        blob=bucket.get_blob(im['path'].lstrip('/'))
        if blob:
            if (blob.metadata or {}).get('sha256')!=im['sha256'] or (blob.metadata or {}).get('artwork-id')!=im['artwork_id']:
                raise ValueError('Storage object ownership/checksum differs')
            c.save(backup/(im['artwork_id']+'-storage.json'),{'name':blob.name,'generation':blob.generation,'metadata':blob.metadata,'size':blob.size})
            blob.delete(if_generation_match=blob.generation)
        local=ROOT/'apps/web/public'/im['path'].lstrip('/')
        if local.exists():local.unlink()
        c.core.event(run,{'provider':im['provider'],'artwork_id':im['artwork_id'],'external_id':im['external_id'],
            'outcome':'withdrawn_for_source_rights_review','reason':policy['decision'],
            'policy_evidence':str(policy_path.relative_to(c.RUN)),'bytes_preserved':str(backup/'derivatives'/local.name)})
    verification={'checked_at':c.core.now(),'policy':policy,'targets':{},'storage':[]}
    for target,dsn in [('local','postgres://127.0.0.1/artline'),('cloud',c.core.cloud_dsn())]:
        with psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
            pairs=[(im['target_ids'][target],im['media_id']) for _,im in images]
            rows=db.execute('''SELECT a.id::text,a.primary_media_id::text,a.status,m.id::text media_id,m.rights_status,m.verified_at
                FROM unnest(%s::uuid[],%s::uuid[]) AS selected(artwork_id,media_id)
                JOIN artworks a ON a.id=selected.artwork_id
                JOIN media_assets m ON m.id=selected.media_id''',
                ([pair[0] for pair in pairs],[pair[1] for pair in pairs])).fetchall()
            if len(rows)!=len(images) or any(r['primary_media_id'] or r['rights_status']!='unknown' or r['verified_at'] for r in rows):
                raise ValueError('Rights withdrawal verification failed')
            verification['targets'][target]=rows
    for _,im in images:
        if bucket.get_blob(im['path'].lstrip('/')):raise ValueError('Own public storage copy remains')
        response=requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app'+im['path'],timeout=35)
        verification['storage'].append({'artwork_id':im['artwork_id'],'object_absent':True,'public_http_status':response.status_code})
        if response.status_code!=404:raise ValueError('Unexpected public response after own-copy withdrawal')
    c.save(out/'verification.json',verification)
    print('Both databases, private backups and removed public copies verified',flush=True)

if __name__=='__main__':main()
