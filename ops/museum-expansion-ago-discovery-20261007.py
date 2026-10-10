#!/usr/bin/env python3
"""Fresh local museum scopes and bounded official AGO catalogue discovery."""
import argparse, importlib.util, json
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-nelson-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
m=d.m;n=d.n;ref=d.ref
IID='6dcf4f5e-695e-515f-b16d-3f5741b8d1d8';RUN=m.RUN/'native/ago';BASE='https://ago.ca'
n.SITES.update(ago=BASE,ago_art='https://art.ago.ca')
def scope(key,iid):
 out=m.RUN/'native'/key/'initial-scope-001.json.gz';assert not out.exists();d.d.IID=iid
 with m.connect() as db:
  ids=[r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id',(iid,iid))];assert len(ids)<=1000
  snap=d.d.snapshot(db,ids)
  counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(iid,)).fetchone()
  authority=[r['row'] for r in db.execute("SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='institution' AND entity_id=%s ORDER BY id",(iid,))]
  aliases=[r['row'] for r in db.execute('SELECT to_jsonb(x) row FROM institutions x WHERE canonical_institution_id=%s OR id=%s ORDER BY id',(iid,iid))]
 m.save(out,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,institution_authorities=authority,authority_scope=aliases,read_only=True,policy='Fresh real local catalogue scope. Pending associations remain unaccepted; no fixtures, writes or current-display inference.'))
 print(json.dumps(dict(provider=key,scoped_records=len(ids),counts=counts,museum=snap['museum'],authority_scope=aliases)),flush=True)
def scopes():
 scope('slam','56d4409a-0bd4-5a2d-b5e6-575dab970235');scope('ago',IID)
def sources():
 for url,name in [(BASE+'/collection','collection-context-001'),(BASE+'/collection/browse','browse-context-001')]:
  result=d.capture_page('ago',url,RUN/(name+'.json.gz'))
  if result.get('error'):break
  print(json.dumps(dict(links=[r for r in result['links'] if any(x in r['url'] for x in ['/collection/','art.ago.ca'])][:40])),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['scopes','sources']);a=p.parse_args();globals()[a.command]()
