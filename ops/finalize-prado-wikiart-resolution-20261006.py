#!/usr/bin/env python3
"""Verify the complete museum scope and publish the durable research audit."""
import collections, concurrent.futures, gzip, hashlib, html, importlib.util, json, shutil
from pathlib import Path
import requests
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/deliver-prado-wikiart-resolution-20261006.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
R=d.RUN;P=d.RESEARCH;r=d.r
data,pin=d.d.pinned();applied=r.load(R/'production-applied.json')
baseline=r.load(R/'fresh-production-snapshot.json.gz')['records'];selected=set(applied['artwork_ids'])
assert applied['plan_sha256']==pin['sha256'] and len(selected)==11
with r.connect('production') as db,db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    after=d.d.snapshots(db,list(baseline))
    counts=db.execute("SELECT count(*) works,count(primary_media_id) images,count(*) FILTER(WHERE status='review') review FROM artworks WHERE current_institution_id=%s",(d.p.MUSEUM,)).fetchone()
    checks=db.execute('''SELECT m.id::text media_id,m.provider_name,m.source_page_url,m.byte_size,m.checksum_sha256,e.source_image_url,e.evidence_json
        FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])''',([x['media_id']for x in data['prepared'].values()],)).fetchall()
assert counts=={'works':548,'images':253,'review':548} and set(after)==set(baseline)
for aid,old in baseline.items():
    new=after[aid]
    if aid not in selected:assert old==new,('Unselected record changed',aid);continue
    allowed={'primary_media_id','revision','updated_at','updated_by'}
    assert {k:v for k,v in old['artwork'].items()if k not in allowed}=={k:v for k,v in new['artwork'].items()if k not in allowed}
    assert old['creators']==new['creators'] and new['artwork']['revision']==old['artwork']['revision']+1
    assert new['artwork']['primary_media_id']==data['prepared'][aid]['media_id']
media={x['media_id']:x for x in checks};assert len(media)==11
for item in data['claims']:
    im=data['prepared'][item['work']['id']];m=media[im['media_id']]
    assert m['provider_name']=='WikiArt' and m['source_page_url']==item['page']['url']
    assert m['checksum_sha256']==im['sha256'] and m['byte_size']==im['bytes']<=100000
    assert m['source_image_url']==item['page']['image_url']
    assert m['evidence_json']['plan_sha256']==pin['sha256']
    assert r.sha(Path(im['visual_path']).read_bytes())==im['sha256']
    with Image.open(im['visual_path'])as image:image.load();assert image.size==(im['width'],im['height'])
    assert r.load(R/'uploads'/(item['work']['id']+'.json'))['public_bytes_verified']

def api(item):
    aid=item['work']['id'];url='https://artlines.org/api/backend/v1/museums/museo-del-prado/works/'+aid
    response=requests.get(url,timeout=(15,45));body=response.json()if response.status_code==200 else {}
    expected=data['prepared'][aid]['path']
    return {'artwork_id':aid,'url':url,'status':response.status_code,'expected_image':expected,'actual_image':body.get('media_url'),
        'verified':response.status_code==200 and body.get('media_url')==expected and body.get('title')==item['work']['title']}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:api_checks=list(pool.map(api,data['claims']))
verification={'at':r.now(),'plan_sha256':pin['sha256'],'artworks_checked':548,'images_before':242,'images_after':253,'added_images':11,
    'remaining_missing_images':295,'all_537_unselected_records_and_attachments_unchanged':True,'selected_metadata_and_creators_preserved':True,
    'all_548_remain_review':True,'source_and_rights_evidence_checked':11,'decoded_files_and_checksums_verified':11,'public_image_checksums_verified':11,
    'maximum_derivative_bytes':max(x['bytes']for x in data['prepared'].values()),'live_artwork_api_checks':api_checks,
    'errors':[x for x in api_checks if not x['verified']],'local_database_writes':0,'new_artworks':0,'publication_changes':0}
r.save(R/'complete-verification.json',verification);assert not verification['errors']

print(json.dumps({k:v for k,v in verification.items() if k != "live_artwork_api_checks"}),flush=True)
