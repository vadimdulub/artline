#!/usr/bin/env python3
"""Bounded documented Princeton API discovery and selected metadata capture."""
import argparse,gzip,hashlib,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urlencode
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-native-20261006.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
m=n.m;RUN=m.RUN/'native/princeton';IID='4ec6f6ac-08d1-5081-8b76-571b89611eda';BASE='https://data.artmuseum.princeton.edu';n.SITES['princeton']=BASE;last_request=0
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def checked(x):
 p=m.ROOT/x['path'];assert ref(p)==x;return p
def body(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'] and cap['receipt']['status']==200;return raw
def capture(url):
 global last_request
 delay=3-(time.monotonic()-last_request)
 if delay>0:time.sleep(delay)
 try:return n.capture('princeton',url)
 finally:last_request=time.monotonic()
def save_capture(path,url,**extras):
 if path.exists():
  x=m.load(path);assert x['url']==url and json.loads(body(x['capture']))==x['data'];return x
 raw,cap=capture(url);x=dict(at=m.now(),url=url,capture=cap,data=json.loads(raw),**extras);m.save(path,x);return x
def search_hits(x):
 data=x['data'];assert json.loads(body(x['capture']))==data and data['status']==200 and not data['timed_out'] and not data['_shards']['failed']
 rows=data['hits']['hits'];assert len(rows)<=24
 for r in rows:assert str(r['_source']['objectid'])==r['_id'] and r['_type']=='artobjects'
 return rows
def pending():
 initial=m.load(RUN/'initial-scope-001.json.gz');rs=[]
 for a in initial['snapshot']['artworks']:
  cs=[c for c in initial['snapshot']['citations'] if c['entity_id']==a['id']];ids={v for c in cs for v in re.findall(r'artmuseum\.princeton\.edu/(?:art/)?collections/objects/(\d+)',c['evidence_note'])};extra=[]
  if not ids:
   # One legacy citation names its preserved source response rather than a URL.
   notes=[json.loads(c['evidence_note']) for c in cs];note=next(c for c in notes if c.get('evidence_path'));p=m.ROOT/note['evidence_path'];raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==note['source_response_sha256'];entity=json.loads(raw)['entities'][note['object_id']]
   ids={v for v in re.findall(r'artmuseum\.princeton\.edu/(?:art/)?collections/objects/(\d+)',json.dumps(entity))};extra=[ref(p)]
  assert len(ids)==1,(a['id'],ids)
  rs.append(dict(artwork_id=a['id'],source_id=next(iter(ids)),title=a['title'],inventory=a['accession_number'],date_display=a['date_display'],initial_reference=ref(RUN/'initial-scope-001.json.gz'),extra_references=extra))
 return rs
def indexes():
 assert not list((RUN/'index-errors-001').glob('*.json')),'Retained failure requires assessment'
 for number in range(1,9):
  url=BASE+'/search?'+urlencode(dict(q='"Oil on canvas"',type='artobjects',size=24,**{'from':24*(number-1)}));path=RUN/'indexes-001'/('oil-canvas-%03d.json.gz'%number)
  try:
   x=save_capture(path,url,documentation_reference=ref(RUN/'api-docs-search-001.json.gz'),selection='First eight24-result pages of the documented public full-text oil-on-canvas query. Not a department or creation filter. Dates and source facts still require review. No images.');rows=search_hits(x);print(json.dumps(dict(index=number,total=x['data']['hits']['total'],rows=len(rows))),flush=True)
  except Exception as e:m.save(RUN/'index-errors-001'/('index-%03d.json'%number),dict(at=m.now(),url=url,error=repr(e)));raise
 package=m.load(RUN/'world-highlights-package-001.json.gz');assert package['data']['packageid']==182962 and len(package['data']['objects'])==12
 leads=[dict(source_id=str(x['id']),kind='world_highlight',selection_reference=ref(RUN/'world-highlights-package-001.json.gz'),package_entry=x) for x in package['data']['objects']]
 leads += [dict(source_id=x['source_id'],kind='existing_pending',selection_reference=x['initial_reference'],pending=x) for x in pending()]
 for lead in leads:
  sid=lead['source_id'];path=RUN/'tombstones-001'/(lead['kind']+'-'+sid+'.json.gz');url=BASE+'/objects/'+sid+'/tombstone'
  try:
   x=save_capture(path,url,selection=lead,documentation_reference=ref(RUN/'api-docs-objects-001.json.gz'));assert str(x['data']['objectid'])==sid;print(json.dumps(dict(tombstone=sid,kind=lead['kind'],date=x['data'].get('displaydate'))),flush=True)
  except Exception as e:m.save(RUN/'index-errors-001'/(lead['kind']+'-'+sid+'.json'),dict(at=m.now(),url=url,error=repr(e)));raise
 m.save(RUN/'index-capture-checkpoint-001.json',dict(at=m.now(),search_pages=8,priority_pages=4,world_highlight_tombstones=12,existing_pending_tombstones=27,images=0,policy='Selected metadata discovery complete; no editorial approvals. Keyword hits may be outside the target medium or tradition. Source dates and object identity still require full detail.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['indexes']);globals()[p.parse_args().command]()
