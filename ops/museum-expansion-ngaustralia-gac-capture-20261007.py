#!/usr/bin/env python3
"""Bounded, metadata-only National Gallery of Australia partner discovery on Google Arts & Culture."""
import argparse,gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-ngaustralia-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
m=d.m;RUN=d.RUN;BASE='https://artsandculture.google.com';d.n.SITES['ngaustralia']=BASE
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def body(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'] and cap['receipt']['status']==200;return raw
def init(raw):
 soup=BeautifulSoup(raw,'html.parser');out=[]
 for script in soup.select('script'):
  t=script.get_text()
  if not t.startswith('window.INIT_data'):continue
  for match in re.finditer(r"window\.INIT_data\['[^']+'\]\s*=\s*",t):out.append(json.JSONDecoder().raw_decode(t[match.end():])[0])
 assert out;return out
def cards(raw):
 rows={}
 def walk(v):
  if not isinstance(v,list):return
  if v and v[0]=='gac.oi' and isinstance(v[4],str) and v[4].startswith('/asset/'):
   sid=v[4].rstrip('/').rsplit('/',1)[-1];r=dict(source_id=sid,title=v[1],creator=v[2],url=BASE+v[4]);assert sid not in rows or rows[sid]==r;rows[sid]=r
  else:
   for child in v:walk(child)
 for v in init(raw):walk(v)
 return list(rows.values())
def parsed_object(raw):
 soup=BeautifulSoup(raw,'html.parser');fields=[]
 for li in soup.select('li.XD0Pkb'):
  label=li.select_one('.PUhAff')
  if label:fields.append(dict(label=label.get_text(' ',strip=True).rstrip(':'),value=li.get_text(' ',strip=True)[len(label.get_text(' ',strip=True)):].strip(),links=[dict(text=a.get_text(' ',strip=True),url=urljoin(BASE,a['href'])) for a in li.select('a[href]')]))
 h1=soup.select('h1');h2=soup.select_one('h2.SThaNc');h3=soup.select_one('h3.To7WBf');canonical=soup.select('link[rel=canonical]')
 return dict(headings=[h.get_text(' ',strip=True) for h in h1],subtitle=h2.get_text(' ',strip=True) if h2 else None,publisher_heading=h3.get_text(' ',strip=True) if h3 else None,fields=fields,canonical=[x.get('href') for x in canonical],partner_links=sorted({a['href'] for a in soup.select('a[href]') if a['href'].startswith('/partner/')}),text=soup.get_text(' ',strip=True))
def indexes():
 partner=m.load(RUN/'gac-partner-001.json.gz');soup=BeautifulSoup(body(partner['capture']),'html.parser')
 # Public facet URLs actually supplied by this museum's partner page. Only
 # the initial 20 records per facet; no pagination or image downloading.
 names=['Sidney Nolan','Arthur Streeton','Thomas Roberts','Modern art','Impressionism','Surrealism','Wood','Paper','Drawing','Photograph','Metal','Australia','Melbourne']
 urls={}
 for a in soup.select('a[href]'):
  label=re.sub(r' \d+$','',a.get_text(' ',strip=True))
  if label in names and a['href'].startswith('/explore/collections/national-gallery-of-australia-canberra?') and 'f=person:' not in a['href']:urls[label]=BASE+a['href']
 assert set(urls)==set(names);allrows={r['source_id']:dict(r,index_refs=[ref(RUN/'gac-partner-001.json.gz')]) for r in cards(body(partner['capture']))}
 for label in names:
  dest=RUN/'gac-indexes-001'/(label.replace(' ','-').lower()+'.json.gz')
  if dest.exists():v=m.load(dest)
  else:
   raw,cap=d.n.capture('ngaustralia',urls[label]);rows=cards(raw);assert len(rows)<=20
   v=dict(label=label,url=urls[label],capture=cap,rows=rows,partner_reference=ref(RUN/'gac-partner-001.json.gz'));m.save(dest,v)
  assert v['rows']==cards(body(v['capture']))
  for row in v['rows']:
   sid=row['source_id']
   if sid in allrows:assert {k:allrows[sid][k] for k in row}==row
   else:allrows[sid]=dict(row,index_refs=[])
   allrows[sid]['index_refs'].append(ref(dest))
  print(label,len(v['rows']),'distinct',len(allrows),flush=True)
 assert len(allrows)<=200
 m.save(RUN/'gac-discovered-001.json.gz',dict(at=m.now(),rows=list(allrows.values()),policy='Bounded museum-partner index leads, not automatic eligible holdings. No images, API pagination or catalogue writes.'))
def objects():
 rows=m.load(RUN/'gac-discovered-001.json.gz')['rows'];assert len(rows)<=200;refs=[]
 for pos,row in enumerate(rows):
  dest=RUN/'gac-objects-001'/(row['source_id']+'.json.gz')
  if not dest.exists():
   raw,cap=d.n.capture('ngaustralia',row['url']);m.save(dest,dict(index=row,capture=cap,parsed=parsed_object(raw)))
  refs.append(ref(dest));print(pos+1,len(rows),row['title'],flush=True)
 m.save(RUN/'gac-selected-capture-001.json.gz',dict(at=m.now(),records=refs,policy='Selected museum-scoped object metadata and receipts; no images downloaded. Individual dates, collection evidence, creator qualifiers, versions and duplicates still require review.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['indexes','objects']);a=p.parse_args();globals()[a.command]()
