#!/usr/bin/env python3
"""Sequential, source-reviewed creator expansion and authentic image delivery."""
import argparse
import base64
import collections
import csv
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import textwrap
import time
import uuid
from urllib.parse import urljoin, urlsplit

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parents[1]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result
c = module('creator_metadata', 'ops/creator-one-by-one-20261010.py')
d = module('creator_images', 'ops/deliver-production-wikiart-images-20261006.py')
r,m,q,s,b = c.r,c.m,c.q,c.s,c.b
CAMPAIGN = 'creators-deep-4h-20261010'
BASE = ROOT/'docs/research'/CAMPAIGN
RECOVERY = Path.home()/'Library/Application Support/Artline/backups'/CAMPAIGN
ORIGINALS = Path.home()/'Library/Application Support/Artline/source-images'/CAMPAIGN
START = '2026-10-10T19:30:43Z'
DEADLINE = '2026-10-10T23:30:43Z'
RUN = BASE
SLUG = None


def bootstrap():
    r.save(BASE/'authorization.json', dict(request='we have a catalog of link that we can use to get info about painters and artworks; do one by one, pick a creator that have only 0-5 artworoks, add at least 10-100, add images make deep research; this reseach should take you 4h',
        start_utc=START, planned_end_utc=DEADLINE, target='production', local_database_connected=False,
        method='One creator at a time. Current 0–5 active works, 10–100 new source-supported review records per completed expansion. Deep object/version/attribution research and visual inspection of every delivered image.',
        supplementary_scope='Finish the missing image work for the immediately preceding Tvorozhnikov selection, whose original count was two. Do not count its previous 25 metadata additions as new in this four-hour campaign.',
        image_policy='WikiArt user-approved source policy. Preserve actual rights labels and exact image identity. Selected dated images created by 1955 initially; unknown dates require additional object-specific evidence, never a date inferred from artist lifespan. No generated artwork substitutes.',
        selection='Personal owner study selections, separate from museum designations. Preserve old catalogue fields, images, review status and holdings. No current-display claims.'))
    r.save(BASE/'source-registry-review.json', r.load(ROOT/'docs/research/creator-one-by-one-20261010/source-registry-review.json'))
    r.save(RECOVERY/'authorization.json', r.load(BASE/'authorization.json'))
    print('Campaign', START, 'through', DEADLINE, flush=True)


def configure(slug):
    global SLUG,RUN
    SLUG = slug; RUN = BASE/'creators'/slug
    c.OP = CAMPAIGN+'-'+slug; c.RUN = RUN; c.BACKUP = RECOVERY/slug
    c.SOURCE = 'https://www.wikiart.org/en/'+slug
    c.m.RUN = c.q.RUN = c.r.RUN = c.s.RUN = c.b.RUN = RUN
    c.m.CACHE = {}; c.r.PORT = 55519
    d.RUN = RUN; d.ORIGINALS = ORIGINALS/slug
    path = RUN/'creator.json'
    if path.exists(): c.AID = r.load(path)['artist']['id']
    c.inventory = inventory
    c.EXISTING_RECORDS = 'expanded-existing-records.json.gz' if (RUN/'expanded-existing-records.json.gz').exists() else 'existing-records.json.gz'


def inventory(db):
    pair = r.load(RUN/'creator.json')
    names = list(pair['comparison_names'])
    ids = list(pair['comparison_creator_ids'])
    if (RUN/'identity-amendment.json').exists():
        amendment=r.load(RUN/'identity-amendment.json')
        names += amendment.get('additional_names',[])
        ids += amendment.get('additional_creator_ids',[])
    query = """SELECT to_jsonb(a) artwork, ma.source_page_url image_source_url,
      coalesce((SELECT jsonb_agg(to_jsonb(e) ORDER BY e.id) FROM external_identifiers e
        WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers,
      coalesce((SELECT jsonb_agg(to_jsonb(c) ORDER BY c.id) FROM citations c
        WHERE c.entity_type='artwork' AND c.entity_id=a.id),'[]') citations
      FROM artworks a LEFT JOIN media_assets ma ON ma.id=a.primary_media_id
      WHERE a.id IN (SELECT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]))
      OR lower(a.unlinked_creator_label)=ANY(%s) ORDER BY a.id"""
    return db.execute(query,(ids,names)).fetchall()


def research():
    if (RUN/'research-selection.json.gz').exists():
        print('Preserving completed creator research'); return
    old = r.load(ROOT/'docs/research/low-count-200-painters-20261008/low-count-audit.json.gz')['painters']
    matches = [p for p in old if p.get('source') and p['source']['url']==c.SOURCE]
    assert len(matches)==1
    lead = matches[0]; c.AID = lead['artist']['id']
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        artist = db.execute('SELECT to_jsonb(a) a FROM artists a WHERE id=%s',(c.AID,)).fetchone()['a']
        aliases = [v['alias'] for v in db.execute('SELECT alias FROM artist_aliases WHERE artist_id=%s',(c.AID,))]
        ids = db.execute("SELECT to_jsonb(e) e FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s",(c.AID,)).fetchall()
        count_sql = "SELECT count(DISTINCT a.id) n FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived'"
        count = db.execute(count_sql,(c.AID,)).fetchone()['n']
        assert 0<=count<=5 and artist['entity_type']=='person' and artist['status']!='archived'
        if not (RUN/'count-query-plan.json').exists():
            r.save(RUN/'count-query-plan.json',db.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+count_sql,(c.AID,)).fetchone())
        identities = db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artist' AND (canonical_url=%s OR (scheme='wikiart-artist' AND external_id=%s))",(c.SOURCE,SLUG)).fetchall()
        authority_ids={x['entity_id'] for x in identities}
        assert authority_ids <= {c.AID}, 'Creator URL is assigned to a different record; resolve identity first'
        if not authority_ids:
            review=r.load(RUN/'creator-identity-review.json')
            assert review['artist_id']==c.AID and review['source_url']==c.SOURCE and review['confidence']>=.98 and review['basis']
            for rc in review['receipts']:
                body=ROOT/rc['body_path'];raw=body.read_bytes()
                if body.suffix=='.gz':raw=gzip.decompress(raw)
                assert r.sha(raw)==rc['sha256']
    raw, profile = c.capture(c.SOURCE)
    soup=m.BeautifulSoup(raw,'html.parser')
    visible=soup.get_text(' ',strip=True)
    assert artist['display_name'] in visible or lead['source']['name'] in visible
    raw_names=[artist['display_name'],lead['source']['name']]+aliases
    for tag in soup.select('[itemprop="name"], .wiki-layout-artist-info h2'):
        if len(tag.get_text(' ',strip=True))<150: raw_names.append(tag.get_text(' ',strip=True))
    names=sorted({x.casefold() for x in raw_names if x})
    with r.connect('production') as db:
        similar=db.execute('SELECT id::text,display_name,birth_year,death_year FROM artists WHERE lower(display_name)=ANY(%s)',(names,)).fetchall()
        compare_ids=sorted({c.AID}|{x['id'] for x in similar})
    pair=dict(artist=artist,aliases=aliases,identifiers=ids,count_at_selection=count,source=lead['source'],profile_receipt=profile,
              comparison_names=names,comparison_creator_ids=compare_ids,similar_named_creators=similar)
    r.save(RUN/'creator.json',pair)
    r.save(RUN/'authorization.json',{**r.load(BASE/'authorization.json'),'creator':artist['display_name'],'creator_id':c.AID})
    with r.connect('production') as db: existing=inventory(db)
    r.save_gz(RUN/'existing-records.json.gz',existing)
    print(artist['display_name'],'currently',count,'active artworks; comparison records',len(existing),flush=True)
    raw,rc=c.capture(c.SOURCE+'/all-works/text-list')
    items={}; soup=m.BeautifulSoup(raw,'html.parser')
    for a in soup.select('li a[href]'):
        if a['href'].startswith(urlsplit(c.SOURCE).path+'/'):
            title=a.get_text(' ',strip=True); ds=a.parent.get_text(' ',strip=True).removeprefix(title).strip(' ,')
            url=urljoin(c.SOURCE,a['href']);items[url]=dict(title=title,url=url,source_date=ds,date=m.dates.creation_date(ds))
    raw,api=c.capture('https://www.wikiart.org/en/App/Painting/PaintingsByArtist?artistUrl='+SLUG+'&json=2')
    metadata=json.loads(raw)
    index_path=RUN/'source-indexes'/(c.AID+'.json.gz')
    index_value=dict(outcome='indexed',items=list(items.values()),metadata=metadata,receipt=rc,metadata_receipt=api)
    if index_path.exists():
        assert r.load(index_path)==index_value, 'Source index changed; preserve and review separately'
    else:
        r.save_gz(index_path,index_value)
    rows,held=b.source_candidates(pair)
    translations=collections.defaultdict(set)
    for lang in ['ru','fr','de']:
        raw,trc=c.capture('https://www.wikiart.org/'+lang+'/App/Painting/PaintingsByArtist?artistUrl='+SLUG+'&json=2')
        values=json.loads(raw)
        translation_path=RUN/(('russian-titles' if lang=='ru' else lang+'-titles')+'.json.gz')
        translation_value=dict(items=values,receipt=trc)
        if translation_path.exists():
            assert r.load(translation_path)==translation_value, 'Translation evidence changed'
        else:
            r.save_gz(translation_path,translation_value)
        for x in values: translations[str(x['contentId'])].add(q.norm(x.get('title')))
    names={q.norm(x['artwork'].get(k)) for x in existing for k in ['title','alternate_title']}-{''}
    urls={e.get('canonical_url') for x in existing for e in x['identifiers']}|{v.get('source_url') for x in existing for v in x['citations']}|{x.get('image_source_url') for x in existing}
    selected=[]; title_counts=collections.Counter(q.norm(x['work']['title']) for x in rows)
    for row in rows[:100]:
        title=row['work']['title']; keys=({q.norm(title)}|translations[row['source_id']])-{''}
        raw,page_rc=c.capture(row['source_url'],'page-captures');page=q.page_metadata(raw,page_rc)
        assert page['metadata']['artistUrl']==urlsplit(c.SOURCE).path
        assert q.norm(page['metadata']['title'])==q.norm(title)
        if q.image_key(page['metadata']['image'])!=q.image_key(row['metadata']['image']):
            held.append(dict(title=title,source_url=row['source_url'],reason='Artwork/index images differ',page=page));continue
        if page['fields'].get('Original Title'): keys.add(q.norm(page['fields']['Original Title']))
        row.update(page=page,wikiart_artwork_id=page['metadata']['_id'],translated_titles_checked=sorted(keys))
        date=s.source_date(page);w=row['work']
        if date and date['creation_year_end']>1970:
            held.append(dict(title=title,source_url=row['source_url'],reason='Date exceeds scope',page=page));continue
        if date: w.update(date)
        else:
            w.update(creation_year_start=None,creation_year_end=None,date_precision='unknown',date_display='Unknown date')
            row['date_review']='Creation date not established by direct source. Retained as explicit review/research candidate; no year inferred from artist lifespan.'
        w['alternate_title']=page['fields'].get('Original Title') or None
        w['medium_text']=(page['fields'].get('Media') or page['fields'].get('Medium') or '').replace(' ,',',') or None
        w['dimensions_text']=page['fields'].get('Dimensions')
        w['work_type']=s.kind(w['medium_text'])
        row['identity_basis']='Direct WikiArt creator URL, object title, stable content and canonical IDs and image URL reconciled across profile, object page and index. Multiple source languages and existing linked/raw-label object leads checked. Additional native-source and visual review required before delivery.'
        row['research_flags']=[]
        if keys&names or row['source_url'] in urls:
            row['research_flags'].append('Possible existing object/title/translation; resolve before creation')
        if title_counts[q.norm(title)]>1: row['research_flags'].append('Repeated title; compare physical versions')
        if re.search(r'\b(copy|after|attributed|workshop|school|follower|detail|fragment)\b',str(page['fields']),re.I):
            row['research_flags'].append('Qualified source wording or version requires review')
        selected.append(row)
        print(len(selected),title,w['date_display'],row['research_flags'],flush=True)
    r.save_gz(RUN/'research-selection.json.gz',dict(pair=pair,rows=selected,held=held,source_index_count=len(items),metadata_count=len(metadata),
        authorization_sha256=r.sha((RUN/'authorization.json').read_bytes())))


def prepare_images():
    plan=r.load(RUN/'image-selection.json.gz')
    pin=r.sha((RUN/'image-selection.json.gz').read_bytes())
    for row in plan['rows']:
        wid=row['artwork_id'];dest=RUN/'prepared-images'/(wid+'.json')
        if dest.exists():continue
        p=row['page'];date=row.get('image_date_evidence') or row['work']
        assert date['creation_year_end'] is not None and date['creation_year_end']<=1955
        assert row.get('image_identity_review') and row['confidence']>=.9
        url=p['image_url'];assert q.image_key(url)==q.image_key(p['metadata']['image'])
        original,rc=d.download(url)
        raw,width,height,quality=d.core.compress(original)
        assert 0<len(raw)<=100000 and min(width,height)>=50 and max(width,height)>=200
        with Image.open(io.BytesIO(original)) as image: original_size=list(ImageOps.exif_transpose(image).size)
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            gray=image.convert('L').resize((17,16));pixels=list(gray.getdata())
            bits=''.join('1' if pixels[y*17+x]>pixels[y*17+x+1] else '0' for y in range(16) for x in range(16))
            dhash=hex(int(bits,2))[2:].zfill(64);stddev=ImageStat.Stat(image.convert('L')).stddev[0]
            assert stddev>1
        assert abs(width/height-original_size[0]/original_size[1])<.025
        digest=r.sha(raw);path='/assets/artworks/imported/'+CAMPAIGN+'/'+SLUG+'/'+wid+'-'+digest[:16]+'.jpg'
        target=ROOT/'apps/web/public'/path.lstrip('/');r.save(target,raw)
        label=p['rights_label'] or 'Rights label not supplied'
        im=dict(artwork_id=wid,artist_id=row['artist_id'],artist=plan['pair']['artist']['display_name'],title=row['work']['title'],
            source_id=row['wikiart_artwork_id'],source_page_url=row['source_url'],source_image_url=url,
            source_rights_label=label,rights_status='public_domain' if label=='Public domain' else ('unknown' if not p['rights_label'] else 'restricted'),
            selection_pin=pin,path=path,visual_path=str(target),sha256=digest,dhash=dhash,bytes=len(raw),width=width,height=height,
            original_dimensions=original_size,jpeg_quality=quality,download=rc,media_id=c.uid('image/'+wid+'/'+digest),
            image_identity_review=row['image_identity_review'],date_evidence=date,confidence=row['confidence'],outcome='prepared')
        r.save(dest,im);print('Prepared',im['title'],width,height,len(raw),flush=True)
    ims=[r.load(RUN/'prepared-images'/(row['artwork_id']+'.json')) for row in plan['rows']]
    duplicates=[]
    for i,x in enumerate(ims):
        for y in ims[i+1:]:
            distance=(int(x['dhash'],16)^int(y['dhash'],16)).bit_count()
            if x['sha256']==y['sha256'] or distance<=8:
                duplicates.append(dict(ids=[x['artwork_id'],y['artwork_id']],titles=[x['title'],y['title']],distance=distance))
    r.save(RUN/'image-file-audit.json',dict(selection_pin=pin,images=len(ims),duplicate_leads=duplicates,all_within_byte_limit=True,full_frame_proportions=True))
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    for start in range(0,len(ims),12):
        batch=ims[start:start+12];sheet=Image.new('RGB',(1440,1260),'white');draw=ImageDraw.Draw(sheet)
        for n,im in enumerate(batch):
            left=n%4*360;top=n//4*420
            with Image.open(im['visual_path']) as src:
                img=src.convert('RGB');img.thumbnail((342,330));sheet.paste(img,(left+(360-img.width)//2,top+(335-img.height)//2))
            for j,line in enumerate(textwrap.wrap(str(start+n+1)+'. '+im['title'],40)[:4]):draw.text((left+8,top+340+j*18),line,font=font,fill='black')
        path=ORIGINALS/SLUG/'contact-sheets'/f'{start//12+1:03d}.jpg';path.parent.mkdir(parents=True,exist_ok=True);sheet.save(path,quality=94)
        r.save(RUN/'visual-sheets'/f'{start//12+1:03d}.json',dict(path=str(path),sha256=r.sha(path.read_bytes()),images=[dict(id=x['artwork_id'],sha256=x['sha256'],title=x['title']) for x in batch]))
        print('Review sheet',path,flush=True)


def reviewed_images():
    plan=r.load(RUN/'image-selection.json.gz');pin=r.sha((RUN/'image-selection.json.gz').read_bytes())
    review=r.load(RUN/'visual-review.json');assert review['selection_pin']==pin
    images=[]
    for row in plan['rows']:
        im=r.load(RUN/'prepared-images'/(row['artwork_id']+'.json'))
        assert im['selection_pin']==pin
        assert review['approved'].get(im['artwork_id'])==im['sha256'], 'Image not visually approved'
        raw=Path(im['visual_path']).read_bytes();assert r.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
        images.append(im)
    assert len(images)==len(review['approved']) and not review['held']
    for sheet in review['sheets']:
        assert r.sha(Path(sheet['path']).read_bytes())==sheet['sha256']
    return plan,pin,images,review


def upload_images():
    plan,pin,images,review=reviewed_images()
    bucket=d.storage.Client(project='artline-508319',credentials=d.core.GcloudCredentials()).bucket(d.core.BUCKET)
    for im in images:
        dest=RUN/'image-uploads'/(im['artwork_id']+'.json')
        if dest.exists():
            rc=r.load(dest);assert rc['sha256']==im['sha256'] and rc['selection_pin']==pin;continue
        raw=Path(im['visual_path']).read_bytes();blob=bucket.blob(im['path'].lstrip('/'))
        blob.metadata={'sha256':im['sha256'],'artwork-id':im['artwork_id'],'provider':'WikiArt','operation':CAMPAIGN,'rights-status':im['rights_status']}
        blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except d.PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=m.requests.get('https://artlines.org'+im['path'],timeout=(15,45));response.raise_for_status()
        assert r.sha(response.content)==im['sha256']
        r.save(dest,dict(at=r.now(),artwork_id=im['artwork_id'],selection_pin=pin,sha256=im['sha256'],path=im['path'],bytes=len(raw),generation=blob.generation,public_bytes_verified=True))
        print('Uploaded and public-verified',im['title'],flush=True)


def attach_images():
    plan,pin,images,review=reviewed_images();ids=[im['artwork_id'] for im in images]
    assert r.load(RECOVERY/'cloud-backup.json')['status']=='SUCCESSFUL'
    for im in images:
        upload=r.load(RUN/'image-uploads'/(im['artwork_id']+'.json'))
        assert upload['selection_pin']==pin and upload['sha256']==im['sha256'] and upload['public_bytes_verified']
    image_source=c.uid('source/images');marker=c.uid('image-attachment/'+pin)
    auth=r.load(RUN/'authorization.json');artist=plan['pair']['artist'];byid={x['artwork_id']:x for x in plan['rows']}
    with r.connect('production',readonly=False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='120s'")
        db.execute('SELECT pg_advisory_xact_lock(2026100607)')
        previous=db.execute('SELECT after_json FROM audit_log WHERE id=%s',(marker,)).fetchone()
        if previous:
            result=previous['after_json'];assert result['selection_pin']==pin and result['ids']==ids
        else:
            db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
            before=s.snapshots(db,ids);assert len(before)==len(ids)
            for im in images:
                record=before[im['artwork_id']]
                assert record['artwork']['primary_media_id'] is None, 'Preserve existing image; reconcile changed target'
                assert record['artwork']['status']!='archived'
                assert any(x['artist_id']==artist['id'] for x in record['creators'])
            r.save_gz(c.BACKUP/'image-preimages.json.gz',dict(selection_pin=pin,records=before))
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://www.wikiart.org/')",(image_source,c.OP+'-images','WikiArt: visually reviewed '+artist['display_name']+' reproductions'))
            updates=[]
            with db.pipeline():
                for im in images:
                    wid=im['artwork_id'];row=byid[wid];p=row['page']
                    attribution=artist['display_name']+'. '+im['title']+'. WikiArt source label: '+im['source_rights_label']+'. Full source frame, proportional resize and JPEG compression. '+im['source_page_url']
                    db.execute("""INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,
                      checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at)
                      VALUES(%s,'local',%s,%s,'WikiArt','image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                      (im['media_id'],im['path'],im['source_page_url'],im['width'],im['height'],im['bytes'],im['sha256'],im['title']+' — '+artist['display_name'],im['rights_status'],im['source_rights_label']+' (WikiArt source label)',c.m.POLICY,artist['display_name']+'; reproduction via WikiArt',attribution,im['download']['at']))
                    evidence=dict(image=im,page=p,authorization=auth,selection_pin=pin,visual_review=review,identity_basis=row['image_identity_review'],editorial_confidence=row['confidence'],confidence_note='Editorial assessment, not a calibrated probability.',source_approval_separate_from_actual_rights=True)
                    db.execute("""INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(im['media_id'],image_source,im['source_id'],p['receipt']['sha256'],im['source_image_url'],c.m.POLICY,
                        'Exact source rights label preserved separately from user-approved WikiArt source policy; no independent licence inferred.',CAMPAIGN+'-v1',p['receipt']['retrieved_at'],m.Jsonb(evidence)))
                    db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s)',(wid,im['media_id'],'Complete source reproduction'))
                    updates.append(db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],c.ACTOR,wid)))
                    db.execute("""INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                      VALUES(%s,'artwork',%s,%s,'deep_creator_image_delivery',%s,%s,%s,%s,%s)""",(c.uid('image-citation/'+wid),wid,image_source,im['source_id'],im['source_page_url'],json.dumps(dict(selection_pin=pin,image=im,scope='Image attachment only; metadata, dates, attribution, holdings and status preserved.'),ensure_ascii=False),p['receipt']['retrieved_at'],c.ACTOR))
            assert all(x.rowcount==1 for x in updates)
            after=s.snapshots(db,ids)
            for im in images:
                wid=im['artwork_id'];a=after[wid];z=before[wid];allowed={'primary_media_id','revision','updated_at','updated_by'}
                assert {k:v for k,v in a['artwork'].items() if k not in allowed}=={k:v for k,v in z['artwork'].items() if k not in allowed}
                assert a['creators']==z['creators'] and a['locations']==z['locations']
                assert a['artwork']['primary_media_id']==im['media_id']
                assert all(v in a['attachments'] for v in z['attachments'])
            r.save_gz(c.BACKUP/'image-postimages.json.gz',dict(selection_pin=pin,records=after))
            result=dict(at=r.now(),artist=artist['display_name'],artist_id=artist['id'],selection_pin=pin,ids=ids,images_attached=len(images),metadata_preserved=True,existing_attachments_preserved=True,local_database_connected=False)
            db.execute("INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,after_json) VALUES(%s,%s,'deep_creator_images','artist',%s,%s)",(marker,c.ACTOR,artist['id'],m.Jsonb(result)))
    r.save(RUN/'images-applied.json',result)
    print('Attached/recovered',result['images_attached'],'images for',artist['display_name'],flush=True)


def verify_images():
    plan,pin,images,review=reviewed_images();ids=[x['artwork_id'] for x in images]
    applied=r.load(RUN/'images-applied.json');assert applied['selection_pin']==pin
    with r.connect('production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        rows=db.execute("""SELECT a.id::text,a.primary_media_id::text,to_jsonb(ma) media,to_jsonb(e) rights
          FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id
          JOIN media_rights_evidence e ON e.media_id=ma.id WHERE a.id=ANY(%s::uuid[])""",(ids,)).fetchall()
        assert s.snapshots(db,ids)==r.load(c.BACKUP/'image-postimages.json.gz')['records']
    byid={x['id']:x for x in rows};assert set(byid)==set(ids)
    public=[]
    for im in images:
        row=byid[im['artwork_id']];ma=row['media'];ev=row['rights']
        assert row['primary_media_id']==im['media_id'] and ma['storage_path']==im['path'] and ma['checksum_sha256']==im['sha256'] and ma['byte_size']==im['bytes']<=100000
        assert ma['rights_status']==im['rights_status'] and ev['source_image_url']==im['source_image_url'] and ev['evidence_json']['selection_pin']==pin
        response=m.requests.get('https://artlines.org'+im['path'],timeout=(15,45));response.raise_for_status();assert r.sha(response.content)==im['sha256']
        public.append(dict(artwork_id=im['artwork_id'],http_status=response.status_code,sha256=im['sha256']))
    result=dict(at=r.now(),artist=plan['pair']['artist']['display_name'],artist_id=plan['pair']['artist']['id'],selection_pin=pin,verified_images=len(images),public_checks=public,metadata_preserved=True,local_database_connected=False)
    r.save(RUN/'images-verified.json',result);print('Verified DB evidence and public bytes:',len(images),'images',flush=True)


def verify_catalogue():
    pair=r.load(RUN/'creator.json');artist=pair['artist']
    added=r.load(RUN/'applied.json') if (RUN/'applied.json').exists() else None
    images=r.load(RUN/'images-verified.json')
    ims=[r.load(RUN/'prepared-images'/(x['artwork_id']+'.json')) for x in r.load(RUN/'image-selection.json.gz')['rows']]
    expected={x['artwork_id']:x for x in r.load(RUN/'reviewed-plan.json.gz')['rows']} if added else {}
    found={};pages=[];cursor=None
    for _ in range(4):
        params=dict(limit=50)
        if cursor:params['cursor']=cursor
        response=m.requests.get('https://artlines.org/api/backend/v1/artists/'+artist['slug']+'/works',params=params,timeout=(15,60));response.raise_for_status()
        data=response.json();assert len(data['items'])<=50;pages.append(dict(url=response.url,data=data))
        found.update({x['id']:x for x in data['items']})
        if not data.get('next_cursor'):break
        assert cursor!=data['next_cursor'];cursor=data['next_cursor']
    assert set(expected)<=set(found)
    for wid,row in expected.items():
        for key in ['title','alternate_title','creation_year_start','creation_year_end','date_display','work_type']:
            assert found[wid][key]==row['work'][key], (key,wid)
        assert found[wid]['status']=='review'
    for im in ims:
        assert found[im['artwork_id']]['media_url']==im['path']
        assert found[im['artwork_id']]['source_page_url']==im['source_page_url']
    r.save_gz(RUN/'live-api-pages.json.gz',pages)
    proof=dict(at=r.now(),artist=artist['display_name'],artist_id=artist['id'],slug=artist['slug'],
        added_this_campaign=added['added'] if added else 0,images_added_this_campaign=images['verified_images'],
        active_total=data['total'],initial_count=pair['count_at_selection'],all_additions_and_images_found=True,
        source=pair['source']['url'],local_database_connected=False)
    r.save(RUN/'creator-verified.json',proof);print(json.dumps(proof),flush=True)


def attach_research():
    """Attach reviewed primary citations and supported holdings to new works only."""
    plan=r.load(RUN/'reviewed-plan.json.gz');c.validate(plan)
    pin=r.sha((RUN/'reviewed-plan.json.gz').read_bytes())
    applied=r.load(RUN/'applied.json');assert applied['plan_sha256']==pin
    assert r.load(RECOVERY/'cloud-backup.json')['status']=='SUCCESSFUL'
    rows=[v for v in plan['rows'] if v.get('native_sources')]
    ids=[v['artwork_id'] for v in rows];assert set(ids)<=set(applied['new_ids'])
    marker=c.uid('native-research/'+pin)
    with r.connect('production',readonly=False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='120s'")
        db.execute('SELECT pg_advisory_xact_lock(2026100607)')
        previous=db.execute('SELECT after_json FROM audit_log WHERE id=%s',(marker,)).fetchone()
        if previous:result=previous['after_json']
        else:
            db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
            before=s.snapshots(db,ids);r.save_gz(RECOVERY/SLUG/'native-research-before.json.gz',before)
            citation_count=0;holding_count=0
            for row in rows:
                wid=row['artwork_id'];record=before[wid]['artwork']
                assert record['status']=='review' and record['published_at'] is None
                assert all(record[k]==v for k,v in row['work'].items())
                for j,src in enumerate(row['native_sources']):
                    assert src['facts'] and src['review'] and src['confidence']>=.9
                    sid=c.uid('native-source/'+urlsplit(src['url']).netloc)
                    db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page',%s) ON CONFLICT(id) DO NOTHING",
                        (sid,c.OP+'-native-'+r.sha(urlsplit(src['url']).netloc.encode())[:12],src['publisher'],urlsplit(src['url']).scheme+'://'+urlsplit(src['url']).netloc))
                    note=dict(operation=c.OP,plan_sha256=pin,source_facts=src['facts'],source_receipt=src['receipt'],editorial_review=src['review'],editorial_confidence=src['confidence'],policy='Native source attribution distinct from WikiArt. Collection credit is not a current-display claim. Review status preserved.')
                    db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,page_or_locator,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'creator_deep_research_native_metadata',%s,%s,%s,%s,%s,%s)",
                        (c.uid('native-citation/'+wid+'/'+str(j)),wid,sid,src.get('record_id'),src['url'],src.get('locator'),json.dumps(note,ensure_ascii=False),src['receipt']['retrieved_at'],c.ACTOR))
                    citation_count+=1
                h=row.get('museum_research')
                if h:
                    assert h['confidence']>=.9 and h['basis'] and h['institution_id']
                    assert record['current_institution_id'] is None and record['accession_number'] is None and not before[wid]['locations']
                    src=row['native_sources'][h['native_source_index']]
                    sid=c.uid('native-source/'+urlsplit(src['url']).netloc)
                    assert db.execute("SELECT id FROM institutions WHERE id=%s AND status<>'archived' FOR SHARE",(h['institution_id'],)).fetchone()
                    db.execute('UPDATE artworks SET current_institution_id=%s,accession_number=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(h['institution_id'],h.get('accession_number'),c.ACTOR,wid))
                    db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",
                        (c.uid('native-holding/'+wid),wid,h['institution_id'],sid,src['url'],json.dumps(dict(operation=c.OP,plan_sha256=pin,basis=h['basis'],confidence=h['confidence'],limitation='Documented collection only; no current-display assertion.'),ensure_ascii=False),src['receipt']['retrieved_at']))
                    holding_count+=1
            after=s.snapshots(db,ids)
            for row in rows:
                wid=row['artwork_id'];old=before[wid];new=after[wid]
                assert old['creators']==new['creators'] and old['attachments']==new['attachments']
                allowed={'current_institution_id','accession_number','revision','updated_at','updated_by'} if row.get('museum_research') else set()
                assert {k:v for k,v in old['artwork'].items() if k not in allowed}=={k:v for k,v in new['artwork'].items() if k not in allowed}
                if row.get('museum_research'):
                    h=row['museum_research'];assert new['artwork']['current_institution_id']==h['institution_id'] and new['artwork']['accession_number']==h.get('accession_number')
                    assert len(new['locations'])==1 and new['locations'][0]['claim_type']=='holding' and new['locations'][0]['display_state'] is None
                else:assert old['locations']==new['locations']
            r.save_gz(RECOVERY/SLUG/'native-research-after.json.gz',after)
            result=dict(at=r.now(),plan_sha256=pin,native_citations=citation_count,holdings_added=holding_count,artwork_ids=ids,current_display_claims=0,local_database_connected=False)
            db.execute("INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,after_json) VALUES(%s,%s,'creator_deep_research_native_enrichment','artist',%s,%s)",(marker,c.ACTOR,c.AID,m.Jsonb(result)))
    with r.connect('production') as db:
        expected=r.load(RECOVERY/SLUG/'native-research-after.json.gz')
        assert s.snapshots(db,ids)==expected
        assert db.execute("SELECT count(*) n FROM citations WHERE id=ANY(%s::uuid[])",([c.uid('native-citation/'+v['artwork_id']+'/'+str(j)) for v in rows for j in range(len(v['native_sources']))],)).fetchone()['n']==result['native_citations']
    r.save(RUN/'native-research-applied.json',result);print(json.dumps(result),flush=True)


def checkpoint():
    creators=[r.load(p) for p in sorted((BASE/'creators').glob('*/creator-verified.json'))]
    state=dict(at=r.now(),start_utc=START,planned_end_utc=DEADLINE,goal_complete=False,
        completed_creators=creators,new_artworks=sum(x['added_this_campaign'] for x in creators),
        new_images=sum(x['images_added_this_campaign'] for x in creators),local_database_connected=False)
    path=BASE/'progress.json';path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.partial');temp.write_text(json.dumps(state,ensure_ascii=False,indent=2));temp.replace(path)
    print(json.dumps(state),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['bootstrap','research','prepare_images','upload_images','attach_images','verify_images','verify_catalogue','attach_research','checkpoint']);p.add_argument('--creator')
    args=p.parse_args()
    if args.creator:configure(args.creator)
    if args.command not in ['bootstrap','checkpoint']:assert args.creator
    globals()[args.command]()
