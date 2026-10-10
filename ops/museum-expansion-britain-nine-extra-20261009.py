"""Exact observed native institutional-history and collection-search leads."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-nine-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN
SOURCES=[('box','https://www.theboxplymouth.com/blog/news/how-it-started-v-how-its-going-part-two'),('york','https://yorkmuseumstrust.org.uk/collections/search/?CL[0]=Fine%20Art')]
def main():
 dest=RUN/'native-extra-001.json.gz';assert not dest.exists();rows=[]
 for provider,url in SOURCES:
  try:
   raw,c=n.capture(provider,url);p=n.parsed(raw);rows.append(dict(provider=provider,url=url,capture=c,parsed=p));print(json.dumps(dict(provider=provider,url=url,forms=p['forms'],links=[v for v in p['links'] if '/collections/search/' in v['href']])),flush=True)
  except Exception as e:rows.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(rows[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=rows,script_reference=n.ref(Path(__file__).resolve()),policy='Box institutional succession context and first native York Fine Art results only. No object additions from discovery,images or form submissions.'))
if __name__=='__main__':main()
