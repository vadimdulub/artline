#!/usr/bin/env python3
"""Pinned primary artist metadata; never downloads collection images or artwork dumps."""
import concurrent.futures,csv,gzip,importlib.util,io,json,re
from pathlib import Path
from urllib.parse import urlsplit
import requests
s=importlib.util.spec_from_file_location('review',Path(__file__).with_name('lifetimes-review-20261010.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
RUN=r.RUN
def capture(url):
    key=r.sha(url.encode());p=RUN/'primary-sources'/(key+'.json')
    if p.exists():return gzip.decompress(p.with_suffix('.body.gz').read_bytes()),r.load(p)
    hold=RUN/'primary-access-holds'/(urlsplit(url).hostname+'.json')
    if hold.exists():raise RuntimeError('Access held: '+url)
    response=requests.get(url,headers={'User-Agent':r.UA},timeout=(15,55))
    receipt=dict(url=url,final_url=response.url,status=response.status_code,at=r.now(),sha256=r.sha(response.content),bytes=len(response.content))
    r.save(p,receipt);p.with_suffix('.body.gz').write_bytes(gzip.compress(response.content,mtime=0))
    if response.status_code in [401,403,429]:r.save(hold,receipt)
    return response.content,receipt
DATASETS={
 'tate':'https://raw.githubusercontent.com/tategallery/collection/master/artist_data.csv',
 'nga':'https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data/constituents.csv',
 'moma':'https://raw.githubusercontent.com/MuseumofModernArt/collection/main/Artists.json',
}
PAGES={
 'uccello':'https://www.nationalgallery.org.uk/artists/paolo-uccello',
 'henner':'https://musee-henner.fr/repertoire-des-eleves',
 'roll':'https://collections.louvre.fr/ark:/53355/cl020215563',
 'locke':'https://www.hewlocke.net',
 'rondinelli':'https://art.thewalters.org/object/37.517A/madonna-and-child-35/',
}
def datasets():
    out=[]
    def one(item):
        name,url=item
        try:
            raw,rc=capture(url);assert rc['status']==200
            rows=json.loads(raw) if name=='moma' else list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
            assert isinstance(rows,list)
            value=dict(receipt=rc,records=rows);r.save(RUN/(name+'-artist-authority.json.gz'),value)
            return dict(name=name,count=len(rows),keys=list(rows[0]),receipt=rc)
        except Exception as e:return dict(name=name,error=str(e))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:out=list(pool.map(one,DATASETS.items()))
    r.save(RUN/'primary-datasets-summary.json',out);print(json.dumps(out,indent=2),flush=True)
def pages():
    from bs4 import BeautifulSoup
    for name,url in PAGES.items():
        try:
            raw,rc=capture(url);text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
            r.save(RUN/'primary-pages'/(name+'.json.gz'),dict(receipt=rc,text=text));print(name,rc['status'],text[:250],flush=True)
        except Exception as e:print(name,type(e).__name__,str(e),flush=True)
if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
