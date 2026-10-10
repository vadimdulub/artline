#!/usr/bin/env python3
"""Resumable, production-only research for the frozen 200-painter cohort.

No database fixtures, publishing, metadata replacement or existing-image
replacement. Explicit user authorization continues the Otto Dix workflow.
"""
import argparse
import collections
import concurrent.futures
import csv
import gzip
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
import uuid
from urllib.parse import urljoin,urlsplit

import requests
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
q=module('random_research','ops/research-production-wikiart-images-20261006.py');r=q.r
dates=module('random_dates','ops/wikiart-selected-images.py')
OP='random-200-painters-round5-20261007';RUN=ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
r.RUN=q.RUN=RUN;r.PORT=55474
ACTOR='local-european-research';COLLECTION='42c83e94-d1f2-539a-accb-b4e9ded61f06'
POLICY='https://www.wikiart.org/en/terms-of-use'
LOCK=threading.Lock();NEXT=0.;STOP=threading.Event()
SOURCE_SESSIONS=threading.local()
_BASE_CONNECT=r.connect;_FIELDS_LOCK=threading.Lock();_PRODUCTION_FIELDS=None


def cached_connection(target='local',readonly=True):
    """Cache the production secret in memory for this process, never on disk."""
    global _PRODUCTION_FIELDS
    if target!='production':return _BASE_CONNECT(target,readonly=readonly)
    with _FIELDS_LOCK:
        if _PRODUCTION_FIELDS is None:
            secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319'],text=True).strip()
            _PRODUCTION_FIELDS=r.psycopg.conninfo.conninfo_to_dict(secret)
            _PRODUCTION_FIELDS.update(host='127.0.0.1',port=str(r.PORT),sslmode='disable',connect_timeout='20')
    return r.psycopg.connect(**_PRODUCTION_FIELDS,autocommit=True,row_factory=r.dict_row,
        options='-c timezone=UTC -c statement_timeout=180000'+(' -c default_transaction_read_only=on' if readonly else ''))


r.connect=cached_connection


def uid(value):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+value))
def cohort():
    data=r.load(RUN/'cohort.json');assert len(data['painters'])==200
    return data['painters']


def status(phase,**values):
    path=RUN/'progress'/f'{phase}.json';path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.partial');tmp.write_text(json.dumps({'at':r.now(),'phase':phase,**values},ensure_ascii=False,indent=2));tmp.replace(path)


def cache_catalogue():
    """Index existing captures, preserving their original retrieval timestamps."""
    path=RUN/'capture-cache.json'
    if path.exists():return r.load(path)
    index={}
    folders=[]
    for parent in (ROOT/'docs/research').iterdir():
        if not parent.is_dir() or parent==RUN:continue
        for name in ['captures','page-captures','retry-captures','translation-captures','artist-link-captures','index-captures','translated-index-captures','artist-index-captures','directory-captures']:
            folder=parent/name
            if folder.is_dir():folders.append(folder)
    for folder in folders:
        for receipt in folder.glob('*.json'):
            try:
                rc=r.load(receipt)
                if not isinstance(rc,dict):continue
                url=rc.get('url')
                if not url or urlsplit(url).hostname!='www.wikiart.org':continue
                code=rc.get('status',rc.get('status_code',200))
                if code!=200:continue
                body=ROOT/rc['body_path'] if rc.get('body_path') else receipt.with_suffix('.body')
                if not body.exists() or not rc.get('sha256'):continue
                when=rc.get('retrieved_at') or rc.get('checked_at') or rc.get('at') or ''
                old=index.get(url)
                if not old or when>old['retrieved_at']:
                    index[url]={'receipt_path':str(receipt.relative_to(ROOT)),'body_path':str(body.relative_to(ROOT)),
                                'retrieved_at':when,'sha256':rc['sha256']}
            except (ValueError,TypeError,KeyError):continue
    r.save(path,index);print('Indexed reusable public metadata captures',len(index),flush=True);return index


CACHE=None
def capture(url,tag='captures',fresh=False):
    global NEXT,CACHE
    key=r.sha(url.encode());dest=RUN/tag/(key+'.receipt.json');bodypath=RUN/tag/(key+'.body.gz')
    if dest.exists():
        rc=r.load(dest);raw=gzip.decompress(bodypath.read_bytes());assert r.sha(raw)==rc['sha256'];return raw,rc
    if CACHE is None:CACHE=cache_catalogue()
    if not fresh and url in CACHE:
        old=CACHE[url];path=ROOT/old['body_path'];raw=path.read_bytes()
        if path.suffix=='.gz':raw=gzip.decompress(raw)
        assert r.sha(raw)==old['sha256']
        original=r.load(ROOT/old['receipt_path'])
        rc={'url':url,'final_url':original.get('final_url',url),'status':200,'retrieved_at':old['retrieved_at'],
            'sha256':old['sha256'],'bytes':len(raw),'body_path':str(bodypath.relative_to(ROOT)),
            'reused_receipt_path':old['receipt_path'],'reused_body_path':old['body_path']}
        r.save(bodypath,gzip.compress(raw,mtime=0));r.save(dest,rc);return raw,rc
    if STOP.is_set():raise RuntimeError('Public source access paused after HTTP 403/429; cached evidence remains usable')
    with LOCK:
        slot=max(NEXT,time.monotonic());NEXT=slot+.2
    time.sleep(max(0,slot-time.monotonic()))
    for attempt in range(3):
        if not hasattr(SOURCE_SESSIONS,'session'):SOURCE_SESSIONS.session=requests.Session()
        response=SOURCE_SESSIONS.session.get(url,headers={'User-Agent':'ArtlineCatalogueResearch/1.0 (selected 200-painter source verification)'},timeout=(15,45))
        if response.status_code in [403,429]:STOP.set();break
        if response.status_code not in [500,502,503,504] or attempt==2:break
        time.sleep(1+attempt*2)
    raw=response.content
    rc={'url':url,'final_url':response.url,'status':response.status_code,'retrieved_at':r.now(),'sha256':r.sha(raw),
        'bytes':len(raw),'body_path':str(bodypath.relative_to(ROOT)),'content_type':response.headers.get('Content-Type'),
        'retry_after':response.headers.get('Retry-After')}
    r.save(bodypath,gzip.compress(raw,mtime=0));r.save(dest,rc);return raw,rc


def snapshot():
    pairs=cohort();ids=[x['artist']['id'] for x in pairs]
    if (RUN/'snapshot.json').exists():print('Preserving completed production snapshot',flush=True);return
    with r.connect('production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        query='''SELECT a.id::text,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_display,
          a.date_precision,a.work_type,a.status,a.current_institution_id::text,a.accession_number,a.primary_media_id::text,
          a.medium_text,a.dimensions_text,a.unlinked_creator_label,to_jsonb(a) artwork,
          ma.source_page_url existing_image_source,ma.checksum_sha256 existing_image_sha256
          FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id LEFT JOIN media_assets ma ON ma.id=a.primary_media_id
          WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived'
          AND (%s::uuid IS NULL OR a.id>%s::uuid) ORDER BY a.id LIMIT 1500'''
        r.save(RUN/'cohort-query-plan.json',db.execute('EXPLAIN (FORMAT JSON) '+query,(ids,None,None)).fetchone())
        cursor=None;allworks={};byartist=collections.defaultdict(list);parts=[]
        while True:
            works=db.execute(query,(ids,cursor,cursor)).fetchall()
            if not works:break
            works=list({w['id']:w for w in works}.values());wids=[x['id'] for x in works]
            creators=collections.defaultdict(list);identifiers=collections.defaultdict(list);citations=collections.defaultdict(list)
            for x in db.execute('SELECT artwork_id::text,artist_id::text,attribution_role,attribution_note FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id,attribution_role',(wids,)).fetchall():
                creators[x.pop('artwork_id')].append(x)
            for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(wids,)).fetchall():identifiers[x.pop('entity_id')].append(x)
            for x in db.execute("SELECT entity_id::text,field_name,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(wids,)).fetchall():citations[x.pop('entity_id')].append(x)
            for w in works:
                w.update(creators=creators[w['id']],identifiers=identifiers[w['id']],citations=citations[w['id']])
                allworks[w['id']]=w
                for c in w['creators']:
                    if c['artist_id'] in ids:byartist[c['artist_id']].append(w)
            path=RUN/'snapshot-parts'/f'{len(parts):04d}.json.gz';r.save_gz(path,works)
            parts.append({'path':str(path.relative_to(ROOT)),'sha256':r.sha(path.read_bytes()),'count':len(works)})
            cursor=works[-1]['id'];print('Scoped catalogue snapshot',len(allworks),'records',flush=True)
        institutions=[x['row'] for x in db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=ANY(%s::uuid[])',
                          (sorted({w['current_institution_id'] for w in allworks.values() if w['current_institution_id']}),)).fetchall()]
        # Scope exact object-level creator labels independently; no authority or holding rewrite here.
        labels=[x['artist']['display_name'] for x in pairs]
        unresolved=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE a.unlinked_creator_label=ANY(%s) AND a.status<>\'archived\'',(labels,)).fetchall()
    for pair in pairs:
        aid=pair['artist']['id'];r.save_gz(RUN/'catalogue-works'/(aid+'.json.gz'),byartist[aid])
    r.save(RUN/'institutions.json',institutions);r.save(RUN/'unlinked-creator-leads.json',unresolved)
    r.save(RUN/'snapshot.json',{'at':r.now(),'parts':parts,'painters':len(pairs),'artworks':len(allworks),
                              'images':sum(bool(w['primary_media_id']) for w in allworks.values()),'target':'production','read_only':True})
    print('Completed scoped production snapshot',len(allworks),'works;',sum(bool(w['primary_media_id']) for w in allworks.values()),'images',flush=True)


def indexes():
    global CACHE
    CACHE=cache_catalogue();pairs=cohort()
    def one(pair):
        aid=pair['artist']['id'];dest=RUN/'indexes'/(aid+'.json.gz')
        if dest.exists():return r.load(dest)
        url=pair['source']['url'];result={'artist_id':aid,'artist_name':pair['artist']['display_name'],'source':pair['source']}
        try:
            # Refresh the artist's complete list; captures of individual historic works can be reused.
            raw,rc=capture(url+'/all-works/text-list','index-captures',fresh=True)
            if rc['status']!=200:raise ValueError('HTTP '+str(rc['status']))
            soup=BeautifulSoup(raw,'html.parser');prefix=urlsplit(url).path+'/'
            works={}
            for a in soup.select('li a[href]'):
                if a['href'].startswith(prefix):
                    title=a.get_text(' ',strip=True);display=a.parent.get_text(' ',strip=True).removeprefix(title).strip(' ,')
                    works[urljoin(url,a['href'])]={'title':title,'url':urljoin(url,a['href']),'source_date':display,'date':dates.creation_date(display)}
            assert works or pair['source']['count']==0 or soup.select('li.painting-list-text-row'),'Empty artwork index'
            result.update(outcome='indexed',receipt=rc,items=list(works.values()))
        except Exception as exc:result.update(outcome='source_unavailable',error=str(exc)[:400],items=[])
        r.save_gz(dest,result);return result
    totals=collections.Counter();entries=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for n,result in enumerate(pool.map(one,pairs),1):
            totals[result['outcome']]+=1;entries+=len(result['items'])
            if n%10==0:
                print('Indexed painters',n,'/ 200;',entries,'artwork entries;',dict(totals),flush=True)
                status('indexes',completed=n,entries=entries,outcomes=dict(totals))
    r.save(RUN/'indexes-summary.json',{'at':r.now(),'painters':len(cohort()),'entries':entries,'outcomes':dict(totals)})


def pages():
    global CACHE
    CACHE=cache_catalogue();jobs=[];excluded=[]
    for pair in cohort():
        idx=r.load(RUN/'indexes'/(pair['artist']['id']+'.json.gz'))
        for item in idx['items']:
            date=item['date']
            if date and date['creation_year_start']>1970:
                excluded.append({'artist_id':pair['artist']['id'],**item,'outcome':'source_creation_after_1970'});continue
            jobs.append((pair,item))
    r.save(RUN/'index-date-exclusions.json.gz',gzip.compress(json.dumps(excluded,ensure_ascii=False).encode(),mtime=0))
    def one(job):
        pair,item=job;aid=pair['artist']['id'];dest=RUN/'pages'/aid/(r.sha(item['url'].encode())+'.json.gz')
        if dest.exists():return r.load(dest)
        result={'artist_id':aid,'index':item}
        try:
            raw,rc=capture(item['url'],'page-captures')
            if rc['status']!=200:raise ValueError('HTTP '+str(rc['status']))
            p=q.page_metadata(raw,rc)
            assert p['metadata']['artistUrl']==urlsplit(pair['source']['url']).path,'Source creator differs'
            soup=BeautifulSoup(raw,'html.parser');label=soup.select_one('.copyright-wrapper')
            p['rights_label']=label.get_text(' ',strip=True) if label else 'Rights label not supplied'
            p['rights_status']='public_domain' if p['rights_label']=='Public domain' else ('restricted' if label else 'unknown')
            p['date']=dates.creation_date(p['metadata'].get('year'))
            p['title']=html.unescape(p['metadata']['title'])
            p['reference_links']=[{'title':a.get_text(' ',strip=True),'url':urljoin(p['url'],a['href'])} for a in soup.select('.wiki-layout-artwork-info a[href]')
                                  if urlsplit(urljoin(p['url'],a['href'])).hostname not in ['www.wikiart.org','www.1st-art-gallery.com']]
            result.update(outcome='captured',page=p)
        except Exception as exc:result.update(outcome='source_unavailable',error=str(exc)[:400])
        r.save_gz(dest,result);return result
    counts=collections.Counter();byartist=collections.defaultdict(collections.Counter)
    print('Selected metadata pages',len(jobs),'; excluded known post-1970 entries',len(excluded),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for n,result in enumerate(pool.map(one,jobs),1):
            counts[result['outcome']]+=1;byartist[result['artist_id']][result['outcome']]+=1
            if n%100==0:
                print('Artwork pages',n,'/',len(jobs),dict(counts),flush=True)
                status('pages',completed=n,total=len(jobs),outcomes=dict(counts),painters_with_progress=len(byartist))
    r.save(RUN/'pages-summary.json',{'at':r.now(),'selected':len(jobs),'excluded_after_1970':len(excluded),'counts':dict(counts),
                                 'by_artist':{k:dict(v) for k,v in byartist.items()}})


def translations():
    global CACHE
    CACHE=cache_catalogue();jobs=[]
    museums={i['id']:i for i in r.load(RUN/'institutions.json')}
    for pair in cohort():
        aid=pair['artist']['id'];works=r.load(RUN/'catalogue-works'/(aid+'.json.gz'));languages={'en'}
        for w in works:
            text=' '.join([w['title'],w.get('alternate_title') or '',(museums.get(w['current_institution_id']) or {}).get('name','')])
            if re.search('[А-Яа-яЁё]',text):languages.add('ru')
            if re.search(r'\b(?:der|die|das|mit|und|bei|im|bildnis|landschaft|kunst|museum|portrait)\b',q.norm(text)):languages.add('de')
            if re.search(r'\b(?:le|la|les|du|des|de|et|portrait|musee|paysage)\b',q.norm(text)):languages.add('fr')
            if re.search(r'\b(?:museo|retrato|paisaje|el|los|las)\b',q.norm(text)):languages.add('es')
            if re.search(r'\b(?:museu|lisboa|porto|portugal|brasil|brazil)\b',q.norm(text)):languages.add('pt')
        for lang in sorted(languages):jobs.append((pair,lang))
    def one(job):
        pair,lang=job;aid=pair['artist']['id'];slug=urlsplit(pair['source']['url']).path.rsplit('/',1)[-1]
        dest=RUN/'translations'/(aid+'-'+lang+'.json.gz')
        if dest.exists():return r.load(dest)
        url='https://www.wikiart.org/'+lang+'/App/Painting/PaintingsByArtist?artistUrl='+slug+'&json=2'
        result={'artist_id':aid,'language':lang,'url':url}
        try:
            raw,rc=capture(url,'translation-captures');assert rc['status']==200
            items=json.loads(raw);assert isinstance(items,list)
            result.update(outcome='indexed',receipt=rc,items=items)
        except Exception as exc:result.update(outcome='source_unavailable',error=str(exc)[:400],items=[])
        r.save_gz(dest,result);return result
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for n,x in enumerate(pool.map(one,jobs),1):
            counts[x['outcome']]+=1
            if n%50==0:print('Translated indexes',n,'/',len(jobs),dict(counts),flush=True)
    r.save(RUN/'translations-summary.json',{'at':r.now(),'selected':len(jobs),'counts':dict(counts)})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','indexes','pages','translations']);args=p.parse_args();globals()[args.phase]()
