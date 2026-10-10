#!/usr/bin/env python3
"""Deliver the explicitly approved, pinned 116-image Otto Dix selection.

Production only. Preserve source rights, existing media, catalogue metadata,
unknown dates and review/publication state. All files retain the source frame.
"""
import argparse
import base64
import collections
import concurrent.futures
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import textwrap
import time
from urllib.parse import urlsplit

from PIL import Image, ImageDraw, ImageFont
from psycopg.types.json import Jsonb
import requests

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
m=module('otto_import','ops/import-otto-dix-20261006.py')
d=module('wiki_delivery','ops/deliver-production-wikiart-images-20261006.py')
r=m.r;RUN=m.RUN;BACKUP=m.BACKUP;OP=m.OP;ACTOR=m.ACTOR
r.PORT=55451
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
d.RUN=RUN;d.ORIGINALS=ORIGINALS
POLICY='https://www.wikiart.org/en/terms-of-use'


def selection():
    data,pin=m.pinned();auth=r.load(RUN/'image-authorization.json')
    assert auth['user_instruction']=='upload them' and auth['metadata_plan_sha256']==pin
    rows=[x for x in data['rows'] if x['action']!='hold' and not x.get('has_image')]
    assert len(rows)==116 and auth['artwork_ids']==[x['artwork_id'] for x in rows]
    assert all(x['rights_status']=='restricted' and x['confidence']>=.9 for x in rows)
    return rows,auth


def snapshots(db,ids):
    return {x['artwork']['id']:x for x in db.execute('''SELECT to_jsonb(a) artwork,
      COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY artist_id,attribution_role) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creators,
      COALESCE((SELECT jsonb_agg(to_jsonb(am) ORDER BY media_id) FROM artwork_media am WHERE am.artwork_id=a.id),'[]') attachments,
      COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') locations
      FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()}


def prepare():
    rows,auth=selection()
    def one(row):
        aid=row['artwork_id'];dest=RUN/'prepared-images'/(aid+'.json')
        if dest.exists():return r.load(dest)
        p=row['page'];url=p['metadata']['image']
        assert m.q.image_key(url)==m.q.image_key(p['image_url'])
        result={'artwork_id':aid,'index':row['index'],'title':row['title'],'source_id':row['source_id'],
                'source_page_url':row['source_url'],'source_image_url':url,'rights_status':'restricted',
                'source_rights_label':row['source_rights_label'],'page_receipt':p['receipt']}
        for attempt in range(3):
            try:
                original,rc=d.download(url)
                raw,width,height,quality=d.core.compress(original)
                assert 0<len(raw)<=100000 and min(width,height)>=50 and max(width,height)>=200
                digest=r.sha(raw);path='/assets/artworks/imported/'+OP+'/'+aid+'-'+digest[:16]+'.jpg'
                target=ROOT/'apps/web/public'/path.lstrip('/')
                r.save(target,raw)
                with Image.open(io.BytesIO(raw)) as image:image.verify()
                with Image.open(io.BytesIO(original)) as source:original_size=list(source.size)
                assert abs(width/height-original_size[0]/original_size[1])<.02
                result.update(outcome='prepared',path=path,visual_path=str(target),sha256=digest,
                              media_id=m.uid('image-media/'+aid+'/'+digest),bytes=len(raw),width=width,height=height,
                              original_dimensions=original_size,jpeg_quality=quality,download=rc)
                break
            except (requests.RequestException,ValueError,AssertionError) as exc:
                if attempt==2:raise RuntimeError('Image preparation failed for '+aid+': '+str(exc)[:250]) from exc
                time.sleep(1+attempt)
        r.save(dest,result);return result
    prepared=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for im in pool.map(one,rows):
            prepared.append(im)
            if len(prepared)%15==0:print('Prepared',len(prepared),'/',len(rows),flush=True)
    groups=collections.defaultdict(list)
    for x in prepared:groups[x['sha256']].append(x['artwork_id'])
    duplicates=[ids for ids in groups.values() if len(ids)>1]
    r.save(RUN/'image-preparation.json',{'at':r.now(),'images':prepared,'duplicate_file_groups':duplicates,
                                       'authorization_sha256':r.sha((RUN/'image-authorization.json').read_bytes())})
    print('Prepared all',len(prepared),'images; duplicate files:',duplicates,flush=True)


def sheets():
    data=r.load(RUN/'image-preparation.json');items=data['images']
    folder=ORIGINALS/'contact-sheets';folder.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
    sheets=[]
    for start in range(0,len(items),12):
        sheet=Image.new('RGB',(1200,1080),'white');draw=ImageDraw.Draw(sheet)
        for offset,im in enumerate(items[start:start+12]):
            left=(offset%4)*300;top=(offset//4)*360
            with Image.open(im['visual_path']) as source:
                image=source.convert('RGB');image.thumbnail((282,275))
                sheet.paste(image,(left+(300-image.width)//2,top+(280-image.height)//2))
            label=str(start+offset+1)+'. '+im['title']+' [source '+str(im['index'])+']'
            for n,line in enumerate(textwrap.wrap(label,42)[:4]):draw.text((left+8,top+285+n*17),line,font=font,fill='black')
        path=folder/f'{start//12+1:03d}.jpg';sheet.save(path,quality=92)
        sheets.append({'path':str(path),'sha256':r.sha(path.read_bytes()),'first':start+1,'last':min(start+12,len(items))})
    r.save(RUN/'image-contact-sheet-index.json',{'images':[{'number':n+1,'artwork_id':im['artwork_id'],'sha256':im['sha256'],'title':im['title']} for n,im in enumerate(items)],'sheets':sheets})
    print(json.dumps({'images':len(items),'sheets':len(sheets),'folder':str(folder)}),flush=True)


def plan():
    rows,auth=selection();prepared=r.load(RUN/'image-preparation.json');visual=r.load(RUN/'image-visual-review.json')
    index=r.load(RUN/'image-contact-sheet-index.json')
    assert visual['contact_index_sha256']==r.sha((RUN/'image-contact-sheet-index.json').read_bytes())
    assert visual['reviewed_sheet_sha256']==[s['sha256'] for s in index['sheets']]
    assert not prepared['duplicate_file_groups']
    approved={x['artwork_id']:x['sha256'] for x in visual['approved']}
    images=[im for im in prepared['images'] if approved.get(im['artwork_id'])==im['sha256']]
    assert len(images)==len(approved) and len(images)+len(visual['held'])==116
    prior=r.load(BACKUP/'metadata-after.json')
    with r.connect('production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        before=snapshots(db,list(prior))
        assert len(before)==len(prior)==182
        for aid,x in before.items():
            assert {'artwork':x['artwork'],'creators':x['creators']}==prior[aid], 'Catalogue changed since metadata import'
        for im in images:
            a=before[im['artwork_id']]
            assert a['artwork']['primary_media_id'] is None
            assert len(a['creators'])==1 and a['creators'][0]['artist_id']==m.ARTIST and a['creators'][0]['attribution_role']=='primary'
            raw=Path(im['visual_path']).read_bytes();assert r.sha(raw)==im['sha256'] and len(raw)==im['bytes']
            assert not db.execute('SELECT id FROM media_assets WHERE id=%s OR storage_path=%s',(im['media_id'],im['path'])).fetchone()
        existing_media=db.execute('SELECT to_jsonb(ma) media FROM media_assets ma WHERE id=ANY(%s::uuid[])',([x['artwork']['primary_media_id'] for x in before.values() if x['artwork']['primary_media_id']],)).fetchall()
    data={'images':images,'rows':{x['artwork_id']:x for x in rows},'preimages':before,'existing_media':existing_media,
          'source_id':m.uid('source/images'),'visual_review_sha256':r.sha((RUN/'image-visual-review.json').read_bytes()),
          'authorization_sha256':r.sha((RUN/'image-authorization.json').read_bytes())}
    r.save(RUN/'image-delivery-plan.json',data);pin=r.sha((RUN/'image-delivery-plan.json').read_bytes())
    r.save(RUN/'image-delivery-plan-pin.json',{'sha256':pin})
    r.save(BACKUP/'image-preimages.json',{'plan_sha256':pin,'records':before,'existing_media':existing_media})
    r.save(BACKUP/'image-delivery-plan.json',data)
    print('Pinned',len(images),'production image attachments; all 182 existing records backed up',flush=True)


def pinned():
    raw=(RUN/'image-delivery-plan.json').read_bytes();pin=r.load(RUN/'image-delivery-plan-pin.json')['sha256']
    assert r.sha(raw)==pin and r.load(BACKUP/'image-preimages.json')['plan_sha256']==pin
    data=json.loads(raw)
    assert r.sha((RUN/'image-authorization.json').read_bytes())==data['authorization_sha256']
    assert r.sha((RUN/'image-visual-review.json').read_bytes())==data['visual_review_sha256']
    return data,pin


def upload():
    data,pin=pinned()
    bucket=d.storage.Client(project='artline-508319',credentials=d.core.GcloudCredentials()).bucket(d.core.BUCKET)
    def one(im):
        dest=RUN/'image-uploads'/(im['artwork_id']+'.json')
        if dest.exists():return r.load(dest)
        raw=Path(im['visual_path']).read_bytes();assert r.sha(raw)==im['sha256'] and len(raw)==im['bytes']
        blob=bucket.blob(im['path'].lstrip('/'))
        blob.metadata={'sha256':im['sha256'],'artwork-id':im['artwork_id'],'provider':'WikiArt','operation':OP,'rights-status':'restricted'}
        blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except d.PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=requests.get('https://artlines.org'+im['path'],timeout=(15,45));response.raise_for_status()
        assert r.sha(response.content)==im['sha256']
        rc={'artwork_id':im['artwork_id'],'at':r.now(),'plan_sha256':pin,'generation':blob.generation,
            'path':im['path'],'sha256':im['sha256'],'bytes':len(raw),'public_http_status':response.status_code,'public_bytes_verified':True}
        r.save(dest,rc);return rc
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for n,_ in enumerate(pool.map(one,data['images']),1):
            if n%20==0:print('Uploaded and publicly verified',n,'/',len(data['images']),flush=True)
    print('All public files verified',len(data['images']),flush=True)


def apply():
    data,pin=pinned()
    visual=r.load(RUN/'image-visual-review.json')
    number_to_id={x['number']:x['artwork_id'] for x in visual['approved']}
    assert not (RUN/'images-applied.json').exists(), 'Already applied; use verify'
    assert r.load(BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
    for im in data['images']:
        rc=r.load(RUN/'image-uploads'/(im['artwork_id']+'.json'))
        assert rc['plan_sha256']==pin and rc['sha256']==im['sha256'] and rc['public_bytes_verified']
    with r.connect('production',readonly=False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('SELECT pg_advisory_xact_lock(2026100607)')
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(list(data['preimages']),)).fetchall()
        assert snapshots(db,list(data['preimages']))==data['preimages'],'Catalogue changed after image preflight'
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://www.wikiart.org/')",(data['source_id'],OP+'-images','WikiArt Otto Dix authorized image attachments, 6 October 2026'))
        for n,im in enumerate(data['images'],1):
            aid=im['artwork_id'];row=data['rows'][aid];p=row['page']
            observations=[x for x in visual['observations'] if x.get('artwork_id',number_to_id.get(x.get('number')))==aid]
            attribution='Otto Dix. '+im['title']+'. WikiArt source label: '+im['source_rights_label']+'. Proportional resize and JPEG compression; no crop. Source: '+im['source_page_url']
            db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,
              checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at)
              VALUES(%s,'local',%s,%s,'WikiArt','image/jpeg',%s,%s,%s,%s,%s,'restricted',%s,%s,%s,%s,%s)''',
              (im['media_id'],im['path'],im['source_page_url'],im['width'],im['height'],im['bytes'],im['sha256'],im['title']+' — Otto Dix',
               im['source_rights_label']+' (WikiArt source label)',POLICY,'Otto Dix; reproduction via WikiArt',attribution,im['download']['at']))
            db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,
              rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
              (im['media_id'],data['source_id'],im['source_id'],im['page_receipt']['sha256'],im['source_image_url'],POLICY,
               'Exact WikiArt territorial public-domain or copyright/Fair Use label retained. User explicitly authorized this selected collection upload; no independent licence or unrestricted clearance is asserted.',
               OP+'-authorized-v1',p['receipt']['retrieved_at'],Jsonb({'image':im,'page':p,'source_rights_label':im['source_rights_label'],
               'authorization':r.load(RUN/'image-authorization.json'),'plan_sha256':pin,'identity_basis':row['identity_basis'],
               'confidence':row['confidence'],'visual_observations':observations})))
            db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s)',(aid,im['media_id'],'Complete source reproduction'))
            changed=db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],ACTOR,aid))
            assert changed.rowcount==1
            db.execute('''INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
              VALUES(%s,'artwork',%s,%s,'otto_dix_image_delivery',%s,%s,%s,%s,%s)''',
              (m.uid('image-citation/'+aid),aid,data['source_id'],im['source_id'],im['source_page_url'],json.dumps({'plan_sha256':pin,
              'rights_label':im['source_rights_label'],'source_image_url':im['source_image_url'],'identity_basis':row['identity_basis'],'visual_observations':observations,
              'user_authorization':'upload them','scope':'Image attachment only; catalogue metadata, unknown dates, museum claims and publication status preserved.'},ensure_ascii=False),r.now(),ACTOR))
            if n%25==0:print('Transaction attachments',n,'/',len(data['images']),flush=True)
        after=snapshots(db,list(data['preimages']));images={im['artwork_id']:im for im in data['images']}
        for aid,before in data['preimages'].items():
            a=after[aid]
            if aid not in images:assert a==before;continue
            allowed={'primary_media_id','revision','updated_at','updated_by'}
            assert {k:v for k,v in a['artwork'].items() if k not in allowed}=={k:v for k,v in before['artwork'].items() if k not in allowed}
            assert a['creators']==before['creators'] and a['locations']==before['locations']
            assert a['artwork']['primary_media_id']==images[aid]['media_id'] and a['artwork']['revision']==before['artwork']['revision']+1
            assert len(a['attachments'])==len(before['attachments'])+1
            assert all(x in a['attachments'] for x in before['attachments'])
    r.save(BACKUP/'image-after.json',after)
    r.save(RUN/'images-applied.json',{'at':r.now(),'plan_sha256':pin,'attached':len(data['images']),
                                   'artwork_ids':list(images),'local_database_changed':False,'metadata_and_publication_preserved':True})
    print('Committed production images',len(data['images']),flush=True)


def verify():
    data,pin=pinned();applied=r.load(RUN/'images-applied.json');expected=r.load(BACKUP/'image-after.json')
    assert applied['plan_sha256']==pin
    with r.connect('production') as db:
        assert snapshots(db,list(expected))==expected
        rows=db.execute('''SELECT to_jsonb(ma) media,to_jsonb(e) rights FROM media_assets ma JOIN media_rights_evidence e ON e.media_id=ma.id WHERE ma.id=ANY(%s::uuid[])''',([im['media_id'] for im in data['images']],)).fetchall()
        actual={x['media']['id']:x for x in rows}
        assert len(actual)==len(data['images'])
        for im in data['images']:
            x=actual[im['media_id']];ma=x['media'];rights=x['rights']
            assert ma['storage_path']==im['path'] and ma['checksum_sha256']==im['sha256'] and ma['byte_size']==im['bytes']<=100000
            assert ma['rights_status']=='restricted' and ma['verified_at'] is None
            assert ma['source_page_url']==im['source_page_url'] and im['source_rights_label'] in ma['license_label']
            assert rights['source_image_url']==im['source_image_url'] and rights['source_record_id']==im['source_id']
            assert rights['evidence_json']['plan_sha256']==pin
        old=db.execute('SELECT to_jsonb(ma) media FROM media_assets ma WHERE id=ANY(%s::uuid[])',([x['media']['id'] for x in data['existing_media']],)).fetchall()
        assert sorted(old,key=lambda x:x['media']['id'])==sorted(data['existing_media'],key=lambda x:x['media']['id'])
        count=db.execute('SELECT count(*) n FROM citations WHERE source_id=%s',(data['source_id'],)).fetchone()['n'];assert count==len(data['images'])
    # Bounded pages verify every new media URL through the actual production API.
    url='https://artlines.org/api/backend/v1/artists/otto-dix-q153104/works';params={'limit':50,'image_only':'true'}
    found={};pages=[]
    while True:
        response=requests.get(url,params=params,timeout=(15,45));response.raise_for_status();body=response.json()
        pages.append({'url':response.url,'status':response.status_code,'body':body})
        for x in body['items']:found[x['id']]=x
        cursor=body.get('next_cursor')
        if not cursor:break
        assert len(pages)<10
        params['cursor']=cursor
    for im in data['images']:
        a=found[im['artwork_id']]
        assert a['media_url']==im['path'] and a['rights_status']=='restricted'
        assert a['source_page_url']==im['source_page_url'] and im['source_rights_label'] in a['license_label']
        assert a['status']==data['preimages'][im['artwork_id']]['artwork']['status']
    r.save(RUN/'image-live-api-pages.json',pages)
    result={'at':r.now(),'plan_sha256':pin,'database_images_verified':len(data['images']),'live_api_images_verified':len(data['images']),
            'live_api_total_images':len(found),'api_pages':len(pages),'existing_images_preserved':len(old),'image_citations_verified':count,
            'public_files_checksum_verified':len(data['images']),'max_derivative_bytes':max(im['bytes'] for im in data['images']),
            'rights_counts':dict(collections.Counter(im['source_rights_label'] for im in data['images'])),'errors':[]}
    r.save(RUN/'image-verification.json',result)
    print(json.dumps(result),flush=True)


def report():
    data,pin=pinned();verified=r.load(RUN/'image-verification.json')
    assert not verified['errors'] and verified['plan_sha256']==pin
    images={x['artwork_id']:x for x in data['images']}
    # Preserve the preceding report and list before updating the current view.
    for name in ['summary.json','report.html','production-otto-dix-artworks.csv']:
        r.save(BACKUP/('before-images-'+name),(RUN/name).read_bytes())
    with (RUN/'production-otto-dix-artworks.csv').open(newline='') as file:
        reader=csv.DictReader(file);fields=reader.fieldnames;rows=list(reader)
    for row in rows:
        im=images.get(row['artwork_id'])
        if im:
            row.update(has_image='True',image_url='https://artlines.org'+im['path'],source_url=im['source_page_url'],
                       source_rights_label=im['source_rights_label'],operation=row['operation']+'; image_added')
    assert len(rows)==182 and sum(x['has_image']=='True' for x in rows)==120
    with (RUN/'production-otto-dix-artworks.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    image_fields=['artwork_id','title','source_page_url','source_image_url','source_rights_label','rights_status','production_image_url','bytes','sha256']
    with (RUN/'uploaded-images.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=image_fields,extrasaction='ignore');writer.writeheader()
        writer.writerows({**im,'production_image_url':'https://artlines.org'+im['path']} for im in data['images'])
    summary=r.load(RUN/'summary.json')
    summary.update(new_image_uploads=116,production_total_images=120,image_policy_choice_pending=False,
                   image_upload_authorization='upload them',image_delivery_verification=verified,
                   image_visual_observations=r.load(RUN/'image-visual-review.json')['observations'])
    (RUN/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    esc=lambda value:m.html.escape(str(value or ''))
    def table(headers,contents):
        return '<table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+cell+'</td>' for cell in row)+'</tr>' for row in contents)+'</tbody></table>'
    plan,_=m.pinned();holds=[x for x in plan['rows'] if x['action']=='hold']
    held_table=table(['Source entry','Reason'],[['<a href="'+esc(x['source_url'])+'">'+esc(x['title'])+'</a>',esc(x['reason'])] for x in holds])
    records=table(['Title','Date','Image','Source rights label'],[[esc(x['title']),esc(x['date_display']),
       '<a href="'+esc(x['image_url'])+'">View image</a>' if x['image_url'] else 'No image',esc(x['source_rights_label'])] for x in rows])
    image_table=table(['Artwork','Production image','Source','Rights label'],[[esc(im['title']),
       '<a href="https://artlines.org'+esc(im['path'])+'">View image</a>',
       '<a href="'+esc(im['source_page_url'])+'">WikiArt</a>',esc(im['source_rights_label'])] for im in data['images']])
    body='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Otto Dix — verified production delivery</title><style>body{font:16px/1.5 system-ui;max-width:1200px;margin:40px auto;padding:0 24px;color:#20252a;background:#faf9f6}h1{font-size:32px}h2{margin-top:36px}a{color:#075f79}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;border-bottom:1px solid #ddd;padding:9px;vertical-align:top}th{background:#ebe9e3}summary{font-size:20px;font-weight:600;cursor:pointer;margin:24px 0}.receipt{background:#e5f1e8;padding:16px}code{overflow-wrap:anywhere}</style><h1>Otto Dix — production delivery verified</h1><p>6 October 2026</p><p class="receipt"><strong>116 images uploaded and attached · 120 images across 182 linked production records</strong><br>All 116 public files passed checksum checks. All 116 database attachments and live API image URLs were verified. The four existing images are preserved.</p><p>The preceding metadata pass added 114 review records and repaired three artist links. New records remain in review, including 14 with unknown dates. Image delivery preserved titles, dates, creators, holdings, existing media and publication status. The local database was read only.</p><p>The user explicitly instructed “upload them” after reviewing the selected images and rights labels. The 46 “Public domain US” and 70 “Otto Dix Fair Use” labels remain recorded; every new image is stored as restricted with its WikiArt source link. This records collection authorization, not an independently obtained licence. Original files are archived separately; complete-frame derivatives are at most 100,000 bytes.</p><p><a href="uploaded-images.csv">Download 116-image delivery list</a> · <a href="production-otto-dix-artworks.csv">Download all 182 production records</a> · <a href="wikiart-import-review.csv">Initial WikiArt identity review</a></p><p>The complete 129-entry <a href="https://www.wikiart.org/en/otto-dix/all-works/text-list">WikiArt index</a> and its artwork pages were captured. Nine unresolved source entries remain held for duplicate, panel/detail or version reconciliation. This is not a complete catalogue raisonné of Dix’s oeuvre.</p><p>Supplemental research inventories contain <a href="moma-otto-dix-inventory.csv">93 MoMA records</a> and <a href="additional-museum-inventory.csv">20 LWL Münster and 10 Pinakothek records</a>. They overlap with other sources and are not counts of additional unique artworks; they were not automatically imported. A documented work about Dix is Conrad Felixmüller’s <em>Bildnis Otto Dix</em> (1920), identified by the <a href="https://von-der-heydt-museum.de/entdecken/forschung/">Von der Heydt Museum</a>; it remains a related research lead.</p><p>Visual review noted a possible “28” inscription on <em>Ursus With Spintop</em> while WikiArt gives 1924. The secure image association was retained, with the date discrepancy recorded for editorial review and the catalogue date preserved.</p>'''
    body+='<details open><summary>Nine source identity holds</summary>'+held_table+'</details><details><summary>116 uploaded images and source links</summary>'+image_table+'</details><details><summary>All 182 production records</summary>'+records+'</details>'
    body+='<h2>Recovery and verification</h2><p>Cloud SQL backup '+esc(summary['backup_id'])+' completed successfully before the metadata import. Exact metadata and image preimages, postimages, plans and recovery receipts are under <code>'+esc(BACKUP)+'</code>. All 182 records were checked for unrelated changes. The largest delivered image is '+str(verified['max_derivative_bytes'])+' bytes.</p><p><a href="image-authorization.json">Authorization</a> · <a href="image-visual-review.json">Visual review</a> · <a href="image-verification.json">Delivery verification</a> · <a href="image-live-api-pages.json">Live API verification</a> · <a href="summary.json">Summary</a></p></html>'
    (RUN/'report.html').write_text(body)
    print('Updated report: 116 uploaded, 120 total images, 182 linked records',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','sheets','plan','upload','apply','verify','report']);args=parser.parse_args()
    globals()[args.phase]()
