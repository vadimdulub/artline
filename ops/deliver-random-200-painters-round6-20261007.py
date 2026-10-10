#!/usr/bin/env python3
"""Resumable, authorized production delivery for the frozen painter cohort.

Source and rights evidence stays attached to every selected object. Preparation
is separate from production writes; all records stay in their review state.
"""
import argparse
import base64
import collections
import concurrent.futures
from contextlib import nullcontext
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import textwrap
import threading
import time

from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageStat
from psycopg.types.json import Jsonb
import requests

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
s=module('cohort_selection','ops/select-random-200-painters-round6-20261007.py');m=s.m;r=s.r;q=s.q
d=module('cohort_image_helpers','ops/deliver-production-wikiart-images-20261006.py')
RUN=m.RUN;BACKUP=m.BACKUP;ORIGINALS=m.ORIGINALS;OP=m.OP;ACTOR=m.ACTOR;POLICY=m.POLICY
d.RUN=RUN;d.ORIGINALS=ORIGINALS


def plans():
    for pair in m.cohort():
        aid=pair['artist']['id'];path=RUN/'selections'/(aid+'.json.gz')
        if not path.exists():continue
        pin=r.load(RUN/'selection-pins'/(aid+'.json'))['sha256'];assert pin==r.sha(path.read_bytes())
        data=r.load(path);assert data['authorization_sha256']==r.sha((RUN/'authorization.json').read_bytes())
        assert r.load(BACKUP/'selection-preimages'/(aid+'.json.gz'))['plan_sha256']==pin
        yield data,pin


def image_rows(data):
    return [x for x in data['rows'] if x['action'] in ['create','existing'] and not x.get('has_image') and not x.get('image_hold')
            and x['page']['date'] and x['page']['date']['creation_year_end']<=1970]


def prepare():
    jobs=[(data,pin,row) for data,pin in plans() for row in image_rows(data)]
    def one(job):
        data,pin,row=job;aid=row['artwork_id'];dest=RUN/'prepared-images'/(aid+'.json')
        if dest.exists():return r.load(dest)
        p=row['page'];url=p['metadata']['image']
        result={'artwork_id':aid,'artist_id':row['artist_id'],'artist':data['artist']['display_name'],'title':row['title'],
                'source_id':row['source_id'],'source_page_url':row['source_url'],'source_image_url':url,
                'source_rights_label':row['source_rights_label'],'rights_status':row['rights_status'],
                'page_receipt':p['receipt'],'selection_pin':pin,'identity_basis':row['identity_basis'],'confidence':row['confidence']}
        if q.image_key(url)!=q.image_key(p['image_url']):
            if p['image_url']=='https://uploads.wikiart.org/Content/images/FRAME-600x480.jpg':
                result['source_display_placeholder']={'display_url':p['image_url'],'artwork_metadata_image_url':url,
                    'basis':'The exact artwork JSON explicitly supplies this public source image URL. The visible page uses a generic frame. Only a successful ordinary public fetch is accepted; every such image receives visual review. No URL substitution or access-control workaround.'}
            else:
                result.update(outcome='preparation_held',error='Artwork JSON and visible image identify different reproductions; unresolved image identity.')
                r.save(dest,result);return result
        for attempt in range(3):
            try:
                try:
                    original,rc=d.download(url)
                    raw,width,height,quality=d.core.compress(original)
                except ValueError as exc:
                    if result.get('source_display_placeholder') or not any(text in str(exc) for text in ['Unexpected source dimensions','Selected image exceeds byte budget','image file is truncated','cannot identify image file']) or url==p['image_url']:raise
                    # Use the display-size URL actually supplied by the artwork page.
                    # This is the same reproduction, not a guessed replacement image.
                    result['original_image_url']=url;url=p['image_url'];result['source_image_url']=url
                    assert q.image_key(url)==q.image_key(p['metadata']['image'])
                    original,rc=d.download(url);raw,width,height,quality=d.core.compress(original)
                assert 0<len(raw)<=100000 and min(width,height)>=50 and max(width,height)>=200
                with Image.open(io.BytesIO(raw)) as image:image.verify()
                with Image.open(io.BytesIO(original)) as source:original_size=list(ImageOps.exif_transpose(source).size)
                assert abs(width/height-original_size[0]/original_size[1])<.025
                with Image.open(io.BytesIO(raw)) as image:
                    gray=image.convert('L').resize((17,16));pixels=list(gray.getdata());bits=''.join('1' if pixels[y*17+x]>pixels[y*17+x+1] else '0' for y in range(16) for x in range(16))
                    dhash=hex(int(bits,2))[2:].zfill(64);stddev=ImageStat.Stat(image.convert('L')).stddev[0]
                    assert stddev>1,'Near-uniform source image requires review'
                digest=r.sha(raw);path='/assets/artworks/imported/'+OP+'/'+aid+'-'+digest[:16]+'.jpg'
                target=ROOT/'apps/web/public'/path.lstrip('/');r.save(target,raw)
                result.update(outcome='prepared',path=path,visual_path=str(target),sha256=digest,dhash=dhash,
                              media_id=m.uid('image-media/'+aid+'/'+digest),bytes=len(raw),width=width,height=height,
                              original_dimensions=original_size,jpeg_quality=quality,download=rc,luminance_stddev=stddev)
                break
            except Exception as exc:
                if attempt==2:result.update(outcome='preparation_held',error=str(exc)[:400])
                else:time.sleep(1+attempt)
        r.save(dest,result);return result
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for n,im in enumerate(pool.map(one,jobs),1):
            counts[im['outcome']]+=1
            if n%50==0:print('Prepared image decisions',n,'/',len(jobs),dict(counts),flush=True)
    m.status('preparation',selected=len(jobs),counts=dict(counts));print('Image preparation',dict(counts),flush=True)


def audits():
    """Whole-set file checks, same-painter duplicate checks, explicit QA samples."""
    for data,pin in plans():
        aid=data['artist']['id'];dest=RUN/'image-audits'/(aid+'.json')
        if dest.exists():continue
        paths=[RUN/'prepared-images'/(row['artwork_id']+'.json') for row in image_rows(data)]
        if not all(path.exists() for path in paths):continue
        ims=[r.load(path) for path in paths];ready=[im for im in ims if im['outcome']=='prepared']
        duplicate_groups=[];holds={}
        for i,left in enumerate(ready):
            for right in ready[i+1:]:
                distance=(int(left['dhash'],16)^int(right['dhash'],16)).bit_count()
                exact=left['sha256']==right['sha256'] or left['download']['sha256']==right['download']['sha256']
                if exact or distance<=3:
                    duplicate_groups.append({'ids':[left['artwork_id'],right['artwork_id']],'exact':exact,'dhash_distance':distance})
                    for im in [left,right]:holds[im['artwork_id']]='Same or nearly identical source reproduction; inspect version identity before import/attachment'
        sample={}
        filtered=[im for im in ready if im['artwork_id'] not in holds]
        if filtered:
            for i in sorted({0,len(filtered)//2,len(filtered)-1}):sample[filtered[i]['artwork_id']]=filtered[i]
        for im in filtered:
            if im['confidence']<.99 or min(im['width'],im['height'])<150 or im['jpeg_quality']<45 or im.get('source_display_placeholder'):
                sample[im['artwork_id']]=im
        r.save(dest,{'artist_id':aid,'artist':data['artist']['display_name'],'selection_pin':pin,
            'prepared':len(ready),'preparation_holds':[im for im in ims if im['outcome']!='prepared'],
            'duplicate_groups':duplicate_groups,'held_artwork_ids':holds,
            'visual_sample_ids':list(sample),'visual_sample_policy':'First, middle and last prepared reproduction for every painter, every title/date-only existing match, every low-resolution/low-quality derivative and every explicitly supplied artwork-JSON image whose page shows a generic frame. All selected files receive automated decoding, dimensions, full-frame proportion, byte-budget, checksum and within-painter duplicate checks. No claim that unsampled images were manually inspected.'})
        print('Audited',data['artist']['display_name'],len(ready),'images;',len(holds),'identity holds;',len(sample),'visual samples',flush=True)


def sheets():
    """Make incremental 24-image sheets; never silently mark visual QA complete."""
    indexed=set()
    for path in (RUN/'visual-batches').glob('*.json'):
        indexed.update(x['artwork_id'] for x in r.load(path)['images'])
    items=[]
    for data,pin in plans():
        path=RUN/'image-audits'/(data['artist']['id']+'.json')
        if path.exists():
            for aid in r.load(path)['visual_sample_ids']:
                if aid not in indexed:items.append(r.load(RUN/'prepared-images'/(aid+'.json')))
    if not items:print('No new visual samples',flush=True);return
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
    folder=ORIGINALS/'contact-sheets';folder.mkdir(parents=True,exist_ok=True)
    number=len(list((RUN/'visual-batches').glob('*.json')))
    for start in range(0,len(items),24):
        batch=items[start:start+24];number+=1;sheet=Image.new('RGB',(1440,1440),'white');draw=ImageDraw.Draw(sheet)
        for offset,im in enumerate(batch):
            left=(offset%6)*240;top=(offset//6)*360
            with Image.open(im['visual_path']) as source:
                image=source.convert('RGB');image.thumbnail((226,260));sheet.paste(image,(left+(240-image.width)//2,top+(265-image.height)//2))
            label=str(offset+1)+'. '+im['artist']+': '+im['title']
            for n,line in enumerate(textwrap.wrap(label,32)[:5]):draw.text((left+6,top+270+n*16),line,font=font,fill='black')
        path=folder/f'{number:04d}.jpg';sheet.save(path,quality=92)
        r.save(RUN/'visual-batches'/f'{number:04d}.json',{'number':number,'path':str(path),'sha256':r.sha(path.read_bytes()),
             'images':[{'artwork_id':im['artwork_id'],'sha256':im['sha256'],'artist':im['artist'],'title':im['title']} for im in batch]})
        print('Visual sheet',number,len(batch),'images',str(path),flush=True)


def visual_decisions():
    approved={};held={}
    for path in (RUN/'visual-reviews').glob('*.json'):
        review=r.load(path);batch=r.load(RUN/'visual-batches'/path.name)
        assert review['sheet_sha256']==batch['sha256']
        expected={x['artwork_id']:x['sha256'] for x in batch['images']}
        assert set(review['approved'])|set(review['held'])==set(expected)
        assert not set(review['approved'])&set(review['held'])
        for aid in review['approved']:approved[aid]=expected[aid]
        held.update(review['held'])
    return approved,held


def delivery_plans():
    approved,visual_held=visual_decisions();counts=collections.Counter()
    global_audit_path=RUN/'cross-creator-image-audit.json'
    expected_count=len(m.cohort())
    assert len(list((RUN/'selections').glob('*.json.gz')))==expected_count,'Finish the frozen cohort before delivery'
    assert len(list((RUN/'image-audits').glob('*.json')))==expected_count,'Finish image validation for the entire cohort'
    assert global_audit_path.exists(),'Cross-creator reproduction checks must precede delivery'
    global_holds=r.load(global_audit_path)['held_artwork_ids']
    additional_audit_path=RUN/'additional-image-reference-audit.json'
    assert additional_audit_path.exists(),'Finish scoped existing-image and Otto Dix comparisons'
    additional_holds=r.load(additional_audit_path)['held_artwork_ids']
    identity_path=RUN/'manual-identity-holds.json'
    identity_holds=r.load(identity_path)['held_artwork_ids'] if identity_path.exists() else {}
    resolution_path=RUN/'duplicate-review-resolutions-v2.json'
    resolutions=r.load(resolution_path)['approved'] if resolution_path.exists() else {}
    source_notes_path=RUN/'reviewed-source-discrepancies.json'
    source_notes=r.load(source_notes_path)['records'] if source_notes_path.exists() else {}
    image_only_path=RUN/'manual-image-holds.json'
    image_only_holds=r.load(image_only_path)['held_artwork_ids'] if image_only_path.exists() else {}
    with r.connect('production') as db:
        for data,pin in plans():
            artist=data['artist'];aid=artist['id'];dest=RUN/'delivery-plans'/(aid+'.json.gz')
            if dest.exists():continue
            retry_state=RUN/'progress/source-retries.json'
            if retry_state.exists() and aid in r.load(retry_state).get('pending_artist_ids',[]):continue
            for row in data['rows']:
                if not row.get('page'):continue
                date=s.source_date(row['page']);row['page']['date']=date
                if row['action']=='create' and date:
                    row['work'].update(date)
            path=RUN/'image-audits'/(aid+'.json')
            if not path.exists():continue
            audit=r.load(path);assert audit['selection_pin']==pin
            if not set(audit['visual_sample_ids'])<=set(approved)|set(visual_held):continue
            holds={**audit['held_artwork_ids'],**{k:v for k,v in visual_held.items() if k in audit['visual_sample_ids'] and k not in image_only_holds}}
            for target,decision in resolutions.items():
                if target in audit['held_artwork_ids'] and target not in visual_held:
                    assert r.load(RUN/'prepared-images'/(target+'.json'))['sha256']==decision['sha256']
                    holds.pop(target,None)
            holds.update({k:v for k,v in global_holds.items() if any(x.get('artwork_id')==k for x in data['rows'])})
            holds.update({k:v for k,v in additional_holds.items() if any(x.get('artwork_id')==k for x in data['rows'])})
            holds.update({k:v for k,v in identity_holds.items() if any(x.get('artwork_id')==k for x in data['rows'])})
            rows=[x for x in data['rows'] if x['action'] in ['create','existing'] and x['artwork_id'] not in holds]
            ids=[x['artwork_id'] for x in rows];before=s.snapshots(db,ids)
            original=r.load(BACKUP/'selection-preimages'/(aid+'.json.gz'))['records']
            for row in rows:
                target=row['artwork_id']
                if row['action']=='existing' and before.get(target)!=original[target]:holds[target]='Production record changed after selection; preserve concurrent work'
                elif row['action']=='create' and target in before:holds[target]='Proposed new ID was concurrently created'
            rows=[x for x in rows if x['artwork_id'] not in holds];images=[]
            for row in rows:
                if row['artwork_id'] in source_notes:row['reviewed_source_discrepancy']=source_notes[row['artwork_id']]
                if row.get('reviewed_source_discrepancy',{}).get('creation_date_unresolved'):
                    assert row['action']=='create','Date classification review cannot change existing catalogue metadata'
                    row['page']['reviewed_date_classification']='unknown'
                    row['page']['date']=None
                    row['work'].update(creation_year_start=None,creation_year_end=None,date_precision='unknown',date_display='Unknown date')
                if row['artwork_id'] in image_only_holds:
                    assert row.get('reviewed_source_discrepancy'),'Image-only hold requires an explicit retained-metadata source qualification'
                    row['image_hold']=image_only_holds[row['artwork_id']]
            image_selected={x['artwork_id'] for x in image_rows(data)}-set(image_only_holds)
            for row in rows:
                assert row['confidence']>=.90
                assert row['page']['metadata']['artistUrl']==m.urlsplit(data['source_artist']['url']).path
                assert row['rights_status']==row['page']['rights_status']
                if row['rights_status']=='public_domain':assert row['source_rights_label']=='Public domain'
                path=RUN/'prepared-images'/(row['artwork_id']+'.json')
                if path.exists() and row['artwork_id'] in image_selected:
                    im=r.load(path)
                    if im['outcome']=='prepared':
                        assert im['selection_pin']==pin
                        raw=Path(im['visual_path']).read_bytes();assert r.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
                        images.append(im)
            plan={'artist':artist,'rows':rows,'images':images,'selection_pin':pin,'image_audit':audit,
                  'held':holds,'image_scope_holds':{x['artwork_id']:'Undated source work: retain review metadata; await creation-date evidence before image attachment.' for x in rows if not x['page']['date'] and not x.get('has_image')},
                  'manual_image_holds':{x['artwork_id']:image_only_holds[x['artwork_id']] for x in rows if x['artwork_id'] in image_only_holds},
                  'preimages':{x['artwork_id']:before[x['artwork_id']] for x in rows if x['action']=='existing'},
                  'authorization_sha256':r.sha((RUN/'authorization.json').read_bytes()),'at':r.now()}
            if global_audit_path.exists():plan['cross_creator_audit_sha256']=r.sha(global_audit_path.read_bytes())
            plan['additional_image_reference_audit_sha256']=r.sha(additional_audit_path.read_bytes())
            if identity_path.exists():plan['manual_identity_holds_sha256']=r.sha(identity_path.read_bytes())
            if resolution_path.exists():plan['duplicate_review_resolutions_sha256']=r.sha(resolution_path.read_bytes())
            if source_notes_path.exists():plan['reviewed_source_discrepancies_sha256']=r.sha(source_notes_path.read_bytes())
            if image_only_path.exists():plan['manual_image_holds_sha256']=r.sha(image_only_path.read_bytes())
            r.save_gz(dest,plan);digest=r.sha(dest.read_bytes())
            r.save(RUN/'delivery-pins'/(aid+'.json'),{'sha256':digest})
            r.save_gz(BACKUP/'delivery-preimages'/(aid+'.json.gz'),{'plan_sha256':digest,'records':plan['preimages']})
            counts['painters']+=1;counts['rows']+=len(rows);counts['images']+=len(images)
            print('Pinned delivery',artist['display_name'],len(rows),'records;',len(images),'images',flush=True)
    print('New delivery plans',dict(counts),flush=True)


def pinned_deliveries():
    for pair in m.cohort():
        aid=pair['artist']['id'];path=RUN/'delivery-plans'/(aid+'.json.gz')
        if not path.exists():continue
        pin=r.load(RUN/'delivery-pins'/(aid+'.json'))['sha256'];assert r.sha(path.read_bytes())==pin
        assert r.load(BACKUP/'delivery-preimages'/(aid+'.json.gz'))['plan_sha256']==pin
        data=r.load(path);assert data['authorization_sha256']==r.sha((RUN/'authorization.json').read_bytes())
        yield data,pin


def location_reviews():
    reviews={};path=RUN/'concurrent-location-review.json'
    paths=[(path,RUN/'concurrent-location-review-pin.json')] if path.exists() else []
    paths.extend((p,p.with_name(p.stem+'.pin.json')) for p in sorted((RUN/'concurrent-location-reviews').glob('*.review.json')))
    for path,pin_path in paths:
        digest=r.sha(path.read_bytes());assert digest==r.load(pin_path)['sha256']
        for aid,review in r.load(path)['reviewed'].items():
            assert aid not in reviews
            reviews[aid]={**review,'review_file':str(path.relative_to(ROOT)),'review_sha256':digest}
    return reviews


def reviewed_location_change(aid,before,after,pin,stage):
    """Accept only an individually recorded concurrent holding update; never write it."""
    review=location_reviews().get(aid)
    if not review or review['stage']!=stage:return None
    assert review['plan_sha256']==pin and review['before']==before and review['after']==after
    allowed={'revision','updated_at','updated_by','location_checked_at','current_location_text','current_institution_id'}
    assert {k:v for k,v in before['artwork'].items() if k not in allowed}=={k:v for k,v in after['artwork'].items() if k not in allowed}
    assert before['creators']==after['creators'] and before['attachments']==after['attachments']
    assert all(loc in after['locations'] for loc in before['locations'])
    added=[loc for loc in after['locations'] if loc not in before['locations']]
    assert added and added==review['added_locations']
    assert all(loc['claim_type']=='holding' and loc['display_state'] is None and json.loads(loc['evidence_note'])['operation'] in {'random-5000-museums-round2-20261006','all-museums-minimum-100-20261006-wikiart-003'} for loc in added)
    assert review['decision']=='preserve_exact_concurrent_holding_update' and review['count_as_this_campaign_holding'] is False
    return {'review_file':review['review_file'],'review_sha256':review['review_sha256'],'artwork_id':aid,'stage':stage,'decision':review['decision']}


def upload():
    jobs=[(im,pin) for data,pin in pinned_deliveries() for im in data['images']]
    bucket=d.storage.Client(project='artline-508319',credentials=d.core.GcloudCredentials()).bucket(d.core.BUCKET)
    public_sessions=threading.local()
    def one(job):
        im,pin=job;dest=RUN/'image-uploads'/(im['artwork_id']+'.json')
        if dest.exists():
            rc=r.load(dest);assert rc['plan_sha256']==pin and rc['sha256']==im['sha256'];return rc
        raw=Path(im['visual_path']).read_bytes();assert r.sha(raw)==im['sha256'] and len(raw)==im['bytes']
        for attempt in range(3):
            try:
                blob=bucket.blob(im['path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'artwork-id':im['artwork_id'],'provider':'WikiArt','operation':OP,'rights-status':im['rights_status']}
                blob.cache_control='public,max-age=31536000,immutable'
                try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
                except d.PreconditionFailed:blob.reload(timeout=30)
                assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
                if not hasattr(public_sessions,'session'):public_sessions.session=requests.Session()
                response=public_sessions.session.get('https://artlines.org'+im['path'],timeout=(15,45));response.raise_for_status()
                assert r.sha(response.content)==im['sha256']
                rc={'artwork_id':im['artwork_id'],'at':r.now(),'plan_sha256':pin,'generation':blob.generation,
                    'path':im['path'],'sha256':im['sha256'],'bytes':len(raw),'public_http_status':response.status_code,'public_bytes_verified':True}
                r.save(dest,rc);return rc
            except Exception:
                if attempt==2:raise
                time.sleep(2+attempt*2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for n,_ in enumerate(pool.map(one,jobs),1):
            if n%50==0:print('Uploaded and publicly verified',n,'/',len(jobs),flush=True)
    print('Verified public files',len(jobs),flush=True)


def apply():
    with r.connect('production',readonly=False) as connection:
        _apply(connection)


def _apply(connection):
    assert r.load(BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
    source=m.uid('source/wikiart');image_source=m.uid('source/images');auth=r.load(RUN/'authorization.json')
    for data,pin in pinned_deliveries():
        artist=data['artist'];artist_id=artist['id'];done=RUN/'applied'/(artist_id+'.json')
        if done.exists():continue
        images={im['artwork_id']:im for im in data['images']}
        if not all((RUN/'image-uploads'/(aid+'.json')).exists() for aid in images):continue
        for aid,im in images.items():
            rc=r.load(RUN/'image-uploads'/(aid+'.json'));assert rc['plan_sha256']==pin and rc['sha256']==im['sha256'] and rc['public_bytes_verified']
        rows=data['rows'];batch_results=[]
        with nullcontext(connection) as db:
            for start in range(0,len(rows),40):
                batch=rows[start:start+40];ids=[row['artwork_id'] for row in batch]
                receipt_path=RUN/'applied-batches'/artist_id/f'{start//40:04d}.json'
                if receipt_path.exists():batch_results.append(r.load(receipt_path));continue
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='5s'")
                    db.execute('SELECT pg_advisory_xact_lock(2026100607)')
                    db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
                    before=s.snapshots(db,ids)
                    # Resume a committed transaction whose filesystem receipt was interrupted.
                    recorded=db.execute('SELECT entity_id::text FROM citations WHERE id=ANY(%s::uuid[])',([m.uid('identity/'+row['source_id']) for row in batch],)).fetchall()
                    if recorded:
                        assert {x['entity_id'] for x in recorded}==set(ids),'Partially recorded transaction'
                        result={'at':r.now(),'plan_sha256':pin,'ids':ids,'created':sum(row['action']=='create' for row in batch),
                                'attached':sum(aid in images for aid in ids),'recovered_committed_transaction':True}
                    else:
                        for row in batch:
                            aid=row['artwork_id']
                            if row['action']=='existing':
                                assert before.get(aid)==data['preimages'][aid] or reviewed_location_change(aid,data['preimages'][aid],before.get(aid),pin,'preapply'), 'Concurrent record change: '+aid
                            else:assert aid not in before,'New artwork ID already exists'
                        sources=db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme IN ('wikiart-artwork','wikiart-legacy-content-id') AND external_id=ANY(%s)",([row['source_id'] for row in batch],)).fetchall()
                        expected_sources={row['source_id']:row['artwork_id'] for row in batch}
                        assert all(expected_sources[x['external_id']]==x['entity_id'] for x in sources)
                        existing_sources={x['external_id'] for x in sources}
                        creator=db.execute('SELECT id::text,display_name,status FROM artists WHERE id=%s FOR SHARE',(artist_id,)).fetchone()
                        assert creator['id']==artist_id and creator['display_name']==artist['display_name'] and creator['status']!='archived'
                        collection=db.execute('SELECT curator_kind,institution_id::text,status FROM curated_collections WHERE id=%s FOR UPDATE',(m.COLLECTION,)).fetchone()
                        assert collection=={'curator_kind':'owner','institution_id':None,'status':'review'}
                        pos=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(m.COLLECTION,)).fetchone()['n']
                        assert pos+sum(row['action']=='create' for row in batch)<=100000
                        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://www.wikiart.org/') ON CONFLICT(id) DO NOTHING",
                                   (source,OP+'-wikiart','WikiArt random 200-painter review selection, 7 October 2026'))
                        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://www.wikiart.org/') ON CONFLICT(id) DO NOTHING",
                                   (image_source,OP+'-images','WikiArt random 200-painter authorized image attachments, 7 October 2026'))
                        r.save_gz(BACKUP/'batch-preimages'/artist_id/f'{start//40:04d}.json.gz',{'plan_sha256':pin,'records':before})
                        updated=[]
                        with db.pipeline():
                            for row in batch:
                                aid=row['artwork_id'];p=row['page']
                                if row['action']=='create':
                                    w=row['work'];keys=['id','slug','title','alternate_title','normalized_title','date_display','creation_year_start','creation_year_end','date_precision','work_type','medium_text','dimensions_text']
                                    db.execute('''INSERT INTO artworks(id,slug,title,alternate_title,normalized_title,date_display,creation_year_start,
                                      creation_year_end,date_precision,work_type,medium_text,dimensions_text,status,research_candidate,created_by,updated_by)
                                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)''',tuple(w[k] for k in keys)+(ACTOR,ACTOR))
                                    db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",
                                               (aid,artist_id,row.get('creator_evidence_note') or 'WikiArt explicitly identifies this sampled creator on the artwork page and complete artist index; review record.'))
                                    pos+=1
                                    db.execute('''INSERT INTO curated_collection_items(id,collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
                                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s)''',(m.uid('selection/'+aid),m.COLLECTION,aid,pos,
                                      'Personal 200-painter research selection explicitly requested 7 October 2026. Separate from museum designations; unknown and cross-cutoff dates require editorial review.',source,p['url'],p['receipt']['retrieved_at']))
                                if row['source_id'] not in existing_sources:
                                    db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,row.get('source_scheme','wikiart-artwork'),row['source_id'],p['url'],source,p['receipt']['retrieved_at']))
                                note={'plan_sha256':pin,'page':p,'identity_basis':row['identity_basis'],'confidence':row['confidence'],
                                      'confidence_note':'Editorial threshold, not a statistically calibrated probability.',
                                      'selection':'User-requested personal research collection. Existing metadata, holdings, display and publication state preserved.'}
                                if row.get('reviewed_source_discrepancy'):note['reviewed_source_discrepancy']=row['reviewed_source_discrepancy']
                                if row['action']=='existing' and before[aid]!=data['preimages'][aid]:
                                    note['concurrent_location_preservation']=reviewed_location_change(aid,data['preimages'][aid],before[aid],pin,'preapply')
                                db.execute('''INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                                  VALUES(%s,'artwork',%s,%s,'random_200_source_identity',%s,%s,%s,%s,%s)''',
                                  (m.uid('identity/'+row['source_id']),aid,source,row['source_id'],p['url'],json.dumps(note,ensure_ascii=False),p['receipt']['retrieved_at'],ACTOR))
                                if aid in images:
                                    im=images[aid];attribution=artist['display_name']+'. '+im['title']+'. WikiArt source label: '+im['source_rights_label']+'. Proportional resize and JPEG compression; no crop. Source: '+im['source_page_url']
                                    db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,
                                      checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at)
                                      VALUES(%s,'local',%s,%s,'WikiArt','image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                                      (im['media_id'],im['path'],im['source_page_url'],im['width'],im['height'],im['bytes'],im['sha256'],im['title']+' — '+artist['display_name'],
                                       im['rights_status'],im['source_rights_label']+' (WikiArt source label)',POLICY,artist['display_name']+'; reproduction via WikiArt',attribution,im['download']['at']))
                                    db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,
                                      rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                                      (im['media_id'],image_source,im['source_id'],p['receipt']['sha256'],im['source_image_url'],POLICY,
                                       'User-approved WikiArt source policy, 6 October 2026. Actual per-image source assertion retained, including restricted or missing labels; approval recorded separately. No independent licence or public-domain status inferred.',
                                       OP+'-v1',p['receipt']['retrieved_at'],Jsonb({'image':im,'page':p,'authorization':auth,'plan_sha256':pin,
                                       'identity_basis':row['identity_basis'],'confidence':row['confidence'],'visual_sampled':aid in data['image_audit']['visual_sample_ids'],
                                       'validation_policy':data['image_audit']['visual_sample_policy']})))
                                    db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s)',(aid,im['media_id'],'Complete source reproduction'))
                                    updated.append(db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],ACTOR,aid)))
                                    db.execute('''INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                                      VALUES(%s,'artwork',%s,%s,'random_200_image_delivery',%s,%s,%s,%s,%s)''',
                                      (m.uid('image-citation/'+aid),aid,image_source,im['source_id'],im['source_page_url'],json.dumps({'plan_sha256':pin,'source_rights_label':im['source_rights_label'],
                                       'source_image_url':im['source_image_url'],'scope':'Image attachment; preserve metadata, holdings, display claims and publication state.'},ensure_ascii=False),r.now(),ACTOR))
                            db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(m.COLLECTION,))
                        assert all(c.rowcount==1 for c in updated)
                        after=s.snapshots(db,ids)
                        for row in batch:
                            aid=row['artwork_id'];current=after[aid]
                            if row['action']=='create':
                                assert current['artwork']['status']=='review' and current['artwork']['research_candidate'] and current['artwork']['published_at'] is None
                                assert current['artwork']['current_institution_id'] is None and not current['locations']
                                assert len(current['creators'])==1 and current['creators'][0]['artist_id']==artist_id
                            else:
                                prior=before[aid];allowed={'primary_media_id','revision','updated_at','updated_by'} if aid in images else set()
                                assert {k:v for k,v in current['artwork'].items() if k not in allowed}=={k:v for k,v in prior['artwork'].items() if k not in allowed}
                                assert current['creators']==prior['creators'] and current['locations']==prior['locations']
                                assert all(x in current['attachments'] for x in prior['attachments'])
                            if aid in images:assert current['artwork']['primary_media_id']==images[aid]['media_id']
                        result={'at':r.now(),'plan_sha256':pin,'ids':ids,'created':sum(row['action']=='create' for row in batch),'attached':sum(aid in images for aid in ids)}
                after=s.snapshots(db,ids);r.save_gz(BACKUP/'batch-after'/artist_id/f'{start//40:04d}.json.gz',{'plan_sha256':pin,'records':after})
                r.save(receipt_path,result);batch_results.append(result)
                print('Committed',artist['display_name'],min(start+40,len(rows)),'/',len(rows),'records',flush=True)
        r.save(done,{'at':r.now(),'plan_sha256':pin,'artist_id':artist_id,'created':sum(x['created'] for x in batch_results),
                    'attached':sum(x['attached'] for x in batch_results),'records':len(rows),'local_database_changed':False,'publication_changed':False})
        print('Completed production painter',artist['display_name'],len(rows),'records;',len(images),'images',flush=True)


def verify():
    jobs=[(data,pin) for data,pin in pinned_deliveries() if (RUN/'applied'/(data['artist']['id']+'.json')).exists()]
    def one(job):
        data,pin=job;artist=data['artist'];artist_id=artist['id'];dest=RUN/'verified'/(artist_id+'.json')
        if dest.exists():return r.load(dest)
        expected={}
        for path in (BACKUP/'batch-after'/artist_id).glob('*.json.gz'):
            part=r.load(path);assert part['plan_sha256']==pin;expected.update(part['records'])
        assert len(expected)==len(data['rows'])
        images={im['artwork_id']:im for im in data['images']}
        with r.connect('production') as db:
            actual=s.snapshots(db,list(expected));assert set(actual)==set(expected)
            for aid,value in actual.items():
                assert value==expected[aid] or reviewed_location_change(aid,expected[aid],value,pin,'postcommit'),'Production differs from committed batch snapshots'
            media=db.execute('''SELECT to_jsonb(ma) media,to_jsonb(e) rights FROM media_assets ma
              JOIN media_rights_evidence e ON e.media_id=ma.id WHERE ma.id=ANY(%s::uuid[])''',([im['media_id'] for im in images.values()],)).fetchall()
            bymedia={x['media']['id']:x for x in media};assert len(bymedia)==len(images)
            for im in images.values():
                x=bymedia[im['media_id']];ma=x['media'];ev=x['rights']
                assert ma['storage_path']==im['path'] and ma['checksum_sha256']==im['sha256'] and ma['byte_size']==im['bytes']<=100000
                assert ma['rights_status']==im['rights_status'] and ma['verified_at'] is None
                assert ma['source_page_url']==im['source_page_url'] and ma['license_label']==im['source_rights_label']+' (WikiArt source label)'
                assert ev['source_record_id']==im['source_id'] and ev['source_image_url']==im['source_image_url'] and ev['evidence_json']['plan_sha256']==pin
            counts=db.execute('''SELECT count(*) artworks,count(*) FILTER(WHERE a.primary_media_id IS NOT NULL) images
              FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived' ''',(artist_id,)).fetchone()
            count=db.execute('SELECT count(*) n FROM citations WHERE id=ANY(%s::uuid[])',([m.uid('identity/'+row['source_id']) for row in data['rows']],)).fetchone()['n']
            assert count==len(data['rows'])
            newids=[row['artwork_id'] for row in data['rows'] if row['action']=='create']
            selections=db.execute('SELECT id::text,artline_has_selection_evidence(id) selected FROM artworks WHERE id=ANY(%s::uuid[])',(newids,)).fetchall()
            assert len(selections)==len(newids) and all(x['selected'] for x in selections)
        pages=[];found={};seen=set()
        if images:
            url='https://artlines.org/api/backend/v1/artists/'+artist['slug']+'/works';params={'limit':50,'image_only':'true'}
            while True:
                for attempt in range(4):
                    try:
                        response=requests.get(url,params=params,timeout=(15,60))
                    except (requests.Timeout,requests.ConnectionError):
                        if attempt==3:raise
                        time.sleep(2+attempt*3)
                        continue
                    if response.status_code not in [500,502,503,504] or attempt==3:break
                    time.sleep(2+attempt*3)
                response.raise_for_status();body=response.json()
                pages.append({'url':response.url,'status':response.status_code,'body':body})
                for item in body['items']:found[item['id']]=item
                cursor=body.get('next_cursor')
                if not cursor:break
                assert cursor not in seen and len(pages)<1000,'Repeated/unbounded API cursor'
                seen.add(cursor);params['cursor']=cursor
            for aid,im in images.items():
                item=found[aid];assert item['media_url']==im['path'] and item['rights_status']==im['rights_status']
        r.save_gz(RUN/'api-verification'/(artist_id+'.json.gz'),{'at':r.now(),'pages':pages,'expected_image_ids':list(images)})
        result={'at':r.now(),'artist_id':artist_id,'artist':artist['display_name'],'plan_sha256':pin,
                'records_verified':len(expected),'images_verified':len(images),'api_pages':len(pages),
                'production_artist_totals':counts,'new_records_remain_review':True,'existing_metadata_preserved':True,'errors':[]}
        r.save(dest,result);print('Verified production',artist['display_name'],len(expected),'records;',len(images),'images;',len(pages),'API pages',flush=True)
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(one,jobs))
    m.status('verification',painters=len(results),records=sum(x['records_verified'] for x in results),images=sum(x['images_verified'] for x in results))


def report():
    import csv,html
    rows=[];source_rows=[]
    for pair in m.cohort():
        artist=pair['artist'];aid=artist['id'];idx=r.load(RUN/'indexes'/(aid+'.json.gz'))
        record={'artist':artist['display_name'],'artist_id':aid,'artist_url':'https://artlines.org/artists/'+artist['slug'],
                'wikiart_url':pair['source']['url'],'source_entries':len(idx['items']),'status':'research_in_progress'}
        path=RUN/'selections'/(aid+'.json.gz')
        if path.exists():
            plan=r.load(path);record.update(before_records=plan['baseline_counts']['works'],before_images=plan['baseline_counts']['images'],
                new_proposed=plan['counts'].get('create',0),existing_matches=plan['counts'].get('existing',0),
                source_holds=plan['counts'].get('hold',0),excluded_after_1970=plan['source_excluded_after_1970']+plan['counts'].get('excluded',0),
                unlinked_creator_leads=len(plan['unlinked_creator_leads']),status='selected')
            for x in plan['rows']:
                source_rows.append({'artist':artist['display_name'],'artist_id':aid,'title':x.get('title',x.get('record',{}).get('index',{}).get('title')),
                  'source_url':x.get('source_url',x.get('record',{}).get('index',{}).get('url')),'action':x['action'],'artwork_id':x.get('artwork_id'),
                  'source_date':x.get('page',{}).get('metadata',{}).get('year'),'source_rights_label':x.get('source_rights_label'),
                  'reason':x.get('reason') or x.get('image_hold') or ('Undated: metadata review; image deferred' if x.get('page') and not x['page']['date'] else '')})
        path=RUN/'delivery-plans'/(aid+'.json.gz')
        if path.exists():
            delivery=r.load(path);record.update(delivery_holds=len(delivery['held']),undated_image_holds=len(delivery['image_scope_holds']),reviewed_image_holds=len(delivery.get('manual_image_holds',{})),status='delivery_planned')
        path=RUN/'applied'/(aid+'.json')
        if path.exists():
            applied=r.load(path);record.update(created=applied['created'],images_added=applied['attached'],status='production_applied')
        path=RUN/'verified'/(aid+'.json')
        if path.exists():
            verified=r.load(path);record.update(after_records=verified['production_artist_totals']['artworks'],after_images=verified['production_artist_totals']['images'],status='production_verified')
        rows.append(record)
    totals={key:sum(x.get(key,0) for x in rows) for key in ['source_entries','before_records','before_images','new_proposed','existing_matches','source_holds','excluded_after_1970','unlinked_creator_leads','delivery_holds','undated_image_holds','reviewed_image_holds','created','images_added','after_records','after_images']}
    summary={'at':r.now(),'operation':OP,'painters':len(rows),'statuses':dict(collections.Counter(x['status'] for x in rows)),'totals':totals,
             'complete':all(x['status']=='production_verified' for x in rows),'painters_report':rows,
             'scope':'Research of available WikiArt indexes for a reproducible random cohort of 200 securely matched production painter identities, excluding Otto Dix and all 1000 painters from the five previous batches. Unavailable indexes are reported explicitly. This is source coverage, not a catalogue raisonne or claim to every artwork worldwide.',
             'date_policy':'Creation after 1970 excluded. Unknown dates retained as review metadata, not invented or automatically eligible. Undated images deferred until creation evidence.',
             'image_policy':'Exact WikiArt per-image rights labels retained; restricted labels do not imply an independent licence. Full supplied frame; application derivatives <=100000 bytes. Original images and recovery snapshots archived outside Documents.',
             'preservation':'New records remain review. Existing images, catalogue metadata, accepted holdings, display claims and publication state preserved. No local database writes.'}
    for filename,values in [('painters.csv',rows),('source-dispositions.csv',source_rows)]:
        fields=list(dict.fromkeys(k for value in values for k in value));temp=RUN/(filename+'.partial')
        with temp.open('w',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader();writer.writerows(values)
        temp.replace(RUN/filename)
    temp=RUN/'summary.partial';temp.write_text(json.dumps(summary,ensure_ascii=False,indent=2));temp.replace(RUN/'summary.json')
    table=''.join('<tr>'+''.join('<td>'+html.escape(str(x.get(key,'')))+'</td>' for key in ['artist','status','source_entries','created','images_added','source_holds','undated_image_holds'])+'</tr>' for x in rows)
    page='<!doctype html><meta charset="utf-8"><title>Random 200 painter production research</title><style>body{font:15px system-ui;max-width:1300px;margin:40px auto;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f3f3f3;position:sticky;top:0}p{line-height:1.5}</style><h1>Random 200-painter production research</h1><p>Updated '+html.escape(summary['at'])+'</p><p>'+html.escape(summary['scope'])+'</p><p>'+html.escape(summary['date_policy'])+'</p><p>'+html.escape(summary['image_policy'])+'</p><p>'+html.escape(summary['preservation'])+'</p><p><a href="painters.csv">Per-painter CSV</a> · <a href="source-dispositions.csv">Every source disposition</a> · <a href="selected-200-painters.csv">Frozen random cohort</a> · <a href="summary.json">Summary JSON</a></p><p>'+html.escape(json.dumps(totals))+'</p><table><thead><tr><th>Painter</th><th>Status</th><th>Source entries</th><th>New records</th><th>Images added</th><th>Source holds</th><th>Undated image holds</th></tr></thead><tbody>'+table+'</tbody></table>'
    temp=RUN/'report.partial';temp.write_text(page);temp.replace(RUN/'report.html')
    print(json.dumps({'complete':summary['complete'],'statuses':summary['statuses'],'totals':totals}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','audits','sheets','delivery_plans','upload','apply','verify','report']);args=parser.parse_args();globals()[args.phase]()
