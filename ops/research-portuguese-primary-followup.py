#!/usr/bin/env python3
"""Twenty primary-source follow-ups on the selected Portuguese creator scopes."""
import importlib.util,json,time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;BASE=m.x.ROOT/'docs/research/overnight-countries-20260913';RUN=BASE/'portugal/primary-followup'
def main():
 session=requests.Session();session.headers['User-Agent']='Artline selected museum object research'
 for n in range(1,21):
  out=RUN/f'round-{n:02d}'/'research.json'
  if out.exists():continue
  records=[]
  for p in sorted((BASE/'portugal/PT'/f'round-{n:02d}/delivery/ready').glob('*.json')):
   w=json.loads(p.read_text())['record'];urls=[v for v in m.m.r.values(w['entity'],'P973') if isinstance(v,str) and urlparse(v).hostname in ('gulbenkian.pt','www.matriznet.dgpc.pt','matriznet.dgpc.pt','www.matrizpix.dgpc.pt','matrizpix.dgpc.pt')];entry=dict(qid=w['qid'],title=w['title'],creator=w['creator_label'],accession=w['accession'],date=w['date'],sources=[])
   for original in urls:
    url=original.replace('http://','https://')
    if urlparse(url).hostname=='gulbenkian.pt':url=url.replace('/museu/works_cam/','/cam/works/')
    key=CORE.sha(url.encode())[:20];folder=RUN/'captures';folder.mkdir(parents=True,exist_ok=True);raw=folder/(key+'.html');rp=folder/(key+'.receipt.json')
    try:
     if not raw.exists():
      response=session.get(url,timeout=30);response.raise_for_status();assert len(response.content)<3000000
      CORE.save_new(raw,response.content);CORE.save_new(rp,dict(original_source_url=original,url=url,final_url=response.url,status=response.status_code,retrieved_at=CORE.now(),sha256=CORE.sha(response.content)))
     receipt=json.loads(rp.read_text());assert CORE.sha(raw.read_bytes())==receipt['sha256'];soup=BeautifulSoup(raw.read_bytes(),'html.parser')
     for node in soup(['script','style','nav','footer','header','noscript']):node.decompose()
     text=soup.get_text('\n',strip=True);tp=raw.with_suffix('.txt')
     if not tp.exists():CORE.save_new(tp,text.encode())
     entry['sources'].append(dict(receipt=receipt,capture_path=str(raw),text_path=str(tp),page_title=soup.title.get_text(' ',strip=True) if soup.title else None,review='Captured primary text. Creation, inventory, maker, institution and image rights require individual review; historical exhibition and acquisition dates are not creation dates.'))
    except Exception as e:entry['sources'].append(dict(url=url,at=CORE.now(),error=type(e).__name__+': '+str(e)[:200]))
    time.sleep(1.5)
   if not urls:entry['followup']='No exact primary URL in source statement; museum search/authority crosswalk required.'
   records.append(entry)
  CORE.save_new(out,dict(at=CORE.now(),round=n,scope='Current primary museum identity/dating follow-up on the distinct selected Portuguese creator scope; metadata only, no image copying.',records=records));print('Portugal primary round',n,'objects',len(records),flush=True)
if __name__=='__main__':main()
