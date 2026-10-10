#!/usr/bin/env python3
"""Bounded native catalogue research for Cyprus; metadata only, no DB writes."""
import concurrent.futures,importlib.util,json,re,time,requests
from pathlib import Path
s=importlib.util.spec_from_file_location('island',Path(__file__).with_name('cyprus-island-20261007.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
h,R=x.h,x.R
def object_page(url,key):
    path=R/'artwork-pages'/(key+'.json')
    if path.exists():return h.load(path)
    for attempt in range(3):
        try:value=x.page(url);break
        except (requests.ConnectionError,requests.Timeout):
            if attempt==2:raise
            time.sleep(2*(attempt+1))
    h.save(path,value);return value
def cvar():
    dest=R/'indexes/cvar-selection.json'
    if dest.exists():selection=h.load(dest)
    else:
        seed=x.page(x.SEEDS['cvar'],'cvar');pages=sorted({int(m[1])for a in seed['links']if(m:=re.search(r'page=(\d+)',a['url']))})
        assert max(pages)>=50
        links={};skips=[];receipts=[]
        for number in range(12,51):
            p=x.page('https://cvar.severis.org/en/explore/collections-archives/paintings/?page='+str(number));assert p['receipt']['status']==200;receipts.append(p['receipt'])
            for a in p['links']:
                if '/en/collections/item/'not in a['url']:continue
                date=re.search(r'(\d{4})(?:--?\d\d){0,2}\s*$',a['text'])
                if date and int(date[1])>1970:skips.append(dict(**a,reason='index_date_after_1970'));continue
                if re.search(r'\bsketchbook\b|\balbum\b|\bfolio\b|\bbook\b',a['text'],re.I):skips.append(dict(**a,reason='group_or_component_requires_separate_identity_review'));continue
                links.setdefault(a['url'],a['text'])
            print('CVAR index',number,'selected',len(links),flush=True)
            if len(links)>=760:break
        selection=dict(selection='Up to 760 selected object records from linked native painting catalogue pages 12–50; obvious post-1970 dates and group/component identities excluded before object requests. No image requests.',links=list(links.items())[:760],excluded=skips,receipts=receipts)
        h.save(dest,selection)
    for i,(url,label)in enumerate(selection['links']):
        object_page(url,'cvar-'+h.sha(url.encode()))
        if(i+1)%25==0:print('CVAR objects',i+1,'/',len(selection['links']),flush=True)
    print('CVAR DONE',len(selection['links']),flush=True)
def makarios():
    seeds=[x.page('http://www.makariosfoundation.org.cy/bmcen.html'),x.page('http://www.makariosfoundation.org.cy/pmenc.html')]
    links={a['url']:a['text']for p in seeds for a in p['links']if re.search(r'/(?:bmen|pmen)\d+\.html$',a['url'])}
    print('Makarios catalogue links',len(links),flush=True)
    done=set();limit=500
    while links.keys()-done and len(done)<limit:
        url=sorted(links.keys()-done)[0];done.add(url)
        match=re.search(r'/(bmen|pmen)(\d+)\.html$',url);number=int(match[2])
        # First 240 Byzantine catalogue objects were already researched.
        if match[1]=='bmen'and number<=240:continue
        p=object_page(url,'makarios-'+url.rsplit('/',1)[-1][:-5])
        if p['receipt']['status']!=200:
            print('Makarios unavailable',url,p['receipt']['status'],flush=True);continue
        links.update({a['url']:a['text']for a in p['links']if re.search(r'/(?:bmen|pmen)\d+\.html$',a['url'])})
        if len(done)%25==0:print('Makarios objects',len(done),flush=True)
    h.save(R/'indexes/makarios-selection.json',dict(selection='Additional native gallery/Byzantine catalogue object links, up to 500; prior first 240 Byzantine records excluded; metadata only.',links=links,visited=sorted(done)))
    print('Makarios DONE',len(done),flush=True)
def leventis():
    base='https://cypriotartists.leventisgallery.org/api/en/'
    raw,rc=h.capture(base+'fetch-artists','POST');assert rc['status']==200;v=json.loads(raw)
    h.save(R/'indexes/leventis-artists.json',dict(data=v,receipt=rc))
    for a in v['artists'][:100]:
        raw,rc=h.capture(base+'fetch-artist/'+a['slug'],'POST');assert rc['status']==200
        h.save(R/'leventis-cypriot-artists'/(a['slug']+'.json'),dict(profile=json.loads(raw),receipt=rc))
    print('Leventis artist catalogues DONE',min(len(v['artists']),100),flush=True)
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        tasks={pool.submit(f):f.__name__ for f in [cvar,makarios,leventis]}
        for task in concurrent.futures.as_completed(tasks):
            try:task.result()
            except Exception as e:print('FAILED',tasks[task],type(e).__name__,str(e),flush=True)
