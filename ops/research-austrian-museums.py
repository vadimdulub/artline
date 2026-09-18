#!/usr/bin/env python3
"""Bounded official Austrian museum research, with cached public-page evidence.

No database writes. Never call Wien Museum's internal API. Belvedere requests
respect its published 30-second crawl delay, including selected image requests.
"""
import argparse, importlib.util, json, re, time
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('core',Path(__file__).with_name('enrich-artwork-images.py'))
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
ALLOWED={'sammlung.belvedere.at','sammlung.wienmuseum.at'}
core.HOSTS.update(ALLOWED)
_original_slot=core.provider_rate_slot

def rate_slot(host,cooldown=None):
    _original_slot(host,cooldown)
    if cooldown is None and host=='sammlung.belvedere.at':
        _original_slot(host,cooldown=30)
core.provider_rate_slot=rate_slot

def canonical(url):
    p=urlsplit(url)
    path=p.path.split(';')[0]
    return urlunsplit((p.scheme,p.netloc,path,'' if re.match(r'^/objects/\d+(?:/|$)',path) else p.query, ''))

def permitted(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.hostname not in ALLOWED:raise ValueError('Unapproved museum source')
    if p.hostname=='sammlung.wienmuseum.at' and re.search(r'/(?:api|graphql)(?:/|$)',p.path,re.I):raise ValueError('Wien Museum internal API is not available for reuse')
    if p.hostname=='sammlung.belvedere.at' and (p.path.startswith(('/assets/','/modules.gz/','/users/login')) or any(s in p.path for s in ('objects.filterpanel','multiviewreportscontroller','detailviewreportscontroller'))):raise ValueError('Source robots restriction')

class PublicPages:
    def __init__(self,run):self.run=run;self.fetcher=core.Fetcher(run/'captures')
    def get(self,url):
        url=canonical(url);permitted(url);key=core.sha(url.encode());path=self.run/'captures'/(key+'.html');receipt=path.with_suffix('.receipt.json')
        if path.exists():return path.read_bytes(),json.loads(receipt.read_text())
        raw,headers=self.fetcher.get(url,12_000_000)
        core.save_new(path,raw);meta={'url':url,'retrieved_at':core.now(),'sha256':core.sha(raw),'bytes':len(raw),'headers':headers};core.save_new(receipt,meta);return raw,meta

def belvedere_discover(run):
    pages=PublicPages(run);found={}
    for page in range(1,10):
        url='https://sammlung.belvedere.at/highlights/images'+(f'?page={page}' if page>1 else '')
        raw,receipt=pages.get(url);soup=BeautifulSoup(raw,'html.parser')
        for a in soup.select('a[href]'):
            if not re.match(r'^/objects/\d+/',a['href']):continue
            link=canonical(urljoin(url,a['href']));oid=re.search(r'/objects/(\d+)/',link)[1]
            found[oid]={'object_id':oid,'url':link,'discovery_label':a.get_text(' ',strip=True),'selection':'Official Belvedere highlights','selection_url':receipt['url'],'selection_receipt':receipt}
        print(core.now(),'Belvedere highlight page',page,'unique objects',len(found),flush=True)
    core.save_new(run/'highlight-selection.json',{'at':core.now(),'records':list(found.values()),'policy':'Official museum highlights, not a claim of current display. Actual type, date, creator and per-image rights require the object page.'})
    return list(found.values())

def belvedere_capture(run,limit):
    selection=run/'highlight-selection.json';rows=json.loads(selection.read_text())['records'] if selection.exists() else belvedere_discover(run)
    pages=PublicPages(run)
    for row in rows[:limit]:
        out=run/'objects'/(row['object_id']+'.json')
        if out.exists():continue
        try:
            raw,receipt=pages.get(row['url']);soup=BeautifulSoup(raw,'html.parser')
            core.save_new(out,{'selection':row,'capture':receipt,'title':soup.h1.get_text(' ',strip=True) if soup.h1 else None,'stage':'Captured official record; facts and rights require parsing and validation.'})
            print(core.now(),'Belvedere official object captured',row['object_id'],flush=True)
        except Exception as exc:
            with (run/'errors.jsonl').open('a') as file:file.write(json.dumps({'at':core.now(),'object_id':row['object_id'],'error':str(exc)[:250]})+'\n')
            print(core.now(),'Belvedere source held',row['object_id'],type(exc).__name__,flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['belvedere']);p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=98);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True);belvedere_capture(a.run,a.limit)
if __name__=='__main__':main()
