#!/usr/bin/env python3
"""Bounded official Birmingham catalogue capture and parsing; never download images."""
import argparse,gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode,urljoin,urlsplit
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-birmingham-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;RUN=d.RUN;BASE=d.BASE

def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def body(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'] and cap['receipt']['status']==200;return raw

def fwp(soup):
 texts=[x.get_text() for x in soup.select('script') if 'window.FWP_JSON =' in x.get_text()];assert len(texts)==1
 return json.JSONDecoder().raw_decode(texts[0].split('window.FWP_JSON =',1)[1].lstrip())[0]

def index(raw):
 soup=BeautifulSoup(raw,'html.parser');grid=soup.select_one('.facetwp-template');rows=[]
 if not grid:
  assert 'There are no pieces to display.' in soup.get_text(' ',strip=True)
  pager=fwp(soup)['preload_data']['settings']['pager'];assert pager['total_rows']==0
  return dict(rows=[],pager=pager)
 for card in grid.select('.piece-block'):
  a=card.select_one('h3.piece-title a[href]');creator=card.select_one('.piece-meta-attribution');medium=card.select_one('.piece-meta-medium');url=a['href'];assert re.fullmatch(re.escape(BASE)+r'/collection/[^/?]+/',url)
  rows.append(dict(source_id=url.rstrip('/').rsplit('/',1)[-1],url=url,title=a.get_text(' ',strip=True),creator_label=creator.get_text(' ',strip=True) if creator else None,medium=medium.get_text(' ',strip=True) if medium else None))
 settings=fwp(soup)['preload_data']['settings'];assert len(rows)<=12;return dict(rows=rows,pager=settings['pager'])

def parsed(raw):
 soup=BeautifulSoup(raw,'html.parser');article=soup.select_one('article.piece-single-main');assert article
 fields=[]
 for li in soup.select('li[class^="piece-meta-"]'):
  label=li.select_one('span.meta-label')
  if label:fields.append(dict(label=label.get_text(' ',strip=True),value=li.get_text(' ',strip=True)[len(label.get_text(' ',strip=True)):].strip(),classes=li.get('class',[]),links=[dict(text=a.get_text(' ',strip=True),url=urljoin(BASE,a['href'])) for a in li.select('a[href]')]))
 text=lambda sel:article.select_one(sel).get_text(' ',strip=True) if article.select_one(sel) else None
 canonical=soup.select_one('link[rel=canonical]');post=article.get('id');assert re.fullmatch(r'post-\d+',post)
 return dict(title=text('h1'),creator_label=text('.piece-attribution'),date_display=text('.piece-date-made'),narrative=text('.entry-content'),fields=fields,native_object_id=post[5:],canonical=canonical.get('href') if canonical else None,article_classes=article.get('class',[]),source_text=soup.get_text(' ',strip=True),footer=soup.select_one('footer').get_text(' ',strip=True) if soup.select_one('footer') else None)

def indexes():
 origin=RUN/'initial-discovery-001.json.gz';raw=body(m.load(origin)['pages'][0]['capture']);config=fwp(BeautifulSoup(raw,'html.parser'));assert config['prefix']=='_'
 for key,val in [('department','european'),('department','american'),('department','asian'),('classification','paintings')]:assert f'data-value="{val}"' in config['preload_data']['facets'][key]
 requests=[dict(department='european',page=n) for n in range(1,9)]+[dict(department='american',page=n) for n in range(1,7)]+[dict(department='asian',page=1),dict(search='icon',page=1)]
 allrows={};refs=[]
 for request in requests:
  params={'_department':request['department']} if 'department' in request else {'_search':request['search']};params['_classification']='paintings'
  if request['page']>1:params['_paged']=request['page']
  url=BASE+'/collection/?'+urlencode(params);dest=RUN/'indexes-001'/(hashlib.sha256(url.encode()).hexdigest()+'.json.gz')
  if dest.exists():v=m.load(dest)
  else:
   raw,cap=d.n.capture('birmingham',url);v=dict(at=m.now(),request=request,url=url,capture=cap,parsed=index(raw),origin_reference=ref(origin));m.save(dest,v)
  assert index(body(v['capture']))==v['parsed'];assert v['parsed']['pager']['page']==request['page'];refs.append(ref(dest))
  for row in v['parsed']['rows']:
   sid=row['source_id']
   if sid in allrows:assert {k:allrows[sid][k] for k in row}==row
   else:allrows[sid]=dict(row,index_refs=[])
   allrows[sid]['index_refs'].append(ref(dest))
  print(request,len(v['parsed']['rows']),'distinct',len(allrows),flush=True)
 assert len(allrows)<=192
 m.save(RUN/'discovered-001.json.gz',dict(at=m.now(),rows=list(allrows.values()),index_references=refs,policy='Bounded16public filtered catalogue pages with12records each. Museum, creator, type and indexed object identities selected before object metadata. No catalogue exhaustion, image download, publication or database write.'))

def objects():
 rows=m.load(RUN/'discovered-001.json.gz')['rows'];refs=[];errors=[]
 for pos,row in enumerate(rows):
  dest=RUN/'objects-001'/(row['source_id']+'.json.gz')
  try:
   if not dest.exists():
    raw,cap=d.n.capture('birmingham',row['url']);m.save(dest,dict(index=row,capture=cap,parsed=parsed(raw)))
   refs.append(ref(dest));print(pos+1,len(rows),row['title'],flush=True)
  except Exception as ex:errors.append(dict(index=row,error=type(ex).__name__+': '+str(ex)));print('FAILED',row['source_id'],str(ex),flush=True)
 m.save(RUN/'selected-capture-001.json.gz',dict(at=m.now(),records=refs,errors=errors,policy='Selected official object metadata and HTTP receipts only. Creation, versions, holdings and duplicates require editorial review.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['indexes','objects']);a=p.parse_args();globals()[a.command]()
