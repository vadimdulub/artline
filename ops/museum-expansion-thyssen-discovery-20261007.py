#!/usr/bin/env python3
"""Read-only scope and bounded official source discovery for the Madrid Thyssen museum."""
import argparse,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-hamburg-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;n=d.n
IID='eb9e002b-1d26-4996-9b58-d34a4c372fc3';RUN=m.RUN/'native/thyssen';BASE='https://www.museothyssen.org';n.SITES['thyssen']=BASE;d.IID=IID
def scope():
 with m.connect() as db:
  ids=[r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id',(IID,IID))];assert len(ids)<=1000
  snap=d.snapshot(db,ids);counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()
  authority=db.execute("SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='institution' AND entity_id=%s ORDER BY id",(IID,)).fetchall()
 m.save(RUN/'initial-scope-001.json.gz',dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,institution_authorities=[r['row'] for r in authority],read_only=True,policy='Madrid museum only. Carmen Thyssen Museum Málaga is a separate institution. Collection ownership/loans/display require object-specific evidence.'))
 print(json.dumps(dict(scoped_records=len(ids),counts=counts,museum=snap['museum'])),flush=True)
def sources():
 pages=[]
 for path in ['/en/collection','/en/collection/permanent-collection','/en/collection/carmen-thyssen']:
  url=BASE+path
  try:
   raw,cap=n.capture('thyssen',url);soup=d.BeautifulSoup(raw,'html.parser');links=[dict(text=a.get_text(' ',strip=True),url=urljoin(url,a['href'])) for a in soup.select('a[href]')]
   pages.append(dict(url=url,capture=cap,full_text=soup.get_text(' ',strip=True),links=links));print(url,len(raw),'bytes',flush=True)
   for a in links:
    if any(v in a['text'].lower() for v in ['all the works','discover','masterpieces','artists']):print(a,flush=True)
  except Exception as ex:pages.append(dict(url=url,error=type(ex).__name__+': '+str(ex)));print('ERROR',url,str(ex),flush=True)
 m.save(RUN/'public-discovery-001.json.gz',dict(at=m.now(),pages=pages,policy='Three official collection-context pages only; no artwork/image crawling or inferred additions. Permanent collection, leased Carmen collection and Málaga museum remain distinct.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['scope','sources']);a=p.parse_args();globals()[a.command]()
