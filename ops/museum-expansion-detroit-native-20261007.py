#!/usr/bin/env python3
"""Bounded primary-source Detroit painting indexes and selected object captures."""
import argparse,collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-detroit-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;n=d.n;RUN=d.RUN;IID=d.IID;BASE=d.BASE;ref=d.ref
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-nelson-web-20261007.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
def body(capture):
 p=m.ROOT/capture['body_path'];raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==capture['receipt']['sha256'];assert capture['receipt']['status']==200;return raw
def creation(raw):
 t=(raw or '').strip();t=re.sub(r'^ca\.\s*','c. ',t,flags=re.I)
 t=re.sub(r'^(c\. )?between (\d{3,4}) and (\d{3,4})$',lambda x:(x[1] or '')+x[2]+'-'+x[3],t,flags=re.I)
 probably=re.fullmatch(r'probably between (\d{3,4}) and (\d{3,4})',t,re.I)
 if probably:t='c. '+probably[1]+'-'+probably[2]
 cent=re.fullmatch(r'between ((?:early |mid-|late )?\d{1,2}(?:st|nd|rd|th)) and ((?:early |mid-|late )?\d{1,2}(?:st|nd|rd|th)) century',t,re.I)
 if cent:t=cent[1]+'-'+cent[2]+' century'
 return w.creation(t)
def index(raw,url):
 soup=BeautifulSoup(raw,'html.parser');rows=[]
 for card in soup.select('.collection-teaser'):
  title=card.select_one('h3.title a[href]');date=card.select_one('time');creator=card.select_one('.carousel_item_body > p');assert title and date
  target=urljoin(url,title['href']);match=re.fullmatch(re.escape(BASE)+r'/collection/(.+?)(?:/|-)(\d+)',target);assert match,target
  rows.append(dict(source_id=match[2],url=target,title=title.get_text(' ',strip=True),creator_label=creator.get_text(' ',strip=True) if creator else None,date_display=date.get_text(' ',strip=True)))
 assert 1<=len(rows)<=30
 links=[dict(text=a.get_text(' ',strip=True),url=urljoin(url,a['href'])) for a in soup.select('a[href]') if 'page=' in a['href']]
 facets=[dict(text=a.get_text(' ',strip=True),value=a.get('data-drupal-facet-filter-value'),url=urljoin(url,a['data-facet-url'])) for a in soup.select('[data-facet-url]')]
 return dict(rows=rows,pagination=links,facets=facets)
def capture_index(url,path,selection):
 if path.exists():
  x=m.load(path);assert index(body(x['capture']),url)==x['parsed'];return x
 raw,cap=n.capture('detroit',url);x=dict(at=m.now(),selection=selection,capture=cap,parsed=index(raw,url));m.save(path,x)
 print(json.dumps(dict(index=path.name,rows=len(x['parsed']['rows']))),flush=True);return x
def indexes():
 source=m.load(RUN/'european-index-context-001.json.gz');url=source['url'];first=index(body(source['capture']),url)
 for key in ['culture_nationality:254','culture_nationality:506']:
  facet=next(v for v in first['facets'] if v['value']==key);capture_index(facet['url'],RUN/'indexes-001'/('priority-'+key.split(':')[1]+'.json.gz'),'Published European Painting '+facet['text']+' facet; Russian/Greek priority')
 for number in range(8):
  path=RUN/'indexes-001'/('european-%03d.json.gz'%(number+1));x=capture_index(url,path,'Bounded European Painting selection, maximum first eight30-row pages')
  if number<7:
   nexts=[r['url'] for r in x['parsed']['pagination'] if r['text'].startswith('Next page')];assert len(nexts)==1;assert nexts[0]!=url;url=nexts[0]
def queue():
 rows={};refs=[]
 for path in sorted((RUN/'indexes-001').glob('*.json.gz'),key=lambda p:(not p.name.startswith('priority-'),p.name)):
  x=m.load(path);rs=index(body(x['capture']),x['capture']['receipt']['url']);assert rs==x['parsed'];refs.append(ref(path))
  for row in rs['rows']:
   lead=dict(row,index_reference=ref(path));sid=row['source_id']
   if sid not in rows:rows[sid]=dict(row,index_references=[lead],creation_screen=creation(row['date_display']))
   else:
    assert all(rows[sid][k]==row[k] for k in row),(sid,'Changed indexed facts');rows[sid]['index_references'].append(lead)
 selected=[];held=[]
 for row in rows.values():
  if row['creation_screen']['date_issue']:held.append(dict(row,state='source_date_hold'))
  else:selected.append(dict(row,number=len(selected)+1,state='selected_metadata_only'))
 assert len(rows)<=247 and len(selected)<=240
 m.save(RUN/'selected-official-queue-001.json',dict(at=m.now(),selected=selected,held=held,index_references=refs,policy='Native official catalogue indexes, maximum240EuropeanPainting leads plus7explicitRussian/Greekfacet leads. Source IDs deduplicate overlap; creation dates screened before any selected object download. Full attributions, credit, version identity, sculpture classification and possible artist-lifespan date errors still require detail review. No images or catalogue writes.'))
 print(json.dumps(dict(distinct=len(rows),selected=len(selected),held=len(held),holds=[(r['title'],r['creator_label'],r['date_display']) for r in held])),flush=True)
def objects():
 queue=m.load(RUN/'selected-official-queue-001.json');qref=ref(RUN/'selected-official-queue-001.json');failures=[]
 for row in queue['selected']:
  path=RUN/'objects-001'/('object-%03d.json.gz'%row['number'])
  if path.exists():continue
  try:
   raw,cap=n.capture('detroit',row['url']);m.save(path,dict(at=m.now(),number=row['number'],index=row,queue_reference=qref,capture=cap));print(json.dumps(dict(number=row['number'],source_id=row['source_id'],bytes=len(raw))),flush=True)
  except Exception as ex:
   fail=dict(number=row['number'],url=row['url'],error=type(ex).__name__+': '+str(ex));failures.append(fail);m.save(RUN/'object-errors-001'/('object-%03d.json'%row['number']),dict(at=m.now(),queue_reference=qref,**fail));print(json.dumps(fail),flush=True)
   break
 if not failures:m.save(RUN/'selected-capture-001.json.gz',dict(at=m.now(),queue_reference=qref,records=[ref(p) for p in sorted((RUN/'objects-001').glob('*.json.gz'))],images_downloaded=0))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['indexes','queue','objects']);a=p.parse_args();globals()[a.command]()
