#!/usr/bin/env python3
"""Bounded primary metadata review of preselected same-title duplicate leads.

No DB writes or artwork-image downloads. Exact museum inventory is read from
the object record, never guessed from its URL or catalogue identifier.
"""
import collections,hashlib,importlib.util,json,re,subprocess,time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;RUN=m.x.BASE/'duplicates/same-title-deep-review'
def main():
 d=json.loads((RUN/'candidates.json').read_text());byid=collections.defaultdict(set)
 for c in d['citations']:
  if c['source_url']:byid[c['entity_id']].add(c['source_url'].rstrip('/'))
 works={w['slug']:w for p in d['pairs'] for w in p['works']};session=requests.Session();session.headers['User-Agent']='Artline museum research (bounded metadata identity review)'
 for index,(slug,w) in enumerate(sorted(works.items()),1):
  filename=slug if len(slug.encode())<=220 else slug[:120]+'-'+hashlib.sha256(slug.encode()).hexdigest()[:16]
  out=RUN/'inventory-review'/(filename+'.json')
  if out.exists():continue
  urls=sorted(u for u in byid[w['id']] if urlparse(u).hostname in ('rusmuseumvrm.ru','www.lombardiabeniculturali.it'))
  result=dict(at=CORE.now(),slug=slug,existing=w,reviews=[])
  for url in urls:
   try:
    key=hashlib.sha256(url.encode()).hexdigest()[:20];host=urlparse(url).hostname;folder=RUN/'inventory-captures';folder.mkdir(exist_ok=True)
    if host=='rusmuseumvrm.ru':
     p=folder/(key+'.html');rp=p.with_suffix('.receipt.json')
     if not p.exists():
      response=session.get(url,timeout=35);response.raise_for_status();assert len(response.content)<10000000
      CORE.save_new(p,response.content);CORE.save_new(rp,dict(url=url,final_url=response.url,retrieved_at=CORE.now(),sha256=CORE.sha(response.content),status=response.status_code))
     receipt=json.loads(rp.read_text());assert CORE.sha(p.read_bytes())==receipt['sha256'];soup=BeautifulSoup(p.read_bytes(),'html.parser')
     text=lambda selector:soup.select_one(selector).get_text(' ',strip=True) if soup.select_one(selector) else None
     inventory=text('[title="Инвентарный номер"]');title=text('.work__title');maker=text('.work__author');link=soup.select_one('.work__author a')
     result['reviews'].append(dict(receipt=receipt,capture=str(p),title=title,inventory=inventory,creator_label=maker,creator_path=link.get('href') if link else None,creator_life=text('.work__desc'),date_text=text('.period'),medium=text('[title="Материал"]'),dimensions=text('[title="Размер"]'),title_matches=m.m.r.norm(title or '')==m.m.r.norm(w['title'])))
    else:
     oid=urlparse(url).path.rstrip('/').rsplit('/',1)[-1];pdfurl='https://www.lombardiabeniculturali.it/opere-arte/schede-complete/'+oid+'/'
     p=folder/(key+'.pdf');rp=p.with_suffix('.receipt.json');tp=p.with_suffix('.txt')
     if not p.exists():
      raw=subprocess.run(['curl','--fail','--silent','--show-error','--location','--max-time','40','--max-filesize','10000000',pdfurl],check=True,capture_output=True).stdout;assert raw.startswith(b'%PDF-')
      CORE.save_new(p,raw);CORE.save_new(rp,dict(url=pdfurl,retrieved_at=CORE.now(),sha256=CORE.sha(raw),client='System curl, verified TLS'))
     receipt=json.loads(rp.read_text());assert CORE.sha(p.read_bytes())==receipt['sha256']
     if not tp.exists():subprocess.run(['pdftotext','-layout',str(p),str(tp)],check=True,capture_output=True)
     body=tp.read_text();sections=re.split(r'\n\s*INVENTARIO(?: \[\d+ / \d+\])?\s*\n',body)[1:];inventories=[]
     for section in sections:
      part=re.split(r'\n\s*(?:STIMA|COLLEZIONI|CRONOLOGIA|RAPPORTO|DEFINIZIONE CULTURALE|UBICAZIONE|LOCALIZZAZIONE|ISCRIZIONI|ALTRI INVENTARI)\b',section)[0]
      number=re.search(r'^\s*Numero:\s*([^\n]+)',part,re.M);label=re.search(r'^\s*Denominazione:\s*([^\n]+)',part,re.M)
      if number:inventories.append(dict(number=number.group(1).strip(),label=label.group(1).strip() if label else None,context=part[:1200]))
     result['reviews'].append(dict(receipt=receipt,capture=str(p),catalogue_id=oid,inventories=inventories,full_text_path=str(tp),decision='individual_primary_inventory_review_required'))
   except Exception as error:result['reviews'].append(dict(url=url,error=type(error).__name__+': '+str(error)[:300]))
   time.sleep(1.25)
  CORE.save_new(out,result)
  if index%10==0:print('Primary same-title review',index,'/',len(works),flush=True)
 CORE.save_new(RUN/'inventory-research-completed.json',dict(at=CORE.now(),unique_objects=len(works),pairs=len(d['pairs']),policy='Metadata-only primary captures; no automatic duplicate merges.'))
if __name__=='__main__':main()
