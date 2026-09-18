#!/usr/bin/env python3
"""Verify new deliveries through the unauthenticated public site, read-only."""
import argparse, concurrent.futures, csv, importlib.util, json
from pathlib import Path
import requests

s=importlib.util.spec_from_file_location('e',Path(__file__).with_name('export-overnight-research-handoff.py'))
e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
CORE=e.CORE;BASE=e.BASE

def main(phase):
    folder=BASE/'final-audit'/phase;dest=folder/'public-delivery.json';assert not dest.exists()
    snap=json.loads((folder/'production-semantic-snapshot.json').read_text())
    with (BASE/'chatgpt-handoff/final-20260914/verified_selected_images.csv').open(encoding='utf-8-sig',newline='') as f:
        prior=list(csv.DictReader(f))
    already_uploaded={r['storage_path'] for r in prior if r['production_upload_verified']=='true'}
    selected=[im for path,im in snap['images'].items() if path not in already_uploaded and im['verified'] and im['rights_status'] in ('public_domain','cc0','cc_by','cc_by_sa','licensed')]
    def image_check(im):
        url=e.m.SITE+im['storage_path'];response=requests.get(url,timeout=(10,45));response.raise_for_status()
        assert len(response.content)==im['byte_size'] and CORE.sha(response.content)==im['checksum_sha256'],url
        return dict(url=url,status=response.status_code,sha256=CORE.sha(response.content),bytes=len(response.content),content_type=response.headers.get('Content-Type'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:images=list(pool.map(image_check,selected))
    pages=[]
    for code in ('NL','PT'):
        url=e.m.SITE+'/api/backend/v1/timeline?start=1100&end=2000&popular=false&women=false&country='+code
        response=requests.get(url,timeout=(10,45));response.raise_for_status();data=response.json();assert data['total']>0
        pages.append(dict(url=url,status=response.status_code,country=code,painters=data['total'],sha256=CORE.sha(response.content)))
    root=BASE/'chatgpt-handoff'/phase
    with (root/'artworks_added_this_session.csv').open(encoding='utf-8-sig',newline='') as f:
        works=[r for r in csv.DictReader(f) if r['status']=='review']
    choices=[]
    for predicate in (lambda r:'PT' in r['artist_country_codes'].split(';'),lambda r:r['artwork_slug']=='wikimedia-artwork-q21619670'):
        work=next(r for r in works if predicate(r) and r['public_artwork_url']);response=requests.get(work['public_artwork_url'],timeout=(10,45));response.raise_for_status()
        api_url=work['public_artwork_url'].replace(e.m.SITE+'/',e.m.SITE+'/api/backend/v1/',1)
        detail=requests.get(api_url,timeout=(10,45));detail.raise_for_status();payload=detail.json()
        assert work['production_artwork_id'] in detail.text
        choices.append(dict(slug=work['artwork_slug'],url=work['public_artwork_url'],status=response.status_code,sha256=CORE.sha(response.content),bytes=len(response.content),api_url=api_url,api_status=detail.status_code,api_sha256=CORE.sha(detail.content)))
    result=dict(at=CORE.now(),scope='Unauthenticated public image bytes for every newly delivered selected asset since the earlier handoff, plus Dutch/Portuguese timelines and two artwork pages. No editor credentials or writes.',images=images,timelines=pages,artwork_pages=choices)
    CORE.save_new(dest,result);print('Public delivery verified',len(images),'new image assets and',len(pages)+len(choices),'public endpoints',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',required=True);a=p.parse_args();assert all(c.isalnum() or c in '-_' for c in a.phase);main(a.phase)
