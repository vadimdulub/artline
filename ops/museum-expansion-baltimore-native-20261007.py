#!/usr/bin/env python3
"""Bounded public Baltimore search and selected native object captures; no images."""
import argparse,gzip,hashlib,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urlencode,urlparse
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
n=module('n','museum-expansion-native-20261006.py');dates=module('dates','museum-expansion-detroit-native-20261007.py')
m=n.m;RUN=m.RUN/'native/baltimore';IID='29b396ab-0d25-5656-adf7-76fe9a4de2b4';BASE='https://artbma.org';API=BASE+'/wp-json/artbma/v1/search/results';n.SITES['baltimore']=BASE
EARLY=[3715,3736,3739,3737,3738,3731,3719,3729,3742];QUEUE=RUN/'selected-official-queue-001.json';last_request=0
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def checked(r):
 p=m.ROOT/r['path'];assert ref(p)==r;return p
def body(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'] and cap['receipt']['status']==200;return raw
def capture(url):
 global last_request
 wait=2-(time.monotonic()-last_request)
 if wait>0:time.sleep(wait)
 try:return n.capture('baltimore',url)
 finally:last_request=time.monotonic()
def validate_index(x):
 data=json.loads(body(x['capture']));assert data==x['data'];assert x['url']==x['capture']['receipt']['url'];assert len(data['results'])<=24 and data['page']>=1
 assert all(v['type']=='artwork' and v['url'].startswith(BASE+'/artwork/') for v in data['results']);return data
def indexes():
 config=m.load(RUN/'public-search-config-001.json.gz');soup=n.BeautifulSoup(body(config['capture']),'html.parser');node=soup.select_one('flynt-component[name="BMAFacetedSearch"]');assert node['data-api']==API
 specs=[]
 for term in ['icon','Russian','Greek','Byzantine']:specs.append(('priority-'+term.lower()+'-001',1,[('s',term)]))
 for group,periods,pages in [('early',EARLY,8),('twentieth',[3714],3)]:
  for number in range(1,pages+1):specs.append((group+'-painting-index-%03d'%number,number,[('classification[]',3696)]+[('period[]',v) for v in periods]))
 for name,page,filters in specs:
  path=RUN/(name+'.json.gz');url=API+'?'+urlencode([('type','art'),('page',page),('per_page',24)]+filters)
  if path.exists():x=m.load(path);assert x['url']==url;validate_index(x);continue
  try:
   raw,cap=capture(url);x=dict(at=m.now(),url=url,capture=cap,data=json.loads(raw),config_reference=ref(RUN/'public-search-config-001.json.gz'),selection='Bounded published public search. First8 pre-twentieth-century painting pages, first3 twentieth-century painting pages and first24results of each explicit tradition-priority term. No source display field is accepted as a display assertion.');data=validate_index(x)
   if any(k=='classification[]' for k,v in filters):assert any(v['value']==3696 and v['selected'] for v in data['facets']['classification'])
   m.save(path,x);print(json.dumps(dict(index=name,total=data['total'],page=data['page'],rows=len(data['results']))),flush=True)
  except Exception as e:
   m.save(RUN/('index-error-'+name+'.json'),dict(at=m.now(),url=url,error=repr(e),policy='Stopped on first error. No automatic retry or alternative transport.'));raise
def queue():
 assert not QUEUE.exists();paths=sorted(list(RUN.glob('priority-*-001.json.gz'))+list(RUN.glob('early-painting-index-*.json.gz'))+list(RUN.glob('twentieth-painting-index-*.json.gz'))+list(RUN.glob('painting-index-001.json.gz')),key=lambda p:(not p.name.startswith('priority'),p.name))
 assert len(paths)==16;rows={}
 for path in paths:
  data=validate_index(m.load(path))
  for original in data['results']:
   url=original['url'];slug=urlparse(url).path.strip('/').split('/')[-1];row=dict(source_id=slug,url=url,title=original['title'],creator_label=original['meta'].get('artist') or None,date_display=original['meta'].get('dated') or None)
   lead=dict(index_reference=ref(path),source_record=original)
   if url in rows:
    assert all(rows[url][k]==v for k,v in row.items()),url;rows[url]['index_references'].append(lead)
   else:rows[url]=dict(row,index_references=[lead],creation_screen=dates.creation(row['date_display']),priority=path.name.startswith('priority'))
 selected=[];held=[];later=[]
 for row in rows.values():
  if row['creation_screen']['date_issue']:held.append(dict(row,state='source_date_hold'));continue
  if len(selected)>=260:later.append(dict(row,state='eligible_index_lead_outside_bounded_selection'));continue
  selected.append(dict(row,number=len(selected)+1,state='selected_metadata_only'))
 assert len(rows)<=384 and len(selected)<=260
 m.save(QUEUE,dict(at=m.now(),selected=selected,held=held,later=later,index_references=[ref(p) for p in paths],parser_reference=ref(Path(__file__).resolve()),policy='Index metadata and source-native dates screened before downloading selected object pages. Maximum260objects; no exhaustive collection or image download. Anonymous/cultural makers and Russian/Greek/Byzantine priorities are retained. Current display labels are evidence only. All selected objects still require full facts, identity, date, credit and physical-version review.'))
 print(json.dumps(dict(distinct=len(rows),selected=len(selected),held_dates=len(held),later=len(later),priority=[dict(title=r['title'],creator=r['creator_label'],date=r['date_display']) for r in selected if r['priority']])),flush=True)
def objects():
 queue=m.load(QUEUE);checked(queue['parser_reference']);assert not list((RUN/'object-errors-001').glob('*.json')),'Retained failure requires review before continuation'
 for row in queue['selected']:
  path=RUN/'objects-001'/('object-%03d.json.gz'%row['number'])
  if path.exists():x=m.load(path);assert x['index']==row and x['queue_reference']==ref(QUEUE);body(x['capture']);continue
  try:
   raw,cap=capture(row['url']);soup=n.BeautifulSoup(raw,'html.parser');assert soup.select_one('flynt-component[name="BMAArtworkDetail"]'),'Missing native object detail; stop for review'
   m.save(path,dict(at=m.now(),number=row['number'],index=row,queue_reference=ref(QUEUE),capture=cap));print(json.dumps(dict(number=row['number'],source_id=row['source_id'],bytes=len(raw))),flush=True)
  except Exception as e:
   m.save(RUN/'object-errors-001'/('object-%03d.json'%row['number']),dict(at=m.now(),number=row['number'],url=row['url'],error=repr(e),queue_reference=ref(QUEUE),policy='Stopped first failure; no retry or transport change.'));raise
 m.save(RUN/'selected-capture-001.json.gz',dict(at=m.now(),queue_reference=ref(QUEUE),records=[ref(p) for p in sorted((RUN/'objects-001').glob('*.json.gz'))],images_downloaded=0));print('Completed selected object captures',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['indexes','queue','objects']);globals()[p.parse_args().command]()
