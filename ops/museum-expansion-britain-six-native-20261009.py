"""Bounded discovery of RWA and Ferens official public collection interfaces."""
import hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-native-20261006.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=m.RUN/'native/britain-six-holdings-20261009';n.RUN=RUN
n.SITES={'rwa':'https://www.rwa.org.uk','ferens':'https://www.hullmuseums.co.uk'}
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def parsed(raw):
 soup=n.BeautifulSoup(raw,'html.parser');return dict(text=soup.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in soup.select('a[href]')],scripts=[v['src'] for v in soup.select('script[src]')],forms=[str(v) for v in soup.select('form')])
def main():
 dest=RUN/'native-probes-001.json';assert not dest.exists();out=[]
 for provider,url in [('rwa','https://www.rwa.org.uk/pages/our-collection/1000'),('rwa','https://www.rwa.org.uk/pages/our-collection-q-a'),('ferens','https://www.hullmuseums.co.uk/collections')]:
  try:
   raw,c=n.capture(provider,url);data=parsed(raw);out.append(dict(provider=provider,url=url,capture=c,parsed=data));print(json.dumps(dict(provider=provider,bytes=c['receipt']['bytes'],links=[v for v in data['links'] if any(t in v['href'].lower() for t in ['collection','ehive','search','catalog','record'])],scripts=data['scripts'])),flush=True)
  except Exception as e:out.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(out[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=out,script_reference=ref(Path(__file__).resolve()),policy='Official collection links discovered from museum homepages. Overview and public search discovery only. No object holding inference,images,authentication,exhaustive crawl or catalogue writes. All earlier source access holds remain; stop on new access failure.'))
if __name__=='__main__':main()
