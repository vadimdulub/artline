#!/usr/bin/env python3
"""Bounded official collection metadata discovery, before object selection."""
import argparse,concurrent.futures,importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('south-america-1000-20261011.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c);d=c.d

def bounds(value,cutoff=1970):
    v=value.strip().replace('\u00a0',' ')
    v=re.sub(r'^(?:ca\.?|c\.?|circa|cerca de|aprox\.?|entre)\s*','',v,flags=re.I)
    v=re.sub(r'\s*\((?:circa|ca\.?|aprox\.?)\)$','',v,flags=re.I)
    if not re.fullmatch(r'\d{4}(?:\s*(?:[-–/]| a | y )\s*\d{2,4})?',v):return None
    years=re.findall(r'\d+',v);lo=int(years[0]);hi=int(years[-1])
    if len(years)>1 and len(years[-1])==2:hi=lo//100*100+hi
    return (lo,hi) if 1000<=lo<=hi<=cutoff else None

def objects(country,tag,rows):
    def one(x):
        path=c.RUN/country/tag/'objects'/(d.sha(x['url'].encode())+'.json.gz')
        if path.exists():return d.load(path)
        try:
            raw,rc=c.capture(x['url']);p=BeautifulSoup(raw,'html.parser')
            result=dict(index=x,evidence=rc,text=p.get_text(' ',strip=True))
        except Exception as e:result=dict(index=x,error=str(e))
        d.save(path,result);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for n,r in enumerate(pool.map(one,rows),1):
            if n%50==0:print(country,tag,'object captures',n,'/',len(rows),flush=True)

def surdoc():
    rows={};receipts=[]
    for tag,institution,pages in [('national',3,30),('regional',None,10)]:
        for page in range(pages):
            params={'first_level_classification':'549','f[0]':'classification:555','page':page}
            if institution:params['f[1]']='institution:'+str(institution)
            raw,rc=c.capture('https://www.surdoc.cl/colecciones',params);p=BeautifulSoup(raw,'html.parser');receipts.append(rc)
            found=p.select('article.view-mode--card_public')
            for node in found:
                a=node.select_one('a.record-title');url=urljoin(rc['url'],a['href']);iid=node.select_one('.field--name-institution-id');creator=node.select_one('.field--name-creators')
                rows[url]=dict(url=url,id=url.rsplit('/',1)[-1],title=a.get_text(' ',strip=True),museum=iid.get_text(' ',strip=True),creator=creator.get_text(' ',strip=True) if creator else None,index_evidence=rc)
            if page%10==0:print('CL index',tag,page,len(rows),flush=True)
            if not p.select_one('.pager__item--next'):break
    d.save(c.RUN/'CL/surdoc/index.json.gz',dict(records=list(rows.values()),receipts=receipts,scope='Bounded first 30 national-gallery pages and 10 broader visual-art pages, metadata only.'))
    objects('CL','surdoc',list(rows.values()))

def masp():
    url='https://masp.org.br/acervo/busca?author=&date-to=1970';raw,rc=c.capture(url);p=BeautifulSoup(raw,'html.parser');rows=[];held=[]
    for node in p.select('.collection-figure'):
        a=node.select_one('a[href]');caption=node.get_text(' ',strip=True);title,sep,date=caption.rpartition(', ')
        if not sep or not bounds(date):held.append(dict(url=a['href'],caption=caption,reason='No unambiguous explicit creation date through 1970 in index caption'));continue
        rows.append(dict(url=a['href'],title=title,date=date,index_evidence=rc))
    assert len({x['url'] for x in rows})==len(rows)
    selected=rows[:650]
    d.save(c.RUN/'BR/masp/index.json.gz',dict(records=rows,held=held,selected=selected,scope='Public search response contains 1810 metadata captions; explicit caption date selected before object detail capture. No image downloads.'))
    print('MASP eligible index',len(rows),'selected',len(selected),flush=True)
    objects('BR','masp',selected)

def mali():
    url='https://coleccion.mali.pe/collections/140/5-obras-destacadas/objects';rows={};held=[];receipts=[]
    seen=set()
    for page in range(1,37):
        if page>1:url='https://coleccion.mali.pe/collections/140/5-obras-destacadas/objects/images?page='+str(page)
        raw,rc=c.capture(url);p=BeautifulSoup(raw,'html.parser');receipts.append(rc)
        for node in p.select('.grid-item-inner'):
            a=node.select_one('.title a[href]');date=node.select_one('.displayDate')
            if not a:continue
            link=urljoin(url,a['href']).split('?')[0];dt=date.get_text(' ',strip=True) if date else ''
            assert link not in seen,'Repeated eMuseum object page; inspect pagination'
            seen.add(link)
            row=dict(url=link,title=a.get_text(' ',strip=True),date=dt,index_evidence=rc)
            if not bounds(dt):held.append(dict(row,reason='Outside explicit dated selection; prehistoric/century/unknown/modern records retained for separate review'));continue
            rows[link]=row
        if not p.select('.grid-item-inner'):break
    d.save(c.RUN/'PE/mali/index-v2.json.gz',dict(records=list(rows.values()),held=held,receipts=receipts,scope='Museum-designated highlights; native page-number pagination checked for repeated IDs; explicit creation years/ranges through 1970 selected.'))
    print('MALI selected index',len(rows),'held',len(held),flush=True);objects('PE','mali',list(rows.values()))

def skin(country):
    base='https://colecciones.banrepcultural.org' if country=='CO' else 'https://colecciones-ecuador.skin-web.org'
    url=base+('/es/pagina/coleccion-de-arte/6357aa7ae27d753f221c618d' if country=='CO' else '/es/pagina/coleccion-de-arte-colonial-y-republicano/6a6c5b5e382a0e1107999100?v=mosaic')
    rows={};held={};receipts=[]
    for page in range(60 if country=='CO' else 15):
        raw,rc=c.capture(url);p=BeautifulSoup(raw,'html.parser');receipts.append(rc)
        for node in p.select('[data-controller="hit-mosaic"]'):
            a=node.select_one('.card-body a[href]');title=node.select_one('h2.label')
            if not a or not title:continue
            link=urljoin(url,a['href']).split('?')[0];fields=[x.get_text(' ',strip=True) for x in a.select('p')];date=fields[0] if fields else ''
            row=dict(url=link,title=title.get_text(' ',strip=True),date=date,caption_fields=fields,index_evidence=rc)
            if country=='CO' and not bounds(date):held[link]=dict(row,reason='No explicit eligible creation bounds in index caption');continue
            rows[link]=row
        button=p.select_one('#sw-search-more-results[data-href],#pagination-next[href]')
        if page%10==0:print(country,'index page',page,'candidates',len(rows),flush=True)
        if not button:break
        url=urljoin(base,button.get('data-href') or button['href'])
    selected=list(rows.values())[:300 if country=='CO' else 150]
    d.save(c.RUN/country/'skin'/('index-v2.json.gz' if country=='EC' else 'index.json.gz'),dict(records=list(rows.values()),held=list(held.values()),selected=selected,receipts=receipts,scope='Bounded native index pages; individual detail fields establish final creation date and institution.'))
    objects(country,'skin',selected)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['surdoc','masp','mali','skin']);p.add_argument('country',nargs='?');a=p.parse_args();skin(a.country) if a.action=='skin' else globals()[a.action]()
