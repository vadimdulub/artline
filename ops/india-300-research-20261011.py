#!/usr/bin/env python3
"""Bounded Indian museum metadata selection from the official public portal."""
import argparse,collections,concurrent.futures,gzip,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import requests
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('cesi-top100-20261010.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OP='india-300-artworks-20261011';RUN=m.ROOT/'docs/research'/OP;m.RUN=RUN
BASE='https://museumsofindia.gov.in/repository/'

def clean(v):return re.sub(r'\s+',' ',str(v or '')).strip()

def api(endpoint,params):
 url=requests.Request('GET',BASE+endpoint,params=params).prepare().url
 key=m.sha((url+'\nAccept: application/json').encode());p=RUN/'captures'/(key+'.json.gz')
 if p.exists():
  rc=m.load(p);raw=gzip.decompress(p.with_name(key+'.body.gz').read_bytes());assert m.sha(raw)==rc['sha256']
 else:
  assert not (RUN/'access-holds/museumsofindia.gov.in.json').exists(),'Source access held'
  r=requests.get(url,headers={'User-Agent':m.UA,'Accept':'application/json'},timeout=(15,60));raw=r.content
  rc=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=m.now(),sha256=m.sha(raw),bytes=len(raw),content_type=r.headers.get('Content-Type'),accept='application/json')
  m.save(p,rc);p.with_name(key+'.body.gz').write_bytes(gzip.compress(raw,mtime=0))
  if r.status_code in [401,403,429]:m.save(RUN/'access-holds/museumsofindia.gov.in.json',rc)
 assert rc['status']==200,(url,rc['status'])
 return json.loads(raw),rc

def museum(code):
 path=RUN/'museum-profiles'/(code+'.json.gz')
 if path.exists():return m.load(path)
 raw,rc=m.capture(BASE+'museum/'+code);assert rc['status']==200
 sp=BeautifulSoup(raw,'html.parser');name=next(n for u,n in m.load(RUN/'portal-museums.json').items() if u.endswith('/'+code))
 for node in sp.select('script,style'):node.decompose()
 result=dict(code=code,name=name,evidence=rc,text=sp.get_text('\n',strip=True),masterpiece_urls=list(dict.fromkeys(urljoin(BASE,a['href']) for a in sp.select('a[href]') if '/record/' in a['href'])),links=[dict(label=clean(a.get_text(' ',strip=True)),url=urljoin(BASE,a['href'])) for a in sp.select('a[href]') if not a['href'].startswith('#')])
 m.save(path,result);return result

def categories():
 codes=[u.rsplit('/',1)[-1] for u in m.load(RUN/'portal-museums.json')]
 def one(code):
  mu=museum(code);data,rc=api('collection/fetchCategories',dict(collectionType='ObjectType',pageNo=1,museum=code,category=''))
  m.save(RUN/'categories'/(code+'.json.gz'),dict(museum=code,data=data,evidence=rc));return code,data
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for code,data in pool.map(one,codes):print(code,data,flush=True)

def indexes():
 selected=m.load(RUN/'selected-categories.json');jobs=[]
 for code,cats in selected.items():
  for cat in cats:
   for page in range(1,3 if code!='avm_pun' else 2):jobs.append((code,cat,page))
 def one(job):
  code,cat,page=job;dest=RUN/'indexes'/(code+'-'+cat.replace(' ','-')+'-'+str(page).zfill(3)+'.json.gz')
  if dest.exists():return m.load(dest)
  data,rc=api('collection/fetchRecords',dict(collectionType='ObjectType',collectionCategory=cat,pageNo=page,museum=code))
  result=dict(museum=code,category=cat,page=page,evidence=rc,data=data);m.save(dest,result);return result
 rows={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for index in pool.map(one,jobs):
   for native in index['data']['listOfResult']:
    key=native['recordIdentifier'];assert key.startswith(index['museum']+'-')
    if key not in rows:rows[key]=dict(museum=index['museum'],category=index['category'],index_page=index['page'],native=native,index_evidence=index['evidence'])
 m.save(RUN/'object-candidates.json.gz',list(rows.values()));print('Selected metadata candidates',len(rows),dict(collections.Counter(r['museum'] for r in rows.values())),flush=True)

def object_record(candidate):
 key=candidate['native']['recordIdentifier'];dest=RUN/'objects'/(key+'.json.gz')
 if dest.exists():return m.load(dest)
 try:
  url=BASE+'record/'+key;raw,rc=m.capture(url);assert rc['status']==200,(url,rc['status'])
  sp=BeautifulSoup(raw,'html.parser');fields={}
  for tr in sp.select('tr'):
   cells=tr.find_all(['th','td'],recursive=False)
   if len(cells)==2:
    label=clean(cells[0].get_text(' ',strip=True));value=clean(cells[1].get_text(' ',strip=True))
    if label:assert label not in fields or fields[label]==value;fields[label]=value
  assert fields.get('Title') and fields.get('Museum Name'),('Missing native identity',key,fields)
  name=fields['Museum Name'];assert candidate['museum'] in ['avm_pun'] or m.norm(name)==m.norm(candidate['native']['museumName']),(key,name)
  out=dict(**candidate,url=url,evidence=rc,fields=fields,result='native object captured')
 except Exception as e:out=dict(**candidate,result='object source gap',error=type(e).__name__+': '+str(e)[:400])
 m.save(dest,out);return out

def objects():
 rows=m.load(RUN/'object-candidates.json.gz');counts=collections.Counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for i,out in enumerate(pool.map(object_record,rows),1):
   counts[out['result']]+=1
   if i%25==0:print('Objects checked',i,'of',len(rows),dict(counts),flush=True)
 print('Object results',dict(counts),flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['categories','indexes','objects']);args=parser.parse_args();globals()[args.action]()
