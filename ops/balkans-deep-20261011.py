#!/usr/bin/env python3
"""Greece, Bulgaria and North Macedonia: immutable research, production audit."""
import collections, concurrent.futures, importlib.util, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/balkans-deep-20261011'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/RUN.name
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/RUN.name
spec=importlib.util.spec_from_file_location('regional_sources',ROOT/'ops/cyprus-deep-20261010.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
h,d=base.h,base.d
base.RUN=RUN;h.RUN=RUN;h.BACKUP=BACKUP
page=base.page

def baseline():
    with d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        museums=db.execute("""SELECT i.id::text,i.name,i.slug,p.name city,p.country_code,
          i.website_url,count(a.id)artworks,count(a.primary_media_id)images
          FROM institutions i JOIN places p ON p.id=i.place_id
          LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived'
          WHERE p.country_code=ANY(%s) AND i.status<>'archived'
          GROUP BY i.id,p.id ORDER BY p.country_code,i.name""",(['GR','BG','MK'],)).fetchall()
        ids=[r['id']for r in museums]
        works=[r['v']for r in db.execute('SELECT to_jsonb(a)v FROM artworks a WHERE current_institution_id=ANY(%s::uuid[])ORDER BY id',(ids,))]
        aids=[a['id']for a in works]
        citations=[r['v']for r in db.execute("SELECT to_jsonb(c)v FROM citations c WHERE entity_type='artwork'AND entity_id=ANY(%s::uuid[])ORDER BY id",(aids,))]
        identifiers=[r['v']for r in db.execute("SELECT to_jsonb(e)v FROM external_identifiers e WHERE entity_type='artwork'AND entity_id=ANY(%s::uuid[])ORDER BY id",(aids,))]
        artists=[r['v']for r in db.execute('SELECT to_jsonb(aa)v FROM artwork_artists aa WHERE artwork_id=ANY(%s::uuid[])ORDER BY artwork_id,artist_id',(aids,))]
    h.save(RUN/'baseline.json.gz',dict(at=h.now(),target='production',museums=museums,artworks=works,citations=citations,identifiers=identifiers,artist_links=artists))
    for cc in ['GR','BG','MK']:
        rows=[r for r in museums if r['country_code']==cc]
        print(cc,dict(institutions=len(rows),nonempty=sum(r['artworks']>0 for r in rows),illustrated=sum(r['images']>0 for r in rows),artworks=sum(r['artworks']for r in rows),images=sum(r['images']for r in rows)),flush=True)
        for r in rows:
            if cc!='GR' or not r['images']:print(r['slug'],r['artworks'],r['images'],r['website_url'],flush=True)

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
            if len(out)%20==0:print('DIRECTORY',len(out),'/',len(urls),flush=True)
    h.save(RUN/'directory-audit.json',dict(at=h.now(),sources=out,museum_count=len(museums)))

if __name__=='__main__':globals()[sys.argv[1]]()
