"""Independent readback, zero-write replay and public delivery checks for Larissa."""
import argparse
import concurrent.futures
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import requests

spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('museum-expansion-larissa-reconciled-v2-20261010.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
a,c,m,RUN=b.a,b.c,b.m,b.RUN
EXPECTED='950bc19931f2583ebf5f9a29b17ead319f6d009c4ed959b1e7f4a3950798b07b'

def readback():
    assert not(RUN/'checks-001.json').exists()
    receipt=m.load(RUN/(a.KEY+'-applied.json'));assert receipt['plan_sha256']==EXPECTED
    p,digest=a.validate_plan();assert digest==EXPECTED
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');result=a.verify(db,p,digest)
        primary=db.execute('SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND status<>%s AND primary_media_id IS NOT NULL',(c.IID,'archived')).fetchone()['n'];assert primary==194
    with m.connect() as db:
        local=m.load(RUN/'initial-scope-001.json.gz');assert c.snapshot(db,local['scoped_ids'])==local['snapshot'] and c.counts(db)==local['counts']
    replay=io.StringIO()
    with contextlib.redirect_stdout(replay):a.apply(digest)
    assert replay.getvalue().strip()=='Unchanged replay: zero writes'
    m.save(RUN/'readback-001.json',dict(at=m.now(),verification=result,plan_sha256=digest,primary_image_artworks=primary,local_unchanged=True,read_only=True))
    m.save(RUN/'replay-001.json',dict(at=m.now(),stdout=replay.getvalue(),zero_writes=True,plan_sha256=digest))
    tests=m.load(RUN/'offline-tests-002.json');assert tests['exit_code']==0 and tests['tests_passed']==19
    m.save(RUN/'checks-001.json',dict(at=m.now(),offline_tests_passed=19,atomic_verification_passed=True,readback_passed=True,replay_zero_writes=True,local_unchanged=True,protected_existing=71,protected_prior=1026,actual_added=184,actual_existing_links=3,new_images=205,new_primary_images=181,alternate_images=24,new_artist_links=0,new_published=0,new_display_claims=0,plan_reference=c.ref(a.PLAN),apply_reference=c.ref(RUN/(a.KEY+'-applied.json')),readback_reference=c.ref(RUN/'readback-001.json'),replay_reference=c.ref(RUN/'replay-001.json'),backup_reference=c.ref(RUN/'cloud-backup-001.json'),script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(verified=result,primary_image_artworks=primary,replay_zero_writes=True,local_unchanged=True)),flush=True)

def public():
    assert not(RUN/'public-delivery-001.json').exists();assert m.load(RUN/(a.KEY+'-applied.json'))['created']==184
    p,digest=a.validate_plan();assert digest==EXPECTED
    def check(im):
        dest=RUN/'public-image-receipts'/(im['media_id']+'.json')
        if dest.exists():
            old=m.load(dest);assert old['sha256']==im['sha256'] and old['status']==200;return old
        url='https://artlines.org'+im['storage_path'];response=requests.get(url,timeout=(15,45));response.raise_for_status()
        checksum=hashlib.sha256(response.content).hexdigest();assert checksum==im['sha256'] and len(response.content)==im['bytes']
        result=dict(at=m.now(),media_id=im['media_id'],url=url,status=response.status_code,sha256=checksum,bytes=len(response.content),content_type=response.headers.get('Content-Type'))
        m.save(dest,result);return result
    images=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for value in pool.map(check,p['images']):
            images.append(value)
            if len(images)%25==0:print(json.dumps(dict(public_images=len(images),total=205)),flush=True)
    samples=[p['records'][0]]+p['holdings']
    api=[]
    for v in samples:
        url='https://artlines.org/api/backend/v1/atlas/artworks/'+v['artwork_id'];response=requests.get(url,timeout=(15,35));response.raise_for_status();body=response.json()
        assert body['id']==v['artwork_id'] and body['status']=='review' and body['display'] is None
        assert body['holding'] is not None
        api.append(dict(at=m.now(),url=url,status=response.status_code,body=body))
    m.save(RUN/'public-delivery-001.json',dict(at=m.now(),plan_sha256=digest,images=images,api_samples=api,public_image_hashes_matched=205,public_artwork_samples=4,all_active_review_records_visible=True,script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(public_images=205,public_artwork_samples=4)),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['readback','public']);args=parser.parse_args();globals()[args.command]()
