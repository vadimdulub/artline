#!/usr/bin/env python3
"""Selected official artist biographies; no new artwork crawling or images."""
import importlib.util,concurrent.futures,threading,time,re,collections
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-poland-collections-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-poland-collections-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
works=m.load(m.RUN/'poland/source-records.json.gz');urls={};s=r.Source()
for w in works:
 if w['provider']!='zacheta':continue
 raw,rc=s.get(w['source_url'],as_json=False)
 for a in BeautifulSoup(raw,'html.parser').select('a[href]'):
  if '/pl/kolekcja/artysci/' in a['href'] and m.norm(a.get_text(' ',strip=True))==m.norm(w['creator_label']):urls['https://zacheta.art.pl'+a['href']]=w['creator_label']
lock=threading.Lock();blocked=threading.Event();last=[0]
def one(pair):
 u,name=pair
 try:
  with lock:
   if blocked.is_set():return dict(url=u,name=name,error='Provider stopped after access restriction')
   time.sleep(max(0,last[0]+.5-time.monotonic()));last[0]=time.monotonic()
  raw,rc=r.Source().get(u,as_json=False);sp=BeautifulSoup(raw,'html.parser');text=sp.get_text(' ',strip=True)
  title=sp.select_one('h1.text-header-main');assert title and m.norm(title.get_text(' ',strip=True))==m.norm(name)
  start=text.index(name,text.index('udostępnij'))+len(name);bio=re.split(r'Artyści \d|Prace artyst|Lorem ipsum',text[start:])[0].strip()
  # Keep the raw page capture; application evidence gets only extracted factual sentences.
  sentences=[x.strip() for x in re.split(r'(?<=[.!?])\s+',bio) if x.strip()]
  facts=[x for x in sentences if re.search(r'urodz|\bur\.|zmar|\bzm\.|stud|prac|mieszka|polsk',x,re.I)]
  return dict(url=u,name=name,evidence=rc,bio_excerpt=bio[:700],factual_sentences=facts[:10])
 except Exception as e:
  if any(v in str(e) for v in ['HTTP 401','HTTP 403','HTTP 429']):blocked.set()
  return dict(url=u,name=name,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:out=list(pool.map(one,urls.items()))
m.save(m.RUN/'artist-biographical-research.json.gz',out);print('Official creator profiles',len(out),'errors',sum('error' in x for x in out),flush=True)
