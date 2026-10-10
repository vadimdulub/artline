#!/usr/bin/env python3
"""Capture two official LaM institutional identity pages; no images or retries."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-france-fifth-native-20261008.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n);m=n.m
URLS={'lam-history':'https://www.musee-lam.fr/fr/lhistoire-du-lam','mel-museum-history':'https://archives.lillemetropole.fr/n/le-musee-d-art-moderne/n%3A170'}
def main():
 refs=[]
 for key,url in URLS.items():
  p=n.RUN/'context-001'/(key+'.html.gz');assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True)
  try:
   with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (institutional identity context; no images)'},timeout=(15,50),stream=True) as r:
    raw=b''
    for part in r.iter_content(65536):
     raw+=part
     if len(raw)>4_000_000:raise ValueError('Context exceeds bound')
    receipt=dict(url=url,final_url=r.url,status=r.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());p.write_bytes(gzip.compress(raw,mtime=0));m.save(p.with_suffix('.receipt.json'),receipt);r.raise_for_status()
   refs.append(dict(body=n.ref(p),receipt=n.ref(p.with_suffix('.receipt.json'))));print(key,r.status_code,len(raw),flush=True)
  except Exception as e:
   m.save(n.RUN/'context-errors-001'/(key+'.json'),dict(at=m.now(),url=url,error=repr(e),policy='First failure stopped; no retry or alternate transport.'));raise
 m.save(n.RUN/'holding-context-001.json',dict(at=m.now(),sources=refs,institution_id='a7c167a4-ca30-4df6-a870-50af7ae5cb4e',museum_code='M0639',basis='Official LaM history and MEL archive identify the former Musee d art moderne Lille Metropole at Villeneuve d Ascq with present LaM and document its donated collections. This supports museum identity, not legal title to any particular object. Each selected object still needs current exact national-catalogue conservation location, museum code and acquisition-to-museum labels; deposits elsewhere and missing objects excluded.',legal_title_claim=False,current_display_claim=False))
if __name__=='__main__':main()
