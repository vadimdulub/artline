"""Selected inventory requests through Brighton's published anonymous search API."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-britain-four-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;n=p.n;RUN=p.RUN;ref=p.ref

def search(inventory):
 url=n.SITES['brighton']+'/api/search?'+urlencode({'q':inventory,'departments':''});raw,c=n.capture('brighton',url);payload=json.loads(raw);assert isinstance(payload,dict) and 'data' in payload;data=payload['data'];assert isinstance(data,list) and len(data)<=10;return data,c

def main():
 dest=RUN/'brighton-sample-001.json';assert not dest.exists();out=[]
 for inventory in ['FA000683','FAH1998.7']:
  data,c=search(inventory);out.append(dict(inventory=inventory,results=data,capture=c));print(json.dumps(out[-1],ensure_ascii=False),flush=True)
 m.save(dest,dict(at=m.now(),rows=out,script_reference=ref(Path(__file__).resolve()),public_search_flow_reference=ref(RUN/'brighton-public-scripts-001.json'),policy='Exact selected inventories only. Public API and query parameters observed in the anonymous homepage script. Search result identity is not itself editorial approval. No images requested.'))
if __name__=='__main__':main()
