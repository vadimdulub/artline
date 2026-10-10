"""Bounded official Leeds collection context and catalogue discovery; metadata only."""
import hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-native-20261006.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=m.RUN/'native/leeds-holdings-20261009';n.RUN=RUN;n.SITES={'leeds':'https://museumsandgalleries.leeds.gov.uk','gac':'https://artsandculture.google.com','henrymoore':'https://henry-moore.org'}
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def parsed(raw):
 s=n.BeautifulSoup(raw,'html.parser');return dict(text=s.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in s.select('a[href]')],scripts=[v['src'] for v in s.select('script[src]')],forms=[str(v) for v in s.select('form')])
SOURCES=[('leeds','https://museumsandgalleries.leeds.gov.uk/fine-art-collection-fcxq'),('leeds','https://museumsandgalleries.leeds.gov.uk/our-collections-69nb'),('gac','https://artsandculture.google.com/partner/leeds-museums-and-galleries'),('henrymoore','https://henry-moore.org/what-we-do/about-the-henry-moore-institute/leeds-sculpture-collections/')]
def main():
 dest=RUN/'native-probes-001.json';assert not dest.exists();out=[];failures={};stopped=set()
 for provider,url in SOURCES:
  if provider in stopped:out.append(dict(provider=provider,url=url,state='unrequested_after_access_hold'));continue
  try:
   raw,c=n.capture(provider,url);p=parsed(raw);out.append(dict(provider=provider,url=url,capture=c,parsed=p));failures[provider]=0;print(json.dumps(dict(provider=provider,url=url,bytes=c['receipt']['bytes'],links=[v for v in p['links'] if any(t in v['href'].lower() for t in ['collection','artsandculture','artuk','fine-art','scottish-art','painting','exhibition'])])),flush=True)
  except Exception as e:
   failures[provider]=failures.get(provider,0)+1;out.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(out[-1]),flush=True)
   if failures[provider]>=3 or any(t in str(e) for t in ['403','429']):stopped.add(provider)
 m.save(dest,dict(at=m.now(),rows=out,stopped_providers=sorted(stopped),script_reference=ref(Path(__file__).resolve()),discovery='Observed redirects and public links,web turn986',policy='Official collection and public catalogue context only. No holding inferred solely from the city-wide museum service. IWM,RCT,ArtUK,Glasgow Navigator and every previous source hold untouched. No images.'))
if __name__=='__main__':main()
