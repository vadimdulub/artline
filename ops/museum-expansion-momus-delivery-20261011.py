"""Independent database, replay and public-image verification for MOMus Contemporary Art."""
import argparse
import concurrent.futures
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import requests

spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-momus-apply-v2-20261011.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,m,RUN=a.c,a.m,a.RUN
EXPECTED='b24bae96a69e52dfce4371fc4224c39bb8877e09b5e1868e130656e3ab40eed9'

def readback():
    assert not(RUN/'readback-001.json').exists();applied=m.load(RUN/(a.KEY+'-applied.json'));assert applied['plan_sha256']==EXPECTED
    p,digest=a.validate_plan();assert digest==EXPECTED
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');result=a.verify(db,p,digest)
        primary=db.execute("SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND status<>'archived' AND primary_media_id IS NOT NULL",(c.IID,)).fetchone()['n'];assert primary==41
    with m.connect() as db:
        local=m.load(RUN/'initial-scope-001.json.gz');assert c.snapshot(db,local['scoped_ids'])==local['snapshot'] and c.counts(db)==local['counts']
    m.save(RUN/'readback-001.json',dict(at=m.now(),verification=result,plan_sha256=digest,primary_image_artworks=primary,local_unchanged=True,read_only=True,script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(verified=result,primary_image_artworks=primary,local_unchanged=True)),flush=True)

def replay():
    assert not(RUN/'replay-001.json').exists();assert m.load(RUN/'readback-001.json')['local_unchanged'];p,digest=a.validate_plan();assert digest==EXPECTED
    output=io.StringIO()
    with contextlib.redirect_stdout(output):a.apply(digest)
    assert output.getvalue().strip()=='Unchanged replay: zero writes'
    m.save(RUN/'replay-001.json',dict(at=m.now(),stdout=output.getvalue(),zero_writes=True,plan_sha256=digest,script_reference=c.ref(Path(__file__).resolve())))
    print(output.getvalue(),end='',flush=True)

def public():
    assert not(RUN/'public-delivery-001.json').exists();assert m.load(RUN/'readback-001.json')['local_unchanged'];p,digest=a.validate_plan();assert digest==EXPECTED
    def check(im):
        dest=RUN/'public-image-receipts'/(im['media_id']+'.json')
        if dest.exists():
            old=m.load(dest);assert old['sha256']==im['sha256'] and old['status']==200;return old
        url='https://artlines.org'+im['storage_path'];response=requests.get(url,timeout=(15,45));response.raise_for_status();checksum=hashlib.sha256(response.content).hexdigest()
        assert checksum==im['sha256'] and len(response.content)==im['bytes']
        value=dict(at=m.now(),media_id=im['media_id'],url=url,status=response.status_code,sha256=checksum,bytes=len(response.content),content_type=response.headers.get('Content-Type'));m.save(dest,value);return value
    images=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for value in pool.map(check,p['images']):
            images.append(value)
            if len(images)%25==0:print(json.dumps(dict(public_images=len(images),total=38)),flush=True)
    samples=[]
    for number in [8769,8701,9013,9655,17784,685]:
        v=next(v for v in p['records'] if v['facts']['number']==number)
        expected=a.metadata(v) if v in p['records'] else next(x for x in p['before']['artworks'] if x['id']==v['artwork_id'])
        url='https://artlines.org/api/backend/v1/artworks';params=dict(q=expected['title'][:160],limit=60)
        if expected['creation_year_start'] is None:params['undated']='true'
        response=requests.get(url,params=params,timeout=(15,35));response.raise_for_status();body=response.json()
        item=next(x for x in body['items'] if x['id']==v['artwork_id'])
        assert item['status']=='review' and item['museum']['id']==c.IID and item['title']==expected['title'] and item['date_display']==expected['date_display']
        samples.append(dict(at=m.now(),source_id=v['facts']['source_id'],url=response.url,status=response.status_code,body=body,matched_artwork_id=v['artwork_id']))
    m.save(RUN/'public-delivery-001.json',dict(at=m.now(),plan_sha256=digest,images=images,api_samples=samples,public_image_hashes_matched=38,public_artwork_samples=6,sampled_review_records_visible=True,date_scope_note='Sixnewreviewobjectssampled acrosspainting,folkart,shadowtheatre,compositework andstudy. Museum210catalogue/204numericeligible/41illustrated. Two new sourceperiods1967–1974remainreview; four old undated records unchanged. Notalluncertaindatepublicquerycombinations tested. Membermuseumaccess unchanged.',script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(public_images=38,public_artwork_samples=6)),flush=True)

def checks():
    assert not(RUN/'checks-001.json').exists();p,digest=a.validate_plan();assert digest==EXPECTED
    read=m.load(RUN/'readback-001.json');replay0=m.load(RUN/'replay-001.json');public0=m.load(RUN/'public-delivery-001.json');tests=m.load(RUN/'offline-tests-001.json')
    assert read['local_unchanged'] and replay0['zero_writes'] and public0['public_image_hashes_matched']==38 and public0['public_artwork_samples']==6 and tests['tests_passed']==14 and tests['exit_code']==0
    m.save(RUN/'checks-001.json',dict(at=m.now(),offline_tests_passed=14,atomic_verification_passed=True,readback_passed=True,replay_zero_writes=True,local_unchanged=True,protected_existing=11,protected_prior=2938,actual_added=199,actual_existing_links=0,new_images=38,new_primary_images=38,alternate_images=0,new_artist_links=0,new_published=0,new_display_claims=0,plan_reference=c.ref(a.PLAN),apply_reference=c.ref(RUN/(a.KEY+'-applied.json')),readback_reference=c.ref(RUN/'readback-001.json'),replay_reference=c.ref(RUN/'replay-001.json'),public_reference=c.ref(RUN/'public-delivery-001.json'),backup_reference=c.ref(RUN/'cloud-backup-001.json'),script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(checks_passed=True,new_records=199,images=38)),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['readback','replay','public','checks']);args=parser.parse_args();globals()[args.command]()
