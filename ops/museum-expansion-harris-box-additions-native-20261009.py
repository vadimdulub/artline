"""Fresh bounded official collection entrypoints; no images or access-hold retries."""
import importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-harris-box-additions-common-20261009.py');n=module('n','museum-expansion-britain-nine-native-20261009.py');m=s.m;RUN=s.RUN;n.RUN=RUN
def main():
 dest=RUN/'native-probes-001.json.gz';assert not dest.exists();rows=[]
 for provider,url in [('harris','https://www.theharris.org.uk/collections/fine-art-collections/'),('box','https://www.theboxplymouth.com/collections')]:
  try:
   raw,cap=n.capture(provider,url);p=n.parsed(raw);soup=n.BeautifulSoup(raw,'html.parser');discovery=[dict(x.attrs) for x in soup.select('link[rel]') if 'api.w.org' in str(x)];rows.append(dict(provider=provider,url=url,capture=cap,parsed=p,api_discovery=discovery));print(json.dumps(dict(provider=provider,bytes=len(raw),api_discovery=discovery,collection_links=[x for x in p['links'] if any(t in x['href'].lower() for t in ['collection','catalogue'])][:25])),flush=True)
  except Exception as e:rows.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(rows[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=rows,script_reference=s.ref(Path(__file__).resolve()),policy='Two official collection entrypoints only. Index labels are discovery,not approved object facts. No images,contact submissions,held-provider requests or database mutations.'))
if __name__=='__main__':main()
