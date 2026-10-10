#!/usr/bin/env python3
"""Cyprus museum research: immutable source captures and production-only audit."""
import concurrent.futures, gzip, importlib.util, json, os, sys
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/cyprus-deep-20261010'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/RUN.name
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/RUN.name
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
h=module('cyprus_deep_sources','research-havre-rouen-cyprus-20261006.py')
d=module('cyprus_deep_delivery','museum-minimum-100-delivery-20261006.py')
h.RUN=RUN;h.BACKUP=BACKUP
def page(url):
    dest=RUN/'pages'/(h.sha(url.encode())+'.json')
    if dest.exists():return h.load(dest)
    raw,receipt=h.capture(url);soup=BeautifulSoup(raw,'html.parser')
    imgs=[dict(url=urljoin(url,x.get('src','')),alt=x.get('alt','')) for x in soup.select('img[src]')]
    links=[dict(url=urljoin(url,a['href']),text=a.get_text(' ',strip=True))for a in soup.select('a[href]')]
    scripts=[dict(src=urljoin(url,a.get('src','')),text=a.get_text())for a in soup.select('script')]
    for x in soup(['script','style','noscript']):x.decompose()
    value=dict(url=url,receipt=receipt,title=soup.title.get_text(' ',strip=True)if soup.title else None,text=soup.get_text('\n',strip=True),images=imgs,links=links,scripts=scripts)
    h.save(dest,value);return value
def baseline():
    with d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        museums=db.execute("""SELECT i.id::text,i.name,i.slug,p.name city,i.website_url,
          count(a.id) artworks,count(a.primary_media_id) images
          FROM institutions i JOIN places p ON p.id=i.place_id
          LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived'
          WHERE p.country_code='CY' AND i.status<>'archived'
          GROUP BY i.id,p.id ORDER BY i.name""").fetchall()
        ids=[r['id']for r in museums]
        works=db.execute("SELECT to_jsonb(a)r FROM artworks a WHERE current_institution_id=ANY(%s::uuid[]) ORDER BY id",(ids,)).fetchall()
        aids=[r['r']['id']for r in works]
        citations=db.execute("SELECT to_jsonb(c)r FROM citations c WHERE entity_type='artwork'AND entity_id=ANY(%s::uuid[]) ORDER BY id",(aids,)).fetchall()
        ext=db.execute("SELECT to_jsonb(e)r FROM external_identifiers e WHERE entity_type='artwork'AND entity_id=ANY(%s::uuid[]) ORDER BY id",(aids,)).fetchall()
        schema=db.execute("SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='public'AND table_name=ANY(%s)ORDER BY table_name,ordinal_position",(['artworks','media_assets','artwork_media','citations','artwork_location_assertions','audit_log','sources'],)).fetchall()
    value=dict(at=h.now(),target='production',museums=museums,artworks=[x['r']for x in works],citations=[x['r']for x in citations],identifiers=[x['r']for x in ext],schema=schema)
    h.save(RUN/'baseline.json.gz',value)
    print('Museums',len(museums),'artworks',len(works),'illustrated museums',sum(x['images']>0 for x in museums))
    for x in museums:
        if x['artworks']:print(x['slug'],x['artworks'],x['images'])
def capture():
    def one(url):
        try:
            p=page(url);print(p['receipt']['status'],url,p['title'],len(p['images']),flush=True)
        except Exception as e:print('FAILED',url,type(e).__name__,str(e)[:150],flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:list(pool.map(one,sys.argv[2:]))
def directory_audit():
    museums=h.load(RUN/'baseline.json.gz')['museums']
    urls=sorted({m['website_url']for m in museums if m['website_url']})
    def one(url):
        try:
            p=page(url);return dict(url=url,status=p['receipt']['status'],capture=p['receipt'],title=p['title'],links=len(p['links']))
        except Exception as e:return dict(url=url,error=type(e).__name__+': '+str(e)[:220])
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        out=[]
        for p in pool.map(one,urls):
            out.append(p)
            if len(out)%10==0:print('Museum source checks',len(out),'/',len(urls),flush=True)
    h.save(RUN/'directory-audit.json',dict(at=h.now(),sources=out,museum_count=len(museums)))
if __name__=='__main__':globals()[sys.argv[1]]()
