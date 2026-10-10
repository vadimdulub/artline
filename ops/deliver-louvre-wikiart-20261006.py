#!/usr/bin/env python3
"""User-authorized Louvre image enrichment, with WikiArt metadata precedence.

Select identities before image download. Production-only guarded attachment;
preserve existing images, source evidence, catalogue review status and holdings.
"""
import argparse
import base64
import collections
import concurrent.futures
import gzip
import hashlib
import html
import importlib.util
import io
import json
import os
import re
import time
import textwrap
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageDraw, ImageFont
from psycopg.types.json import Jsonb
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

research=module('louvre_research','research-louvre-wikiart-20261006.py')
r=research.r
r.PORT=int(os.environ.get('ARTLINE_LOUVRE_PROXY_PORT','55467'))
core=module('image_core','enrich-artwork-images.py')
wiki=module('wikiart','wikiart-selected-images.py')
RUN=r.RUN/'delivery-20261006'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/louvre-wikiart-20261006'
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images/louvre-wikiart-20261006'
OP='louvre-wikiart-20261006'
ACTOR='local-european-research'


def ident(x):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+x))
def source_key(url):return re.sub(r'^/(en|fr|ru|de|es|pt|uk|zh)/','/',urlparse(url).path)
def load_records():return r.load(r.RUN/'artwork-image-results.json')
def snapshot_records():return {x['artwork']['id']:x for x in r.load(r.RUN/'production-artworks.json.gz')}


def source_date(candidate):
    page=r.load(ROOT/candidate['page_evidence'])
    for line in page['object_info']:
        if line.startswith('Date:'):
            # WikiArt's JSON year omits circa qualifiers present on the page.
            return line.split(':',1)[1].split(';',1)[0].strip()
    return candidate.get('source_date')


def valid_date(record,candidate):
    date=wiki.creation_date(source_date(candidate))
    if date:return date if date['creation_year_end']<=1970 else None
    w=record['artwork']
    if w['creation_year_start'] is not None and w['creation_year_end'] is not None and w['creation_year_end']<=1970:
        return {k:w[k]for k in ('creation_year_start','creation_year_end','date_display','date_precision')}
    return None


def safety_reason(record,candidate):
    if not candidate.get('image_url') or not candidate.get('source_public_domain_label'):return 'No explicit usable source image/rights label'
    if not valid_date(record,candidate):return 'Creation date unknown or outside cutoff'
    a=research.norm(record['artwork']['title']);b=research.norm(candidate['source_title'])
    partial={'detail','details','study','sketch','copy','copie','esquisse','etude','fragment','panel','panneau','central','wing','volet'}
    aa=set(a.split())&partial;bb=set(b.split())&partial
    if bool(aa)!=bool(bb):return 'Full work versus detail/study/copy/component differs'
    if any('Qualified catalogue' in f or 'identifier changed' in f or 'creator differs' in f for f in candidate['review_flags']):return 'Qualified or changed creator/object identity'
    return None


def select():
    originals=snapshot_records();records=load_records();selected=[];held=[]
    overrides=r.load(RUN/'manual-review.json') if (RUN/'manual-review.json').exists() else {}
    if (RUN/'visual-review-corrections.json').exists():overrides.update(r.load(RUN/'visual-review-corrections.json'))
    object_review=r.load(RUN/'final-object-review.json') if (RUN/'final-object-review.json').exists() else {}
    overrides.update({k:v for k,v in object_review.items()if v.get('source_id')})
    for x in records:
        aid=x['artwork_id'];w=originals[aid]
        if x['existing_image']:held.append({'artwork_id':aid,'reason':'Existing image preserved'});continue
        if object_review.get(aid,{}).get('hold'):
            held.append({'artwork_id':aid,'title':x['title'],'reason':object_review[aid]['reason']});continue
        choices=[]
        override=overrides.get(aid)
        for c in x['candidates']:
            reason=safety_reason(w,c)
            if reason:continue
            if override:
                if override.get('source_id')==c['source_id']:choices.append((100,c,override['reason']))
                continue
            if c.get('basis')=='identifier_crosswalk':choices.append((90,c,'Exact catalogue object identifier cross-reference to WikiArt'));continue
            location=c.get('source_location')or''
            if location and 'louvre' not in location.casefold():continue
            if x['artist_match_basis']=='name_variant_candidate':continue
            score=c.get('page_title_score',0)
            if score>=.97:
                # Semicolons often separate historical title aliases, but a
                # multi-object or multi-panel entry needs explicit review.
                title=x['title'].lower()
                if ';' in title and not re.search(r';\s*(?:dit|dite|ou)\b',title):continue
                choices.append((80 if 'louvre' in location.casefold() else 70,c,'Same artist and exact title/identifier-backed title alias; WikiArt date takes precedence'))
        # Multiple language pages with the same WikiArt id are one source work.
        bysource={}
        for value in sorted(choices,key=lambda q:-q[0]):bysource.setdefault(value[1]['source_id'],value)
        choices=list(bysource.values())
        if len(choices)>1:
            best=[v for v in choices if v[0]==max(q[0]for q in choices)]
            if len(best)==1:choices=best
        if len(choices)!=1:
            held.append({'artwork_id':aid,'title':x['title'],'reason':'Ambiguous source identity' if choices else 'No securely matched eligible image yet','prior_outcome':x['outcome']});continue
        _,c,reason=choices[0]
        date=valid_date(w,c)
        selected.append({'artwork_id':aid,'title':x['title'],'artist':c['source_artist'],'candidate':c,'dates':date,
          'wikiart_date_used':bool(wiki.creation_date(source_date(c))),'displayed_source_date':source_date(c),'identity_reason':reason,
          'object_review':object_review.get(aid),
          'date_changes':{k:{'before':w['artwork'][k],'after':v}for k,v in date.items()if w['artwork'][k]!=v}})
    value={'at':r.now(),'operation':OP,'source_precedence':'WikiArt — explicit user instruction 6 October 2026',
      'selected':selected,'held':held}
    digest=core.sha(core.encode({'selected':selected,'held':held}))[:16]
    path=RUN/'selections'/(digest+'.json');r.save(path,value)
    (RUN/'selection-pointer.txt').write_text(str(path))
    print(json.dumps({'selection':str(path),'selected':len(selected),'date_updates':sum(bool(x['date_changes'])for x in selected),'held':len(held)},ensure_ascii=False),flush=True)


def selection():return r.load(Path((RUN/'selection-pointer.txt').read_text()))


def audit_holds():
    selected={x['artwork_id']for x in selection()['selected']};n=0
    for x in load_records():
        if x['existing_image'] or x['artwork_id']in selected or not x['candidates']:continue
        c=x['candidates'][0]
        if c.get('source_location') and 'louvre'not in c['source_location'].lower():continue
        n+=1
        print(f"{n:03d} {x['artwork_id']} | {x['creator_labels'][0] if x['creator_labels'] else ''} | {x['title']} => {c['source_title']} [{c['source_date']}; {c.get('source_location') or '?'}]",flush=True)


def prepare():
    items={x['candidate']['source_id']:x for x in selection()['selected']}
    def one(item):
        c=item['candidate'];sid=c['source_id'];dest=RUN/'prepared'/(sid+'.json')
        if dest.exists():return r.load(dest)
        page=r.load(ROOT/c['page_evidence'])
        assert page['metadata']['_id']==sid and page['public_domain_label']
        assert core.sha(gzip.decompress((ROOT/page['receipt']['body_path']).read_bytes()))==page['receipt']['sha256']
        urls=list(dict.fromkeys([c['image_url'],page.get('displayed_image_url')]))
        errors=[]
        for url in urls:
            if not url:continue
            assert urlparse(url).scheme=='https' and re.fullmatch(r'uploads\d*\.wikiart\.org',urlparse(url).hostname or '')
            key=core.sha(url.encode());source=ORIGINALS/(key+'.image');rcpath=RUN/'downloads'/(key+'.json')
            try:
                if source.exists():
                    body=source.read_bytes();receipt=r.load(rcpath);assert core.sha(body)==receipt['sha256']
                else:
                    with requests.get(url,headers={'User-Agent':r.UA},stream=True,timeout=(15,45))as response:
                        if response.status_code in (403,429):raise RuntimeError('WikiArt requested a pause: '+str(response.status_code))
                        response.raise_for_status();assert response.headers.get('content-type','').startswith('image/')
                        data=bytearray()
                        for chunk in response.iter_content(65536):
                            data.extend(chunk)
                            if len(data)>8_000_000:raise ValueError('Selected source image exceeds 8 MB budget')
                        body=bytes(data)
                        receipt={'url':url,'final_url':response.url,'checked_at':r.now(),'bytes':len(body),'sha256':core.sha(body),'content_type':response.headers.get('content-type')}
                    r.save(source,body);r.save(rcpath,receipt)
                compressed,width,height,quality=core.compress(body)
                assert max(width,height)>=150 and min(width,height)>=32
                checksum=core.sha(compressed);path='/assets/artworks/wikiart-louvre-20261006/'+sid+'-'+checksum[:16]+'.jpg'
                r.save(ROOT/'apps/web/public'/path.lstrip('/'),compressed)
                image={'source_id':sid,'page':c['url'],'source_image_url':url,'title':c['source_title'],'artist':c['source_artist'],
                  'source_date':c['source_date'],'media_id':ident('media/'+sid+'/'+checksum),'path':path,'sha256':checksum,'bytes':len(compressed),
                  'width':width,'height':height,'jpeg_quality':quality,'rights_status':'public_domain','license_label':page['rights_label'],
                  'policy_url':'https://www.wikiart.org/en/terms-of-use','page_receipt':page['receipt'],'download':receipt,
                  'source_metadata':page['metadata'],'source_object_info':page['object_info'],
                  'attribution_text':c['source_artist']+'. '+c['source_title']+'. Image: WikiArt. '+page['rights_label']+'. Full-frame proportional resize and JPEG compression; no crop.',
                  'transform':'Full-frame proportional resize and JPEG compression; no crop'}
                r.save(dest,image);return image
            except (requests.RequestException,ValueError,AssertionError)as error:errors.append(str(error)[:250])
        r.save(RUN/'prepare-held'/(sid+'.json'),{'source_id':sid,'errors':errors});return {'error':errors}
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for i,value in enumerate(pool.map(one,items.values()),1):
            counts['prepared' if 'media_id'in value else 'held']+=1
            if i%20==0:print('Selected image preparation',i,'of',len(items),dict(counts),flush=True)
    print('Preparation finished',dict(counts),flush=True)


def sheets():
    items=selection()['selected'];dest=Path('/tmp/artline-louvre-wikiart-qa');dest.mkdir(exist_ok=True)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',12)
    labels=[]
    for start in range(0,len(items),36):
        sheet=Image.new('RGB',(1200,1380),'#f1f1ed');draw=ImageDraw.Draw(sheet)
        for offset,item in enumerate(items[start:start+36]):
            im=r.load(RUN/'prepared'/(item['candidate']['source_id']+'.json'))
            with Image.open(ROOT/'apps/web/public'/im['path'].lstrip('/'))as opened:
                thumb=opened.copy();thumb.thumbnail((190,169))
                x=(offset%6)*200+(200-thumb.width)//2;y=(offset//6)*230
                sheet.paste(thumb,(x,y+(170-thumb.height)//2))
            label=f"{start+offset+1}. {item['title']}"
            for line_no,line in enumerate(textwrap.wrap(label,width=28)[:3]):draw.text(((offset%6)*200+5,(offset//6)*230+174+line_no*15),line,font=font,fill='#18282a')
            labels.append({'number':start+offset+1,'artwork_id':item['artwork_id'],'title':item['title'],'source_title':im['title'],'source_id':im['source_id']})
        path=dest/f'{start//36+1:02d}.jpg';sheet.save(path,quality=90)
    (dest/'index.json').write_text(json.dumps(labels,ensure_ascii=False,indent=2))
    print('QA sheets',len(list(dest.glob('*.jpg'))),dest,flush=True)


def live_records(db,ids):
    rows=db.execute('''SELECT to_jsonb(a) artwork,
      COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creators,
      COALESCE((SELECT jsonb_agg(to_jsonb(am) ORDER BY am.media_id) FROM artwork_media am WHERE am.artwork_id=a.id),'[]') attachments,
      COALESCE((SELECT jsonb_agg(to_jsonb(c) ORDER BY c.id) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id),'[]') citations
      FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()
    return {x['artwork']['id']:x for x in rows}


def plan():
    chosen=selection();items=chosen['selected'];ids=[x['artwork_id']for x in items];original=snapshot_records()
    ready=[];held=[]
    with r.connect('production')as db:
        current=live_records(db,ids)
        assert db.execute('SELECT current_database()name').fetchone()['name']=='artline'
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s',(ACTOR,)).fetchone()
        louvre=str(db.execute("SELECT id FROM institutions WHERE slug='musee-du-louvre'").fetchone()['id'])
        for item in items:
            aid=item['artwork_id'];row=current.get(aid)
            if not row or row['artwork']!=original[aid]['artwork']:
                held.append({'artwork_id':aid,'reason':'Production record changed since research snapshot'});continue
            assert row['artwork']['status']=='review' and not row['artwork']['primary_media_id'] and row['artwork']['current_institution_id']==louvre
            ipath=RUN/'prepared'/(item['candidate']['source_id']+'.json')
            if not ipath.exists():held.append({'artwork_id':aid,'reason':'Image preparation incomplete'});continue
            im=r.load(ipath);body=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
            assert len(body)==im['bytes']<=100000 and core.sha(body)==im['sha256']
            ready.append(item)
    value={'operation':OP,'target':'production','selected':ready,'held':held,
      'before':{x['artwork_id']:current[x['artwork_id']]for x in ready},'selection_path':(RUN/'selection-pointer.txt').read_text()}
    digest=core.sha(core.encode(value))
    path=RUN/'plans'/(digest+'.json');r.save(path,value)
    r.save_gz(BACKUP/(digest+'-before.json.gz'),value)
    (RUN/'plan-pointer.txt').write_text(str(path))
    print(json.dumps({'ready':len(ready),'held':held,'plan_sha256':digest,'backup':str(BACKUP/(digest+'-before.json.gz'))}),flush=True)


def load_plan():return r.load(Path((RUN/'plan-pointer.txt').read_text()))


def upload():
    plan=load_plan();items={x['candidate']['source_id']:x for x in plan['selected']}
    bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    for i,sid in enumerate(items,1):
        dest=RUN/'uploaded'/(sid+'.json')
        if dest.exists():continue
        im=r.load(RUN/'prepared'/(sid+'.json'));body=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        assert len(body)==im['bytes']<=100000 and core.sha(body)==im['sha256']
        blob=bucket.blob(im['path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'provider':'WikiArt','source-record-id':sid,'operation':OP}
        blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(body,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(body) and blob.md5_hash==base64.b64encode(hashlib.md5(body).digest()).decode()
        r.save(dest,{'source_id':sid,'path':im['path'],'bytes':len(body),'sha256':im['sha256'],'generation':blob.generation,'at':r.now()})
        if i%25==0:print('Uploaded selected images',i,'of',len(items),flush=True)
    print('Uploads finished',len(items),flush=True)


def apply():
    plan=load_plan();digest=core.sha(core.encode(plan));backup=BACKUP/(digest+'-before.json.gz')
    assert r.load(backup)==plan
    counts=collections.Counter()
    with r.connect('production',readonly=False)as db:
        for item in plan['selected']:
            aid=item['artwork_id'];dest=RUN/'applied'/(aid+'.json');im=r.load(RUN/'prepared'/(item['candidate']['source_id']+'.json'))
            upload=r.load(RUN/'uploaded'/(im['source_id']+'.json'));assert upload['sha256']==im['sha256']
            if dest.exists():counts['already_recorded']+=1;continue
            before=plan['before'][aid]
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='3s'")
                db.execute('SELECT pg_advisory_xact_lock(202610061)')
                db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(aid,))
                current=live_records(db,[aid])[aid]
                if current['artwork']['primary_media_id']==im['media_id']:
                    assert db.execute('SELECT 1 FROM citations WHERE id=%s',(ident('image/'+aid),)).fetchone()
                    after=current;outcome='already_applied'
                else:
                    assert current==before,'Catalogue record changed after pinned backup: '+aid
                    source=db.execute("""INSERT INTO sources(id,slug,name,source_type,base_url)
                      VALUES(%s,%s,'WikiArt Louvre image and date reconciliation','collection_page','https://www.wikiart.org/')
                      ON CONFLICT(slug) DO UPDATE SET slug=EXCLUDED.slug RETURNING id""",(ident('source'),OP)).fetchone()['id']
                    db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,
                      checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
                      VALUES(%s,'local',%s,%s,'WikiArt','image/jpeg',%s,%s,%s,%s,%s,'public_domain',%s,%s,%s,%s,%s,%s,%s)
                      ON CONFLICT(id) DO NOTHING''',(im['media_id'],im['path'],im['page'],im['width'],im['height'],im['bytes'],im['sha256'],im['title']+' — '+im['artist'],im['license_label'],im['policy_url'],im['artist']+'; WikiArt',im['attribution_text'],im['download']['checked_at'],im['page_receipt']['retrieved_at'],ACTOR))
                    media=db.execute('SELECT to_jsonb(m)row FROM media_assets m WHERE id=%s',(im['media_id'],)).fetchone()['row']
                    assert media['storage_path']==im['path'] and media['checksum_sha256']==im['sha256'] and media['rights_status']=='public_domain'
                    db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(media_id) DO NOTHING''',
                      (im['media_id'],source,im['source_id'],im['page_receipt']['sha256'],im['source_image_url'],im['policy_url'],
                       'Explicit WikiArt per-artwork public-domain label preserved as supplied; user selected WikiArt as source of truth. No independent licensing assessment.',OP,im['page_receipt']['retrieved_at'],Jsonb(im)))
                    db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label)VALUES(%s,%s,0,%s)ON CONFLICT DO NOTHING',(aid,im['media_id'],'Full composition'))
                    date=item['dates']
                    db.execute('''UPDATE artworks SET primary_media_id=%s,creation_year_start=%s,creation_year_end=%s,date_display=%s,date_precision=%s,
                      revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL''',
                      (im['media_id'],date['creation_year_start'],date['creation_year_end'],date['date_display'],date['date_precision'],ACTOR,aid))
                    note={'operation':OP,'user_instruction':'WikiArt is the source of truth; add as many supported images as possible.',
                      'identity_reason':item['identity_reason'],'source_title':im['title'],'source_artist':im['artist'],'source_year':im['source_date'],
                      'displayed_source_date':item['displayed_source_date'],
                      'object_review':item.get('object_review'),
                      'source_location_label':item['candidate'].get('source_location'),'date_changes':item['date_changes'],'plan_sha256':digest,
                      'backup_path':str(backup),'review_status_preserved':True,'no_current_display_claim':True}
                    for field in ['image_identity']+(['creation_date']if item['date_changes']else[]):
                        db.execute('''INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                          VALUES(%s,'artwork',%s,%s,%s,%s,%s,%s,%s,%s)''',
                          (ident(('image/'if field=='image_identity'else'date/')+aid),aid,field,source,im['source_id'],im['page'],json.dumps(note,ensure_ascii=False),im['page_receipt']['retrieved_at'],ACTOR))
                    after=live_records(db,[aid])[aid]
                    allowed={'primary_media_id','creation_year_start','creation_year_end','date_display','date_precision','revision','updated_at','updated_by'}
                    assert {k:v for k,v in after['artwork'].items()if k not in allowed}=={k:v for k,v in before['artwork'].items()if k not in allowed}
                    assert after['artwork']['status']=='review' and after['creators']==before['creators']
                    outcome='attached'
            r.save_gz(BACKUP/'after'/(aid+'.json.gz'),after)
            r.save(dest,{'artwork_id':aid,'outcome':outcome,'media_id':im['media_id'],'source_id':im['source_id'],'at':r.now(),'date_changes':item['date_changes'],'plan_sha256':digest})
            counts[outcome]+=1
            if sum(counts.values())%25==0:print('Production attachments',dict(counts),flush=True)
    print('Production delivery complete',dict(counts),flush=True)


def verify_assets():
    items=load_plan()['selected']
    prepared={x['candidate']['source_id']:r.load(RUN/'prepared'/(x['candidate']['source_id']+'.json'))for x in items}
    def asset(im):
        dest=RUN/'public-image-checks'/(im['source_id']+'.json')
        if dest.exists():return r.load(dest)
        url='https://artlines.org'+im['path']
        for attempt in range(3):
            try:
                response=requests.get(url,timeout=(15,45));response.raise_for_status()
                assert response.headers.get('content-type','').startswith('image/jpeg')
                assert len(response.content)==im['bytes'] and core.sha(response.content)==im['sha256']
                with Image.open(io.BytesIO(response.content))as opened:assert opened.size==(im['width'],im['height'])
                result={'url':url,'status':response.status_code,'sha256':im['sha256'],'bytes':len(response.content),'at':r.now()}
                r.save(dest,result);return result
            except requests.RequestException:
                if attempt==2:raise
                time.sleep(1+attempt)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6)as pool:
        checked=[]
        for i,value in enumerate(pool.map(asset,prepared.values()),1):
            checked.append(value)
            if i%50==0:print('Public image delivery verified',i,'of',len(prepared),flush=True)
    print('Public image verification complete',len(checked),flush=True)
    return checked


def verify():
    plan=load_plan();items=plan['selected'];ids=[x['artwork_id']for x in items]
    prepared={x['candidate']['source_id']:r.load(RUN/'prepared'/(x['candidate']['source_id']+'.json'))for x in items}
    media_ids=[x['media_id']for x in prepared.values()]
    allowed={'primary_media_id','creation_year_start','creation_year_end','date_display','date_precision','revision','updated_at','updated_by'}
    with r.connect('production')as db:
        current=live_records(db,ids)
        media={str(x['id']):x for x in db.execute('SELECT * FROM media_assets WHERE id=ANY(%s::uuid[])',(media_ids,)).fetchall()}
        rights={str(x['media_id']):x for x in db.execute('SELECT * FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',(media_ids,)).fetchall()}
        audits=db.execute("SELECT entity_id,before_json,after_json FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND after_json->>'primary_media_id'=ANY(%s::text[])",(ids,media_ids)).fetchall()
        audited={str(x['entity_id'])for x in audits if x['before_json']==plan['before'][str(x['entity_id'])]['artwork'] and x['after_json']==current[str(x['entity_id'])]['artwork']}
        for item in items:
            aid=item['artwork_id'];before=plan['before'][aid];after=current[aid];im=prepared[item['candidate']['source_id']]
            assert after['artwork']['primary_media_id']==im['media_id']
            assert after['artwork']['status']=='review' and after['artwork']['published_at']==before['artwork']['published_at']
            assert {k:v for k,v in after['artwork'].items()if k not in allowed}=={k:v for k,v in before['artwork'].items()if k not in allowed}
            assert after['artwork']['revision']==before['artwork']['revision']+1 and after['creators']==before['creators']
            assert all(after['artwork'][k]==v for k,v in item['dates'].items())
            assert all(x in after['citations']for x in before['citations'])
            assert all(x in after['attachments']for x in before['attachments'])
            assert any(x['media_id']==im['media_id']for x in after['attachments'])
            for field in ['image_identity']+(['creation_date']if item['date_changes']else[]):
                assert any(x['id']==ident(('image/'if field=='image_identity'else'date/')+aid) and x['source_record_id']==im['source_id'] and x['source_url']==im['page']for x in after['citations'])
            m=media[im['media_id']];e=rights[im['media_id']]
            assert m['storage_path']==im['path'] and m['checksum_sha256']==im['sha256'] and m['byte_size']==im['bytes']<=100000
            assert m['rights_status']=='public_domain' and e['evidence_json']==im
            assert aid in audited and r.load(BACKUP/'after'/(aid+'.json.gz'))==after
        louvre=str(next(iter(current.values()))['artwork']['current_institution_id'])
        totals=db.execute('SELECT count(*) artworks,count(primary_media_id) with_images FROM artworks WHERE current_institution_id=%s',(louvre,)).fetchone()
    print('Production database verified',len(items),'records; checking',len(prepared),'public image URLs',flush=True)
    checked=verify_assets()
    samples=items[::max(1,len(items)//10)][:10]
    def api_check(item):
        url='https://artlines.org/api/backend/v1/museums/musee-du-louvre/works/'+item['artwork_id']
        response=requests.get(url,timeout=(15,45));response.raise_for_status();body=response.json()
        im=prepared[item['candidate']['source_id']]
        assert body['id']==item['artwork_id'] and body['title']==item['title'] and body['media_url']==im['path']
        assert all(body[k]==v for k,v in item['dates'].items())
        return {'url':url,'artwork_id':item['artwork_id'],'status':response.status_code,'image_url':im['path'],'dates':item['dates'],'at':r.now()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:api=list(pool.map(api_check,samples))
    r.save(RUN/'production-api-checks.json',api)
    summary={'operation':OP,'verified_at':r.now(),'target':'production','artworks_updated':len(items),'unique_images':len(prepared),
      'date_metadata_updated':sum(bool(x['date_changes'])for x in items),
      'year_bounds_updated':sum(any(k in x['date_changes']for k in ['creation_year_start','creation_year_end'])for x in items),
      'previously_unknown_years_filled':sum(plan['before'][x['artwork_id']]['artwork']['creation_year_start']is None and x['dates']['creation_year_start']is not None for x in items),
      'review_status_preserved':len(items),'audited_records':len(audited),'public_images_verified':len(checked),
      'live_api_records_verified':len(api),
      'largest_image_bytes':max(x['bytes']for x in prepared.values()),'image_bytes':sum(x['bytes']for x in prepared.values()),
      'louvre_totals':totals,'remaining_without_images':totals['artworks']-totals['with_images'],
      'plan_sha256':core.sha(core.encode(plan)),'backup_directory':str(BACKUP),'production_plan_holds':plan['held']}
    r.save(RUN/'verification.json',summary)
    esc=html.escape;rows=[]
    for item in items:
        im=prepared[item['candidate']['source_id']];aid=item['artwork_id'];old=plan['before'][aid]['artwork']['date_display']or'Unknown'
        rows.append('<tr><td>'+esc(item['title'])+'<br><small>'+aid+'</small></td><td>'+esc(item['artist'])+'</td><td>'+esc(old)+' → '+esc(item['dates']['date_display']or'Unknown')+'</td><td><a href="'+esc(im['page'],quote=True)+'">WikiArt</a> · <a href="https://artlines.org'+esc(im['path'],quote=True)+'">Image</a></td></tr>')
    report='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Louvre WikiArt production delivery</title><style>body{max-width:1400px;margin:40px auto;padding:0 24px;font:16px/1.5 system-ui;color:#142728;background:#f8f7f2}table{border-collapse:collapse;width:100%}td,th{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #ccc}small{font-size:10px}a{color:#006766}</style><h1>Louvre WikiArt production delivery</h1><p>Verified '+esc(summary['verified_at'])+'. '+str(len(items))+' records received '+str(len(prepared))+' distinct WikiArt images. All records remain in review. Existing images, creators, holdings and publication status were preserved.</p><p>'+str(summary['date_metadata_updated'])+' date labels/precision/ranges updated from the displayed WikiArt dates; '+str(summary['year_bounds_updated'])+' changed numeric year bounds, including '+str(summary['previously_unknown_years_filled'])+' previously unknown dates. Source receipts, rights labels, before/after backups and database audit history retained.</p><p>Every new image URL returned the expected JPEG bytes and SHA-256 checksum. Images are at most 100,000 bytes; full-frame resize and JPEG compression only.</p><table><thead><tr><th>Catalogue record</th><th>Artist</th><th>Date before → after</th><th>Evidence and image</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></html>'
    r.save(RUN/'report.html',report.encode())
    print(json.dumps(summary,ensure_ascii=False),flush=True)


def report_md():
    v=r.load(RUN/'verification.json');p=load_plan()
    assert v['artworks_updated']==len(p['selected']) and v['plan_sha256']==core.sha(core.encode(p))
    corrected=v['year_bounds_updated']-v['previously_unknown_years_filled']
    labels=v['date_metadata_updated']-v['year_bounds_updated']
    previous=v['louvre_totals']['with_images']-v['artworks_updated']
    body=textwrap.dedent(f'''\
    # Louvre WikiArt images — 6 October 2026

    Verified production delivery at {v['verified_at']}.

    - Added images to **{v['artworks_updated']} existing Louvre records**, using **{v['unique_images']} distinct WikiArt images**.
    - Preserved the {previous} existing primary images. The Louvre catalogue now has **{v['louvre_totals']['with_images']} of {v['louvre_totals']['artworks']} records with images**.
    - Reconciled date metadata on {v['date_metadata_updated']} records: {v['previously_unknown_years_filled']} previously unknown numeric dates filled, {corrected} existing numeric dates/ranges corrected, and {labels} changes to date labels or precision only.
    - All {v['review_status_preserved']} updated records remain in review. Creators, titles, museum holdings, display assertions and publication state were preserved.
    - {v['remaining_without_images']} records still lack a securely matched image. The final object review held 28 provisional selections because of unresolved versions, studies or dimension discrepancies.

    The user instructed: “wiki art is the source of truth” and “go ahead and add as much as possible.” The policy is recorded in [AGENTS.md](../../../AGENTS.md) and [Artline image use](../../ARTLINE_IMAGE_USE.md). Explicit WikiArt dates take precedence once the same object is identified; displayed circa qualifiers and unknown fields are retained. A shared title alone does not establish the same version.

    Every selected source has its WikiArt page, image URL, rights label and attribution retained. Originals are archived separately. Derivatives preserve the complete supplied frame and are at most 100,000 bytes; the largest delivered file is {v['largest_image_bytes']:,} bytes. WikiArt's public-domain label records its assertion, not an independently obtained licence.

    Verification covered all {v['artworks_updated']} database changes, field-level source citations, rights evidence, automatic audit history and before/after backups. All {v['public_images_verified']} public image URLs returned HTTP 200 with the expected JPEG bytes and SHA-256 checksum. {v['live_api_records_verified']} sampled production artwork API responses returned the expected image and dates.

    ## Delivery evidence

    - [All attached records, source pages and images](delivery-20261006/report.html)
    - [Production verification](delivery-20261006/verification.json)
    - [Pinned production plan](delivery-20261006/plans/{v['plan_sha256']}.json)
    - [Final object/version decisions](delivery-20261006/final-object-review.json)
    - [343 dimension comparisons and flagged candidates](delivery-20261006/dimension-review.json)
    - [Source date, image and visual checks](delivery-20261006/selected-records-qa.json)
    - [Sampled production API responses](delivery-20261006/production-api-checks.json)

    Backup directory: `{v['backup_directory']}`. Source originals: `{ORIGINALS}`. Per-record before/after snapshots and database audit history preserve the previous values. Catalogue records were not merged or deleted; two independently identified catalogue records share one WikiArt image.

    [The original research report](report.html) is an immutable earlier snapshot. Its match counts precede this user-authorized source-precedence and object-review pass; use the delivery evidence above for the production result.
    ''')
    r.save(r.RUN/'README.md',body.encode())
    print('Markdown delivery report',r.RUN/'README.md',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['select','audit_holds','prepare','sheets','plan','upload','apply','verify_assets','verify','report_md']);args=p.parse_args()
    globals()[args.command]()
