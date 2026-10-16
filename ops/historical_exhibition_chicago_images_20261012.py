#!/usr/bin/env python3
"""Selected CC0 native-object images for the reviewed 1933 Chicago links."""
import importlib.util
import io
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image,ImageOps,ImageDraw,ImageFont
from psycopg.types.json import Jsonb
import requests
import exhibitions_common as c
import historical_exhibition_chicago_aic_20261012 as links

OUT=links.OUT/'images'
OP='historical-exhibition-chicago-images-20261012'
SID=c.uid('source/'+OP)
POLICY='https://www.artic.edu/open-access/open-access-images'
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
spec=importlib.util.spec_from_file_location('historical_cma_image_helpers',Path(__file__).with_name('historical_exhibition_cma_images_20261012.py'))
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
helper.OP=OP
helper.batchdir=lambda _:OUT


def select():
    p=c.load(links.OUT/'aic-delivery-plan.json');chosen=[];held=[]
    for row in p['records']:
        a=row['before'];o=row['object']
        if a['primary_media_id']:continue
        if not o.get('image_id')or o.get('is_public_domain')is not True or o.get('copyright_notice'):
            held.append(dict(nativeID=row['nativeID'],id=row['id'],reason='No explicit unconflicted public-domain primary image; continue separately with approved WikiArt matching',publicDomain=o.get('is_public_domain'),copyrightNotice=o.get('copyright_notice')));continue
        assert re.fullmatch(r'[a-f0-9-]{36}',o['image_id'])
        assert not o.get('fiscal_year_deaccession')and a['status']!='archived'
        assert a['creation_year_end']is not None and a['creation_year_end']<=1970 or(row['nativeID']=='87479'and o['date_display']=='1577–79')
        chosen.append(dict(**row,title=o['title'],creators=o.get('artist_title')or o.get('artist_display')or'Unknown artist',
            imageURL='https://www.artic.edu/iiif/2/'+o['image_id']+'/full/843,/0/default.jpg',
            rightsBasis='Exact official native object record explicitly marks this primary image public domain, with no conflicting copyright notice; AIC open-access image policy provides CC0.'))
    c.save(OUT/'selection.json',dict(at=c.now(),records=chosen,held=held,linkPlanSHA256=c.sha((links.OUT/'aic-delivery-plan.json').read_bytes()),sourcePins=links.evidence_pins(),realLocalDatabaseWrites=False))
    c.save(links.BACKUP/'aic-image-preimage.json.gz',dict(at=c.now(),records=chosen))
    print('Selected',len(chosen),'exact CC0 image gaps;',len(held),'additional gaps retained.',flush=True)


def prepare():
    selected=c.load(OUT/'selection.json');results=[]
    for row in selected['records']:
        nid=row['nativeID'];dest=OUT/'prepared'/f'{nid}.json'
        if dest.exists():results.append(c.load(dest));continue
        assert not (OUT/'access-hold.json').exists()and not (c.RUN/'access-holds'/(urlsplit(row['imageURL']).hostname+'.json')).exists()
        source=OUT/'originals'/f'{nid}.jpg';rcpath=source.with_suffix('.receipt.json')
        if source.exists():rc=c.load(rcpath);raw=source.read_bytes();assert c.sha(raw)==rc['sha256']
        else:
            time.sleep(.5)
            response=requests.get(row['imageURL'],headers={'User-Agent':c.UA},allow_redirects=False,timeout=(15,45))
            if response.status_code in (401,403,429):
                rc=dict(at=c.now(),url=row['imageURL'],status=response.status_code);c.save(OUT/'access-hold.json',rc);raise RuntimeError('Image access held')
            response.raise_for_status();assert response.status_code==200 and response.headers.get('Content-Type','').startswith('image/')
            raw=response.content;assert 0<len(raw)<12000000
            rc=dict(url=row['imageURL'],status=200,retrievedAt=c.now(),sha256=c.sha(raw),bytes=len(raw))
            source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(raw);c.save(rcpath,rc)
        with Image.open(io.BytesIO(raw))as opened:
            assert opened.width*opened.height<40000000
            opened.load();im=ImageOps.exif_transpose(opened).convert('RGB')
        original=im.size;encoded=None
        for edge in [1200,1050,900,800,700,600]:
            resized=im.copy();resized.thumbnail((edge,edge),Image.Resampling.LANCZOS)
            for quality in [90,85,80,75,70,65,60,55]:
                buf=io.BytesIO();resized.save(buf,'JPEG',quality=quality,optimize=True,progressive=True)
                if buf.tell()<=100000:encoded=buf.getvalue();break
            if encoded:break
        assert encoded and min(resized.size)>70
        assert abs(resized.width/resized.height-original[0]/original[1])<.02
        digest=c.sha(encoded);path=OUT/'derivatives'/f'{nid}.jpg';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(encoded)
        thumb=row['object'].get('thumbnail')or{};declared=[thumb.get('width'),thumb.get('height')];flags=[]
        if all(declared)and abs(declared[0]/declared[1]-original[0]/original[1])>.03:flags.append('metadata_aspect_ratio_difference')
        if 'recto' in row['title'].lower()or'verso'in row['title'].lower():flags.append('recto_verso_primary_view')
        item=dict(state='prepared',id=row['id'],nativeID=nid,title=row['title'],path=str(path),originalPath=str(source),sourceReceipt=rc,
            sourceSHA256=rc['sha256'],sha256=digest,width=resized.width,height=resized.height,bytes=len(encoded),quality=quality,originalDimensions=original,declaredThumbnailDimensions=declared,flags=flags,
            mediaID=c.uid(OP+'/media/'+row['id']+'/'+digest),imagePath='/assets/artworks/'+OP+'/'+row['id']+'-'+digest[:16]+'.jpg')
        c.save(dest,item);results.append(item);print(nid,'prepared',flags,flush=True)
    c.save(OUT/'prepared.json',dict(at=c.now(),rows=results,selectionSHA256=c.sha((OUT/'selection.json').read_bytes())))
    by={r['id']:r for r in selected['records']};font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    for start in range(0,len(results),12):
        sheet=Image.new('RGB',(1600,1140),'#eee9e1');draw=ImageDraw.Draw(sheet)
        for n,r in enumerate(results[start:start+12]):
            row=by[r['id']];x=n%4*400;y=n//4*380;im=Image.open(r['path']);im.thumbnail((390,290))
            sheet.paste(im,(x+(400-im.width)//2,y+(290-im.height)//2))
            labels=[f"{start+n+1}. {r['nativeID']} | cat. {row['catalogueNumber'] or '?'}",row['title'][:49],row['creators'][:49],'; '.join(r['flags'])or'Native primary image; full frame']
            for j,label in enumerate(labels):draw.text((x+5,y+296+j*19),label,font=font,fill='#151515')
        sheet.save(OUT/f'review-sheet-{start//12+1:02d}.jpg',quality=92)
    print('All',len(results),'images ready for visual review.',flush=True)


def upload():
    helper.upload(1)


def apply():
    dest,by,chosen,decisions=helper.accepted(1);p=c.load(OUT/'selection.json');uploaded=c.load(OUT/'uploaded.json');reviewsha=c.sha((OUT/'visual-review.json').read_bytes())
    assert uploaded['visualReviewSHA256']==reviewsha and len(uploaded['receipts'])==len(chosen)
    assert links.evidence_pins()==p['sourcePins']
    ids=[r['id']for r in chosen]
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(links.ACTOR,))
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        current=links.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(ids,)).fetchall())
        assert len(current)==len(ids)and all(r==by[r['id']]['before']for r in current)
        assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([r['sha256']for r in chosen],)).fetchall(),'Identical existing image requires reconciliation'
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,terms_url)VALUES(%s,%s,'Art Institute of Chicago — historical exhibition images','museum_api','https://api.artic.edu/api/v1/artworks',%s)",(SID,OP,POLICY))
        for im in chosen:
            r=by[im['id']];o=r['object'];assert o['is_public_domain']is True and not o.get('copyright_notice')
            assert db.execute('SELECT 1 FROM exhibition_entries WHERE id=%s AND artwork_id=%s AND exhibition_id=%s',(r['entryID'],im['id'],links.EID)).fetchone()
            credit=r['creators']+'. '+r['title']+'. Art Institute of Chicago. '+(o.get('credit_line')or'')
            db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)VALUES(%s,'local',%s,%s,'Art Institute of Chicago','image/jpeg',%s,%s,%s,%s,%s,'cc0','CC0 1.0',%s,%s,%s,%s,now(),%s)",
                (im['mediaID'],im['imagePath'],'https://www.artic.edu/artworks/'+r['nativeID'],im['width'],im['height'],im['bytes'],im['sha256'],r['title']+' — '+r['creators'],POLICY,r['creators'],credit+' Full primary source frame preserved.',im['sourceReceipt']['retrievedAt'],links.ACTOR))
            db.execute('INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)',
                (im['mediaID'],SID,r['nativeID'],r['recordSHA256'],r['imageURL'],POLICY,r['rightsBasis'],OP,Jsonb(dict(nativeObject=o,sourcePins=p['sourcePins'],download=im['sourceReceipt'],visualReview=decisions[r['nativeID']],visualReviewSHA256=reviewsha,sourceDatePreserved=o['date_display'],catalogueMetadataUnchanged=True))))
            db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label)VALUES(%s,%s,0,%s)',(im['id'],im['mediaID'],decisions[r['nativeID']].get('viewLabel','Full artwork reproduction')))
            db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(im['mediaID'],im['id']))
    c.save(OUT/'delivered.json',dict(at=c.now(),newImages=len(chosen),newArtworks=0,newEvents=0,visualReviewSHA256=reviewsha,realLocalDatabaseWrites=False))
    print('Attached',len(chosen),'reviewed CC0 images.',flush=True)


def verify():
    _,by,chosen,_=helper.accepted(1);ids=[r['id']for r in chosen];expected={r['id']:r for r in chosen}
    with c.connect()as db:
        rows=links.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall())
        for r in rows:
            assert r['primary_media_id']==expected[r['id']]['mediaID']
            assert all(r[k]==v for k,v in by[r['id']]['before'].items()if k not in ['primary_media_id','updated_at','revision'])
        media=db.execute('SELECT m.*,am.artwork_id FROM media_assets m JOIN artwork_media am ON am.media_id=m.id JOIN media_rights_evidence re ON re.media_id=m.id WHERE m.id=ANY(%s::uuid[])',([r['mediaID']for r in chosen],)).fetchall()
        assert len(media)==len(chosen)
        for m in media:
            r=expected[str(m['artwork_id'])];assert m['checksum_sha256']==r['sha256']and m['byte_size']==r['bytes']<=100000 and m['license_label']=='CC0 1.0'
    c.save(OUT/'verified.json',dict(at=c.now(),images=len(chosen),allPrimaryJunctionAndRightsRelationsVerified=True,allCatalogueMetadataPreserved=True,realLocalDatabaseWrites=False))
    print('Verified',len(chosen),'image records and preserved catalogue fields.',flush=True)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1]not in ['select','prepare','upload','apply','verify']:raise SystemExit('Use select, prepare, upload, apply or verify')
    globals()[sys.argv[1]]()
