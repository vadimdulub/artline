#!/usr/bin/env python3
"""Capture exact indexed object pages; preserve unresolved metadata and access holds."""
import importlib.util,re,json,hashlib,argparse
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter,defaultdict
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('native',Path(__file__).with_name('source-index-native-20261010.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n);m=n.m;RUN=n.RUN

def selected():
    refs,_=n.refs();native={r['id'] for pp in refs.values() for rr in pp.values() for r in rr}
    return [r for r in m.resources() if r['id'] not in native and (r['kind']=='museum_or_collection_object' or any(b['entity_type']=='artwork' for b in r['artline_bindings']))]

def one(r):
    dest=RUN/'object-pages'/(r['id']+'.json.gz')
    if dest.exists():return m.load(dest)['state']
    result=dict(source_index_id=r['id'],url=r['url'],provider=r['provider_id'],index_bindings=r['artline_bindings'])
    try:
        raw,rc=n.f.get(r['url']);soup=BeautifulSoup(raw,'html.parser');text=' '.join(soup.get_text(' ',strip=True).split())
        metas={}
        for tag in soup.select('meta[content]'):
            key=tag.get('property') or tag.get('name')
            if key:metas.setdefault(key,[]).append(tag['content'])
        result.update(state='captured',receipt=rc,title=soup.title.get_text(' ',strip=True) if soup.title else None,h1=[t.get_text(' ',strip=True) for t in soup.select('h1')],meta=metas,rights_links=[dict(url=urljoin(r['url'],a['href']),text=a.get_text(' ',strip=True)) for a in soup.select('a[href]') if re.search(r'creativecommons.org|rightsstatements.org|copyright|licen[sc]e',a['href'],re.I)],text_excerpt=text[:30000])
        if r['provider_id']=='wikiart':
            tag=soup.select_one('.wiki-layout-painting-info-bottom[ng-init]');image=soup.select_one('img[itemprop=image]');copyright=soup.select_one('.copyright-wrapper .copyright')
            if tag:
                data=json.loads(tag['ng-init'].split('=',1)[1].strip());result.update(wikiart_metadata=data,image=image.get('src') if image else None,image_rights=copyright.get_text(' ',strip=True) if copyright else 'No per-image rights label stated',public_domain=bool(copyright and copyright.select_one('.copyright-icon-public-domain')))
    except Exception as e:result.update(state='held',reason=type(e).__name__+': '+str(e)[:350])
    m.save(dest,result);return result['state']

def run():
    n.configure();groups=defaultdict(list)
    for r in selected():groups[r['provider_id']].append(r)
    print('Selected other object pages',sum(map(len,groups.values())),'providers',len(groups),flush=True)
    def provider(pair):
        name,rr=pair;counts=Counter()
        for i,r in enumerate(rr,1):
            counts[one(r)]+=1
            if i%50==0:print('Object pages',name,i,'/',len(rr),dict(counts),flush=True)
        print('Completed object pages',name,dict(counts),flush=True);return name,dict(counts)
    counts={}
    with ThreadPoolExecutor(max_workers=12) as pool:
        for job in as_completed([pool.submit(provider,pair) for pair in sorted(groups.items(),key=lambda kv:len(kv[1]),reverse=True)]):
            name,cc=job.result();counts[name]=cc
    m.save(RUN/'object-page-summary.json',dict(at=m.now(),providers=counts))

if __name__=='__main__':run()
