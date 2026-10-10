"""Two bounded primary-metadata probes; no images, retries or catalogue writes."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-arco-20261006.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
RUN=m.RUN/'native/italy-second-minimum-20261008'
def main():
 root=RUN/'probe-001';assert not root.exists();root.mkdir();out=[]
 uri='https://w3id.org/arco/resource/HistoricOrArtisticProperty/1100140530'
 query='SELECT ?p ?o WHERE { <'+uri+'> ?p ?o } LIMIT 500'
 jobs=[('fano-object','https://catalogo.cultura.gov.it/detail/HistoricOrArtisticProperty/1100140530',None),('fano-root','https://dati.cultura.gov.it/sparql',dict(query=query,format='application/sparql-results+json'))]
 for name,url,params in jobs:
  try:
   with requests.get(url,params=params,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected official metadata; no images)'},timeout=(12,40),stream=True) as res:
    raw=b''
    for part in res.iter_content(65536):
     raw+=part
     if len(raw)>4_000_000:raise ValueError('Metadata response exceeds bound')
    receipt=dict(url=url,params=params,final_url=res.url,status=res.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),content_type=res.headers.get('Content-Type'))
    body=root/(name+'.body.gz');body.write_bytes(gzip.compress(raw,mtime=0));m.save(root/(name+'.receipt.json'),receipt)
    row=dict(name=name,receipt=receipt,body_path=str(body.relative_to(m.ROOT)))
    if res.status_code==200:
     if params:row['data']=json.loads(raw)
     else:
      row['fields']=a.fields(raw);soup=BeautifulSoup(raw,'html.parser')
      for tag in soup(['script','style','noscript']):tag.decompose()
      tp=root/(name+'.txt');tp.write_text(soup.get_text('\n',strip=True));row['text_path']=str(tp.relative_to(m.ROOT))
    else:row['state']='source_http_failure_no_retry'
    out.append(row);print(json.dumps(dict(name=name,status=res.status_code,bytes=len(raw),fields=row.get('fields'),triples=len(row.get('data',{}).get('results',{}).get('bindings',[]))),ensure_ascii=False),flush=True)
  except Exception as error:
   failure=dict(at=m.now(),name=name,url=url,params=params,error=repr(error),state='source_failure_no_retry');m.save(root/(name+'.error.json'),failure);out.append(failure);print(json.dumps(failure),flush=True)
 m.save(RUN/'probe-001.json.gz',dict(at=m.now(),rows=out,database_writes=0,images=0))
if __name__=='__main__':main()
