"""Two bounded public catalogue searches for the remaining Leeds target gap."""
import gzip,hashlib,importlib.util,json,re
from pathlib import Path
import requests
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-leeds-drawings-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;PRIOR=m.RUN/'native/leeds-additions-20261009'
def search(params,label):
 config=m.load(PRIOR/'public-search-script-001.json');raw=gzip.decompress((m.ROOT/config['capture']['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==config['capture']['receipt']['sha256'];text=raw.decode();app=re.search(r"appId:\s*'([^']+)'",text)[1];key=re.search(r"apiKey:\s*'([^']+)'",text)[1];index=re.search(r"indexName:\s*'([^']+)'",text)[1];assert index=='prod_cotmania';url='https://'+app.lower()+'-dsn.algolia.net/1/indexes/'+index;dest=RUN/(label+'.json.gz');assert not dest.exists()
 with requests.get(url,params=params,headers={'X-Algolia-Application-Id':app,'X-Algolia-API-Key':key,'User-Agent':'ArtlineMuseumResearch/1.0 bounded public metadata'},timeout=(12,45)) as response:
  data=response.content;assert len(data)<4_000_000;body=RUN/(label+'.body.gz');assert not body.exists();body.write_bytes(gzip.compress(data,mtime=0));receipt=dict(url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),request_method='GET',public_frontend_config_reference=ref(PRIOR/'public-search-script-001.json'));m.save(RUN/(label+'-receipt.json'),receipt);response.raise_for_status();x=json.loads(data)
 m.save(dest,dict(at=m.now(),data=x,capture=dict(receipt=receipt,body_path=str(body.relative_to(m.ROOT))),script_reference=ref(Path(__file__).resolve()),policy='Bounded public frontend metadata query. No private index,write API,images or exhaustive catalogue retrieval.'))
 print(json.dumps(dict(label=label,total_index_hits=x.get('nbHits'),returned=len(x['hits']),bytes=len(data))),flush=True)
def main():
 RUN.mkdir(parents=True,exist_ok=True);attrs=json.dumps(['url','reference','title','maker','objectname','type','date','searchdate','description'])
 search(dict(query='',hitsPerPage=40,page=1,facetFilters=json.dumps(['type:Works of Art','objectname:Watercolour']),attributesToRetrieve=attrs),'watercolour-index-001')
 search(dict(query='',hitsPerPage=120,page=0,facetFilters=json.dumps(['type:Works of Art','objectname:Drawing']),attributesToRetrieve=attrs),'drawing-index-001')
if __name__=='__main__':main()
