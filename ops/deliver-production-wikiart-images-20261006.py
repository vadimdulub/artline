#!/usr/bin/env python3
"""Prepare and deliver only pinned, visually reviewed production WikiArt matches.

Does not alter the local database, artwork metadata, review state or holdings.
Existing pictures are never replaced. Recovery records live outside Documents.
"""
import argparse
import base64
import collections
import concurrent.futures
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import textwrap
import uuid
from urllib.parse import urlsplit

import psycopg
from psycopg.types.json import Jsonb
import requests
from PIL import Image, ImageDraw, ImageFont
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('research',ROOT/'ops/research-production-wikiart-images-20261006.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q);r=q.r
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
RUN=q.RUN
OP=RUN.name
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
ACTOR='local-european-research'
POLICY='https://www.wikiart.org/en/terms-of-use'


def uid(value):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+value))


def review():
    pointer=r.load(RUN/'latest-review-pass.json');path=ROOT/pointer['path']
    assert r.sha(path.read_bytes())==pointer['sha256']
    return r.load(path),pointer


def snapshots(db,ids):
    rows=db.execute('''SELECT to_jsonb(a) artwork,
      COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY artist_id,attribution_role) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creators,
      COALESCE((SELECT jsonb_agg(to_jsonb(am) ORDER BY media_id) FROM artwork_media am WHERE am.artwork_id=a.id),'[]') attachments
      FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()
    return {x['artwork']['id']:x for x in rows}


def existing_media(db,pages):
    rows=db.execute('''SELECT to_jsonb(m) media,to_jsonb(e) rights FROM media_assets m
      JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.source_page_url=ANY(%s)
      AND m.rights_status='public_domain' AND m.byte_size<=100000 ORDER BY m.id''',(pages,)).fetchall()
    bypage=collections.defaultdict(list)
    for x in rows:bypage[x['media']['source_page_url']].append(x)
    return bypage


def download(url):
    assert urlsplit(url).scheme=='https' and re.fullmatch(r'uploads\d*\.wikiart\.org',urlsplit(url).hostname or '')
    key=r.sha(url.encode());path=ORIGINALS/(key+'.body');receipt=RUN/'image-downloads'/(key+'.json')
    if receipt.exists():
        rc=r.load(receipt);raw=path.read_bytes();assert r.sha(raw)==rc['sha256'];return raw,rc
    with requests.get(url,headers={'User-Agent':r.UA},timeout=(15,45),stream=True) as response:
        response.raise_for_status()
        assert re.fullmatch(r'uploads\d*\.wikiart\.org',urlsplit(response.url).hostname or '')
        assert response.headers.get('Content-Type','').startswith('image/')
        chunks=[];size=0
        for chunk in response.iter_content(65536):
            size+=len(chunk)
            if size>15_000_000:raise ValueError('Selected image exceeds byte budget')
            chunks.append(chunk)
        raw=b''.join(chunks)
        rc={'url':url,'final_url':response.url,'at':r.now(),'bytes':len(raw),'sha256':r.sha(raw),'content_type':response.headers.get('Content-Type')}
    r.save(path,raw);r.save(receipt,rc);return raw,rc


def prepare():
    data,pointer=review();ready=data['ready']
    with r.connect('production') as db:
        media=existing_media(db,[x['page']['url'] for x in ready])
    def one(item):
        w=item['work'];page=item['page'];dest=RUN/'prepared'/(w['id']+'.json')
        if dest.exists():return r.load(dest)
        im={'artwork_id':w['id'],'page':page,'review_outcome':item['review_outcome'],'review_pin':pointer,
            'title':w['title'],'artist':page['metadata']['artistName'],'outcome':'prepared'}
        try:
            reusable=[x for x in media[page['url']] if q.image_key(x['rights']['source_image_url'])==q.image_key(page['image_url'])
                and re.fullmatch(r'/assets/[a-zA-Z0-9/_-]+\.(?:jpg|jpeg|png|webp|avif)',x['media'].get('storage_path') or '')]
            if reusable:
                row=reusable[0];m=row['media']
                response=requests.get('https://artlines.org'+m['storage_path'],timeout=(15,45));response.raise_for_status();raw=response.content
                assert len(raw)==m['byte_size'] and r.sha(raw)==m['checksum_sha256'],'Existing production image differs'
                path=ORIGINALS/(w['id']+'-existing.jpg');r.save(path,raw)
                im.update(reuse=True,media=row,path=m['storage_path'],media_id=m['id'],sha256=m['checksum_sha256'],
                    bytes=m['byte_size'],width=m['width'],height=m['height'],visual_path=str(path))
            else:
                original,rc=download(page['image_url'])
                raw,width,height,quality=core.compress(original)
                if min(width,height)<50 or max(width,height)<200:raise ValueError('Source image too small')
                digest=r.sha(raw);path='/assets/artworks/imported/'+OP+'/'+w['id']+'-'+digest[:16]+'.jpg'
                r.save(ROOT/'apps/web/public'/path.lstrip('/'),raw)
                im.update(reuse=False,path=path,media_id=uid('media/'+digest),sha256=digest,bytes=len(raw),
                    width=width,height=height,jpeg_quality=quality,download=rc,visual_path=str(ROOT/'apps/web/public'/path.lstrip('/')))
            with Image.open(im['visual_path']) as image:
                image.verify()
        except Exception as exc:
            im.update(outcome='preparation_held',error=str(exc)[:400])
        r.save(dest,im);return im
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for n,im in enumerate(pool.map(one,ready),1):
            counts[im['outcome']]+=1
            if im.get('reuse'):counts['reused_production_media']+=1
            if n%20==0:print('Prepared selected images',n,'/',len(ready),dict(counts),flush=True)
    print('Preparation',dict(counts),flush=True)


def contact_sheets():
    data,_=review();items=[]
    for item in data['ready']:
        path=RUN/'prepared'/(item['work']['id']+'.json')
        if path.exists():
            im=r.load(path)
            if im['outcome']=='prepared':items.append(im)
    folder=ORIGINALS/'contact-sheets';folder.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
    for start in range(0,len(items),12):
        group=items[start:start+12];sheet=Image.new('RGB',(1200,1050),'white');draw=ImageDraw.Draw(sheet)
        for n,im in enumerate(group):
            left=(n%4)*300;top=(n//4)*350
            with Image.open(im['visual_path']) as source:
                image=source.convert('RGB');image.thumbnail((280,265))
                sheet.paste(image,(left+(300-image.width)//2,top+(265-image.height)//2))
            label=str(start+n+1)+'. '+im['artwork_id'][:8]+' '+im['artist']+' — '+im['title']
            for row,line in enumerate(textwrap.wrap(label,43)[:4]):draw.text((left+8,top+270+row*17),line,font=font,fill='black')
        path=folder/f'{start//12+1:03d}.jpg'
        sheet.save(path,quality=90)
    r.save(RUN/'contact-sheet-index.json',[{'number':n+1,'artwork_id':im['artwork_id'],'media_sha256':im['sha256'],'title':im['title']} for n,im in enumerate(items)])
    print(json.dumps({'images':len(items),'sheets':(len(items)+11)//12,'folder':str(folder)}),flush=True)


def record_visual_review():
    """Record the completed assistant inspection of all 27 labelled sheets."""
    index=r.load(RUN/'contact-sheet-index.json')
    assert len(index)==324
    rejected={
        97:('primary_rights_conflict','Artist-designed lace frame confirmed by Whitney; the exact primary object page states © artist or artist\'s estate, conflicting with the WikiArt public-domain label. Hold further attachment pending clearance.'),
        189:('technical_capture_border','Source photograph contains a colour calibration strip and damaged outer canvas edges. Hold this reproduction for a cleaner source image.'),
        250:('explicit_reproduction_copyright','The image itself states Copyright © The Andrew Brownsword Art Foundation. Hold despite WikiArt label.'),
        317:('photograph_watermark','The source photograph includes a camera-logo watermark in its lower-right corner; photograph-specific clearance is not established.'),
    }
    raw,rc=r.capture('https://whitney.org/collection/works/2997',tag='primary-visual-followup',timeout=40)
    assert rc['status']==200
    text=q.BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
    assert 'Rights and reproductions' in text and "artist or artist" in text
    approved=[];held=[];archived=[]
    for x in index:
        if x['number'] not in rejected:
            approved.append(x);continue
        reason,note=rejected[x['number']]
        hold={**x,'reason':reason,'note':note}
        if x['number']==97:hold['primary_source_receipt']=rc
        held.append(hold)
        im=r.load(RUN/'prepared'/(x['artwork_id']+'.json'))
        if not im['reuse']:
            src=Path(im['visual_path']);dst=ORIGINALS/'held-derivatives'/src.name
            assert src.parent==ROOT/'apps/web/public/assets/artworks/imported'/OP
            if src.exists():
                assert r.sha(src.read_bytes())==x['media_sha256'];dst.parent.mkdir(parents=True,exist_ok=True)
                assert not dst.exists();src.rename(dst)
            assert r.sha(dst.read_bytes())==x['media_sha256']
            archived.append({'artwork_id':x['artwork_id'],'sha256':x['media_sha256'],'former_path':str(src),'private_path':str(dst)})
    result={'at':r.now(),'contact_index_sha256':r.sha((RUN/'contact-sheet-index.json').read_bytes()),
        'reviewer':'assistant visual inspection','sheets_reviewed':list(range(1,28)),
        'criteria':'Inspected every selected reproduction for visible subject agreement, full composition, advertisements, error images, damage, colour strips and reproduction copyright/watermarks. Metadata identity and rights review are separate pinned checks.',
        'approved':approved,'held':held,'private_archives':archived}
    r.save(RUN/'visual-review.json',result)
    print(json.dumps({'visually_approved':len(approved),'held':held,'private_archives':len(archived)}),flush=True)


def plan():
    data,pointer=review();candidate=q.candidate_pass()
    assert data['candidate_pass']==r.load(RUN/'latest-candidate-pass.json'),'Review must use the current complete candidate pass'
    assert candidate['snapshot_complete'] and candidate['indexes_complete'] and (RUN/'translations-summary.json').exists()
    assert len(candidate['outcomes'])==r.load(RUN/'snapshot.json')['artworks']
    visual=r.load(RUN/'visual-review.json')
    assert visual['contact_index_sha256']==r.sha((RUN/'contact-sheet-index.json').read_bytes())
    approved={x['artwork_id']:x['media_sha256'] for x in visual['approved']}
    ready=[];held=[]
    prepared={}
    for x in data['ready']:
        aid=x['work']['id'];path=RUN/'prepared'/(aid+'.json')
        if not path.exists():held.append({'artwork_id':aid,'reason':'not_prepared'});continue
        im=r.load(path)
        if im['outcome']!='prepared' or approved.get(aid)!=im.get('sha256'):
            held.append({'artwork_id':aid,'reason':'not_visually_approved'});continue
        assert im['page']['metadata']['_id']==x['page']['metadata']['_id']
        assert q.image_key(im['page']['image_url'])==q.image_key(x['page']['image_url'])
        raw=Path(im['visual_path']).read_bytes()
        assert len(raw)==im['bytes']<=100000 and r.sha(raw)==im['sha256']
        prepared[aid]=im;ready.append(x)
    digest_counts=collections.Counter(prepared[x['work']['id']]['sha256'] for x in ready)
    source_counts=collections.Counter(x['page']['metadata']['_id'] for x in ready)
    unique=[]
    for x in ready:
        aid=x['work']['id']
        if digest_counts[prepared[aid]['sha256']]!=1 or source_counts[x['page']['metadata']['_id']]!=1:
            held.append({'artwork_id':aid,'reason':'duplicate_source_object_or_image_pixels'})
        else:unique.append(x)
    ready=[]
    with r.connect('production') as db:
        before=snapshots(db,[x['work']['id'] for x in unique])
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s',(ACTOR,)).fetchone()
        for x in unique:
            aid=x['work']['id'];w=x['work'];current=before.get(aid)
            if not current:held.append({'artwork_id':aid,'reason':'record_disappeared'});continue
            actual=current['artwork'];keys=['title','alternate_title','creation_year_start','creation_year_end','date_precision','status','accession_number','unlinked_creator_label','primary_media_id']
            expected_creators=sorted((c['artist_id'],c['role']) for c in w['creators'])
            actual_creators=sorted((c['artist_id'],c['attribution_role']) for c in current['creators'])
            if any(actual[k]!=w[k] for k in keys) or actual['current_institution_id']!=w['institution_id'] or expected_creators!=actual_creators:
                held.append({'artwork_id':aid,'reason':'production_identity_changed_since_snapshot'});continue
            assert actual['primary_media_id'] is None
            assert not re.search('louvre|prado',x['institution']['name']+' '+x['institution']['slug'],re.I)
            if prepared[aid]['reuse']:
                im=prepared[aid]
                row=db.execute('SELECT to_jsonb(m) media,to_jsonb(e) rights FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=%s',(im['media_id'],)).fetchone()
                assert row==im['media'],'Existing media or rights changed'
            prepared[aid]['attachment_was_present']=any(am['media_id']==prepared[aid]['media_id'] for am in current['attachments'])
            ready.append(x)
    ids=[x['work']['id'] for x in ready]
    result={'operation':OP,'at':r.now(),'review_pin':pointer,'claims':ready,'prepared':{aid:prepared[aid] for aid in ids},
        'preimages':{aid:before[aid] for aid in ids},'held':held,'source_id':uid('source'),
        'visual_review_sha256':r.sha((RUN/'visual-review.json').read_bytes()),
        'policy':'Production only. Fill missing primary images; preserve all artwork metadata, review/publication states, holdings and creators.'}
    assert ready,'No verified images to deliver'
    r.save_gz(RUN/'production-plan.json.gz',result)
    digest=r.sha((RUN/'production-plan.json.gz').read_bytes())
    r.save(RUN/'production-plan-pin.json',{'sha256':digest,'claims':len(ready)})
    r.save_gz(BACKUP/'production-preimages.json.gz',{'plan_sha256':digest,'preimages':result['preimages']})
    r.save_gz(BACKUP/'production-plan.json.gz',result)
    print(json.dumps({'ready':len(ready),'new_images':sum(not prepared[aid]['reuse'] for aid in ids),'reuse_images':sum(prepared[aid]['reuse'] for aid in ids),'held':held,'plan_sha256':digest}),flush=True)


def pinned():
    path=RUN/'production-plan.json.gz';pin=r.load(RUN/'production-plan-pin.json')
    assert r.sha(path.read_bytes())==pin['sha256']
    data=r.load(path)
    assert r.sha((RUN/'visual-review.json').read_bytes())==data['visual_review_sha256']
    assert r.load(BACKUP/'production-preimages.json.gz')['plan_sha256']==pin['sha256']
    return data,pin


def backup():
    description='Before verified WikiArt production museum image update 20261006'
    def gcloud(*args):
        return subprocess.check_output(['gcloud',*args,'--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True)
    rows=json.loads(gcloud('sql','backups','list','--instance=artline-postgres','--limit=40'))
    matching=[x for x in rows if x.get('description')==description]
    if not matching:
        operation=json.loads(gcloud('sql','backups','create','--instance=artline-postgres','--description='+description,'--async'))
        r.save(BACKUP/'cloud-sql-backup-operation.json',operation)
        print('Cloud SQL recovery backup requested',flush=True);return
    current=max(matching,key=lambda x:int(x['id']))
    if current['status']!='SUCCESSFUL':
        print('Cloud SQL backup status',current['status'],flush=True);return
    r.save(BACKUP/'cloud-sql-backup.json',current)
    r.save(RUN/'cloud-sql-backup.json',{'id':current['id'],'status':current['status'],'at':r.now()})
    print('Cloud SQL backup verified',current['id'],flush=True)


def upload():
    data,pin=pinned()
    bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    def one(im):
        dest=RUN/'uploads'/(im['artwork_id']+'.json')
        if dest.exists():return r.load(dest)
        raw=Path(im['visual_path']).read_bytes();assert len(raw)==im['bytes'] and r.sha(raw)==im['sha256']
        if not im['reuse']:
            blob=bucket.blob(im['path'].lstrip('/'))
            blob.metadata={'sha256':im['sha256'],'artwork-id':im['artwork_id'],'provider':'WikiArt','operation':OP}
            blob.cache_control='public,max-age=31536000,immutable'
            try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
            except PreconditionFailed:blob.reload(timeout=30)
            assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=requests.get('https://artlines.org'+im['path'],timeout=(15,45));response.raise_for_status()
        assert r.sha(response.content)==im['sha256'],'Public image delivery differs'
        result={'artwork_id':im['artwork_id'],'at':r.now(),'plan_sha256':pin['sha256'],'path':im['path'],'sha256':im['sha256'],
            'reuse':im['reuse'],'public_http_status':response.status_code,'public_bytes_verified':True}
        r.save(dest,result);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for n,_ in enumerate(pool.map(one,data['prepared'].values()),1):
            if n%25==0:print('Uploaded/verified selected files',n,'/',len(data['prepared']),flush=True)


def apply():
    data,pin=pinned();claims=data['claims'];ids=[x['work']['id'] for x in claims]
    for aid in ids:
        upload_receipt=r.load(RUN/'uploads'/(aid+'.json'))
        assert upload_receipt['plan_sha256']==pin['sha256'] and upload_receipt['public_bytes_verified']
    assert r.load(BACKUP/'cloud-sql-backup.json')['status']=='SUCCESSFUL','Successful Cloud SQL backup required'
    with r.connect('production',readonly=False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('SELECT pg_advisory_xact_lock(202610066)')
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        assert snapshots(db,ids)==data['preimages'],'Catalogue changed after pinned preflight; no changes applied'
        reuse=[im for im in data['prepared'].values() if im['reuse']]
        if reuse:
            db.execute('SELECT id FROM media_assets WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',([im['media_id'] for im in reuse],)).fetchall()
            for im in reuse:
                actual=db.execute('SELECT to_jsonb(m) media,to_jsonb(e) rights FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=%s',(im['media_id'],)).fetchone()
                assert actual==im['media'],'Reused image/rights changed'
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://www.wikiart.org/')",(data['source_id'],OP,'WikiArt verified production museum image matches, 6 October 2026'))
        for n,item in enumerate(claims,1):
            aid=item['work']['id'];im=data['prepared'][aid];page=item['page'];source_id=page['metadata']['_id']
            if not im['reuse']:
                artist=q.html.unescape(page['metadata']['artistName'])
                db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,
                  width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,
                  attribution_text,retrieved_at,verified_at,verified_by)
                  VALUES(%s,'local',%s,%s,'WikiArt','image/jpeg',%s,%s,%s,%s,%s,'public_domain',%s,%s,%s,%s,%s,%s,%s)''',
                  (im['media_id'],im['path'],page['url'],im['width'],im['height'],im['bytes'],im['sha256'],item['work']['title']+' — '+artist,
                   'Public domain (WikiArt per-object label)',POLICY,artist+'; reproduction via WikiArt',
                   artist+'. '+item['work']['title']+'. WikiArt: Public domain. Proportional resize and JPEG compression; no crop.',
                   im['download']['at'],page['receipt']['retrieved_at'],ACTOR))
                db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,
                  policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                  (im['media_id'],data['source_id'],source_id,page['receipt']['sha256'],page['image_url'],POLICY,
                   'Explicit non-territorial WikiArt per-object Public domain label, captured and preserved. No clearance inferred from age; no independent legal determination.',
                   OP,page['receipt']['retrieved_at'],Jsonb({'page':page,'download':im['download'],'identity_review':item['review_outcome'],'plan_sha256':pin['sha256']})))
            attachment=db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s) ON CONFLICT(artwork_id,media_id) DO NOTHING',(aid,im['media_id'],'Full composition'))
            assert attachment.rowcount==int(not im['attachment_was_present'])
            changed=db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],ACTOR,aid))
            assert changed.rowcount==1
            note=json.dumps({'operation':OP,'identity_review':item['review_outcome'],'source_title':page['metadata']['title'],
                'source_artist':page['metadata']['artistName'],'source_dates':page['date'],'source_location':page['fields'].get('Location'),
                'plan_sha256':pin['sha256'],'reuse_existing_media':im['reuse'],
                'scope':'Image identity only. No accepted holding, current display, publication, date or artist change.'},ensure_ascii=False)
            db.execute('''INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
              VALUES(%s,'artwork',%s,'image_identity',%s,%s,%s,%s,%s,%s)''',(uid('citation/'+aid),aid,data['source_id'],source_id,page['url'],note,page['receipt']['retrieved_at'],ACTOR))
            if n%50==0:print('Transaction image attachments',n,'/',len(claims),flush=True)
        after=snapshots(db,ids)
        for aid in ids:
            before=data['preimages'][aid];current=after[aid];allowed={'primary_media_id','revision','updated_at','updated_by'}
            assert {k:v for k,v in before['artwork'].items() if k not in allowed}=={k:v for k,v in current['artwork'].items() if k not in allowed}
            assert current['creators']==before['creators']
            assert current['artwork']['primary_media_id']==data['prepared'][aid]['media_id']
            assert current['artwork']['revision']==before['artwork']['revision']+1
            assert len(current['attachments'])==len(before['attachments'])+int(not data['prepared'][aid]['attachment_was_present'])
    r.save_gz(BACKUP/'production-after.json.gz',{'plan_sha256':pin['sha256'],'records':after})
    r.save(RUN/'production-applied.json',{'at':r.now(),'plan_sha256':pin['sha256'],'attached':len(ids),'artwork_ids':ids,
        'new_media':sum(not im['reuse'] for im in data['prepared'].values()),'reused_media':sum(im['reuse'] for im in data['prepared'].values()),
        'local_database_changed':False,'artwork_metadata_changed':False,'publication_changed':False})
    print('Production image update committed',len(ids),flush=True)


def verify():
    data,pin=pinned();applied=r.load(RUN/'production-applied.json')
    assert applied['plan_sha256']==pin['sha256']
    ids=applied['artwork_ids'];errors=[]
    with r.connect('production') as db:
        after=snapshots(db,ids)
        mids=[im['media_id'] for im in data['prepared'].values()]
        media={x['media']['id']:x for x in db.execute('SELECT to_jsonb(m) media,to_jsonb(e) rights FROM media_assets m LEFT JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])',(mids,)).fetchall()}
        citations=db.execute("SELECT entity_id::text,source_record_id,source_url FROM citations WHERE source_id=%s AND entity_type='artwork' AND field_name='image_identity'",(data['source_id'],)).fetchall()
        assert len(citations)==len(ids)
        for item in data['claims']:
            aid=item['work']['id'];old=data['preimages'][aid];new=after[aid];im=data['prepared'][aid]
            allowed={'primary_media_id','revision','updated_at','updated_by'}
            if {k:v for k,v in old['artwork'].items() if k not in allowed}!={k:v for k,v in new['artwork'].items() if k not in allowed}:errors.append({'artwork_id':aid,'error':'unrelated_artwork_metadata_changed'})
            if new['creators']!=old['creators']:errors.append({'artwork_id':aid,'error':'creator_changed'})
            if new['artwork']['primary_media_id']!=im['media_id']:errors.append({'artwork_id':aid,'error':'wrong_primary_image'})
            m=media[im['media_id']]['media'];rights=media[im['media_id']]['rights']
            if m['storage_path']!=im['path'] or m['checksum_sha256']!=im['sha256'] or m['byte_size']!=im['bytes'] or m['rights_status']!='public_domain' or not rights:errors.append({'artwork_id':aid,'error':'image_or_rights_mismatch'})
            if not any(c['entity_id']==aid and c['source_record_id']==item['page']['metadata']['_id'] and c['source_url']==item['page']['url'] for c in citations):errors.append({'artwork_id':aid,'error':'identity_citation_missing'})
        museums=db.execute('''SELECT i.id::text,i.slug,i.name,count(*) works,count(a.primary_media_id) images FROM institutions i
          JOIN artworks a ON a.current_institution_id=i.id WHERE a.status<>'archived' AND i.id=ANY(%s::uuid[]) GROUP BY i.id ORDER BY i.name''',
          (sorted({x['work']['institution_id'] for x in data['claims']}),)).fetchall()
        exclusions=db.execute("SELECT i.slug,count(a.id) works,count(a.primary_media_id) images FROM institutions i LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived' WHERE i.slug IN ('musee-du-louvre','museo-del-prado') GROUP BY i.slug ORDER BY i.slug").fetchall()
    sample={}
    for item in data['claims']:sample.setdefault(item['institution']['slug'],item)
    selected=list(sample.values())[:20]
    def one(item):
        aid=item['work']['id'];url='https://artlines.org/api/backend/v1/museums/'+item['institution']['slug']+'/works/'+aid
        try:
            response=requests.get(url,timeout=(15,45));body=response.json() if response.status_code==200 else {}
            expected=data['prepared'][aid]['path']
            return {'artwork_id':aid,'url':url,'status':response.status_code,'expected_image':expected,'actual_image':body.get('media_url'),
                'verified':response.status_code==200 and body.get('media_url')==expected and body.get('title')==item['work']['title']}
        except Exception as exc:return {'artwork_id':aid,'url':url,'verified':False,'error':str(exc)[:200]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:api=list(pool.map(one,selected))
    errors.extend({'artwork_id':x['artwork_id'],'error':'live_api_verification_failed','details':x} for x in api if not x['verified'])
    result={'at':r.now(),'plan_sha256':pin['sha256'],'database_images_verified':len(ids),'source_citations_verified':len(citations),
        'public_files_verified_before_attachment':len(ids),'live_api_checks':api,'museums':museums,'excluded_museums':exclusions,'errors':errors,
        'metadata_and_publication_preserved':not any(x['error'] in ['unrelated_artwork_metadata_changed','creator_changed'] for x in errors)}
    r.save(RUN/'production-verification.json',result)
    print(json.dumps({'database_images_verified':len(ids),'museums':len(museums),'api_verified':sum(x['verified'] for x in api),'api_checked':len(api),'errors':errors}),flush=True)
    assert not errors,'Verification failures retained for investigation'


def report():
    data,pin=pinned();applied=r.load(RUN/'production-applied.json');verified=r.load(RUN/'production-verification.json')
    assert not verified['errors']
    candidate=q.candidate_pass();reviewed,_=review();snapshot=r.load(RUN/'snapshot.json')
    review_by_id={x['work']['id']:x for x in reviewed['ready']+reviewed['held']}
    claims={x['work']['id']:x for x in data['claims']}
    visual_holds={x['artwork_id']:x for x in r.load(RUN/'visual-review.json')['held']}
    delivery_holds={x['artwork_id']:x for x in data['held']}
    results=[]
    for row in candidate['outcomes']:
        aid=row['artwork_id'];detail=review_by_id.get(aid)
        out={**row,'production_updated':aid in claims}
        if detail:
            out['review_outcome']=detail['review_outcome']
            page=detail.get('page')
            if page:out.update(wikiart_page=page['url'],verified_source_image=page['image_url'],source_rights_label=page['rights_label'],page_receipt=page['receipt'])
        if aid in claims:
            im=data['prepared'][aid];out.update(media_id=im['media_id'],production_image_url='https://artlines.org'+im['path'])
        if aid in delivery_holds:out['delivery_hold']=delivery_holds[aid]
        if aid in visual_holds:out['visual_hold']=visual_holds[aid]
        results.append(out)
    assert len(results)==snapshot['artworks'] and sum(x['production_updated'] for x in results)==applied['attached']
    r.save_gz(RUN/'all-artwork-results.json.gz',results)
    by_museum=collections.Counter(x['institution']['name'] for x in data['claims'])
    summary={'at':r.now(),'audited_artworks':snapshot['artworks'],'audited_institutions':len(snapshot['museum_counts']),
        'baseline_images':sum(x['images'] for x in snapshot['museum_counts']),
        'baseline_missing_images':sum(x['works']-x['images'] for x in snapshot['museum_counts']),
        'wikiart_artist_indexes':r.load(RUN/'indexes-summary.json'),'translated_indexes':r.load(RUN/'translations-summary.json'),
        'discovery_outcomes':{k:v for k,v in candidate['counts'].items() if k not in ['missing_image','with_existing_image']},'matching_image_candidates':len(candidate['candidates']),
        'missing_image_candidates':len(reviewed['ready'])+len(reviewed['held']),
        'production_images_added':applied['attached'],'new_image_assets':applied['new_media'],'reused_image_assets':applied['reused_media'],
        'updated_institutions':len(by_museum),'images_added_by_museum':dict(by_museum),
        'held_review_reasons':dict(collections.Counter(x['review_outcome'] for x in reviewed['held'])),
        'delivery_holds':data['held'],'visual_holds':list(visual_holds.values()),'excluded_institutions':[x['name'] for x in snapshot['excluded_institutions']],
        'verification':{'database_images':verified['database_images_verified'],'live_api_checks':len(verified['live_api_checks']),'errors':verified['errors']},
        'backup':r.load(RUN/'cloud-sql-backup.json'),'plan_sha256':pin['sha256'],
        'limits':['Unmatched titles/artist identities are unresolved, not proof that WikiArt has no image.',
            'No fuzzy-only, duplicate-version, uncertain-date, restricted-rights or territory-limited matches were applied.',
            'Artworks remain in their existing editorial state. Holdings, dates, creator identities, existing primary images and the local database were preserved.',
            'Confidence gates implement the requested 90% threshold as high-corroboration rules, not a statistically calibrated probability.']}
    r.save(RUN/'summary.json',summary)
    esc=q.html.escape
    rows=[]
    for item in sorted(data['claims'],key=lambda x:(x['institution']['name'],x['work']['title'])):
        w=item['work'];im=data['prepared'][w['id']]
        artline='https://artlines.org/museums/'+item['institution']['slug']+'?work='+w['id']
        rows.append('<tr><td>'+esc(item['institution']['name'])+'</td><td><a href="'+esc(artline,quote=True)+'">'+esc(w['title'])+'</a></td><td>'+esc(q.html.unescape(item['page']['metadata']['artistName']))+'</td><td>'+esc(str(w.get('date_display') or 'Unknown'))+'</td><td><a href="'+esc(item['page']['url'],quote=True)+'">WikiArt</a> · <a href="https://artlines.org'+esc(im['path'],quote=True)+'">Image</a></td></tr>')
    museum_rows=''.join('<tr><td>'+esc(name)+'</td><td>'+str(count)+'</td></tr>' for name,count in by_museum.most_common())
    hold_rows=''.join('<tr><td>'+esc(reason.replace('_',' '))+'</td><td>'+str(count)+'</td></tr>' for reason,count in collections.Counter(x['review_outcome'] for x in reviewed['held']).most_common())
    hold_rows+=''.join('<tr><td>Visual review: '+esc(x['reason'].replace('_',' '))+'</td><td>1</td></tr>' for x in visual_holds.values())
    body='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Production WikiArt image update — 6 October 2026</title>
    <style>body{font:16px/1.5 system-ui,sans-serif;color:#182329;background:#f6f4ed;max-width:1300px;margin:40px auto;padding:0 28px}h1{font-family:Georgia,serif;font-size:38px;line-height:1.15}h2{margin-top:36px}p{max-width:950px}table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px 12px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top}th{background:#203b43;color:white}a{color:#12616d}.stats{font-size:22px;font-weight:650}.muted{color:#586164}details{margin:20px 0}summary{cursor:pointer;font-weight:650}</style>
    <h1>Production WikiArt image update</h1><p class="muted">6 October 2026 · Louvre and Prado excluded</p>'''
    body+='<p class="stats">'+str(applied['attached'])+' images added across '+str(len(by_museum))+' museums.</p>'
    body+='<p>Audited '+format(snapshot['artworks'],',')+' artwork records across '+format(len(snapshot['museum_counts']),',')+' institutions. '+format(summary['baseline_missing_images'],',')+' lacked a primary image. WikiArt matching produced '+format(len(candidate['candidates']),',')+' dated candidates; '+format(summary['missing_image_candidates'],',')+' were for records without images.</p>'
    body+='<p>Updates passed creator, title, date and version checks, source-rights checks, visual review, database preimage checks and live image verification. Existing pictures, editorial status, dates, holdings and creator records were preserved. Confidence is an evidence-based review gate, not a calibrated percentage.</p>'
    body+='<p>Recovery backup: '+str(summary['backup']['id'])+'. '+str(verified['database_images_verified'])+' database image links and '+str(len(verified['live_api_checks']))+' live artwork API responses verified. '+str(applied['new_media'])+' new image files; '+str(applied['reused_media'])+' existing verified image assets reused.</p>'
    body+='<details><summary>Images added by museum</summary><table><tr><th>Museum</th><th>Added</th></tr>'+museum_rows+'</table></details>'
    body+='<details><summary>Why candidates were held</summary><table><tr><th>Reason</th><th>Artworks</th></tr>'+hold_rows+'</table><p>Unresolved artist or title matches do not establish that WikiArt lacks an image. They remain in the complete research results.</p></details>'
    body+='<p><a href="all-artwork-results.json.gz">Complete artwork results (compressed JSON)</a> · <a href="summary.json">Machine-readable summary</a> · <a href="production-verification.json">Verification evidence</a></p>'
    body+='<h2>Updated artworks</h2><table><tr><th>Museum</th><th>Artwork</th><th>Creator</th><th>Date</th><th>Source and image</th></tr>'+''.join(rows)+'</table></html>'
    r.save(RUN/'report.html',body.encode())
    print(json.dumps({'updated':applied['attached'],'museums':len(by_museum),'report':str(RUN/'report.html'),'all_artwork_outcomes':len(results)}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','contact_sheets','record_visual_review','plan','backup','upload','apply','verify','report'])
    args=p.parse_args();globals()[args.command]()
