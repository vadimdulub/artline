"""Selected official/estate version evidence, metadata only."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-eight-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN
URLS={'gulbenkian':'https://gulbenkian.pt/cam/en/works/brown-blue-and-violet-no-2/','flowers':'https://www.flowersgallery.com/news/889-michael-kidner-featured-in-shadows-and-light/'}
def main():
 out=[];dest=RUN/'kidner-selected-native-001.json';assert not dest.exists()
 for provider,url in URLS.items():
  n.n.SITES[provider]=url.split('/cam/')[0] if provider=='gulbenkian' else 'https://www.flowersgallery.com'
  try:
   raw,cap=n.n.capture(provider,url);p=n.parsed(raw);out.append(dict(provider=provider,url=url,capture=cap,parsed=p));print(json.dumps(dict(provider=provider,text=p['text'])),flush=True)
  except Exception as e:out.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(out[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=out,script_reference=n.ref(Path(__file__).resolve()),policy='Two selected version checks. No images or catalogue metadata changes. Failures retained; no access bypass.'))
if __name__=='__main__':main()
