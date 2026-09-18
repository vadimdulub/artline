#!/usr/bin/env python3
"""Attach selected, visually reviewed Met CC0 reproductions to both DBs."""
import argparse,base64,hashlib,importlib.util,json
from pathlib import Path
import requests
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-dutch-met-images.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
m=r.m;CORE=r.CORE;RUN=r.RUN;SOURCE='overnight-dutch-met-images-20260913'

def plan(n):
    folder=RUN/f'round-{n:02d}';dest=folder/'application-plan.json'
    if dest.exists():return
    prep=json.loads((folder/'preparation.json').read_text());qa=json.loads((folder/'quality-review.json').read_text())
    assert qa['contact_sheet_sha256']==prep['contact_sheet_sha256']==CORE.sha((folder/'contact-sheet.jpg').read_bytes())
    images=[]
    for name,checksum in prep['prepared_hashes'].items():
        raw=(folder/'prepared'/name).read_bytes();assert CORE.sha(raw)==checksum;im=json.loads(raw)
        if im['key'] in qa['accepted']:images.append(im)
    targets={}
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');rows=[]
            for im in images:
                found=db.execute("SELECT DISTINCT to_jsonb(w) work FROM artworks w JOIN external_identifiers e ON e.entity_id=w.id AND e.entity_type='artwork' WHERE e.scheme IN ('met-object','european-met-the-met-object') AND e.external_id=%s AND w.status<>'archived'",(im['key'],)).fetchall();assert len(found)==1
                w=found[0]['work'];assert w['slug']==im['artwork_slug'] and w['status']=='review' and w['primary_media_id'] is None and w['published_at'] is None
                assert w['creation_year_end'] is not None and w['creation_year_end']<=1970
                assert db.execute("SELECT 1 FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id JOIN artist_countries c ON c.artist_id=a.id AND c.country_code='NL' AND c.relationship_type='cultural_affiliation' WHERE aa.artwork_id=%s AND a.slug=%s",(w['id'],im['artist_slug'])).fetchone()
                rows.append(dict(key=im['key'],work=w))
        targets[target]=rows;CORE.save_new(m.BACKUPS/f'dutch-met-images-round-{n:02d}-{target}-preimages.json',rows)
    def signature(rows):return [{k:v for k,v in row['work'].items() if k in ('slug','title','creation_year_start','creation_year_end','date_precision','status','published_at','primary_media_id')} for row in rows]
    assert signature(targets['local'])==signature(targets['production'])
    CORE.save_new(dest,dict(at=CORE.now(),round=n,images=images,targets=targets,qa=qa));CORE.save_new(folder/'application-manifest.json',dict(at=CORE.now(),images=len(images),plan_sha256=CORE.sha(dest.read_bytes())))

def apply(n):
    folder=RUN/f'round-{n:02d}';raw=(folder/'application-plan.json').read_bytes();pin=CORE.sha(raw);data=json.loads(raw)
    assert pin==json.loads((folder/'application-manifest.json').read_text())['plan_sha256']
    images={im['key']:im for im in data['images']};bucket=CORE.storage.Client(project='artline-508319',credentials=CORE.GcloudCredentials()).bucket(CORE.BUCKET)
    for im in images.values():
        raw=(m.x.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert CORE.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
        blob=bucket.blob(im['path'].lstrip('/'))
        if not blob.exists():
            blob.metadata=dict(sha256=im['sha256'],license='CC0',museum_object=im['key']);blob.cache_control='public,max-age=31536000,immutable';blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
    for target in ('local','production'):
        done=folder/f'{target}-verified.json'
        if done.exists():continue
        with m.m.r.base.connect(target=='production') as db:
            for row in data['targets'][target]:
                im=images[row['key']];old=row['work'];mid=im['media_id']
                with db.transaction():
                    db.execute('SELECT pg_advisory_xact_lock(559220260914)');w=db.execute('SELECT to_jsonb(w) work FROM artworks w WHERE id=%s FOR UPDATE',(old['id'],)).fetchone()['work']
                    if w['primary_media_id']==mid:
                        assert db.execute('SELECT 1 FROM media_assets WHERE id=%s AND checksum_sha256=%s',(mid,im['sha256'])).fetchone();continue
                    assert w==old,'Artwork changed after concrete image plan'
                    sid=m.m.source(db,SOURCE,'The Metropolitan Museum of Art — selected Dutch Open Access reproductions','museum_api','https://collectionapi.metmuseum.org/')
                    m.m.r.base.insert(db,'media_assets',dict(id=mid,storage_kind='local',storage_path=im['path'],source_page_url=im['page'],provider_name='The Metropolitan Museum of Art',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=im['title']+' — '+im['artist'],rights_status='cc0',license_label='CC0',license_url=im['license_url'],creator_credit=im['creator_credit'],attribution_text=im['attribution_text'],retrieved_at=im['download']['retrieved_at'],verified_at=im['checked_at'],verified_by=m.m.ACTOR))
                    m.m.r.base.insert(db,'media_rights_evidence',dict(media_id=mid,source_id=sid,source_record_id=im['key'],source_checksum=im['identity']['evidence']['receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=r.CC0,rights_basis=im['identity']['rights_basis']+' Full-frame visual review recorded separately; no metadata or publication changes.',adapter_version='dutch-met-images-v1',checked_at=im['checked_at'],evidence_json=Jsonb(im)))
                    m.m.r.base.insert(db,'artwork_media',dict(artwork_id=old['id'],media_id=mid,sort_order=0,view_label='Selected reproduction'))
                    db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(mid,m.m.ACTOR,old['id']))
            with db.transaction():
                db.execute('SET TRANSACTION READ ONLY')
                for row in data['targets'][target]:
                    im=images[row['key']];now=db.execute('SELECT to_jsonb(w) work FROM artworks w WHERE id=%s',(row['work']['id'],)).fetchone()['work'];ignore={'primary_media_id','revision','updated_at','updated_by'}
                    assert {k:v for k,v in now.items() if k not in ignore}=={k:v for k,v in row['work'].items() if k not in ignore}
                    assert now['primary_media_id']==im['media_id'] and now['status']=='review'
                    assert db.execute("SELECT 1 FROM media_assets ma JOIN media_rights_evidence re ON re.media_id=ma.id JOIN artwork_media am ON am.media_id=ma.id WHERE ma.id=%s AND ma.checksum_sha256=%s AND ma.rights_status='cc0' AND am.artwork_id=%s",(im['media_id'],im['sha256'],now['id'])).fetchone()
        CORE.save_new(done,dict(at=CORE.now(),plan_sha256=pin,images_verified=len(images)));print(target,'Dutch Met image round',n,'verified',len(images),flush=True)
    dest=folder/'public-verification.json'
    if not dest.exists():
        checked=[]
        for im in images.values():
            resp=requests.get(m.SITE+im['path'],timeout=90);resp.raise_for_status();assert resp.headers['Content-Type'].startswith('image/jpeg') and CORE.sha(resp.content)==im['sha256'];checked.append(dict(url=m.SITE+im['path'],sha256=im['sha256'],status=resp.status_code))
        CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,images=checked))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);p.add_argument('--round',required=True,type=int);a=p.parse_args();assert 1<=a.round<=20;globals()[a.command](a.round)
