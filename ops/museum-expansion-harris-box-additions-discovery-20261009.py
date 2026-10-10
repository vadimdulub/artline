"""Follow exposed public API discovery and two selected museum context links."""
import importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-harris-box-additions-common-20261009.py');n=module('n','museum-expansion-britain-nine-native-20261009.py');m=s.m;RUN=s.RUN;n.RUN=RUN
def main():
 dest=RUN/'native-discovery-001.json.gz';assert not dest.exists();probes=m.load(RUN/'native-probes-001.json.gz');rows=[]
 for r in probes['rows']:
  if not r.get('capture'):continue
  url=r['api_discovery'][0]['href'];provider=r['provider']
  try:
   raw,cap=n.capture(provider,url);d=json.loads(raw);routes=d.get('routes',{});chosen={k:v for k,v in routes.items() if k.startswith('/wp/v2/') and any(t in k for t in ['types','taxonomies','collection','art'])};rows.append(dict(provider=provider,url=url,capture=cap,public_routes=chosen,namespaces=d.get('namespaces')));print(json.dumps(dict(provider=provider,bytes=len(raw),route_names=list(chosen))),flush=True)
  except Exception as e:rows.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(rows[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=rows,entrypoints_reference=s.ref(RUN/'native-probes-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='Read-only public WordPress API root explicitly advertised by each museum page. Route discovery only,no collection enumeration,images or protected endpoints. Refusal stops provider.'))
if __name__=='__main__':main()
