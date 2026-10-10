#!/usr/bin/env python3
"""Deliver pinned, index-backed metadata and reviewed images to production only."""
import argparse
import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import uuid
from urllib.parse import urlsplit, urljoin

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from PIL import Image, ImageDraw, ImageFont
import requests
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

spec=importlib.util.spec_from_file_location('native',Path(__file__).with_name('source-index-native-20261009.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
m=n.m;RUN=m.RUN;OP=m.OP
spec=importlib.util.spec_from_file_location('image_core',Path(__file__).with_name('enrich-artwork-images.py'))
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
ACTOR='local-european-research'
POLICY={'cleveland':'https://www.clevelandart.org/open-access','chicago':'https://www.artic.edu/open-access/open-access-images','smk':'https://creativecommons.org/publicdomain/mark/1.0/'}
PROVIDER={'cleveland':'Cleveland Museum of Art','chicago':'Art Institute of Chicago','smk':'Statens Museum for Kunst'}
IMAGE_HOSTS={'cleveland':{'openaccess-cdn.clevelandart.org'},'chicago':{'www.artic.edu','artic.edu'},'smk':{'iip.smk.dk'}}


def uid(value):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+value))


def reviews():return m.load(RUN/'native-review.json')['rows']


def prepare_images():
    selected=[r for r in reviews() if r.get('image_candidate')]
    ORIGINALS.mkdir(parents=True,exist_ok=True)
    def one(r):
        aid=r['artwork_id'];dest=RUN/'prepared-images'/(aid+'.json')
        if dest.exists():return m.load(dest)
        source=m.load(m.ROOT/r['native_object_file']);facts=source['facts'];provider=r['provider'];url=facts['image']
        im=dict(artwork_id=aid,provider=provider,title=r['title'],source_url=facts['page'],source_image_url=url)
        try:
            assert r['decision']=='exact_identity' and facts['image_open']
            if (RUN/('image-host-hold-'+provider+'.json')).exists():raise ValueError('Image provider access hold')
            assert urlsplit(url).scheme=='https' and urlsplit(url).hostname in IMAGE_HOSTS[provider]
            original=ORIGINALS/(aid+'.source')
            receipt=ORIGINALS/(aid+'.receipt.json')
            if receipt.exists():
                rc=m.load(receipt);raw=original.read_bytes();assert hashlib.sha256(raw).hexdigest()==rc['sha256']
            else:
                dest_url=url
                for _ in range(4):
                    assert urlsplit(dest_url).hostname in IMAGE_HOSTS[provider] and urlsplit(dest_url).scheme=='https'
                    with requests.get(dest_url,headers={'User-Agent':n.f.UA},timeout=(15,45),stream=True,allow_redirects=False) as response:
                        if response.status_code in (301,302,303,307,308):
                            dest_url=urljoin(dest_url,response.headers['Location']);continue
                        if response.status_code in (401,403,429):
                            m.save(RUN/('image-host-hold-'+provider+'.json'),dict(at=m.now(),url=dest_url,status=response.status_code))
                        response.raise_for_status()
                        assert response.headers.get('Content-Type','').startswith('image/')
                        parts=[];size=0
                        for chunk in response.iter_content(65536):
                            size+=len(chunk)
                            if size>15_000_000:raise ValueError('Selected image exceeds byte budget')
                            parts.append(chunk)
                        raw=b''.join(parts)
                        rc=dict(url=url,final_url=dest_url,at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),content_type=response.headers.get('Content-Type'))
                        original.write_bytes(raw);m.save(receipt,rc);break
                else:raise ValueError('Too many image redirects')
            raw,width,height,quality=core.compress(raw)
            assert min(width,height)>=100 and max(width,height)>=300,'Image too small for a useful reproduction'
            digest=hashlib.sha256(raw).hexdigest()
            path='/assets/artworks/imported/'+OP+'/'+aid+'-'+digest[:16]+'.jpg'
            local=m.ROOT/'apps/web/public'/path.lstrip('/')
            local.parent.mkdir(parents=True,exist_ok=True)
            if local.exists():assert local.read_bytes()==raw
            else:local.write_bytes(raw)
            with Image.open(local) as opened:opened.verify()
            im.update(state='prepared',storage_path=path,path=str(local),sha256=digest,bytes=len(raw),width=width,height=height,
                quality=quality,media_id=uid('media/'+aid+'/'+digest),download=rc,original_path=str(original),image_rights=facts['image_rights'])
        except Exception as exc:
            im.update(state='held',reason=type(exc).__name__+': '+str(exc)[:350])
        m.save(dest,im);return im
    # One sequential stream for each provider; parallelism never hammers one museum.
    def provider_batch(provider):
        rows=[]
        for r in selected:
            if r['provider']!=provider:continue
            rows.append(one(r))
            if len(rows)%20==0:print('Prepared',provider,len(rows),flush=True)
        return rows
    with ThreadPoolExecutor(max_workers=3) as pool:
        all_rows=[x for rows in pool.map(provider_batch,sorted(PROVIDER)) for x in rows]
    m.save(RUN/'image-preparation-summary.json',dict(at=m.now(),counts=dict(Counter(r['state'] for r in all_rows)),selected=len(selected)))
    print('Image preparation',dict(Counter(r['state'] for r in all_rows)),flush=True)


def sheets():
    rows=[m.load(p) for p in sorted((RUN/'prepared-images').glob('*.json')) if m.load(p)['state']=='prepared']
    output=ORIGINALS/'contact-sheets';output.mkdir(parents=True,exist_ok=True)
    try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    except OSError:font=ImageFont.load_default()
    index=[]
    for offset in range(0,len(rows),20):
        subset=rows[offset:offset+20];sheet=Image.new('RGB',(1500,1400),'#eeeeee');draw=ImageDraw.Draw(sheet)
        items=[]
        for j,r in enumerate(subset):
            x=(j%5)*300;y=(j//5)*350
            with Image.open(r['path']) as opened:
                image=opened.convert('RGB');image.thumbnail((285,290),Image.Resampling.LANCZOS)
                sheet.paste(image,(x+(300-image.width)//2,y+(290-image.height)//2))
            label=f'{offset+j+1}. {r["provider"]} {r["artwork_id"][:8]}'
            draw.text((x+5,y+296),label,fill='black',font=font)
            draw.text((x+5,y+316),r['title'][:33],fill='black',font=font)
            items.append(dict(number=offset+j+1,artwork_id=r['artwork_id'],image_sha256=r['sha256'],title=r['title']))
        path=output/f'sheet-{offset//20+1:02d}.jpg';sheet.save(path,quality=90)
        index.append(dict(path=str(path),sha256=m.sha(path),items=items))
    m.save(RUN/'contact-sheet-index.json',dict(at=m.now(),sheets=index,images=len(rows)))
    print('Review sheets',len(index),'images',len(rows),flush=True)


def snapshot(db,ids):
    rows=db.execute('''SELECT a.id::text,to_jsonb(a) artwork,
      COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY artist_id,attribution_role) FROM artwork_artists x WHERE x.artwork_id=a.id),'[]') creators,
      COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY media_id) FROM artwork_media x WHERE x.artwork_id=a.id),'[]') attachments
      FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()
    return {r['id']:r for r in rows}


def make_plan():
    assert not (RUN/'delivery-plan.json.gz').exists(),'Plan already pinned'
    visual=m.load(RUN/'visual-review.json');sheets=m.load(RUN/'contact-sheet-index.json')
    assert visual['contact_index_sha256']==m.sha(RUN/'contact-sheet-index.json')
    reviewed={v['artwork_id']:v for v in visual['decisions']}
    sheet_items={v['artwork_id']:v for s in sheets['sheets'] for v in s['items']}
    for s in sheets['sheets']:assert m.sha(s['path'])==s['sha256']
    assert set(reviewed)==set(sheet_items),'Every prepared image requires a visual decision'
    index={r['url']:r for r in (json.loads(line) for line in (RUN/'sources.jsonl').open())}
    selected=[r for r in reviews() if r.get('field_updates') or r.get('image_candidate')]
    with m.connect() as db:before=snapshot(db,[r['artwork_id'] for r in selected])
    claims=[];held=[]
    for r in selected:
        aid=r['artwork_id'];source=m.load(m.ROOT/r['native_object_file']);old=source['target']['artwork'];current=before.get(aid)
        if not current or current['artwork']['status']=='archived':
            held.append(dict(artwork_id=aid,reason='Missing or archived target'));continue
        a=current['artwork']
        identity_keys=['title','alternate_title','accession_number','current_institution_id','creation_year_start','creation_year_end','date_precision','date_display']
        if any(a.get(k)!=old.get(k) for k in identity_keys):
            held.append(dict(artwork_id=aid,reason='Identity or date evidence changed since research'));continue
        fields={k:v for k,v in r.get('field_updates',{}).items() if not str(a.get(k) or '').strip()}
        image=None
        prepared=RUN/'prepared-images'/(aid+'.json')
        if not a['primary_media_id'] and prepared.exists():
            im=m.load(prepared)
            if im['state']=='prepared' and reviewed.get(aid,{}).get('decision')=='accept':
                assert sheet_items[aid]['image_sha256']==im['sha256']==reviewed[aid]['image_sha256']==m.sha(im['path'])
                image=dict(im,view_label=reviewed[aid].get('view_label','Full source reproduction'),visual_note=reviewed[aid]['note'])
        if not fields and not image:continue
        record=index.get(m.canonical_url(source['facts']['page']))
        assert record and record['review_state']=='fresh_metadata_verified','Delivery must resolve through the fresh source index'
        assert any(b['entity_id']==aid and b['entity_type']=='artwork' for b in record['artline_bindings'])
        assert any(e.get('body_sha256')==source['receipt']['sha256'] for e in record['discovery_evidence'])
        claims.append(dict(artwork_id=aid,provider=r['provider'],title=r['title'],updates=fields,image=image,
            source_index_id=record['id'],source_url=record['url'],source_record_id=source['facts']['native_id'],
            source_facts=source['facts'],source_receipt=source['receipt'],identity_review=r['identity']))
    assert claims,'No supported changes'
    plan=dict(at=m.now(),operation=OP,index_sha256=m.sha(RUN/'sources.jsonl'),review_sha256=m.sha(RUN/'native-review.json'),
        visual_review_sha256=m.sha(RUN/'visual-review.json'),claims=claims,preimages={c['artwork_id']:before[c['artwork_id']] for c in claims},
        source_ids={p:uid('source/'+p) for p in {c['provider'] for c in claims}},concurrent_holds=held,
        policy='Production only. Exact native identity; fill empty medium/dimensions/accession fields and empty primary image. Preserve dates, titles, existing images, attribution, holding, display and publication state.')
    m.save(RUN/'delivery-plan.json.gz',plan)
    BACKUP.mkdir(parents=True,exist_ok=True)
    m.save(BACKUP/'delivery-plan-and-preimages.json.gz',plan)
    pin=dict(path=str((RUN/'delivery-plan.json.gz').relative_to(m.ROOT)),sha256=m.sha(RUN/'delivery-plan.json.gz'),index_sha256=plan['index_sha256'],
        artworks=len(claims),metadata_artworks=sum(bool(c['updates']) for c in claims),metadata_fields=sum(len(c['updates']) for c in claims),images=sum(bool(c['image']) for c in claims))
    m.save(RUN/'delivery-plan-pin.json',pin);print(json.dumps(pin,indent=2),flush=True)


def pinned():
    pin=m.load(RUN/'delivery-plan-pin.json')
    assert m.sha(m.ROOT/pin['path'])==pin['sha256']
    plan=m.load(m.ROOT/pin['path'])
    assert m.sha(RUN/'sources.jsonl')==plan['index_sha256']==pin['index_sha256']
    assert m.sha(RUN/'visual-review.json')==plan['visual_review_sha256']
    return plan,pin


def backup():
    BACKUP.mkdir(parents=True,exist_ok=True)
    def cloud(*args):return json.loads(subprocess.check_output(['gcloud',*args,'--project=artline-508319','--format=json'],text=True))
    description='Before source-index museum enrichment 20261009'
    matches=[x for x in cloud('sql','backups','list','--instance=artline-postgres','--limit=50') if x.get('description')==description]
    if not matches:
        result=cloud('sql','backups','create','--instance=artline-postgres','--description='+description,'--async')
        m.save(BACKUP/'cloud-backup-operation.json',result);print('Recovery backup requested',flush=True);return
    row=max(matches,key=lambda x:int(x['id']))
    print('Recovery backup',row['id'],row['status'],flush=True)
    if row['status']=='SUCCESSFUL':
        m.save(BACKUP/'cloud-backup.json',row)
        m.save(RUN/'cloud-backup.json',dict(id=row['id'],status=row['status'],description=description))


def upload():
    plan,pin=pinned()
    bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    def one(c):
        im=c['image'];dest=RUN/'uploads'/(c['artwork_id']+'.json')
        if dest.exists():
            receipt=m.load(dest);assert receipt['plan_sha256']==pin['sha256'];return receipt
        raw=Path(im['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==im['sha256'] and len(raw)==im['bytes']<=100000
        blob=bucket.blob(im['storage_path'].lstrip('/'))
        blob.metadata={'sha256':im['sha256'],'artwork-id':c['artwork_id'],'provider':c['provider'],'operation':OP}
        blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,45));response.raise_for_status()
        assert hashlib.sha256(response.content).hexdigest()==im['sha256']
        receipt=dict(at=m.now(),artwork_id=c['artwork_id'],path=im['storage_path'],plan_sha256=pin['sha256'],sha256=im['sha256'],public_verified=True)
        m.save(dest,receipt);return receipt
    images=[c for c in plan['claims'] if c['image']]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for i,_ in enumerate(pool.map(one,images),1):
            if i%20==0:print('Uploaded and publicly verified',i,'/',len(images),flush=True)
    print('Public image delivery verified',len(images),flush=True)


def validate_after(plan,after):
    for c in plan['claims']:
        aid=c['artwork_id'];before=plan['preimages'][aid];a=after[aid]
        expected=dict(before['artwork'],**c['updates'])
        if c['image']:expected['primary_media_id']=c['image']['media_id']
        expected['revision']+=1
        for k in ['updated_at','updated_by']:expected.pop(k)
        assert expected=={k:v for k,v in a['artwork'].items() if k not in ('updated_at','updated_by')},('Unexpected artwork change',aid)
        assert a['artwork']['updated_by']==ACTOR
        assert a['creators']==before['creators']
        old={r['media_id']:r for r in before['attachments']};current={r['media_id']:r for r in a['attachments']}
        assert all(current[k]==v for k,v in old.items())
        assert len(current)==len(old)+int(bool(c['image']))
        if c['image']:assert current[c['image']['media_id']]['view_label']==c['image']['view_label']


def apply():
    plan,pin=pinned()
    if (RUN/'production-applied.json').exists():
        assert m.load(RUN/'production-applied.json')['plan_sha256']==pin['sha256'];print('Already applied: zero writes');return
    assert m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'
    for c in plan['claims']:
        if c['image']:
            rc=m.load(RUN/'uploads'/(c['artwork_id']+'.json'));assert rc['public_verified'] and rc['plan_sha256']==pin['sha256']
    spec=importlib.util.spec_from_file_location('alignment',m.ROOT/'ops/align-catalogues-20261008.py')
    dbm=importlib.util.module_from_spec(spec);spec.loader.exec_module(dbm)
    ids=[c['artwork_id'] for c in plan['claims']]
    with dbm.connect('production',readonly=False) as db:
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        assert snapshot(db,ids)==plan['preimages'],'Concurrent catalogue change: no writes applied'
        m.save(BACKUP/'locked-preimages.json.gz',dict(plan_sha256=pin['sha256'],preimages=plan['preimages']))
        for p,sid in plan['source_ids'].items():
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,terms_url,priority) VALUES(%s,%s,%s,'museum_api',%s,%s,10)",
                (sid,OP+'-'+p,PROVIDER[p]+' — verified source-index enrichment, 9 October 2026',{'cleveland':'https://openaccess-api.clevelandart.org/','chicago':'https://api.artic.edu/','smk':'https://api.smk.dk/'}[p],POLICY[p]))
        for i,c in enumerate(plan['claims'],1):
            aid=c['artwork_id'];p=c['provider'];sid=plan['source_ids'][p];im=c['image'];fields=dict(c['updates'])
            if im:
                rights='cc0' if p in ('chicago','cleveland') else 'public_domain'
                label='CC0 1.0 — museum open-access image' if rights=='cc0' else 'Public Domain Mark 1.0 — SMK per-object label'
                credit='; '.join(v for v in [PROVIDER[p],c['source_facts'].get('credit')] if v)
                db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,
                    checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
                    VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                    (im['media_id'],im['storage_path'],c['source_url'],PROVIDER[p],im['width'],im['height'],im['bytes'],im['sha256'],c['title'],rights,label,
                    'https://creativecommons.org/publicdomain/zero/1.0/' if rights=='cc0' else POLICY[p],credit,
                    c['title']+'. '+credit+'. Proportional resize and JPEG compression; no crop.',im['download']['at'],m.now(),ACTOR))
                db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(im['media_id'],sid,c['source_record_id'],c['source_receipt']['sha256'],im['source_image_url'],POLICY[p],
                    'Explicit source object open-image label and museum reuse policy. Actual source rights retained; object age alone is not clearance.',OP,c['source_receipt']['retrieved_at'],
                    Jsonb(dict(source_facts=c['source_facts'],receipt=c['source_receipt'],download=im['download'],source_index_id=c['source_index_id'],index_sha256=plan['index_sha256'],plan_sha256=pin['sha256']))))
                db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s)",(aid,im['media_id'],im['view_label']))
                fields['primary_media_id']=im['media_id']
            assert set(fields)<={'medium_text','dimensions_text','accession_number','primary_media_id'}
            assignments=[sql.SQL('{}=%s').format(sql.Identifier(k)) for k in fields]
            query=sql.SQL('UPDATE artworks SET ')+sql.SQL(',').join(assignments)+sql.SQL(',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s')
            assert db.execute(query,[*fields.values(),ACTOR,aid]).rowcount==1
            note=dict(operation=OP,source_index_id=c['source_index_id'],index_sha256=plan['index_sha256'],plan_sha256=pin['sha256'],
                field_updates=c['updates'],image_added=bool(im),source_facts=c['source_facts'],identity_review=c['identity_review'],
                scope='Missing-field and image enrichment only; dates, holdings, display and publication state preserved.')
            db.execute('''INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                VALUES(%s,'artwork',%s,'source_index_verified_enrichment',%s,%s,%s,%s,%s,%s)''',
                (uid('citation/'+aid),aid,sid,c['source_record_id'],c['source_url'],json.dumps(note,ensure_ascii=False),c['source_receipt']['retrieved_at'],ACTOR))
            if i%50==0:print('Transaction enriched objects',i,'/',len(plan['claims']),flush=True)
        after=snapshot(db,ids);validate_after(plan,after)
        for c in plan['claims']:
            aid=c['artwork_id']
            db.execute('''INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)
                VALUES(%s,%s,'source_index_enrichment','artwork',%s,%s,%s,%s)''',
                (uid('audit/'+aid),ACTOR,aid,OP,Jsonb(plan['preimages'][aid]),Jsonb(after[aid])))
        m.save(BACKUP/'transaction-after.json.gz',dict(plan_sha256=pin['sha256'],after=after))
    receipt=dict(at=m.now(),plan_sha256=pin['sha256'],index_sha256=plan['index_sha256'],artworks=len(plan['claims']),
        metadata_artworks=sum(bool(c['updates']) for c in plan['claims']),metadata_fields=sum(len(c['updates']) for c in plan['claims']),
        new_images=sum(bool(c['image']) for c in plan['claims']),citations=len(plan['claims']),audit_rows=len(plan['claims']),
        sources=len(plan['source_ids']),local_catalogue_writes=0,new_artworks=0,status_changes=0,current_display_claims=0)
    m.save(RUN/'production-applied.json',receipt);print(json.dumps(receipt,indent=2),flush=True)


def verify():
    plan,pin=pinned();applied=m.load(RUN/'production-applied.json');assert applied['plan_sha256']==pin['sha256']
    ids=[c['artwork_id'] for c in plan['claims']]
    with m.connect() as db:
        after=snapshot(db,ids);validate_after(plan,after)
        citation_ids=[uid('citation/'+aid) for aid in ids];audit_ids=[uid('audit/'+aid) for aid in ids]
        assert db.execute('SELECT count(*) n FROM citations WHERE id=ANY(%s::uuid[])',(citation_ids,)).fetchone()['n']==len(ids)
        assert db.execute('SELECT count(*) n FROM audit_log WHERE id=ANY(%s::uuid[])',(audit_ids,)).fetchone()['n']==len(ids)
        media_ids=[c['image']['media_id'] for c in plan['claims'] if c['image']]
        media=db.execute('SELECT to_jsonb(m) media,to_jsonb(e) evidence FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])',(media_ids,)).fetchall()
        by={v['media']['id']:v for v in media}
        for c in plan['claims']:
            if not c['image']:continue
            im=c['image'];actual=by[im['media_id']]
            assert actual['media']['checksum_sha256']==im['sha256'] and actual['media']['byte_size']==im['bytes']<=100000
            assert actual['evidence']['source_checksum']==c['source_receipt']['sha256']
    result=dict(at=m.now(),plan_sha256=pin['sha256'],verified_artworks=len(ids),verified_images=len(media_ids),verified_citations=len(ids),verified_audit_rows=len(ids),
        original_artwork_fields_preserved=True,original_artist_links_preserved=True,original_image_attachments_preserved=True,
        local_catalogue_writes=0,scope='Independent production readback; full preimage comparison allowing only pinned missing fields and new primary images.')
    m.save(RUN/'production-verification.json',result);print(json.dumps(result,indent=2),flush=True)


def public_verify(retry=False):
    plan,pin=pinned()
    catalogue=m.load(RUN/'catalogue-export.json.gz')
    institutions={i['id']:i for i in catalogue['institutions']}
    def one(c):
        aid=c['artwork_id'];before=plan['preimages'][aid]['artwork'];institution=institutions[before['current_institution_id']]
        url='https://artlines.org/api/backend/v1/museums/'+institution['slug']+'/works/'+aid
        result=dict(artwork_id=aid,url=url,at=m.now())
        try:
            response=requests.get(url,timeout=(15,45));result['http_status']=response.status_code
            response.raise_for_status();body=response.json()
            assert body['title']==c['title'],'Title changed in public response'
            for k,value in c['updates'].items():assert body.get(k)==value,('Public metadata differs',k)
            if c['image']:assert body.get('media_url')==c['image']['storage_path'],'Public primary image differs'
            result.update(verified=True,response=body)
        except Exception as exc:
            result.update(verified=False,error=type(exc).__name__+': '+str(exc)[:300])
        return result
    previous=m.load(RUN/'public-api-verification.json') if retry else None
    failed={r['artwork_id'] for r in previous['rows'] if not r['verified']} if previous else set()
    selected=[c for c in plan['claims'] if c['artwork_id'] in failed] if retry else plan['claims']
    with ThreadPoolExecutor(max_workers=1 if retry else 3) as pool:rows=list(pool.map(one,selected))
    if previous:
        rows=[r for r in previous['rows'] if r['verified']]+rows
    result=dict(at=m.now(),plan_sha256=pin['sha256'],checked=len(rows),verified=sum(r['verified'] for r in rows),rows=rows)
    if previous:result.update(rechecked=len(selected),prior_check_file='public-api-verification.json')
    m.save(RUN/('public-api-recheck.json' if retry else 'public-api-verification.json'),result)
    print('Public artwork API',result['verified'],'/',result['checked'],flush=True)
    assert result['verified']==result['checked'],'Public verification failures retained for investigation'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare-images','sheets','plan','backup','upload','apply','verify','public-verify','public-recheck']);args=p.parse_args()
    {'prepare-images':prepare_images,'sheets':sheets,'plan':make_plan,'backup':backup,'upload':upload,'apply':apply,'verify':verify,'public-verify':public_verify,'public-recheck':lambda:public_verify(True)}[args.command]()
