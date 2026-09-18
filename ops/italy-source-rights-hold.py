#!/usr/bin/env python3
"""Withdraw only this campaign's two newly attached Ambrosiana reproductions.

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
EXPECTED={'1b4d4dc2-f5a7-479d-bf76-f620226717f7','97b452a8-3b80-4e9f-8602-96de29d9c4fd'}
POLICY={
    'institution_slug':'pinacoteca-ambrosiana',
    'source_url':'https://www.ambrosiana.it/ambrosiana-info/pinacoteca/faq/',
    'supporting_url':'https://www.ambrosiana.it/en/discover/masterpieces/image-requests/photo-reproduction-request/',
    'access':'Official FAQ indexed in web search with crawl reported yesterday; direct open returned a verification page. Official reproduction-request form separately indexed.',
    'finding':'The museum states that redistribution of photographs requires prior authorization through its exclusive image distributor; a publishing-licence process is offered.',
    'decision':'Rights unresolved for this app despite Commons public-domain labels. Hold selected museum-source reproductions pending explicit authorization; no legal determination about the underlying paintings.',
    'affected_campaign_artworks':sorted(EXPECTED),
}

def main():
    policy_path=c.RUN/'institution-rights-holds/ambrosiana.json'
    if not policy_path.exists():c.save(policy_path,dict(POLICY,checked_at=c.core.now()))
    policy=c.load(policy_path);images=[]
    for run in c.RUN.glob('round-*'):
        for path in (run/'images').glob('*/*.json'):
            im=c.load(path)
            if im['artwork_id'] in EXPECTED:
                images.append((run,im))
    if {im['artwork_id'] for _,im in images}!=EXPECTED or len(images)!=2:
        raise ValueError('Exact two campaign image receipts required')
    backup=c.BACKUP/'ambrosiana-rights-hold';out=c.RUN/'ambrosiana-rights-hold'
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
                        ('HOLD: newly found museum redistribution terms conflict with the earlier Commons-based clearance; source evidence retained pending explicit authorization.',Jsonb({'subsequent_rights_hold':policy}),im['media_id']))
        print(target,'two own image links withdrawn; artwork metadata retained',flush=True)
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
            rows=db.execute('''SELECT a.id::text,a.primary_media_id::text,a.status,m.id::text media_id,m.rights_status,m.verified_at
                FROM artworks a JOIN media_assets m ON m.id=ANY(%s::uuid[])
                WHERE a.id=ANY(%s::uuid[]) AND m.id=(CASE WHEN a.id=%s THEN %s::uuid ELSE %s::uuid END)''',
                ([im['media_id'] for _,im in images],[im['target_ids'][target] for _,im in images],images[0][1]['target_ids'][target],images[0][1]['media_id'],images[1][1]['media_id'])).fetchall()
            if len(rows)!=2 or any(r['primary_media_id'] or r['rights_status']!='unknown' or r['verified_at'] for r in rows):raise ValueError('Rights withdrawal verification failed')
            verification['targets'][target]=rows
    for _,im in images:
        if bucket.get_blob(im['path'].lstrip('/')):raise ValueError('Own public storage copy remains')
        response=requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app'+im['path'],timeout=35)
        verification['storage'].append({'artwork_id':im['artwork_id'],'object_absent':True,'public_http_status':response.status_code})
        if response.status_code!=404:raise ValueError('Unexpected public response after own-copy withdrawal')
    c.save(out/'verification.json',verification)
    print('Both databases, private backups and removed public copies verified',flush=True)

if __name__=='__main__':main()
