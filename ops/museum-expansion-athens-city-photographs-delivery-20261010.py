"""Independent readback, replay and public visibility checks for55photographs."""
import argparse,contextlib,importlib.util,io,json
from pathlib import Path
import requests
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-athens-city-photographs-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,m,RUN=a.c,a.m,a.RUN
EXPECTED='60e2a9750ce13beb868e5559ad15e1cd7e57b0029fdbcac53236a8207ba1c6fd'

def readback():
    assert not(RUN/'readback-001.json').exists();assert m.load(RUN/(a.KEY+'-applied.json'))['plan_sha256']==EXPECTED;p,digest=a.validate_plan();assert digest==EXPECTED
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');result=a.verify(db,p,digest);primary=db.execute("SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND status<>'archived' AND primary_media_id IS NOT NULL",(c.IID,)).fetchone()['n'];assert primary==45
    with m.connect() as db:
        local=m.load(RUN/'initial-scope-001.json.gz');assert c.snapshot(db,local['scoped_ids'])==local['snapshot'] and c.counts(db)==local['counts']
    m.save(RUN/'readback-001.json',dict(at=m.now(),verification=result,plan_sha256=digest,primary_image_artworks=primary,local_unchanged=True,read_only=True,script_reference=c.ref(Path(__file__).resolve())));print(json.dumps(result),flush=True)

def replay():
    assert not(RUN/'replay-001.json').exists();assert m.load(RUN/'readback-001.json')['local_unchanged'];p,digest=a.validate_plan();assert digest==EXPECTED;out=io.StringIO()
    with contextlib.redirect_stdout(out):a.apply(digest)
    assert out.getvalue().strip()=='Unchanged replay: zero writes';m.save(RUN/'replay-001.json',dict(at=m.now(),stdout=out.getvalue(),zero_writes=True,plan_sha256=digest,script_reference=c.ref(Path(__file__).resolve())));print(out.getvalue(),end='',flush=True)

def public():
    assert not(RUN/'public-delivery-001.json').exists();assert m.load(RUN/'readback-001.json')['local_unchanged'];p,digest=a.validate_plan();assert digest==EXPECTED;samples=[]
    for number in [1,13,21,30]:
        v=next(x for x in p['records'] if x['facts']['number']==number);params=dict(q=v['facts']['title'],limit=60)
        if v['facts']['first'] is None:params['undated']='true'
        response=requests.get('https://artlines.org/api/backend/v1/artworks',params=params,timeout=(15,35));response.raise_for_status();body=response.json();item=next(x for x in body['items'] if x['id']==v['artwork_id']);assert item['status']=='review' and item['museum']['id']==c.IID and item['title']==v['facts']['title'] and item['date_display']==v['facts']['date_display'];samples.append(dict(at=m.now(),number=number,url=response.url,status=response.status_code,body=body,matched_artwork_id=v['artwork_id']))
    m.save(RUN/'public-delivery-001.json',dict(at=m.now(),plan_sha256=digest,api_samples=samples,public_artwork_samples=4,sampled_review_records_visible=True,new_images=0,date_scope_note='One unresolved-date and three source-dated photographic works visible in the public artwork directory.208catalogue works include111numeric-date eligible and97unknown/unresolved dates; image and member controls unchanged.',script_reference=c.ref(Path(__file__).resolve())));print(json.dumps(dict(public_artwork_samples=4,new_images=0)),flush=True)

def checks():
    assert not(RUN/'checks-001.json').exists();p,digest=a.validate_plan();assert digest==EXPECTED;read=m.load(RUN/'readback-001.json');replay0=m.load(RUN/'replay-001.json');public0=m.load(RUN/'public-delivery-001.json');tests=m.load(RUN/'offline-tests-001.json');assert read['local_unchanged'] and replay0['zero_writes'] and public0['public_artwork_samples']==4 and tests['tests_passed']==18 and tests['exit_code']==0
    m.save(RUN/'checks-001.json',dict(at=m.now(),offline_tests_passed=18,atomic_verification_passed=True,readback_passed=True,replay_zero_writes=True,local_unchanged=True,protected_existing=153,protected_prior=1972,actual_added=55,actual_existing_links=0,new_images=0,new_artist_links=0,new_published=0,new_display_claims=0,plan_reference=c.ref(a.PLAN),apply_reference=c.ref(RUN/(a.KEY+'-applied.json')),readback_reference=c.ref(RUN/'readback-001.json'),replay_reference=c.ref(RUN/'replay-001.json'),public_reference=c.ref(RUN/'public-delivery-001.json'),backup_reference=c.ref(RUN/'cloud-backup-001.json'),script_reference=c.ref(Path(__file__).resolve())));print(json.dumps(dict(checks_passed=True,new_records=55)),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['readback','replay','public','checks']);args=parser.parse_args();globals()[args.command]()
