"""Bounded public collection taxonomy and one sample object metadata response."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-harris-box-additions-common-20261009.py');n=module('n','museum-expansion-britain-nine-native-20261009.py');m=s.m;RUN=s.RUN;n.RUN=RUN
def main():
 dest=RUN/'harris-taxonomy-001.json.gz';assert not dest.exists();discovery=m.load(RUN/'native-discovery-001.json.gz');h=next(r for r in discovery['rows'] if r['provider']=='harris');rows=[]
 for route,params in [('/wp/v2/collections',{'per_page':50}),('/wp/v2/collection-item',{'per_page':1,'_fields':'id,link,slug,title,content,acf,meta,collections,hf_cat_collection-item'})]:
  assert route in h['public_routes'];url='https://theharris.org.uk/wp-json'+route+'?'+urlencode(params)
  try:
   raw,cap=n.capture('harris',url);data=json.loads(raw);assert isinstance(data,list);rows.append(dict(route=route,url=url,capture=cap,data=data));print(json.dumps(dict(route=route,data=data),ensure_ascii=False)[:9000],flush=True)
  except Exception as e:rows.append(dict(route=route,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(rows[-1]),flush=True);break
 m.save(dest,dict(at=m.now(),rows=rows,discovery_reference=s.ref(RUN/'native-discovery-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='Public GET routes found in advertised native API. At most50collection taxonomy terms and1sample object,not bulk collection enumeration. WordPress publication timestamps never used as artwork dates; image URLs remain unrequested.'))
if __name__=='__main__':main()
