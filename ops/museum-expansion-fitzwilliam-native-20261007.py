#!/usr/bin/env python3
"""Bounded Fitzwilliam public index and object metadata captures; no image assets."""
import argparse,hashlib,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urljoin,urlencode
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-native-20261006.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n);m=n.m
RUN=m.RUN/'native/fitzwilliam';BASE='https://data.fitzmuseum.cam.ac.uk';PROVIDER='fitzwilliam-data';IID='5dc5171c-7a3d-5f36-bc85-6c56f6afeb64';n.SITES[PROVIDER]=BASE

def reference(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def parse_index(raw):
 soup=BeautifulSoup(raw,'html.parser');out=[]
 for block in soup.select('.contents-label'):
  a=block.select_one('h3.lead a[href]')
  if not a:continue
  match=re.fullmatch(re.escape(BASE)+r'/id/object/(\d+)',a['href'])
  if match:out.append(dict(source_id=match[1],url=a['href'],title=a.get_text(' ',strip=True),index_text=block.get_text(' ',strip=True)))
 assert len(out)<=24 and len(out)==len({r['source_id'] for r in out})
 return dict(rows=out,page_text=soup.get_text(' ',strip=True),pagination=[dict(title=a.get_text(' ',strip=True),url=a['href']) for a in soup.select('a[href]') if re.search(r'[?&]page=\d+',a['href'])])

def parse_page(raw):
 soup=BeautifulSoup(raw,'html.parser');h1=soup.select_one('h1');assert h1
 sections={}
 for h in soup.select('h3.collection'):
  key=h.get_text(' ',strip=True);parts=[]
  for child in h.next_siblings:
   if getattr(child,'name',None) in ['h1','h2','h3','div']:break
   if getattr(child,'name',None):parts.append(child.get_text(' ',strip=True))
  sections.setdefault(key,[]).append(' '.join(parts).strip())
 jsonlinks=[a['href'] for a in soup.select('a[href]') if a.get_text(' ',strip=True)=='JSON']
 return dict(heading=h1.get_text(' ',strip=True),sections=sections,full_text=soup.get_text(' ',strip=True),json_links=jsonlinks,canonical=[a['href'] for a in soup.select('link[rel=canonical]')])

def index():
 assert not (RUN/'native-index-001.json.gz').exists();pages=[];seen={}
 queries=[('painting',{'query':'painting','operator':'AND','sort':'desc','object_type':'painting'},12),('icon',{'query':'icon','operator':'AND','sort':'desc'},2)]
 for kind,query,limit in queries:
  for page in range(1,limit+1):
   url=BASE+'/search/results?'+urlencode(dict(**query,page=page))
   try:
    raw,cap=n.capture(PROVIDER,url);parsed=parse_index(raw);pages.append(dict(kind=kind,page=page,url=url,capture=cap,parsed=parsed));print('INDEX',kind,page,len(parsed['rows']),flush=True)
    for row in parsed['rows']:
     if row['source_id'] not in seen:seen[row['source_id']]=dict(**row,index_kinds=[kind])
     elif kind not in seen[row['source_id']]['index_kinds']:seen[row['source_id']]['index_kinds'].append(kind)
    if len(parsed['rows'])<24:break
   except Exception as error:pages.append(dict(kind=kind,page=page,url=url,error=type(error).__name__+': '+str(error)));print('INDEX ERROR',url,str(error),flush=True);break
   time.sleep(.4)
 assert len(seen)<=336
 m.save(RUN/'native-index-001.json.gz',dict(at=m.now(),pages=pages,unique_objects=list(seen.values()),policy='Bounded12 painting pages and2 icon search pages. Index membership does not approve artwork type, date, holding or addition. No image assets fetched.'))
 print('UNIQUE',len(seen),flush=True)

def capture():
 queue=m.load(RUN/'native-object-queue-001.json');out=RUN/'native-objects-001';out.mkdir(exist_ok=True)
 for i,row in enumerate(queue['objects'],1):
  dest=out/(row['source_id']+'.json.gz')
  if dest.exists():continue
  try:
   raw,html=n.capture(PROVIDER,row['url']);parsed=parse_page(raw);url=row['url']+'?format=json';assert url in parsed['json_links'],'Public JSON link missing'
   time.sleep(.4);rawj,jsoncap=n.capture(PROVIDER,url);j=json.loads(rawj);assert j['admin']['id']=='object-'+row['source_id'] and j['admin']['uri']==row['url']
   m.save(dest,dict(index=row,url=row['url'],native=dict(capture=html,parsed=parsed),json=dict(capture=jsoncap,parsed=j)));print('OBJECT',i,len(queue['objects']),row['source_id'],row['title'],flush=True)
  except Exception as error:m.save(out/(row['source_id']+'-error.json'),dict(at=m.now(),index=row,error=type(error).__name__+': '+str(error)));print('OBJECT ERROR',i,row['source_id'],str(error),flush=True)
  time.sleep(.4)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['index','capture']);args=p.parse_args();index() if args.command=='index' else capture()
