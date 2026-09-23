#!/usr/bin/env python3
"""Selected WikiArt image enrichment; immutable evidence and explicit review gates."""
import argparse
import collections
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import re
import base64
import concurrent.futures
import threading
import time
import unicodedata
import uuid
from urllib.parse import urljoin, urlparse

import psycopg
from psycopg.rows import dict_row
import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/wikiart-selected-images-20260919'
BACKUP = Path.home() / 'Library/Application Support/Artline/backups/wikiart-selected-images-20260919'
ORIGINALS = Path.home() / 'Library/Application Support/Artline/source-images/wikiart-selected-images-20260919'
ACTOR='local-european-research'
FETCH_GATE=threading.Lock()
FETCH_NEXT=0.0
FETCH_INTERVAL=1.1
PREPARE_WORKERS=4
spec = importlib.util.spec_from_file_location('core', ROOT / 'ops/enrich-artwork-images.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def save_atomic(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    data=value if isinstance(value,bytes) else core.encode(value)
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        try:os.link(temporary,path)
        except FileExistsError:
            if path.read_bytes()!=data:raise ValueError('Existing evidence differs: '+str(path))
    finally:
        temporary.unlink(missing_ok=True)


core.save_new=save_atomic


def norm(text):
    text = ''.join(c for c in unicodedata.normalize('NFKD', html.unescape(str(text or '')).casefold()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[^\W_]+', text))


def creation_date(value):
    """Keep explicit numeric dates, including BCE ranges; never invent year zero."""
    value=str(value or '')
    match=re.fullmatch(r'(c\.|ок\.)?\s*(\d{1,4})\s*(BCE|BC|AD|CE)?(?:\s*[-–]\s*(c\.|ок\.)?\s*(\d{1,4})\s*(BCE|BC|AD|CE)?)?',value,re.I)
    if not match:return None
    first=int(match[2]);last=int(match[5] or match[2])
    first_era=(match[3] or match[6] or 'AD').upper();last_era=(match[6] or match[3] or 'AD').upper()
    start=-first if first_era in ('BC','BCE') else first
    end=-last if last_era in ('BC','BCE') else last
    if not first or not last or start>end:return None
    circa=bool(match[1] or match[4])
    return {'creation_year_start':start,'creation_year_end':end,'date_display':value,
        'date_precision':('circa_range' if circa else 'range') if match[5] else ('circa' if circa else 'exact')}


def read_only(dsn='postgres://localhost/artline'):
    return psycopg.connect(dsn, row_factory=dict_row, options='-c default_transaction_read_only=on -c statement_timeout=120000')


def audit():
    RUN.mkdir(parents=True, exist_ok=True)
    with read_only() as db:
        artists = db.execute("""SELECT p.id::text,p.slug,p.display_name,p.death_year,p.entity_type,
          EXISTS(SELECT 1 FROM artist_countries c WHERE c.artist_id=p.id AND c.country_code IN ('RU','GR')) priority,
          EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=p.id AND d.is_popular) popular,
          (SELECT count(*) FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
           WHERE aa.artist_id=p.id AND a.primary_media_id IS NULL AND a.status<>'archived'
           AND a.work_type IN ('painting','drawing','watercolor','print','fresco','icon')
           AND a.creation_year_end<=1955 AND a.creation_year_start IS NOT NULL) gaps
          FROM artists p WHERE p.status<>'archived'
          ORDER BY popular DESC,priority DESC,gaps DESC,p.slug LIMIT 100""").fetchall()
        artists = [a for a in artists if a['gaps']]
        previous=json.loads((RUN/'audit.json').read_bytes()) if (RUN/'audit.json').exists() else {'artists':[],'works':[]}
        previous_ids={p['id'] for p in previous['artists']}
        works = list(previous['works'])
        for p in artists:
            if p['id'] in previous_ids:continue
            rows = db.execute("""SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,
              a.creation_year_start,a.creation_year_end,a.date_display,a.date_precision,a.work_type,a.status,
              a.accession_number,a.current_institution_id::text,to_jsonb(a) before_record,
              (SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'external_id',e.external_id,'url',e.canonical_url,'source_id',e.source_id))
                FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers,
              (SELECT jsonb_agg(jsonb_build_object('id',p2.id,'slug',p2.slug,'name',p2.display_name,'role',aa2.attribution_role))
                FROM artwork_artists aa2 JOIN artists p2 ON p2.id=aa2.artist_id WHERE aa2.artwork_id=a.id) creators,
              (SELECT to_jsonb(i)
                FROM institutions i WHERE i.id=a.current_institution_id) institution
              FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
              WHERE aa.artist_id=%s AND a.primary_media_id IS NULL AND a.status<>'archived'
              AND a.work_type IN ('painting','drawing','watercolor','print','fresco','icon')
              AND a.creation_year_end<=1955 AND a.creation_year_start IS NOT NULL
              AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
              AND artline_has_selection_evidence(a.id)
              ORDER BY a.id LIMIT 2000""", (p['id'],)).fetchall()
            for w in rows:
                w['artist'] = p
                works.append(w)
    unique = {w['artwork_id']:w for w in works}
    all_artists={p['id']:p for p in artists+previous['artists']}
    core.save_new(RUN/'audit-expanded.json', {'at':core.now(),'artists':list(all_artists.values()),'works':list(unique.values())})
    print(json.dumps({'eligible_gaps':len(unique),'artists':len(all_artists)},ensure_ascii=False,default=str),flush=True)


class Fetcher:
    def __init__(self):
        self.session=requests.Session()
        self.session.headers['User-Agent']='Artline/1.0 (+https://github.com/vadimdulub/artline; selected historical artwork research)'
        self.last=0

    def get(self,url,limit=5_000_000,image=False):
        if urlparse(url).scheme!='https' or not re.fullmatch(r'(?:www|uploads\d*)\.wikiart\.org',urlparse(url).hostname or ''):
            raise ValueError('Unexpected WikiArt host')
        key=core.sha(url.encode());path=(ORIGINALS if image else RUN/'captures')/(key+'.body');receipt=RUN/'captures'/(key+'.json')
        if path.exists():
            raw=path.read_bytes();r=json.loads(receipt.read_bytes())
            if core.sha(raw)!=r['sha256']:raise ValueError('Capture checksum changed')
            return raw,r
        global FETCH_NEXT
        with FETCH_GATE:
            slot=max(time.monotonic(),FETCH_NEXT);FETCH_NEXT=slot+FETCH_INTERVAL
        time.sleep(max(0,slot-time.monotonic()))
        with self.session.get(url,timeout=(15,40),stream=True,allow_redirects=True) as r:
            if any(urlparse(x.url).hostname!='www.wikiart.org' for x in r.history):raise ValueError('Unexpected redirect')
            if urlparse(r.url).hostname!=urlparse(url).hostname:raise ValueError('Redirect left source host')
            r.raise_for_status()
            data=bytearray()
            for chunk in r.iter_content(65536):
                data.extend(chunk)
                if len(data)>limit:raise ValueError('Source exceeds selected byte budget')
            raw=bytes(data)
            record={'url':url,'final_url':r.url,'checked_at':core.now(),'sha256':core.sha(raw),'bytes':len(raw),
                    'content_type':r.headers.get('Content-Type'),'etag':r.headers.get('ETag')}
        core.save_new(path,raw);core.save_new(receipt,record)
        return raw,record


def probe():
    f=Fetcher()
    raw,receipt=f.get('https://www.wikiart.org/en/ivan-aivazovsky/all-works/text-list')
    soup=BeautifulSoup(raw,'html.parser')
    links=[{'url':urljoin(receipt['final_url'],a['href']),'text':a.get_text(' ',strip=True),'context':a.parent.get_text(' ',strip=True)}
           for a in soup.select('a[href]') if a['href'].startswith('/en/ivan-aivazovsky/')]
    print(json.dumps({'links':links[:15],'n':len(links)},ensure_ascii=False),flush=True)


def discover():
    audit=json.loads((RUN/'audit-expanded.json').read_bytes());f=Fetcher();all_matches=[];outcomes=[]
    for artist in audit['artists']:
        slug='-'.join(norm(artist['display_name']).split())
        result_path=RUN/'discovery-v2'/(artist['id']+'.json')
        if result_path.exists():
            r=json.loads(result_path.read_bytes());all_matches.extend(r['matches']);outcomes.append(r);continue
        r={'artist':artist,'matches':[]}
        try:
            raw,receipt=f.get('https://www.wikiart.org/en/'+slug+'/all-works/text-list')
            soup=BeautifulSoup(raw,'html.parser')
            rows=[w for w in audit['works'] if w['artist']['id']==artist['id']]
            pages=[(soup,receipt)]
            if any(re.search('[А-Яа-я]',w['title']) for w in rows):
                ru=soup.select_one('link[hreflang="ru"]')
                if ru:
                    ru_raw,ru_receipt=f.get(ru['href']);pages.append((BeautifulSoup(ru_raw,'html.parser'),ru_receipt))
            links={}
            for page,page_receipt in pages:
                prefix=urlparse(page_receipt['final_url']).path.removesuffix('/all-works/text-list')+'/'
                for a in page.select('a[href]'):
                    if not a['href'].startswith(prefix):continue
                    tail=a.parent.get_text(' ',strip=True).removeprefix(a.get_text(' ',strip=True)).strip(' ,')
                    if not re.fullmatch(r'(?:c\.|ок\.)?\s*\d{4}',tail):continue
                    year=int(re.search(r'\d{4}',tail)[0])
                    links[a['href']]={'title':a.get_text(' ',strip=True),'year':year,'url':urljoin(page_receipt['final_url'],a['href']),'index_receipt':page_receipt}
            for w in rows:
                if len(w['creators'])!=1 or w['creators'][0]['role']!='primary':continue
                titles={norm(w['title']),norm(w.get('alternate_title'))}-{''}
                matches=[l for l in links.values() if norm(l['title']) in titles and w['creation_year_start']<=l['year']<=w['creation_year_end'] and l['year']<=1955]
                language='/ru/' if re.search('[А-Яа-я]',w['title']) else '/en/'
                preferred=[l for l in matches if language in l['url']]
                if preferred:matches=preferred
                if len(matches)==1:
                    r['matches'].append({'work':w,'wikiart':matches[0],'index_receipt':matches[0]['index_receipt']})
            r.update(outcome='matched',index_entries=len(links),gaps=len(rows))
        except (ValueError,requests.RequestException) as e:
            r.update(outcome='source_unavailable',reason=str(e)[:300])
            if isinstance(e,requests.HTTPError) and e.response.status_code in (403,429):
                core.save_new(result_path,r);print('Source paused',r,flush=True);break
        core.save_new(result_path,r);all_matches.extend(r['matches']);outcomes.append(r)
        print(artist['display_name'],r['outcome'],len(r['matches']),'total',len(all_matches),flush=True)
    # A single source work cannot be automatically attached to multiple local identities.
    counts=collections.Counter(m['wikiart']['url'] for m in all_matches)
    unique=[m for m in all_matches if counts[m['wikiart']['url']]==1]
    core.save_new(RUN/'discovered-v2.json',{'matches':unique,'ambiguous':[m for m in all_matches if counts[m['wikiart']['url']]>1],
        'artist_outcomes':[{k:v for k,v in r.items() if k!='matches'} for r in outcomes]})
    print('Distinct matched artwork candidates',len(unique),flush=True)


def discovered_matches():
    matches=[]
    for path in sorted((RUN/'discovery-v2').glob('*.json')):
        matches.extend(json.loads(path.read_bytes())['matches'])
    count=collections.Counter(m['wikiart']['url'] for m in matches)
    identities=collections.defaultdict(set)
    for match in matches:identities[match['work']['artwork_id']].add(match['wikiart']['url'])
    result=[]
    for match in matches:
        aid=match['work']['artwork_id'];url=match['wikiart']['url']
        if count[url]!=1:continue
        if len(identities[aid])>1:
            resolution=RUN/'identity-resolutions'/(aid+'.json')
            if not resolution.exists() or json.loads(resolution.read_bytes())['selected_url']!=url:continue
        result.append(match)
    return result


def page_record(match,raw,receipt):
    w=match['work'];soup=BeautifulSoup(raw,'html.parser')
    tag=soup.select_one('.wiki-layout-painting-info-bottom[ng-init]')
    if not tag:raise ValueError('Artwork metadata missing')
    value=tag['ng-init'].split('=',1)[1].strip();record=json.loads(value)
    if match.get('wikiart',{}).get('source_id') and match['wikiart']['source_id']!=record['_id']:
        raise ValueError('Selected source object identifier changed')
    if norm(record['title']) not in {norm(w['title']),norm(w.get('alternate_title'))}:
        raise ValueError('Artwork title changed')
    dates=creation_date(record.get('year'))
    if not dates:raise ValueError('Artwork creation date needs disambiguation')
    year=dates['creation_year_start'];end=dates['creation_year_end']
    if year>end or end>1955 or end<w['creation_year_start'] or year>w['creation_year_end']:raise ValueError('Artwork date differs or exceeds cutoff')
    source_artist=urlparse(receipt['final_url']).path.rsplit('/',1)[0]
    if record['artistUrl']!=source_artist:raise ValueError('Artist page identity differs')
    image=soup.select_one('img[itemprop="image"]')
    if not image:raise ValueError('Selected artwork image missing')
    label=soup.select_one('.copyright-wrapper .copyright')
    public_domain=bool(label and label.select_one('.copyright-icon-public-domain'))
    rights='public_domain' if public_domain else ('restricted' if label else 'unknown')
    variants=[dict(n.attrs) for n in soup.select('.image-variants-container a[data-image-url]')]
    text=(soup.select_one('.wiki-layout-artwork-info article') or soup).get_text(' ',strip=True)
    return {'artwork_id':w['artwork_id'],'title':w['title'],'artist':w['artist']['display_name'],
            'artist_slug':w['artist']['slug'],'work':w,'page':receipt['final_url'],'source_image_url':image['src'],
            'source_id':record['_id'],'source_year':year,'source_year_end':end,'rights_status':rights,
            'license_label':'Public domain (WikiArt label)' if public_domain else ('Copyright protected (WikiArt label)' if label else 'Rights not specified'),
            'source_rights_label':label.get_text(' ',strip=True) if label else None,
            'policy_url':'https://www.wikiart.org/en/terms-of-use','page_receipt':receipt,
            'source_metadata':record,'source_image_variants':variants,'source_description':text[:5000],
            'checked_at':core.now(),'selection_basis':'User-authorized artwork creation cutoff <=1955; existing collection record; exact artist index, normalized title and compatible creation date. Source rights label recorded without treating age as clearance.'}


def prepare_one(match):
    f=Fetcher();aid=match['work']['artwork_id'];output=RUN/'images'/(aid+'.json');held=RUN/'prepare-held'/(aid+'.json')
    if output.exists() or held.exists():return 'already_processed'
    try:
        selected=RUN/'selected'/(aid+'.json')
        if selected.exists():im=json.loads(selected.read_bytes())
        else:
            raw,receipt=f.get(match['wikiart']['url']);im=page_record(match,raw,receipt);core.save_new(selected,im)
        original,download=f.get(im['source_image_url'],limit=8_000_000,image=True)
        data,width,height,quality=core.compress(original)
        if max(width,height)<150 or min(width,height)<32:raise ValueError('Image too small for catalogue')
        digest=core.sha(data);path='/assets/artworks/wikiart/'+aid+'-'+digest[:16]+'.jpg'
        core.save_new(ROOT/'apps/web/public'/path.lstrip('/'),data)
        im.update(path=path,sha256=digest,bytes=len(data),width=width,height=height,jpeg_quality=quality,
            media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,path)),download=download,
            attribution_text=im['artist']+'. '+im['title']+'. Image: WikiArt. '+im['license_label']+'. Proportionally resized and JPEG compressed; no crop.',
            transform='Full-frame proportional resize and JPEG compression; no generated content')
        core.save_new(output,im)
        print('Prepared',im['artist'],im['title'][:70],im['rights_status'],flush=True)
        return 'prepared'
    except (ValueError,requests.RequestException,OSError) as error:
        core.save_new(held,{'artwork_id':aid,'url':match['wikiart']['url'],'error':str(error)[:400]})
        print('Held',aid,str(error)[:160],flush=True)
        if isinstance(error,requests.HTTPError) and error.response.status_code in (403,429):
            raise RuntimeError('Image preparation paused for source response') from error
        return 'held'


def prepare():
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=PREPARE_WORKERS) as pool:
        while True:
            matches=[m for m in discovered_matches() if not (RUN/'images'/(m['work']['artwork_id']+'.json')).exists()
                     and not (RUN/'prepare-held'/(m['work']['artwork_id']+'.json')).exists()]
            # Bounded chunks limit in-flight work and allow new discovery checkpoints.
            for start in range(0,len(matches),40):
                for result in pool.map(prepare_one,matches[start:start+40]):counts[result]+=1
                print('Preparation progress',dict(counts),flush=True)
            if (RUN/'discovered-v2.json').exists() and all((RUN/'images'/(m['work']['artwork_id']+'.json')).exists()
                or (RUN/'prepare-held'/(m['work']['artwork_id']+'.json')).exists() for m in discovered_matches()):break
            time.sleep(5)
    print('Preparation finished',dict(counts),flush=True)
    core.save_new(RUN/'preparation-finished.json',{'at':core.now(),'prepared':len(list((RUN/'images').glob('*.json'))),'held':len(list((RUN/'prepare-held').glob('*.json')))})


def retry_held():
    matches={m['work']['artwork_id']:m for m in discovered_matches()};counts=collections.Counter()
    for path in sorted((RUN/'prepare-held').glob('*.json')):
        previous=json.loads(path.read_bytes());aid=previous['artwork_id']
        if previous['error'] not in ('Artwork creation date needs disambiguation','Artwork title changed'):continue
        match=matches[aid]
        try:
            raw,receipt=Fetcher().get(match['wikiart']['url']);page_record(match,raw,receipt)
        except ValueError:continue
        archived=RUN/'prepare-held-history'/path.name;archived.parent.mkdir(parents=True,exist_ok=True)
        path.rename(archived)
        counts[prepare_one(match)]+=1
    print('Rechecked preparation outcomes',dict(counts),flush=True)


def same_artwork(a,b):
    excluded={'id','current_institution_id','primary_media_id','revision','created_at','updated_at','published_at','created_by','updated_by','location_checked_at'}
    return {k:v for k,v in a.items() if k not in excluded}=={k:v for k,v in b.items() if k not in excluded}


def preflight():
    images=[json.loads(p.read_bytes()) for p in sorted((RUN/'images').glob('*.json')) if not (RUN/'delivery'/p.name).exists()][:100]
    if not images:return None
    batch=core.sha(core.encode([im['artwork_id'] for im in images]))[:16]
    plan_path=RUN/'delivery-plans'/(batch+'.json')
    if plan_path.exists():return plan_path
    dsns={'local':'postgres://localhost/artline','cloud':core.cloud_dsn()};targets={};held=[]
    for target,dsn in dsns.items():
        with read_only(dsn) as db:
            ids=[im['artwork_id'] for im in images]
            rows=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
            byid={r['record']['id']:r['record'] for r in rows}
            all_identifiers=[{'aid':im['artwork_id'],'scheme':e['scheme'],'external_id':e['external_id']} for im in images for e in (im['work'].get('identifiers') or [])]
            links=db.execute("""WITH input AS(SELECT * FROM jsonb_to_recordset(%s) AS x(aid text,scheme text,external_id text))
                SELECT i.aid,to_jsonb(a) record FROM input i JOIN external_identifiers e
                ON e.entity_type='artwork' AND e.scheme=i.scheme AND e.external_id=i.external_id
                JOIN artworks a ON a.id=e.entity_id""",(Jsonb(all_identifiers),)).fetchall()
            alternatives=collections.defaultdict(dict)
            for r in links:alternatives[r['aid']][r['record']['id']]=r['record']
            selected={}
            for im in images:
                aid=im['artwork_id'];record=byid.get(aid)
                if record is None and len(alternatives[aid])==1:record=next(iter(alternatives[aid].values()))
                if not record or not same_artwork(record,im['work']['before_record']):
                    held.append({'target':target,'artwork_id':aid,'reason':'Target identity missing or different'});continue
                if record['primary_media_id'] not in (None,im['media_id']):
                    held.append({'target':target,'artwork_id':aid,'reason':'Existing image preserved'});continue
                selected[aid]=record
            institutions={r['id']:r['slug'] for r in db.execute('SELECT id::text,slug FROM institutions WHERE id=ANY(%s::uuid[])',
                ([r['current_institution_id'] for r in selected.values() if r['current_institution_id']],)).fetchall()}
            for im in images:
                aid=im['artwork_id']
                if aid in selected and institutions.get(selected[aid]['current_institution_id'])!=(im['work']['institution'] or {}).get('slug'):
                    held.append({'target':target,'artwork_id':aid,'reason':'Holding institution differs'});del selected[aid]
            target_ids=[r['id'] for r in selected.values()]
            creators=db.execute("""SELECT aa.artwork_id::text,p.slug,aa.attribution_role FROM artwork_artists aa
                JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY p.slug""",(target_ids,)).fetchall()
            for im in images:
                aid=im['artwork_id']
                if aid not in selected:continue
                actual=[(r['slug'],r['attribution_role']) for r in creators if r['artwork_id']==selected[aid]['id']]
                expected=sorted((r['slug'],r['role']) for r in im['work']['creators'])
                if actual!=expected:
                    held.append({'target':target,'artwork_id':aid,'reason':'Creator attribution differs'});del selected[aid]
            targets[target]=selected
            core.save_new(BACKUP/batch/(target+'-before.json'),{'artworks':selected,'creators':creators})
    plan={'targets':targets,'held':held,'images':[im['artwork_id'] for im in images],
        'backups':{t:{'path':str(BACKUP/batch/(t+'-before.json')),'sha256':core.sha((BACKUP/batch/(t+'-before.json')).read_bytes())} for t in targets}}
    core.save_new(plan_path,plan)
    print(json.dumps({'prepared':len(images),'targets':{t:len(v) for t,v in targets.items()},'held':len(held)}),flush=True)
    return plan_path


def attach(db,im,before):
    with db.transaction():
        db.execute("SET LOCAL lock_timeout='3s'")
        row=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',(before['id'],)).fetchone()
        if not row:raise ValueError('Target disappeared')
        current=row['record']
        if current['primary_media_id']==im['media_id']:return 'already_attached'
        if current!=before:raise ValueError('Target changed after backup')
        creators=db.execute("""SELECT p.slug,aa.attribution_role FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id
            WHERE aa.artwork_id=%s ORDER BY p.slug""",(before['id'],)).fetchall()
        if [(r['slug'],r['attribution_role']) for r in creators]!=sorted((r['slug'],r['role']) for r in im['work']['creators']):raise ValueError('Target creator changed')
        source=db.execute("SELECT id FROM sources WHERE slug='wikiart-selected-images-20260919'").fetchone()
        if source is None:
            source=db.execute("""INSERT INTO sources(slug,name,source_type,base_url) VALUES('wikiart-selected-images-20260919','WikiArt selected artwork reproductions','collection_page','https://www.wikiart.org/')
                ON CONFLICT(slug) DO UPDATE SET slug=EXCLUDED.slug RETURNING id""").fetchone()
        sid=source['id']
        db.execute("""INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,
            checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
            VALUES(%s,'local',%s,%s,'WikiArt','image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING""",
            (im['media_id'],im['path'],im['page'],im['width'],im['height'],im['bytes'],im['sha256'],im['title']+' — '+im['artist'],
             im['rights_status'],im['license_label'],im['policy_url'],im['artist']+'; WikiArt',im['attribution_text'],im['download']['checked_at'],
             im['checked_at'] if im['rights_status']=='public_domain' else None,ACTOR))
        db.execute("""INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
            VALUES(%s,%s,%s,%s,%s,%s,%s,'wikiart-user-selected-v1',%s,%s) ON CONFLICT(media_id) DO NOTHING""",
            (im['media_id'],sid,im['source_id'],im['page_receipt']['sha256'],im['source_image_url'],im['policy_url'],
             'WikiArt per-artwork rights label recorded as supplied. Creation age is the user selection rule, not a legal rights determination. No independent licensing assessment.',
             im['checked_at'],Jsonb({k:v for k,v in im.items() if k!='work'})))
        db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',
            (im['media_id'],ACTOR,before['id']))
    return 'attached'


def deliver(plan_path=None):
    if plan_path is None:
        for path in sorted((RUN/'delivery-plans').glob('*.json')):deliver(path)
        return
    plan=json.loads(plan_path.read_bytes())
    for b in plan['backups'].values():
        if core.sha(Path(b['path']).read_bytes())!=b['sha256']:raise ValueError('Recovery snapshot mismatch')
    bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    dbs={'local':psycopg.connect('postgres://localhost/artline',autocommit=True,row_factory=dict_row),
          'cloud':psycopg.connect(core.cloud_dsn(),autocommit=True,row_factory=dict_row)}
    counts=collections.Counter()
    try:
        for aid in plan['images']:
            result_path=RUN/'delivery'/(aid+'.json')
            if result_path.exists():continue
            im=json.loads((RUN/'images'/(aid+'.json')).read_bytes());data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
            if core.sha(data)!=im['sha256'] or len(data)!=im['bytes'] or len(data)>100000:raise ValueError('Derivative checksum mismatch')
            blob=bucket.blob(im['path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'artwork-id':aid,'provider':'WikiArt','source-record-id':im['source_id']}
            blob.cache_control='public,max-age=31536000,immutable'
            try:blob.upload_from_string(data,content_type='image/jpeg',if_generation_match=0,timeout=60)
            except PreconditionFailed:blob.reload(timeout=30)
            if blob.size!=len(data) or blob.md5_hash!=base64.b64encode(hashlib.md5(data).digest()).decode():raise ValueError('Uploaded image checksum mismatch')
            result={'artwork_id':aid,'at':core.now(),'path':im['path'],'sha256':im['sha256'],'generation':blob.generation,'targets':{}}
            for target,db in dbs.items():
                before=plan['targets'][target].get(aid)
                if before:
                    result['targets'][target]=attach(db,im,before);counts[target]+=1
                else:result['targets'][target]='not_selected'
            core.save_new(result_path,result);counts['uploaded']+=1
            print('Delivered',dict(counts),im['artist'],im['title'][:70],flush=True)
    finally:
        for db in dbs.values():db.close()
    print('Delivery finished',dict(counts),flush=True)


def deliver_ready():
    # Preparation and attachment have separate checkpoints; never read partially
    # flushed evidence, and never claim an image the producer has not finished.
    while True:
        plan_path=preflight()
        if plan_path:deliver(plan_path)
        elif (RUN/'preparation-finished.json').exists():break
        else:time.sleep(15)


def inspect_holds():
    held={}
    for path in (RUN/'delivery-plans').glob('*.json'):
        for item in json.loads(path.read_bytes())['held']:
            if item['target']=='cloud':held[item['artwork_id']]=item
    images={aid:json.loads((RUN/'images'/(aid+'.json')).read_bytes()) for aid in held}
    with read_only(core.cloud_dsn()) as db:
        rows=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])',(list(held),)).fetchall()
        byid={r['record']['id']:r['record'] for r in rows}
    output=[]
    for aid,im in images.items():
        current=byid.get(aid);before=im['work']['before_record']
        differences={k:{'local':str(v)[:120],'cloud':str(current.get(k))[:120]} for k,v in before.items() if current and v!=current.get(k)}
        output.append({'artwork_id':aid,'title':im['title'],'cloud_present':bool(current),'differences':differences})
    print(json.dumps(output,ensure_ascii=False,indent=2),flush=True)


def verify():
    receipts=[json.loads(p.read_bytes()) for p in sorted((RUN/'delivery').glob('*.json'))]
    images={r['artwork_id']:json.loads((RUN/'images'/(r['artwork_id']+'.json')).read_bytes()) for r in receipts}
    before={t:{} for t in ('local','cloud')}
    for path in sorted((RUN/'delivery-plans').glob('*.json')):
        plan=json.loads(path.read_bytes())
        for target in before:before[target].update(plan['targets'][target])
    errors=[];databases={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        attached=[r for r in receipts if r['targets'].get(target) in ('attached','already_attached')]
        with read_only(dsn) as db:
            ids=[before[target][r['artwork_id']]['id'] for r in attached]
            rows=db.execute('''SELECT to_jsonb(a) artwork,to_jsonb(m) media FROM artworks a
                JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])''',(ids,)).fetchall()
            byid={r['artwork']['id']:r for r in rows};checked=0
            ignored={'primary_media_id','revision','updated_at','updated_by'}
            for r in attached:
                aid=r['artwork_id'];im=images[aid];old=before[target][aid];current=byid.get(old['id'])
                if not current or {k:v for k,v in current['artwork'].items() if k not in ignored}!={k:v for k,v in old.items() if k not in ignored}:
                    errors.append({'target':target,'artwork_id':aid,'error':'Catalogue metadata changed'});continue
                m=current['media']
                if m['id']!=im['media_id'] or m['checksum_sha256']!=im['sha256'] or m['rights_status']!=im['rights_status'] or m['source_page_url']!=im['page']:
                    errors.append({'target':target,'artwork_id':aid,'error':'Media differs'});continue
                checked+=1
            databases[target]={'attached':len(attached),'verified':checked}
    def check(r):
        im=images[r['artwork_id']];local=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        result={'artwork_id':r['artwork_id'],'local_file_verified':len(local)==im['bytes'] and core.sha(local)==im['sha256']}
        try:
            response=requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app'+im['path'],timeout=(15,45))
            result.update(status=response.status_code,public_file_verified=response.status_code==200 and core.sha(response.content)==im['sha256'])
        except requests.RequestException as error:result.update(public_file_verified=False,error=str(error)[:160])
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:files=list(pool.map(check,receipts))
    for r in files:
        if not r['local_file_verified'] or not r['public_file_verified']:errors.append(r)
    sample={}
    for r in receipts:
        if r['targets'].get('cloud') in ('attached','already_attached'):
            im=images[r['artwork_id']];sample.setdefault((im['artist_slug'],im['rights_status']),r)
    api_checks=[]
    for r in list(sample.values())[:30]:
        im=images[r['artwork_id']];cloud_id=before['cloud'][r['artwork_id']]['id']
        url='https://artline-web-lpuqqlugnq-ew.a.run.app/api/backend/v1/artists/'+im['artist_slug']+'/works/'+cloud_id
        response=requests.get(url,timeout=(15,45));record=response.json() if response.status_code==200 else {}
        expected=im['path']
        okay=response.status_code==200 and record.get('title')==im['title'] and record.get('media_url')==expected
        api_checks.append({'artwork_id':r['artwork_id'],'http_status':response.status_code,'verified':okay,'rights_status':im['rights_status']})
        if not okay:errors.append({'artwork_id':r['artwork_id'],'error':'Artwork API differs','http_status':response.status_code})
    result={'at':core.now(),'uploaded':len(receipts),'artists':len({im['artist_slug'] for im in images.values()}),
        'rights_labels':dict(collections.Counter(im['rights_status'] for im in images.values())),
        'bytes':sum(im['bytes'] for im in images.values()),'databases':databases,'file_checks':files,'api_checks':api_checks,'errors':errors}
    path=RUN/('verification-'+str(len(receipts))+'-'+str(int(time.time()))+'.json');core.save_new(path,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('file_checks','api_checks')},ensure_ascii=False),flush=True)
    print('Verification receipt',path,flush=True)
    if errors:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['audit','probe','discover','prepare','retry_held','preflight','deliver','deliver_ready','inspect_holds','verify']);args=p.parse_args()
    globals()[args.phase]()
