#!/usr/bin/env python3
"""Bounded public-source metadata capture. No image downloads or catalogue writes."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import threading
import time
from urllib.parse import urlencode, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

spec = importlib.util.spec_from_file_location('index', Path(__file__).with_name('source-index-20261009.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
RUN = m.RUN
UA = 'ArtlineSourceIndex/1.0 (https://artlines.org/about; selected scholarly metadata research)'
LOCKS = {}
GUARD = threading.Lock()


def blocked_hosts():
    rows = m.load(RUN / 'inherited-source-access-holds.json')
    hosts = {m.host(r.get('url') or 'https://' + (r.get('host') or r.get('provider'))) for r in rows}
    hosts.update({'metmuseum.org','collectionapi.metmuseum.org','nga.gov','royalcollection.org.uk'})
    for p in (RUN / 'access-holds').glob('*.json') if (RUN / 'access-holds').exists() else []:
        hosts.add(m.load(p)['host'])
    return hosts


def get(url, json_required=False):
    url = m.canonical_url(url)
    assert url and url.startswith('https://'), url
    key = hashlib.sha256(url.encode()).hexdigest()
    receipt_path = RUN / 'captures' / (key + '.json')
    body_path = RUN / 'captures' / (key + '.body.gz')
    if receipt_path.exists():
        rc = m.load(receipt_path)
        if rc['http_status'] != 200:
            raise ValueError('Previously failed request: ' + str(rc['http_status']))
        raw = gzip.decompress(body_path.read_bytes())
        assert hashlib.sha256(raw).hexdigest() == rc['sha256']
        return json.loads(raw) if json_required else raw, rc
    h = m.host(url)
    if h in blocked_hosts():
        raise ValueError('Inherited or current access hold for ' + h)
    with GUARD:
        lock = LOCKS.setdefault(h, threading.Lock())
    with lock:
        if h in blocked_hosts():
            raise ValueError('Access hold for ' + h)
        started = m.now()
        # Disable automatic redirects so an access-held host is never reached via alias.
        dest = url
        for _ in range(5):
            if m.host(dest) in blocked_hosts():
                raise ValueError('Redirect target has access hold')
            with requests.get(dest, headers={'User-Agent':UA}, timeout=(10,35), stream=True, allow_redirects=False) as response:
                if response.status_code in (301,302,303,307,308):
                    dest = urljoin(dest,response.headers['Location'])
                    if urlsplit(dest).scheme != 'https':
                        raise ValueError('Non-HTTPS redirect')
                    continue
                pieces, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 12_000_000:
                        raise ValueError('Metadata response exceeds selected byte budget')
                    pieces.append(chunk)
                raw = b''.join(pieces)
                rc = dict(url=url,final_url=dest,retrieved_at=started,http_status=response.status_code,
                    content_type=response.headers.get('Content-Type'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                    body_path=str(body_path.relative_to(m.ROOT)),etag=response.headers.get('ETag'),last_modified=response.headers.get('Last-Modified'))
                body_path.parent.mkdir(parents=True,exist_ok=True)
                body_path.write_bytes(gzip.compress(raw,mtime=0))
                m.save(receipt_path,rc)
                if response.status_code in (401,403,429):
                    m.save(RUN / 'access-holds' / (key+'.json'),dict(host=h,url=url,http_status=response.status_code,at=started,receipt=str(receipt_path.relative_to(m.ROOT))))
                response.raise_for_status()
                if any(x in raw[:12000].lower() for x in [b'just a moment...', b'verify you are human', b'access denied']):
                    m.save(RUN / 'access-holds' / (key+'.json'),dict(host=h,url=url,http_status=response.status_code,at=started,reason='Challenge or denial HTML'))
                    raise ValueError('Challenge or denial page')
                time.sleep(0.3)
                return json.loads(raw) if json_required else raw, rc
        raise ValueError('Too many redirects')


def evidence(rc, locator=None):
    r = dict(capture_url=rc['url'],captured_at=rc['retrieved_at'],body_path=rc['body_path'],body_sha256=rc['sha256'])
    if locator is not None:
        r['record_locator'] = locator
    return r


def getty_books():
    output = RUN / 'fresh-resources/getty-books.json'
    if output.exists():
        print('Getty books already captured',len(m.load(output)));return
    results = {}
    for offset in range(0,800,100):
        url = 'https://www.getty.edu/publications-reports/api/search?' + urlencode(dict(size=100,**{'from':offset},can_download='true'))
        data, rc = get(url,True)
        assert isinstance(data.get('data'),list) and isinstance(data.get('total'),int)
        for b in data['data']:
            assert b['entity_type']=='work' and b['primary_name'] and b['slug_with_path'].startswith('/item/')
            title = b['primary_name'] + (': ' + b['subtitle'] if b.get('subtitle') else '')
            results[b['id']] = dict(url='https://www.getty.edu/publications-reports'+b['slug_with_path'],title=title,
                kind='book_or_catalogue',verified=rc['retrieved_at'],evidence=evidence(rc,b['id']),
                facts=dict(source_record_id=b['id'],publication_year=b.get('publication_year'),authors=b.get('authorship_description'),
                    contributors=b.get('contributors',[]),languages=b.get('language',[]),free_download_listed=True,
                    usage='Bibliographic metadata only. Full text and page-level claims not reviewed; downloadable does not mean image reuse permission.'))
        print('Getty publication metadata',len(results),'of',data['total'],flush=True)
        if offset+len(data['data'])>=data['total']:
            break
    m.save(output,list(results.values()))


def archive_books():
    output=RUN/'fresh-resources/library-books.json'
    if output.exists():
        print('Library books already captured',len(m.load(output)));return
    selections=[
        '(collection:getty OR collection:metmuseumlibraries OR collection:smithsonian) AND mediatype:texts AND (title:painting OR title:painters)',
        '(collection:getty OR collection:metmuseumlibraries) AND mediatype:texts AND (title:Byzantine OR title:Russian OR title:Greek OR title:icons)',
        '(collection:getty OR collection:metmuseumlibraries OR collection:smithsonian) AND mediatype:texts AND (title:history AND subject:Art)',
        '(collection:getty OR collection:metmuseumlibraries OR collection:smithsonian) AND mediatype:texts AND (title:catalogue OR title:catalog) AND (subject:Paintings OR subject:Art)',
    ]
    out={}
    for query in selections:
        params=[('q',query),('output','json'),('rows',200),('page',1),('sort[]','date asc')]
        params += [('fl[]',field) for field in ['identifier','title','creator','date','publisher','subject','language','collection','rights','licenseurl']]
        data,rc=get('https://archive.org/advancedsearch.php?'+urlencode(params),True)
        for b in data['response']['docs']:
            if not b.get('title') or not re.fullmatch('[A-Za-z0-9_.-]+',b['identifier']):
                continue
            out[b['identifier']]=dict(url='https://archive.org/details/'+b['identifier'],title=b['title'],kind='book_or_catalogue',
                verified=rc['retrieved_at'],evidence=evidence(rc,b['identifier']),facts=dict(b,bibliographic_only=True,
                    limitation='Institutional-library supplied bibliographic metadata; text, current holdings and reproduction rights require page-level review.'))
        print('Institutional art-library metadata',len(out),flush=True)
    m.save(output,list(out.values()))


def provider_checks():
    providers=m.load(RUN/'providers.json')
    def one(p):
        dest=RUN/'provider-checks'/(p['id']+'.json')
        if dest.exists():return m.load(dest)
        result=dict(provider_id=p['id'],url=p['url'],at=m.now())
        try:
            raw,rc=get(p.get('api_docs_url') or p['url'])
            soup=BeautifulSoup(raw,'html.parser')
            title=soup.title.get_text(' ',strip=True) if soup.title else None
            text=soup.get_text(' ',strip=True)
            result.update(receipt=rc,title=title,state='entrypoint_reachable_content_captured' if len(text)>100 else 'needs_content_review',
                limitation='Availability check only; provider authority and individual objects require separate evidence.')
        except Exception as exc:
            result.update(state='unavailable_or_held',error=type(exc).__name__+': '+str(exc)[:350])
        m.save(dest,result)
        print('Provider',p['id'],result['state'],flush=True)
        return result
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(one,providers))
    m.save(RUN/'provider-check-summary.json',dict(at=m.now(),counts=dict(Counter(r['state'] for r in rows)),providers=rows))


def probes():
    targets={
        'cleveland':'https://openaccess-api.clevelandart.org/api/artworks/?limit=1',
        'chicago':'https://api.artic.edu/api/v1/artworks?limit=1',
        'smk':'https://api.smk.dk/api/v1/art/search?keys=*&offset=0&rows=1',
    }
    for name,url in targets.items():
        try:
            data,rc=get(url,True)
            m.save(RUN/'native-probes'/(name+'.json'),dict(data=data,receipt=rc))
            rows=data.get('items',data.get('data',[]))
            print(name,'records',len(rows),'fields',list(rows[0]) if rows else [],flush=True)
        except Exception as exc:
            m.save(RUN/'native-probes'/(name+'-failure.json'),dict(url=url,at=m.now(),error=str(exc)))
            print(name,type(exc).__name__,str(exc)[:250],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['getty-books','library-books','providers','probes'])
    args=p.parse_args()
    {'getty-books':getty_books,'library-books':archive_books,'providers':provider_checks,'probes':probes}[args.command]()
