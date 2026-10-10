#!/usr/bin/env python3
"""Public institutional pages, regional museum directories and native metadata."""
import concurrent.futures,gzip,importlib.util,re
from pathlib import Path
from urllib.parse import urljoin
s=importlib.util.spec_from_file_location('island',Path(__file__).with_name('cyprus-island-20261007.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
def regional():
    p=x.h.load(x.R/'pages/north-department.json')
    links=[a for a in p['links']if any(k in a['text']for k in ['Müzesi','Müzeleri'])and '/Lefkoşa-'not in a['url']]
    for a in links:
        v=x.page(a['url'],'north-'+x.h.sha(a['url'].encode())[:20]);print('North',a['text'],v['receipt']['status'],flush=True)
    p=x.h.load(x.R/'pages/larnaka-directory.json')
    links=[a for a in p['links']if '/directory/product/'in a['url']]
    for a in links:
        v=x.page(a['url'],'larnaka-'+a['url'].rsplit('/',1)[-1]);print('Larnaka',a['text'].removesuffix(' READ MORE'),v['receipt']['status'],flush=True)
def kykkos():
    links={'https://kykkos.org.cy/kykkos-museum.cy.net/room1/eg-index.html'};done=set()
    while links-done and len(done)<50:
        url=sorted(links-done)[0];done.add(url);v=x.page(url,'kykkos-'+x.h.sha(url.encode())[:20])
        links.update(a['url']for a in v['links']if re.search(r'/room\d/eg-(?:page\d+|index)\.html$',a['url']))
    x.h.save(x.R/'indexes/kykkos-guide.json',dict(urls=sorted(done),limit=50))
    print('Kykkos native guide',len(done),'pages',flush=True)
def frontend_metadata():
    for key in ['kyrenia-objects','christian-virtual']:
        p=x.h.load(x.R/'pages'/(key+'.json'));raw=gzip.decompress((x.n.REPO/p['receipt']['body_path']).read_bytes());soup=x.BeautifulSoup(raw,'html.parser')
        scripts=[urljoin(p['url'],s['src'])for s in soup.select('script[src]')]
        inline=[s.get_text()for s in soup.find_all('script',src=False)]
        x.h.save(x.R/'indexes'/(key+'-frontend.json'),dict(scripts=scripts,inline=inline))
        print(key,scripts,[z[:1500]for z in inline],flush=True)
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        tasks={pool.submit(f):f.__name__ for f in [regional,kykkos,frontend_metadata]}
        for task in concurrent.futures.as_completed(tasks):
            try:task.result()
            except Exception as e:print('FAILED',tasks[task],type(e).__name__,str(e),flush=True)
