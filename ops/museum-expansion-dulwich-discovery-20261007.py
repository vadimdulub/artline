#!/usr/bin/env python3
"""Read-only Dulwich scope and bounded public collection discovery, without images."""
import importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-native-20261006.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n);m=n.m
IID='ae8b7a8a-c065-515b-95c3-cc2be0786cf9';RUN=m.RUN/'native/dulwich';BASE='https://www.dulwichpicturegallery.org.uk';n.SITES['dulwich']=BASE

def snapshot(db,ids):
    queries=dict(artworks='SELECT to_jsonb(x) row FROM artworks x WHERE id=ANY(%s::uuid[]) ORDER BY id',artists='SELECT to_jsonb(x) row FROM artwork_artists x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id,attribution_role',media='SELECT to_jsonb(x) row FROM artwork_media x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',identifiers="SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",citations="SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",assertions='SELECT to_jsonb(x) row FROM artwork_location_assertions x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,id')
    out={k:[r['row'] for r in db.execute(q,(ids,))] for k,q in queries.items()}
    out['museum']=db.execute('SELECT to_jsonb(x) row FROM institutions x WHERE id=%s',(IID,)).fetchone()['row'];return out

def main():
    RUN.mkdir(exist_ok=True)
    scope=RUN/'initial-scope-001.json.gz'
    if not scope.exists():
        with m.connect() as db:
            ids=[r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id',(IID,IID))]
            assert len(ids)<=1000
            snap=snapshot(db,ids)
            counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()
            authorities=db.execute("SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='institution' AND entity_id=%s ORDER BY id",(IID,)).fetchall()
        m.save(scope,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,institution_authorities=[r['row'] for r in authorities],read_only=True))
    pages=[]
    for path in ['/','/explore/about-our-collection/','/explore/explore-the-collection/']:
        url=BASE+path
        try:
            raw,cap=n.capture('dulwich',url);soup=BeautifulSoup(raw,'html.parser')
            links=[dict(text=a.get_text(' ',strip=True),url=urljoin(url,a['href'])) for a in soup.select('a[href]')]
            pages.append(dict(url=url,capture=cap,heading=[x.get_text(' ',strip=True) for x in soup.select('h1')],full_text=soup.get_text(' ',strip=True),links=links,scripts=[urljoin(url,a['src']) for a in soup.select('script[src]')],forms=[str(x) for x in soup.select('form')]))
            print('CAPTURE',url,len(raw),len(links),flush=True)
        except Exception as ex:
            pages.append(dict(url=url,error=type(ex).__name__+': '+str(ex)));print('SOURCE ERROR',url,str(ex),flush=True)
    dest=RUN/'initial-discovery-001.json.gz';assert not dest.exists()
    m.save(dest,dict(at=m.now(),pages=pages,policy='Initial discovery only. No object-level approvals, artwork additions, images, publication or display claims. Artist biographies and historical events are not creation-date evidence.'))
    x=m.load(scope);print(json.dumps(dict(scoped_records=len(x['scoped_ids']),counts=x['counts'],museum=x['snapshot']['museum'],source_pages=len(pages))),flush=True)

if __name__=='__main__':main()
