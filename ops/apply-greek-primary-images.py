#!/usr/bin/env python3
"""Attach visually reviewed, exact-object Commons images to both catalogues."""
import argparse,base64,hashlib,importlib.util,json
from pathlib import Path
import requests
from google.api_core.exceptions import PreconditionFailed
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-greek-primary-images.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
m=r.m;RUN=r.RUN;CORE=r.CORE
PLAN_NAME='application-plan.json';MANIFEST_NAME='application-manifest.json'

def plan():
    prepared=json.loads((RUN/'preparation.json').read_text());qa=json.loads((RUN/'quality-review.json').read_text())
    assert qa['contact_sheet_sha256']==prepared['contact_sheet_sha256']==CORE.sha((RUN/'contact-sheet.jpg').read_bytes())
    images=[]
    for name,sha in sorted(prepared['prepared_hashes'].items()):
        raw=(RUN/'prepared'/name).read_bytes();assert CORE.sha(raw)==sha;im=json.loads(raw);assert im['key'] in qa['accepted'];images.append(im)
    targets={}
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');rows=[]
            for im in images:
                a=db.execute("SELECT to_jsonb(a) work FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='nationalgallery-gr-work' WHERE e.external_id=%s",(im['key'],)).fetchall();assert len(a)==1
                w=a[0]['work'];assert w['slug']==im['artwork_slug'] and w['status']=='review' and w['primary_media_id'] is None
                assert w['creation_year_start'] is not None and w['creation_year_end'] is not None and w['creation_year_end']<=1970
                assert db.execute('SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=%s AND a.slug=%s',(w['id'],im['artist_slug'])).fetchone()
                rows.append(dict(key=im['key'],work=w))
        targets[target]=rows;CORE.save_new(m.BACKUPS/('greek-primary-images-'+target+'-preimages.json'),rows)
    data=dict(at=CORE.now(),images=images,targets=targets,qa=qa);path=RUN/'application-plan.json';CORE.save_new(path,data)
    CORE.save_new(RUN/'application-manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha(path.read_bytes()),images=len(images)))
    print('Greek image plan',len(images),flush=True)

def read_plan():
    raw=(RUN/PLAN_NAME).read_bytes();pin=json.loads((RUN/MANIFEST_NAME).read_text())['plan_sha256'];assert CORE.sha(raw)==pin;return json.loads(raw),pin

def apply():
    data,pin=read_plan();images={im['key']:im for im in data['images']}
    bucket=CORE.storage.Client(project='artline-508319',credentials=CORE.GcloudCredentials()).bucket(CORE.BUCKET) if 'production' in data['targets'] else None
    for im in images.values():
        raw=(m.x.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert CORE.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
        if bucket is None:continue
        blob=bucket.blob(im['path'].lstrip('/'))
        if not blob.exists():
            blob.metadata={'sha256':im['sha256'],'license':im['license_label'],'museum_object':im['key']};blob.cache_control='public,max-age=31536000,immutable'
            try:
                blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
            except PreconditionFailed:
                # A completed upload whose response was lost can be retried by
                # the client. Keep the create-only precondition and accept an
                # existing generation only after verifying its actual bytes.
                blob.reload()
                existing=blob.download_as_bytes(if_generation_match=blob.generation,timeout=60)
                assert CORE.sha(existing)==im['sha256'], 'Existing storage object differs from the reviewed image'
        blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
    for target in data['targets']:
        with m.m.r.base.connect(target=='production') as db:
            for row in data['targets'][target]:
                im=images[row['key']];dest=RUN/'applied'/target/(im['key']+'.json')
                if dest.exists():continue
                old=row['work'];mid=im['media_id']
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(559220260914)')
                    w=db.execute('SELECT to_jsonb(a) work FROM artworks a WHERE id=%s FOR UPDATE',(old['id'],)).fetchone()['work']
                    if w['primary_media_id']==mid:
                        assert db.execute('SELECT 1 FROM media_assets WHERE id=%s AND checksum_sha256=%s',(mid,im['sha256'])).fetchone()
                    else:
                        assert w==old,'Artwork changed after image review'
                        sid=m.m.source(db,im.get('source_slug','overnight-greek-primary-images-20260913'),im.get('source_name','Wikimedia Commons — exact Greek museum object reproductions'),'collection_page',im.get('source_root','https://commons.wikimedia.org/'))
                        m.m.r.base.insert(db,'media_assets',dict(id=mid,storage_kind='local',storage_path=im['path'],source_page_url=im['page'],provider_name=im.get('provider_name','Wikimedia Commons'),mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=im['title']+' — '+im['artist'],rights_status=im['rights_status'],license_label=im['license_label'],license_url=im['license_url'],creator_credit=im['creator_credit'],attribution_text=im['attribution_text'],retrieved_at=im['download']['retrieved_at'],verified_at=im['checked_at'],verified_by=m.m.ACTOR))
                        m.m.r.base.insert(db,'media_rights_evidence',dict(media_id=mid,source_id=sid,source_record_id=im['identity']['choice']['page']['title'],source_checksum=im['identity']['choice']['receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=im['license_url'],rights_basis=im['identity']['identity_basis']+' Actual visual review of full-frame reproduction; primary museum dating retained.',adapter_version=im.get('adapter_version','greek-primary-images-v1'),checked_at=im['checked_at'],evidence_json=Jsonb(im)))
                        m.m.r.base.insert(db,'artwork_media',dict(artwork_id=old['id'],media_id=mid,sort_order=0,view_label='Selected reproduction'))
                        db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(mid,m.m.ACTOR,old['id']))
                CORE.save_new(dest,dict(at=CORE.now(),target=target,artwork_id=old['id'],media_id=mid,plan_sha256=pin));print(target,'Greek image attached',im['key'],flush=True)

def verify():
    data,pin=read_plan();images={im['key']:im for im in data['images']};report=dict(at=CORE.now(),plan_sha256=pin,databases={},public_images=[])
    for target in data['targets']:
        verified=[]
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY')
            for row in data['targets'][target]:
                im=images[row['key']];w=db.execute('SELECT to_jsonb(a) work FROM artworks a WHERE id=%s',(row['work']['id'],)).fetchone()['work'];ignored={'primary_media_id','revision','updated_at','updated_by'}
                assert {k:v for k,v in w.items() if k not in ignored}=={k:v for k,v in row['work'].items() if k not in ignored};assert w['status']=='review' and w['primary_media_id']==im['media_id']
                media=db.execute('SELECT to_jsonb(a) media FROM media_assets a WHERE id=%s',(im['media_id'],)).fetchone()['media'];assert media['checksum_sha256']==im['sha256'] and media['creator_credit']==im['creator_credit'] and media['license_url']==im['license_url']
                assert db.execute('SELECT 1 FROM media_rights_evidence WHERE media_id=%s',(im['media_id'],)).fetchone();assert db.execute('SELECT 1 FROM artwork_media WHERE artwork_id=%s AND media_id=%s',(w['id'],im['media_id'])).fetchone();verified.append(w['slug'])
        report['databases'][target]=verified
    if len(data['targets'])==2:assert report['databases']['local']==report['databases']['production']
    for im in (images.values() if 'production' in data['targets'] else []):
        resp=requests.get(m.SITE+im['path'],timeout=90);resp.raise_for_status();assert resp.headers['Content-Type'].startswith('image/jpeg') and CORE.sha(resp.content)==im['sha256'];report['public_images'].append(dict(url=m.SITE+im['path'],status=resp.status_code,sha256=im['sha256']))
    name='verification.json' if len(data['targets'])==2 else 'verification-'+next(iter(data['targets']))+'.json'
    report['production_delivery_verified']='production' in data['targets'];CORE.save_new(RUN/name,report);print('Primary images verified',list(data['targets']),len(images),'public HTTP checked',report['production_delivery_verified'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();globals()[a.command]()
