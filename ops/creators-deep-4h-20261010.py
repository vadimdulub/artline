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


def inventory(db):
    pair = r.load(RUN/'creator.json')
    names = pair['comparison_names']
    ids = pair['comparison_creator_ids']
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
        r.save(RUN/'count-query-plan.json',db.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+count_sql,(c.AID,)).fetchone())
        identities = db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artist' AND (canonical_url=%s OR (scheme='wikiart-artist' AND external_id=%s))",(c.SOURCE,SLUG)).fetchall()
        assert {x['entity_id'] for x in identities}=={c.AID}
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
    r.save_gz(RUN/'source-indexes'/(c.AID+'.json.gz'),dict(outcome='indexed',items=list(items.values()),metadata=metadata,receipt=rc,metadata_receipt=api))
    rows,held=b.source_candidates(pair)
    translations=collections.defaultdict(set)
    for lang in ['ru','fr','de']:
        raw,trc=c.capture('https://www.wikiart.org/'+lang+'/App/Painting/PaintingsByArtist?artistUrl='+SLUG+'&json=2')
        values=json.loads(raw);r.save_gz(RUN/(('russian-titles' if lang=='ru' else lang+'-titles')+'.json.gz'),dict(items=values,receipt=trc))
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


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['bootstrap','research','prepare_images']);p.add_argument('--creator')
    args=p.parse_args()
    if args.creator:configure(args.creator)
    if args.command!='bootstrap':assert args.creator
    globals()[args.command]()
