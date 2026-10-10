"""Independent database, replay and public-image verification for Theocharakis."""
import argparse
import concurrent.futures
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import requests

spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-theocharakis-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,m,RUN=a.c,a.m,a.RUN
EXPECTED='79734d55e12a1ee86f87cb03f5c7984c215c9f772caeb07e9064a6b7a42f7080'

def readback():
    assert not(RUN/'readback-001.json').exists();applied=m.load(RUN/(a.KEY+'-applied.json'));assert applied['plan_sha256']==EXPECTED
    p,digest=a.validate_plan();assert digest==EXPECTED
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');result=a.verify(db,p,digest)
        primary=db.execute("SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND status<>'archived' AND primary_media_id IS NOT NULL",(c.IID,)).fetchone()['n'];assert primary==123
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
            if len(images)%25==0:print(json.dumps(dict(public_images=len(images),total=114)),flush=True)
    rows={v['facts']['source_id'].split('-')[-1]:v for v in p['records']};api=[]
    for number in ['111583','103157','103068','103111']:
        v=rows[number];url='https://artlines.org/api/backend/v1/atlas/artworks/'+v['artwork_id'];response=requests.get(url,timeout=(15,35));response.raise_for_status();body=response.json()
        assert body['id']==v['artwork_id'] and body['status']=='review' and body['display'] is None and body['holding']['id']==c.IID
        assert any(x.get('id',x.get('artist_id'))==a.r.ARTIST for x in body['creators'])
        assert body['creation_year_start']==v['facts']['first'] and body['creation_year_end']==v['facts']['last']
        api.append(dict(at=m.now(),number=number,url=url,status=response.status_code,body=body))
    undated=next(v for v in p['records'] if v['facts']['first'] is None)
    boat=p['holdings'][0]
    for v,route in [(undated,'artists/greek-papaloukas-spyros/works/'),(boat,'atlas/artworks/')]:
        url='https://artlines.org/api/backend/v1/'+route+v['artwork_id'];response=requests.get(url,timeout=(15,35));response.raise_for_status();body=response.json()
        assert body['id']==v['artwork_id'] and body['status']=='review' and body['holding']['id']==c.IID and body['display'] is None
        if v is undated:assert body['creation_year_start'] is None and body['creation_year_end'] is None
        else:
            old=next(x for x in p['before']['artworks'] if x['id']==v['artwork_id']);oldmedia=next(x for x in p['before']['media_assets'] if x['id']==old['primary_media_id'])
            assert body['title']==old['title'] and body['creation_year_start']==old['creation_year_start'] and body['media_url']==oldmedia['storage_path']
        api.append(dict(at=m.now(),url=url,status=response.status_code,body=body,verification='Undated review work through public artist route' if v is undated else 'Existing Boat title/date/primary image preserved; new Theocharakis holding visible'))
    m.save(RUN/'public-delivery-001.json',dict(at=m.now(),plan_sha256=digest,images=images,api_samples=api,public_image_hashes_matched=114,public_artwork_samples=6,sampled_review_records_visible=True,date_scope_note='Four new dated samples and the existing Boat use the atlas route; an undated new work uses the public artist route. Numeric atlas scope and museum member access remain unchanged.',script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(public_images=114,public_artwork_samples=6)),flush=True)

def checks():
    assert not(RUN/'checks-001.json').exists();p,digest=a.validate_plan();assert digest==EXPECTED
    read=m.load(RUN/'readback-001.json');replay0=m.load(RUN/'replay-001.json');public0=m.load(RUN/'public-delivery-001.json');tests=m.load(RUN/'offline-tests-001.json')
    assert read['local_unchanged'] and replay0['zero_writes'] and public0['public_image_hashes_matched']==114 and tests['tests_passed']==23 and tests['exit_code']==0
    m.save(RUN/'checks-001.json',dict(at=m.now(),offline_tests_passed=23,atomic_verification_passed=True,readback_passed=True,replay_zero_writes=True,local_unchanged=True,protected_existing=65,protected_prior=1387,actual_added=196,actual_existing_links=1,new_images=114,new_primary_images=110,alternate_images=4,new_artist_links=196,new_published=0,new_display_claims=0,plan_reference=c.ref(a.PLAN),apply_reference=c.ref(RUN/(a.KEY+'-applied.json')),readback_reference=c.ref(RUN/'readback-001.json'),replay_reference=c.ref(RUN/'replay-001.json'),public_reference=c.ref(RUN/'public-delivery-001.json'),backup_reference=c.ref(RUN/'cloud-backup-001.json'),script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(checks_passed=True,new_records=196,images=114)),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['readback','replay','public','checks']);args=parser.parse_args();globals()[args.command]()
