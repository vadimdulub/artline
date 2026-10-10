#!/usr/bin/env python3
"""Bounded native Belvedere index/object metadata; no images or catalogue writes."""
import argparse,gzip,hashlib,importlib.util,re,collections
from pathlib import Path
from urllib.parse import urljoin,urlsplit,urlunsplit,parse_qs
from functools import lru_cache
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-belvedere-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
s=importlib.util.spec_from_file_location('dates',Path(__file__).with_name('museum-expansion-birmingham-facts-20261007.py'));dates=importlib.util.module_from_spec(s);s.loader.exec_module(dates)
m=d.m;RUN=d.RUN;BASE=d.BASE
INDEX=BASE+'/advancedsearch/Objects/beginDate%3A100%3BendDate%3A1970%3Bclassifications_en%3APainting/images'
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def body(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'] and cap['receipt']['status']==200;return raw
def cleanurl(url,query=False):
 p=urlsplit(urljoin(BASE,url));return urlunsplit((p.scheme,p.netloc,p.path.split(';',1)[0],p.query if query else '', ''))
def creation(raw):
 t=re.sub(r'^um\s+','c. ',raw or '',flags=re.I);t=re.sub(r'^vor\s+','before ',t,flags=re.I);t=re.sub(r'^nach\s+','after ',t,flags=re.I)
 return dates.creation(t)
def index(raw):
 soup=BeautifulSoup(raw,'html.parser');rows=[]
 for card in soup.select('.result.grid-item'):
  a=card.select_one('.grid-item-inner > a[href]');url=cleanurl(a['href']);match=re.fullmatch(re.escape(BASE)+r'/objects/(\d+)/[^/]+',url);assert match
  txt=lambda sel:card.select_one(sel).get_text(' ',strip=True) or None if card.select_one(sel) else None
  rows.append(dict(source_id=match[1],url=url,title=txt('.title'),date_display=txt('.displayDate'),creator_label=txt('.primaryMaker'),index_internal_id=card.get('data-emuseum-id'),image_caption=card.img.get('alt') if card.img else None))
 pager=soup.select_one('input[name=pageField]');assert pager and 0<len(rows)<=12
 nexts={cleanurl(a['href'],True) for a in soup.select('a.next-page-link')};assert len(nexts)<=1
 return dict(rows=rows,page=int(pager['value']),last_page=int(pager['max']),next_url=next(iter(nexts),None))
def parsed(raw):
 soup=BeautifulSoup(raw,'html.parser');detail=soup.select_one('.detail-item-details');assert detail
 fields=[]
 for li in detail.select('.detailField'):
  label=li.select_one('.detailFieldLabel');value=li.select_one('.detailFieldValue')
  if not label or not value:continue
  row=dict(label=label.get_text(' ',strip=True),value=value.get_text(' ',strip=True),classes=li.get('class',[]),links=[dict(text=a.get_text(' ',strip=True),url=cleanurl(a['href'])) for a in value.select('a[href]')])
  if 'peopleField' in row['classes']:
   clean=BeautifulSoup(str(value),'html.parser');[x.decompose() for x in clean.select('.person-numbers')]
   raw_creator=clean.get_text(' ',strip=True)
   # Only the separate trailing life/activity parentheses are removed from the
   # object label; original biography and any attribution qualification survive.
   row['creator_label']=re.sub(r'\s*\([^()]*\b\d{3,4}\b[^()]*\)\s*$', '',raw_creator).strip();row['creator_with_biography']=raw_creator
  fields.append(row)
 title=detail.select_one('.titleField h1');assert title
 can=soup.select_one('link[rel=canonical]');assert can
 hist=detail.select_one('.objecthistoryField')
 return dict(title=title.get_text(' ',strip=True),fields=fields,canonical=cleanurl(can['href']),history_text=hist.get_text(' ',strip=True) if hist else None,history_html=str(hist) if hist else None,captions=[x.get_text(' ',strip=True) for x in soup.select('.media-info-caption')],source_text=soup.get_text(' ',strip=True))
@lru_cache(maxsize=32)
def checked_index(path,digest):
 p=m.ROOT/path;assert ref(p)['sha256']==digest;x=m.load(p);assert index(body(x['capture']))==x['parsed'];return x['parsed']['rows']
def checked_record(path):
 x=m.load(path);p=parsed(body(x['capture']));assert p==x['parsed'];assert cleanurl(x['capture']['receipt']['final_url'])==p['canonical']==x['index']['url']
 for r in x['index']['index_refs']:
  assert {k:x['index'][k] for k in ['source_id','url','title','date_display','creator_label','index_internal_id','image_caption']} in checked_index(r['path'],r['sha256'])
 return x,p
def indexes():
 rows={};refs=[];url=INDEX
 for page in range(1,21):
  dest=RUN/'indexes-001'/f'{page:03}.json.gz'
  if dest.exists():x=m.load(dest);assert x['url']==url
  else:
   raw,cap=d.n.capture('belvedere',url);x=dict(at=m.now(),url=url,capture=cap,parsed=index(raw),selection_reference=ref(RUN/'filtered-sample-001.json.gz'));m.save(dest,x)
  p=index(body(x['capture']));assert p==x['parsed'] and p['page']==page;reference=ref(dest);refs.append(reference)
  for r in p['rows']:
   sid=r['source_id']
   if sid in rows:assert {k:rows[sid][k] for k in r}==r
   else:rows[sid]=dict(r,index_refs=[])
   rows[sid]['index_refs'].append(reference)
  print('Page',page,'distinct',len(rows),flush=True);url=p['next_url'];assert url
 old=m.load(RUN/'initial-scope-001.json.gz')['snapshot'];oldids=set()
 for row in old['citations']+old['identifiers']:
  u=row.get('source_url') or row.get('canonical_url') or '';hit=re.search(r'sammlung\.belvedere\.at/(?:de/)?objects/(\d+)',u)
  if hit:oldids.add(hit[1])
 selected=[];held=[]
 for r in rows.values():
  dt=creation(r['date_display']);reasons=[]
  if dt['date_issue']:reasons.append(dt['date_issue'])
  if not r['creator_label']:reasons.append('No creator label on index; caption identity requires separate review')
  if r['source_id'] in oldids:reasons.append('Native object URL already in initial museum scope; reconcile existing object separately')
  (held if reasons else selected).append(dict(**r,index_holds=reasons))
 m.save(RUN/'discovered-001.json.gz',dict(at=m.now(),rows=list(rows.values()),selected=selected,unselected=held,index_references=refs,policy='20 bounded public pre1971 Painting index pages; select eligible literal index dates and supplied creators before fetching objects. Known existing native URLs retained without repeat capture. No exhaustive catalogue or image download.'))
 print('Selected',len(selected),'held',len(held),flush=True)
def objects():
 rows=m.load(RUN/'discovered-001.json.gz')['selected'];refs=[];errors=[]
 for pos,row in enumerate(rows):
  dest=RUN/'objects-001'/(row['source_id']+'.json.gz')
  try:
   if not dest.exists():
    raw,cap=d.n.capture('belvedere',row['url']);m.save(dest,dict(index=row,capture=cap,parsed=parsed(raw)))
   refs.append(ref(dest));print(pos+1,len(rows),row['title'],flush=True)
  except Exception as ex:errors.append(dict(index=row,error=type(ex).__name__+': '+str(ex)));print('FAILED',row['source_id'],str(ex),flush=True)
 m.save(RUN/'selected-capture-001.json.gz',dict(at=m.now(),records=refs,errors=errors,policy='Selected native metadata only. Individual identity, attribution, object/version and collection/provenance review required.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['indexes','objects']);globals()[p.parse_args().command]()
