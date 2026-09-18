#!/usr/bin/env python3
"""Twenty distinct Dutch-painter reviews of existing Met image gaps.

At most four metadata objects inspected and three rights-cleared images
selected per painter. This never downloads the full museum image collection.
"""
import argparse,collections,importlib.util,json,re,time,uuid
from pathlib import Path
from urllib.parse import urlparse
import requests
from PIL import Image,ImageOps,ImageDraw
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;RUN=m.x.BASE/'dutch-met-images';ORIGINALS=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/overnight-countries-20260913/dutch-met')
POLICY='https://www.metmuseum.org/policies/image-resources';CC0='https://creativecommons.org/publicdomain/zero/1.0/'

def roster():
    path=RUN/'roster.json'
    if path.exists():return json.loads(path.read_text())
    with m.m.r.base.connect(False) as db,db.transaction():
        db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
        artists=db.execute("""SELECT a.slug,a.display_name,a.birth_year,a.death_year,count(DISTINCT w.id) n
        FROM artists a JOIN artist_countries c ON c.artist_id=a.id AND c.country_code='NL' AND c.relationship_type='cultural_affiliation'
        JOIN artwork_artists aa ON aa.artist_id=a.id JOIN artworks w ON w.id=aa.artwork_id
        JOIN institutions i ON i.id=w.current_institution_id
        WHERE a.status='review' AND a.entity_type='person' AND a.death_year<=1920
        AND w.status='review' AND w.primary_media_id IS NULL AND w.creation_year_end<=1970
        AND w.work_type IN ('painting','drawing','watercolor') AND i.slug='the-met'
        AND EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=w.id AND e.scheme IN ('met-object','european-met-the-met-object'))
        GROUP BY a.slug,a.display_name,a.birth_year,a.death_year ORDER BY n DESC,a.slug LIMIT 20""").fetchall()
        scopes=[]
        for n,a in enumerate(artists,1):
            person=db.execute("SELECT a.id::text,a.slug,a.display_name,coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases FROM artists a WHERE slug=%s",(a['slug'],)).fetchone()
            works=db.execute("""SELECT to_jsonb(w) work,e.external_id object_id,e.scheme,i.slug institution_slug
            FROM artists a JOIN artwork_artists aa ON aa.artist_id=a.id JOIN artworks w ON w.id=aa.artwork_id JOIN institutions i ON i.id=w.current_institution_id
            JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=w.id AND e.scheme IN ('met-object','european-met-the-met-object')
            WHERE a.slug=%s AND w.status='review' AND w.primary_media_id IS NULL AND w.creation_year_end<=1970
            AND w.work_type IN ('painting','drawing','watercolor') AND i.slug='the-met'
            ORDER BY CASE WHEN w.work_type='painting' THEN 0 ELSE 1 END,w.slug LIMIT 4""",(a['slug'],)).fetchall()
            scopes.append(dict(round=n,artist=person,works=works,question='Verify primary Met object identity, source maker, creation dates and per-object CC0 image availability for a selected Dutch painter; retain existing metadata and review status.'))
    assert len(scopes)==20,'Need twenty genuinely distinct eligible painter scopes'
    result=dict(at=CORE.now(),rounds=scopes,policy='Four metadata checks and at most three selected licensed reproductions per painter. Existing museum object authority and country affiliation required; no new artworks or date changes.');CORE.save_new(path,result);return result

def capture(object_id):
    path=RUN/'primary-captures'/(object_id+'.json')
    if path.exists():return json.loads(path.read_text())
    url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+object_id
    time.sleep(1.5);r=requests.get(url,timeout=(15,50),headers={'User-Agent':'Artline/1.0 (https://github.com/vadimdulub/artline; selected museum research)'})
    r.raise_for_status();data=r.json();assert data.get('objectID')==int(object_id)
    result=dict(data=data,receipt=dict(url=url,retrieved_at=CORE.now(),bytes=len(r.content),sha256=CORE.sha(r.content)))
    CORE.save_new(path,result);return result

def research(n):
    scope=roster()['rounds'][n-1];folder=RUN/f'round-{n:02d}';dest=folder/'research.json'
    if dest.exists():return
    selected=[];held=[];a=scope['artist'];names={m.f.names.namekey(x) for x in [a['display_name'],*a['aliases']]}
    for w in scope['works']:
        ev=capture(w['object_id']);d=ev['data'];old=w['work'];reason=None
        if d.get('isPublicDomain') is not True:reason='Primary object does not authorize Open Access reproduction'
        elif not d.get('primaryImage'):reason='No primary image supplied'
        elif m.f.names.namekey(d.get('artistDisplayName','')) not in names:reason='Primary source maker differs or attribution requires review'
        elif m.m.r.norm(d.get('title','')) not in {m.m.r.norm(old['title']),m.m.r.norm(old['alternate_title'] or '')}:reason='Primary object title requires identity review'
        elif not d.get('objectDate') or not d.get('objectEndDate') or d['objectEndDate']>1970:reason='Primary creation date missing or outside scope'
        elif d.get('objectBeginDate') is not None and old['creation_year_end'] is not None and (d['objectBeginDate']>old['creation_year_end'] or d['objectEndDate']<old['creation_year_start']):reason='Primary and catalogue artwork date ranges disagree'
        elif urlparse(d['primaryImage']).hostname not in ('images.metmuseum.org','collectionapi.metmuseum.org'):reason='Image host requires review'
        elif len(selected)>=3:reason='Three selected reproductions per painter cap'
        if reason:held.append(dict(slug=old['slug'],object_id=w['object_id'],reason=reason));continue
        selected.append(dict(target=w,artist=a,evidence=ev,rights_basis='The exact Met Open Access object API states isPublicDomain=true and supplies this primaryImage. The museum Open Access programme dedicates eligible images to CC0. Existing source object ID, normalized title and named maker corroborated independently.'))
    result=dict(at=CORE.now(),round=n,artist=a['display_name'],metadata_inspected=len(scope['works']),selected=selected,held=held,complete=True)
    CORE.save_new(dest,result);print('Dutch Met image round',n,a['display_name'],'selected',len(selected),'held',len(held),flush=True)

def prepare(n):
    folder=RUN/f'round-{n:02d}';dest=folder/'preparation.json'
    if dest.exists():return
    selections=json.loads((folder/'research.json').read_text())['selected'];images=[];holds=[]
    CORE.HOSTS.update({'images.metmuseum.org','collectionapi.metmuseum.org'});fetcher=CORE.Fetcher(folder/'downloads')
    for s in selections:
        w=s['target'];d=s['evidence']['data'];oid=w['object_id'];p=folder/'prepared'/(oid+'.json')
        if p.exists():images.append(json.loads(p.read_text()));continue
        original=ORIGINALS/(oid+'.original');receipt=folder/'download-receipts'/(oid+'.json')
        try:
            if original.exists():raw=original.read_bytes();download=json.loads(receipt.read_text());assert CORE.sha(raw)==download['sha256']
            else:
                raw,headers=fetcher.get(d['primaryImage'],20_000_000);download=dict(url=d['primaryImage'],retrieved_at=CORE.now(),sha256=CORE.sha(raw),bytes=len(raw),headers=headers);CORE.save_new(original,raw);CORE.save_new(receipt,download)
            encoded,width,height,quality=CORE.compress(raw);checksum=CORE.sha(encoded);path='/assets/artworks/imported/dutch-met/'+oid+'-'+checksum[:16]+'.jpg';CORE.save_new(m.x.ROOT/'apps/web/public'/path.lstrip('/'),encoded)
        except Exception as e:
            holds.append(dict(object_id=oid,reason=type(e).__name__+': '+str(e)[:250]));continue
        im=dict(key=oid,artwork_slug=w['work']['slug'],artist_slug=s['artist']['slug'],artist=s['artist']['display_name'],title=w['work']['title'],path=path,sha256=checksum,bytes=len(encoded),width=width,height=height,quality=quality,media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/dutch-met-image/'+oid+'/'+checksum)),page='https://www.metmuseum.org/art/collection/search/'+oid,source_image_url=d['primaryImage'],rights_status='cc0',license_label='CC0',license_url=CC0,creator_credit=d['artistDisplayName'],attribution_text=d['artistDisplayName']+'. '+d['title']+'. '+d.get('creditLine','')+'. The Metropolitan Museum of Art, Open Access, CC0. Full-frame resize and JPEG compression.',checked_at=CORE.now(),download=download,identity=s)
        CORE.save_new(p,im);images.append(im)
    canvas=Image.new('RGB',(1000,260),'#f0eee9');draw=ImageDraw.Draw(canvas)
    for i,im in enumerate(images):
        with Image.open(m.x.ROOT/'apps/web/public'/im['path'].lstrip('/')) as src:tile=ImageOps.contain(src.convert('RGB'),(315,205));canvas.paste(tile,(i*330+(330-tile.width)//2,0))
        draw.text((i*330+5,212),im['key']+' '+im['title'][:42],fill='#111111');draw.text((i*330+5,234),im['artist'][:40],fill='#111111')
    sheet=folder/'contact-sheet.jpg';canvas.save(sheet,quality=87)
    CORE.save_new(dest,dict(at=CORE.now(),round=n,images=len(images),held=holds,contact_sheet_sha256=CORE.sha(sheet.read_bytes()),prepared_hashes={p.name:CORE.sha(p.read_bytes()) for p in (folder/'prepared').glob('*.json')}));print('Dutch Met prepared round',n,len(images),flush=True)

if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('command',choices=['roster','research','prepare']);cli.add_argument('--round',type=int);a=cli.parse_args()
    if a.command=='roster':roster()
    else:
        for n in ([a.round] if a.round else range(1,21)):globals()[a.command](n)
