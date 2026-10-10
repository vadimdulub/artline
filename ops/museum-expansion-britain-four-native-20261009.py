"""Bounded discovery of the two publicly linked native collection catalogues."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-britain-four-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-native-20261006.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n)
n.RUN=RUN;n.SITES={'brighton':'https://collections.brightonmuseums.org.uk','ulster':'https://collections.nationalmuseumsni.org'}
def main():
 dest=RUN/'native-probes-001.json';assert not dest.exists();out=[]
 for provider,url in [('brighton',n.SITES['brighton']+'/'),('ulster',n.SITES['ulster']+'/home')]:
  try:
   raw,c=n.capture(provider,url);p=n.BeautifulSoup(raw,'html.parser');r=dict(provider=provider,url=url,capture=c,text=p.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in p.select('a[href]')],scripts=[a['src'] for a in p.select('script[src]')],forms=[str(f) for f in p.select('form')]);out.append(r);print(json.dumps(dict(provider=provider,bytes=c['receipt']['bytes'],scripts=r['scripts'])),flush=True)
  except Exception as e:out.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(out[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=out,script_reference=ref(Path(__file__).resolve()),previous_native_discovery_reference=ref(s.prior.RUN/'native-probes-001.json'),policy='Official public collection links discovered from native institution pages in preceding pass. Overview and search-form discovery only, no object holding inferred. Preserve all earlier source access holds; stop on access failure and do not download images.'))
if __name__=='__main__':main()
