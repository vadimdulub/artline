#!/usr/bin/env python3
"""Bounded, resumable primary-catalogue metadata selection. Never writes a DB."""
import concurrent.futures,gzip,importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('nicosia',Path(__file__).with_name('nicosia-museums-20261007.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
R=n.ROOT;h=n.h
def page(url,key):
    p=R/'artwork-pages'/(key+'.json')
    if p.exists():return h.load(p)
    raw,rc=h.capture(url);soup=BeautifulSoup(raw,'html.parser')
    for t in soup(['script','style','noscript']):t.decompose()
    value=dict(url=url,receipt=rc,text=soup.get_text('\n',strip=True),links=[dict(url=urljoin(url,a['href']),text=a.get_text(' ',strip=True))for a in soup.select('a[href]')])
    h.save(p,value);return value
def makarios():
    base='http://www.makariosfoundation.org.cy/'
    seed=h.load(R/'pages/byzantine-first.json')
    links={x['url']for x in seed['links']if re.search(r'/bmen\d{3}\.html$',x['url'])}
    # Select the first 240 catalogue entries, using actual pagination links.
    for url in sorted(links):
        number=int(re.search(r'bmen(\d+)',url)[1])
        if number>240:continue
        x=page(url,'makarios-'+url.rsplit('/',1)[-1][:-5])
        links.update(a['url']for a in x['links']if re.search(r'/bmen\d{3}\.html$',a['url'])and int(re.search(r'bmen(\d+)',a['url'])[1])<=240)
    selected=sorted(u for u in links if int(re.search(r'bmen(\d+)',u)[1])<=240)
    h.save(R/'artwork-indexes/makarios.json',dict(selection='First 240 linked catalogue objects; no image download.',urls=selected))
    for index,url in enumerate(selected):
        page(url,'makarios-'+url.rsplit('/',1)[-1][:-5])
        if(index+1)%25==0:print('Makarios',index+1,'/',len(selected),flush=True)
    return len(selected)
def cvar():
    links={};receipts=[];base='https://cvar.severis.org/en/explore/collections-archives/paintings/'
    for number in range(5,12):
        x=page(base+'?page='+str(number),'cvar-index-'+str(number));receipts.append(x['receipt'])
        for a in x['links']:
            if '/collections/item/'in a['url']:links[a['url']]=a['text']
    h.save(R/'artwork-indexes/cvar.json',dict(selection='Paintings catalogue pages 5–11, following previously delivered pages 1–4.',links=links,receipts=receipts))
    for index,(url,label)in enumerate(links.items()):
        end=re.search(r'(\d{4})(?:--\d\d--\d\d)?\s*$',label)
        if end and int(end[1])>1970:continue
        page(url,'cvar-'+h.sha(url.encode()))
        if(index+1)%25==0:print('CVAR',index+1,'/',len(links),flush=True)
    return len(links)
def leventis():
    selected=[];indexes=[]
    for number in range(1,4):
        url='https://leventisgallery.org/wp-json/wp/v2/artworks?per_page=100&page='+str(number)
        raw,rc=h.capture(url);assert rc['status']==200
        rows=json.loads(raw);indexes.append(dict(receipt=rc,records=rows))
        # Gold collection pages describe multi-coin groups and restrikes.
        selected.extend(x for x in rows if 34 not in x['collections'])
        if len(rows)<100:break
    selected=selected[:200]
    h.save(R/'artwork-indexes/leventis.json',dict(selection='Up to 200 individual art records from the first three API pages; gold coin series excluded.',indexes=indexes,objects=selected))
    for index,x in enumerate(selected):
        page(x['link'],'leventis-'+str(x['id']))
        if(index+1)%25==0:print('Leventis',index+1,'/',len(selected),flush=True)
    return len(selected)
def municipal():
    seed=h.load(R/'pages/leventis-municipal.json');wanted={'phylactou-collection','jewellery-collection','ancient-times','byzantine-period','frankish-period','venetian-period','ottoman-period','british-rule','nicosia-1960-until-today'}
    links=sorted({a['url']for a in seed['links']if urlparse(a['url']).path.strip('/')in wanted})
    for url in links:page(url,'municipal-'+urlparse(url).path.strip('/'))
    return len(links)
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        futures={pool.submit(fn):fn.__name__ for fn in [makarios,cvar,leventis,municipal]}
        for f in concurrent.futures.as_completed(futures):
            try:print('DONE',futures[f],f.result(),flush=True)
            except Exception as e:print('FAILED',futures[f],type(e).__name__,str(e),flush=True)
