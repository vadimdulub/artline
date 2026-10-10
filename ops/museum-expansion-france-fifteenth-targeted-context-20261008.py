"""Selected independent primary pages for remaining object-identity questions."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-fifteenth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m;RUN=f.RUN
SOURCES=[
 ('esteve-micmac',6,'https://collections.ville-bourges.fr/fr/document/a-922-micmac-aux-pattes/67ebdef1a2974a50930afc79?pageId=68add223ec2b3c3de5343849&v=mosaic&pos=8&pgn=0'),
 ('louvre-oa427',585,'https://collections.louvre.fr/ark:/53355/cl010097192'),
 ('louvre-oa431',531,'https://collections.louvre.fr/ark:/53355/cl010109869'),
]
def main():
 root=RUN/'targeted-context-001';assert not root.exists();root.mkdir();out=[]
 for name,n,url in SOURCES:
  try:
   with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected museum identity evidence)'},timeout=(15,45),stream=True) as response:
    raw=b''
    for chunk in response.iter_content(65536):
     raw+=chunk
     if len(raw)>4_000_000:raise ValueError('Bounded response exceeded')
    receipt=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    body=root/(name+'.html.gz');rp=root/(name+'.receipt.json');body.write_bytes(gzip.compress(raw,mtime=0));m.save(rp,receipt);response.raise_for_status()
   soup=BeautifulSoup(raw,'html.parser')
   for tag in soup(['script','style','noscript']):tag.decompose()
   text=soup.get_text('\n',strip=True);tp=root/(name+'.txt');tp.write_text(text)
   out.append(dict(number=n,name=name,body_reference=f.ref(body),receipt_reference=f.ref(rp),text_reference=f.ref(tp),literal_text=text,**receipt));print(json.dumps(dict(name=name,status=receipt['status'])),flush=True)
  except Exception as error:
   ep=root/(name+'.error.json');m.save(ep,dict(at=m.now(),url=url,error=repr(error),policy='No retry or access bypass. Independent requests may continue.'));out.append(dict(number=n,name=name,error_reference=f.ref(ep)));print(json.dumps(dict(name=name,error=repr(error))),flush=True)
 m.save(RUN/'targeted-context-001.json.gz',dict(at=m.now(),rows=out,capture_reference=f.ref(Path(__file__).resolve()),database_writes=0,images=0))
if __name__=='__main__':main()
