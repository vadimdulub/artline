#!/usr/bin/env python3
"""Bounded public Yale LUX metadata discovery; never call authenticated backends."""
import argparse,hashlib,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urlencode,urlsplit,parse_qs
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-yale-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
m=d.m;RUN=d.RUN;BASE=d.BASE
d.n.SITES['yale-public-docs']='https://raw.githubusercontent.com'
def capture(url):
 provider='yale' if url.startswith(BASE+'/') else 'yale-public-docs'
 assert provider=='yale' or url.startswith('https://raw.githubusercontent.com/project-lux/')
 return d.n.capture(provider,url)
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def body(c):
 raw=gzip.decompress((m.ROOT/c['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==c['receipt']['sha256'];return raw
def save_capture(name,url):
 path=RUN/(name+'.json.gz')
 if path.exists():
  x=m.load(path);assert x['url']==url;return body(x['capture'])
 raw,cap=capture(url);m.save(path,dict(at=m.now(),url=url,capture=cap));return raw
def indexes():
 seed=m.load(RUN/'lux-item-selected-index-001.json.gz');url=seed['url'];query=json.loads(parse_qs(urlsplit(url).query)['q'][0]);rows={};refs=[]
 for page in range(1,13):
  name=f'indexes-001/{page:03}';p=json.loads(save_capture(name,url));assert p['type']=='OrderedCollectionPage' and len(p['orderedItems'])<=20
  assert json.loads(parse_qs(urlsplit(p['id']).query)['q'][0])==query
  reference=ref(RUN/(name+'.json.gz'));refs.append(reference)
  for row in p['orderedItems']:
   assert row['type']=='HumanMadeObject' and row['id'].startswith(BASE+'/data/object/')
   rows.setdefault(row['id'],dict(**row,index_refs=[]))['index_refs'].append(reference)
  print('Index page',page,'selected object IDs',len(rows),flush=True)
  url=p.get('next',{}).get('id');assert url or page==12
 m.save(RUN/'discovered-001.json.gz',dict(at=m.now(),query=query,selected=list(rows.values()),index_references=refs,policy='First12 pages, at most240 physical painting records from YUAG departmental collection curation and pre1971 production-date search. Counts are estimates; every actual creation date, department, credit and object identity requires review. No all-Yale scan and no images.'))
def objects():
 rows=m.load(RUN/'discovered-001.json.gz')['selected'];refs=[];errors=[]
 for pos,row in enumerate(rows,1):
  sid=row['id'].rsplit('/',1)[1];dest=RUN/'objects-001'/(sid+'.json.gz')
  try:
   if not dest.exists():
    raw,cap=capture(row['id']);p=json.loads(raw);assert p['id']==row['id'];m.save(dest,dict(index=row,capture=cap,parsed=p))
   refs.append(ref(dest));print(pos,len(rows),sid,flush=True)
  except Exception as ex:errors.append(dict(index=row,error=type(ex).__name__+': '+str(ex)));print('FAILED',sid,str(ex),flush=True)
 m.save(RUN/'selected-capture-001.json.gz',dict(at=m.now(),records=refs,errors=errors,policy='Selected public LUX JSON-LD metadata and HTTP receipts. No images or catalogue writes.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('url',nargs='?');a=p.parse_args()
 if a.name in ['indexes','objects']:globals()[a.name]()
 else:assert a.url;print(save_capture(a.name,a.url).decode()[:35000])
