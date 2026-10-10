#!/usr/bin/env python3
"""Read-only museum scope and bounded official Nelson-Atkins source discovery."""
import argparse, hashlib, importlib.util, json
from pathlib import Path
from urllib.parse import urljoin
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-hamburg-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;n=d.n
IID='dff2f52f-6fa0-5768-a4c8-ab768f518f07';RUN=m.RUN/'native/nelson';BASE='https://art.nelson-atkins.org';MAIN='https://nelson-atkins.org';d.IID=IID
n.SITES.update(nelson=BASE,nelson_main=MAIN)
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def scope():
 with m.connect() as db:
  ids=[r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id',(IID,IID))];assert len(ids)<=1000
  snap=d.snapshot(db,ids);counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()
  authority=db.execute("SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='institution' AND entity_id=%s ORDER BY id",(IID,)).fetchall()
  aliases=db.execute("SELECT to_jsonb(x) row FROM institutions x WHERE canonical_institution_id=%s OR id=%s OR lower(name) LIKE '%%nelson%%atkins%%' ORDER BY id",(IID,IID)).fetchall()
 m.save(RUN/'initial-scope-001.json.gz',dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,institution_authorities=[r['row'] for r in authority],authority_scope=[r['row'] for r in aliases],read_only=True,policy='Fresh real local museum scope. No database writes or test fixtures. Pending associations remain unaccepted; custody, ownership and current display require separate evidence.'))
 print(json.dumps(dict(scoped_records=len(ids),counts=counts,museum=snap['museum'],authority_scope=[r['row'] for r in aliases])),flush=True)
def capture_page(provider,url,path):
 try:
  raw,cap=n.capture(provider,url);soup=d.BeautifulSoup(raw,'html.parser');links=[dict(text=a.get_text(' ',strip=True),url=urljoin(url,a['href'])) for a in soup.select('a[href]')]
  result=dict(url=url,capture=cap,full_text=soup.get_text(' ',strip=True),links=links)
 except Exception as ex:result=dict(url=url,error=type(ex).__name__+': '+str(ex))
 m.save(path,result);print(json.dumps(dict(url=url,error=result.get('error'),text_length=len(result.get('full_text','')),reference=ref(path))),flush=True);return result
def sources():
 for provider,url,name in [('nelson_main',MAIN+'/art/','art-context-001'),('nelson_main',MAIN+'/art/collections/european/','european-context-001'),('nelson',BASE+'/collections','collections-context-001')]:
  result=capture_page(provider,url,RUN/(name+'.json.gz'))
  if 'error' in result:break
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['scope','sources']);a=p.parse_args();globals()[a.command]()
