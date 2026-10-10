"""Bounded public Cotmania search using the museum frontend's published search-only configuration."""
import gzip,hashlib,importlib.util,json,re
from pathlib import Path
import requests
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-leeds-additions-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref

def search(params,label):
 config=m.load(RUN/'public-search-script-001.json');raw=gzip.decompress((m.ROOT/config['capture']['body_path']).read_bytes()).decode();app=re.search(r"appId:\s*'([^']+)'",raw)[1];key=re.search(r"apiKey:\s*'([^']+)'",raw)[1];index=re.search(r"indexName:\s*'([^']+)'",raw)[1];assert index=='prod_cotmania';url='https://'+app.lower()+'-dsn.algolia.net/1/indexes/'+index;dest=RUN/(label+'.json.gz');assert not dest.exists()
 with requests.get(url,params=params,headers={'X-Algolia-Application-Id':app,'X-Algolia-API-Key':key,'User-Agent':'ArtlineMuseumResearch/1.0 bounded public metadata'},timeout=(12,45)) as response:
  data=response.content;assert len(data)<4_000_000;body=RUN/(label+'.body.gz');assert not body.exists();body.write_bytes(gzip.compress(data,mtime=0));receipt=dict(url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),request_method='GET',public_frontend_config_reference=ref(RUN/'public-search-script-001.json'));m.save(RUN/(label+'-receipt.json'),receipt);response.raise_for_status();x=json.loads(data)
 m.save(dest,dict(at=m.now(),data=x,capture=dict(receipt=receipt,body_path=str(body.relative_to(m.ROOT))),script_reference=ref(Path(__file__).resolve()),policy='Only public frontend search index; bounded metadata,not a collection export. No images. Search-only key not printed or used for writes.'))
 print(json.dumps(dict(label=label,nbHits=x.get('nbHits'),facets=x.get('facets'),hits=x['hits']),ensure_ascii=False),flush=True)
if __name__=='__main__':search(dict(query='Watercolour',hitsPerPage=40,page=0,facets=json.dumps(['type','objectname'])),'cotmania-discovery-001')
